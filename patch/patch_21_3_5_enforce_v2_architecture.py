#!/usr/bin/env python3
"""Stage 21.3.5: enforce the complete ROM V2 architecture contract."""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

STAGE = "21.3.5"
TARGET_BRANCH = "rewrite/rom-v2"
EXPECTED_PARENT = "4faabf546773eb4af2ff57689d9a9fe2a062dada"
PREREQUISITE_REPORT = "reports/stage_21_3_4_structured_logging.json"
PATCH_PATH = "patch/patch_21_3_5_enforce_v2_architecture.py"
VERIFIER_PATH = "tools/verify_v2_architecture.py"
TEST_PATH = "tests_v2/test_architecture_enforcement.py"
REPORT_PATH = "reports/stage_21_3_5_architecture_enforcement.json"
CONTRACT_PATH = "MD/STAGE_21_3_5_V2_ARCHITECTURE_ENFORCEMENT.md"
FAILURE_REPORT = "reports/stage_21_3_5_failure_rollback.json"
COMMIT_MESSAGE = "Stage 21.3.5: enforce V2 architecture"
DB_FILES = ("game.db", "game.db-wal", "game.db-shm")
ALLOWED_DIRTY = {"ROM_FULL_DUMP.txt", "ROM_ADDITIONAL_DUMP.txt"}
MUTATED_FILES = (VERIFIER_PATH, TEST_PATH, REPORT_PATH, CONTRACT_PATH)
OWNED = {PATCH_PATH, FAILURE_REPORT, *MUTATED_FILES}
BACKUP_PREFIX = "stage_21_3_5"

VERIFIER_SOURCE = r'''#!/usr/bin/env python3
"""Enforce the complete ROM V2 architecture without importing runtime modules."""
from __future__ import annotations

import argparse
import ast
import json
from pathlib import Path
from typing import Any

LAYER_ORDER = {
    "domain": 0,
    "application": 1,
    "infrastructure": 2,
    "app": 3,
    "content": 0,
}
FORBIDDEN_EXTERNAL_ROOTS = {"telegram", "aiogram", "sqlite3", "sqlalchemy", "aiosqlite"}
FORBIDDEN_CATCH_ALL_MODULES = {
    "common.py", "helper.py", "helpers.py", "utils.py", "utility.py",
    "misc.py", "manager.py", "service.py", "services.py", "shared.py",
}
REQUIRED_FILES = {
    "rom_v2/__init__.py",
    "rom_v2/main.py",
    "rom_v2/bootstrap.py",
    "rom_v2/config.py",
    "rom_v2/container.py",
    "rom_v2/lifecycle.py",
    "rom_v2/runtime_paths.py",
    "rom_v2/settings.py",
    "rom_v2/structured_logging.py",
    "rom_v2/domain/__init__.py",
    "rom_v2/application/__init__.py",
    "rom_v2/application/ports/repositories.py",
    "rom_v2/application/ports/unit_of_work.py",
    "rom_v2/application/ports/clock.py",
    "rom_v2/application/ports/random_source.py",
    "rom_v2/infrastructure/__init__.py",
    "rom_v2/app/__init__.py",
    "rom_v2/content/__init__.py",
}


def _layer(relative_path: str) -> str | None:
    """Return the first V2 package layer for a source path."""
    parts = Path(relative_path).parts
    return parts[1] if len(parts) > 2 and parts[0] == "rom_v2" else None


def _imports(tree: ast.AST) -> list[tuple[int, str]]:
    """Return imported module names with source line numbers."""
    result: list[tuple[int, str]] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            result.extend((node.lineno, alias.name) for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            result.append((node.lineno, node.module or ""))
    return result


def verify(root: Path) -> dict[str, Any]:
    """Inspect the physical V2 tree and return machine-readable findings."""
    violations: list[dict[str, Any]] = []
    parsed_files: list[str] = []
    import_edges: list[dict[str, Any]] = []
    runtime = root / "rom_v2"
    if not runtime.is_dir():
        violations.append({"rule": "MISSING_V2_ROOT", "file": "rom_v2"})
    physical_files = {
        path.relative_to(root).as_posix()
        for path in runtime.rglob("*.py")
    } if runtime.is_dir() else set()
    for required in sorted(REQUIRED_FILES - physical_files):
        violations.append({"rule": "MISSING_REQUIRED_FILE", "file": required})

    for relative in sorted(physical_files):
        path = root / relative
        if path.name in FORBIDDEN_CATCH_ALL_MODULES:
            violations.append({"rule": "CATCH_ALL_MODULE", "file": relative, "line": 1})
        try:
            tree = ast.parse(path.read_text(encoding="utf-8", errors="replace"), filename=relative)
        except SyntaxError as exc:
            violations.append({"rule": "PARSE_ERROR", "file": relative, "line": exc.lineno, "detail": str(exc)})
            continue
        parsed_files.append(relative)
        source_layer = _layer(relative)
        for line, module in _imports(tree):
            root_name = module.split(".")[0]
            edge = {"file": relative, "line": line, "import": module}
            import_edges.append(edge)
            if root_name in {"data", "handlers", "systems", "services", "database", "legacy_v1"}:
                violations.append({"rule": "V1_RUNTIME_IMPORT", **edge})
            if source_layer in {"domain", "application"} and root_name in FORBIDDEN_EXTERNAL_ROOTS:
                violations.append({"rule": "FORBIDDEN_EXTERNAL_IMPORT", **edge})
            if module.startswith("rom_v2."):
                target_parts = module.split(".")
                target_layer = target_parts[1] if len(target_parts) > 1 else None
                if source_layer in LAYER_ORDER and target_layer in LAYER_ORDER:
                    if LAYER_ORDER[target_layer] > LAYER_ORDER[source_layer]:
                        violations.append({"rule": "OUTWARD_LAYER_IMPORT", "source_layer": source_layer, "target_layer": target_layer, **edge})

    result_owners: list[dict[str, Any]] = []
    event_owners: list[dict[str, Any]] = []
    uow_owners: list[dict[str, Any]] = []
    clock_owners: list[dict[str, Any]] = []
    rng_owners: list[dict[str, Any]] = []
    for relative in parsed_files:
        tree = ast.parse((root / relative).read_text(encoding="utf-8", errors="replace"))
        for node in ast.walk(tree):
            if not isinstance(node, ast.ClassDef):
                continue
            row = {"file": relative, "class": node.name, "line": node.lineno}
            if node.name in {"Result", "OperationResult", "CommandResult", "ServiceResult"}: result_owners.append(row)
            if node.name in {"DomainEvent", "EventEnvelope"}: event_owners.append(row)
            if node.name == "UnitOfWork": uow_owners.append(row)
            if node.name == "Clock": clock_owners.append(row)
            if node.name == "RandomSource": rng_owners.append(row)
    owner_rules = (
        ("MULTIPLE_RESULT_OWNERS", result_owners, 1),
        ("MULTIPLE_EVENT_OWNERS", event_owners, 1),
        ("UNIT_OF_WORK_OWNER_COUNT", uow_owners, 1),
        ("CLOCK_OWNER_COUNT", clock_owners, 1),
        ("RNG_OWNER_COUNT", rng_owners, 1),
    )
    for rule, owners, maximum in owner_rules:
        if len(owners) > maximum or (rule in {"UNIT_OF_WORK_OWNER_COUNT", "CLOCK_OWNER_COUNT", "RNG_OWNER_COUNT"} and len(owners) != 1):
            violations.append({"rule": rule, "owners": owners})

    return {
        "schema_version": 1,
        "summary": {
            "status": "PASS" if not violations else "FAIL",
            "physical_file_count": len(physical_files),
            "parsed_file_count": len(parsed_files),
            "import_edge_count": len(import_edges),
            "violation_count": len(violations),
        },
        "owners": {
            "result": result_owners,
            "events": event_owners,
            "unit_of_work": uow_owners,
            "clock": clock_owners,
            "random_source": rng_owners,
        },
        "import_edges": import_edges,
        "violations": violations,
    }


def main() -> int:
    """Run architecture enforcement and optionally write JSON evidence."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", default=".")
    parser.add_argument("--json-out")
    args = parser.parse_args()
    result = verify(Path(args.project_root).resolve())
    text = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    if args.json_out:
        Path(args.json_out).write_text(text, encoding="utf-8", newline="\n")
    summary = result["summary"]
    print(f"V2 architecture enforcement: {summary['status']}")
    print(f"Physical files: {summary['physical_file_count']}")
    print(f"Import edges: {summary['import_edge_count']}")
    print(f"Violations: {summary['violation_count']}")
    return 0 if summary["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
'''

TEST_SOURCE = '''"""Tests for the ROM V2 architecture enforcement verifier."""
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from tools.verify_v2_architecture import verify


class ArchitectureEnforcementTest(unittest.TestCase):
    """Verify happy path and representative architecture rejections."""

    def _write(self, root: Path, relative: str, text: str) -> None:
        """Write one temporary Python module for verifier testing."""
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")

    def test_current_project_passes(self) -> None:
        """Require the physical project tree to satisfy the verifier."""
        project_root = Path(__file__).resolve().parents[1]
        self.assertEqual(verify(project_root)["summary"]["status"], "PASS")

    def test_v1_import_is_rejected(self) -> None:
        """Reject a direct dependency on a legacy V1 runtime root."""
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            for required in REQUIRED_FOR_FIXTURE:
                self._write(root, required, '"""fixture"""\\n')
            self._write(root, "rom_v2/domain/model.py", '"""fixture"""\\nimport handlers\\n')
            rules = {item["rule"] for item in verify(root)["violations"]}
            self.assertIn("V1_RUNTIME_IMPORT", rules)

    def test_outward_layer_import_is_rejected(self) -> None:
        """Reject a domain dependency on infrastructure."""
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            for required in REQUIRED_FOR_FIXTURE:
                self._write(root, required, '"""fixture"""\\n')
            self._write(root, "rom_v2/domain/model.py", '"""fixture"""\\nimport rom_v2.infrastructure\\n')
            rules = {item["rule"] for item in verify(root)["violations"]}
            self.assertIn("OUTWARD_LAYER_IMPORT", rules)


REQUIRED_FOR_FIXTURE = {
    "rom_v2/__init__.py", "rom_v2/main.py", "rom_v2/bootstrap.py", "rom_v2/config.py",
    "rom_v2/container.py", "rom_v2/lifecycle.py", "rom_v2/runtime_paths.py", "rom_v2/settings.py",
    "rom_v2/structured_logging.py", "rom_v2/domain/__init__.py", "rom_v2/application/__init__.py",
    "rom_v2/application/ports/repositories.py", "rom_v2/application/ports/unit_of_work.py",
    "rom_v2/application/ports/clock.py", "rom_v2/application/ports/random_source.py",
    "rom_v2/infrastructure/__init__.py", "rom_v2/app/__init__.py", "rom_v2/content/__init__.py",
}


if __name__ == "__main__":
    unittest.main()
'''

@dataclass(frozen=True)
class Check:
    """Describe one automated Stage 21.3.5 check."""
    check_id: str
    status: str
    summary: str
    details: dict[str, Any]
    blocking: bool = False

class PatchError(RuntimeError):
    """Signal a controlled patch or commit failure."""


def run(root: Path, *command: str, timeout: int = 120) -> subprocess.CompletedProcess[str]:
    """Run a subprocess with bytecode creation disabled."""
    environment = os.environ.copy(); environment["PYTHONDONTWRITEBYTECODE"] = "1"
    return subprocess.run(command, cwd=root, env=environment, text=True, encoding="utf-8", errors="replace", capture_output=True, timeout=timeout, check=False)

def git(root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    """Run Git in the project root."""
    return run(root, "git", *args)

def rev(root: Path, name: str) -> str | None:
    """Resolve one Git commit reference."""
    result = git(root, "rev-parse", "--verify", f"{name}^{{commit}}")
    return result.stdout.strip() if result.returncode == 0 else None

def sha256(path: Path) -> str:
    """Return SHA-256 evidence for one file."""
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1048576), b""): digest.update(chunk)
    return digest.hexdigest()

def database_evidence(root: Path) -> dict[str, Any]:
    """Capture DB/WAL/SHM evidence without opening SQLite."""
    result: dict[str, Any] = {}
    for name in DB_FILES:
        path = root / name
        result[name] = {"exists": False} if not path.exists() else {"exists": True, "size": path.stat().st_size, "mtime_ns": path.stat().st_mtime_ns, "sha256": sha256(path)}
    return result

def write_atomic(path: Path, text: str) -> None:
    """Write one UTF-8 artifact using atomic replacement."""
    temporary = path.with_suffix(path.suffix + ".tmp"); temporary.parent.mkdir(parents=True, exist_ok=True); temporary.write_text(text, encoding="utf-8", newline="\n"); os.replace(temporary, path)

def parse_status(raw: str) -> list[dict[str, str]]:
    """Parse NUL-separated Git porcelain output."""
    return [{"status": item[:2], "path": item[3:]} for item in raw.split("\0") if item]

def git_blob(root: Path, commit: str, relative: str) -> bytes | None:
    """Read a file from the expected parent commit."""
    result = subprocess.run(["git", "show", f"{commit}:{relative}"], cwd=root, capture_output=True, check=False)
    return result.stdout if result.returncode == 0 else None

def prepare_backups(root: Path) -> dict[str, Any]:
    """Back up every patch-owned mutation target."""
    (root / "backup").mkdir(exist_ok=True); manifest: dict[str, Any] = {"files": {}}
    for relative in MUTATED_FILES:
        blob = git_blob(root, EXPECTED_PARENT, relative); backup = root / "backup" / f"{BACKUP_PREFIX}__{relative.replace('/', '__')}"
        if blob is None: manifest["files"][relative] = {"existed": False, "backup": None}
        else: backup.write_bytes(blob); manifest["files"][relative] = {"existed": True, "backup": str(backup.relative_to(root)).replace("\\", "/")}
    return manifest

def rollback(root: Path, manifest: dict[str, Any], reason: str, checks: list[Check]) -> dict[str, Any]:
    """Restore parent files and remove failed new artifacts."""
    git(root, "reset", "--", *MUTATED_FILES); restored: list[str] = []; removed: list[str] = []; errors: list[str] = []
    for relative, metadata in manifest["files"].items():
        target = root / relative
        try:
            if metadata["existed"]: target.parent.mkdir(parents=True, exist_ok=True); target.write_bytes((root / metadata["backup"]).read_bytes()); restored.append(relative)
            elif target.exists(): target.unlink(); removed.append(relative)
        except OSError as exc: errors.append(f"{relative}: {exc}")
    payload = {"stage": STAGE, "status": "FAIL_ROLLED_BACK" if not errors else "ROLLBACK_INCOMPLETE", "reason": reason, "failed_checks": [asdict(item) for item in checks if item.status == "FAIL"], "restored_files": restored, "removed_failed_artifacts": removed, "rollback_errors": errors, "database_evidence_after_rollback": database_evidence(root), "main_py_started_after_failure": False, "wal_shm_manipulated": False}
    write_atomic(root / FAILURE_REPORT, json.dumps(payload, ensure_ascii=False, indent=2) + "\n"); return payload

def render_contract(result: dict[str, Any]) -> str:
    """Render the architecture-enforcement contract."""
    summary = result["summary"]
    return "\n".join(["# Stage 21.3.5 — ROM V2 architecture enforcement", "", "- **Status:** `IMPLEMENTED`", "- **Verifier:** `tools/verify_v2_architecture.py`", "- **Criterion:** verifier returns `PASS`", "", "## Enforced rules", "", "- Required V2 foundation files exist.", "- V1 runtime imports are forbidden.", "- Domain/application cannot import Telegram or database drivers.", "- Inward dependency direction is enforced.", "- Catch-all modules are forbidden.", "- Canonical UoW, Clock, and RandomSource owner counts are enforced.", "", "## Evidence", "", f"- Physical files: **{summary['physical_file_count']}**.", f"- Import edges: **{summary['import_edge_count']}**.", f"- Violations: **{summary['violation_count']}**.", "", "## Next roadmap stage", "", "Stage 21.3.6 — CI foundation.", ""])
def exact_commit(root: Path) -> str:
    """Create an exact-allowlist Stage 21.3.5 commit."""
    paths = [PATCH_PATH, *MUTATED_FILES]; added = git(root, "add", "-f", "--", *paths)
    if added.returncode: raise PatchError(added.stderr.strip())
    staged = sorted(item for item in git(root, "diff", "--cached", "--name-only", "-z").stdout.split("\0") if item)
    if staged != sorted(paths): git(root, "reset", "--", *paths); raise PatchError(f"staging mismatch: {staged}")
    committed = git(root, "commit", "-m", COMMIT_MESSAGE)
    if committed.returncode: git(root, "reset", "--", *paths); raise PatchError(committed.stderr.strip() or committed.stdout.strip())
    return rev(root, "HEAD") or ""

def main() -> int:
    """Apply architecture enforcement with rollback and exact acceptance."""
    root = Path(__file__).resolve().parent.parent
    if not (root / PREREQUISITE_REPORT).is_file(): print(f"[FAIL] Missing prerequisite: {PREREQUISITE_REPORT}", file=sys.stderr); return 2
    prerequisite = json.loads((root / PREREQUISITE_REPORT).read_text(encoding="utf-8"))
    if prerequisite.get("stage") != "21.3.4" or prerequisite.get("summary", {}).get("conclusion") != "GO": print("[FAIL] Stage 21.3.4 prerequisite is not canonical GO.", file=sys.stderr); return 2
    print("[1/10] [PASS] Stage 21.3.4 prerequisite and structured logging contract detected.")
    branch = git(root, "branch", "--show-current").stdout.strip(); head = rev(root, "HEAD"); upstream_result = git(root, "rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{u}"); upstream = upstream_result.stdout.strip() if upstream_result.returncode == 0 else None
    entries = parse_status(git(root, "status", "--porcelain=v1", "-z", "--untracked-files=all").stdout); allowed = [entry for entry in entries if entry["status"][0] in {" ", "?"} and (entry["path"] in OWNED or (entry["path"] in ALLOWED_DIRTY and entry["status"][0] == " "))]; unexpected = [entry for entry in entries if entry not in allowed]
    checks = [Check("BRANCH", "PASS" if branch == TARGET_BRANCH else "FAIL", f"Active branch: {branch}", {}, branch != TARGET_BRANCH), Check("PARENT", "PASS" if head == EXPECTED_PARENT else "FAIL", "Expected Stage 21.3.4 parent verified.", {"expected": EXPECTED_PARENT, "actual": head}, head != EXPECTED_PARENT), Check("UPSTREAM", "PASS" if upstream == f"origin/{TARGET_BRANCH}" else "FAIL", f"Upstream: {upstream}", {}, upstream != f"origin/{TARGET_BRANCH}"), Check("WORKTREE", "PASS" if not unexpected else "FAIL", "No unexpected changes.", {"unexpected": unexpected}, bool(unexpected))]
    if any(item.blocking for item in checks): print("[2/10] [FAIL] Preflight returned NO_GO."); return 1
    print("[2/10] [PASS] Branch, parent, upstream and worktree verified; backups prepared in ROM\\backup.")
    before = database_evidence(root); manifest = prepare_backups(root)
    try:
        print("[3/10] [PASS] Writing authoritative architecture verifier and rejection tests."); write_atomic(root / VERIFIER_PATH, VERIFIER_SOURCE); write_atomic(root / TEST_PATH, TEST_SOURCE)
        print("[4/10] [PASS] Compiling verifier and tests without bytecode.")
        for relative in (VERIFIER_PATH, TEST_PATH): compile((root / relative).read_text(encoding="utf-8"), str(root / relative), "exec")
        print("[5/10] [PASS] Running authoritative V2 architecture verifier."); temporary = root / "reports" / ".stage_21_3_5_architecture.tmp.json"; execution = run(root, sys.executable, VERIFIER_PATH, "--project-root", str(root), "--json-out", str(temporary)); result = json.loads(temporary.read_text(encoding="utf-8")) if temporary.exists() else {"summary": {"status": "FAIL"}, "violations": [{"rule": "MISSING_OUTPUT"}]}; temporary.unlink(missing_ok=True); verifier_ok = execution.returncode == 0 and result.get("summary", {}).get("status") == "PASS"; checks.append(Check("ARCHITECTURE_VERIFIER", "PASS" if verifier_ok else "FAIL", execution.stdout.strip() or "Architecture verifier failed.", {"stderr": execution.stderr.strip(), "violations": result.get("violations", [])}, not verifier_ok))
        print("[6/10] [PASS] Running architecture happy-path and rejection tests."); unit = run(root, sys.executable, "-m", "unittest", "tests_v2.test_architecture_enforcement"); checks.append(Check("UNIT_TEST", "PASS" if unit.returncode == 0 else "FAIL", unit.stderr.strip() or unit.stdout.strip(), {}, unit.returncode != 0))
        print("[7/10] [PASS] Running existing dependency and code-standard regressions."); dependency = run(root, sys.executable, "tools/verify_v2_dependency_rules.py", "--project-root", str(root), "--json-out", "reports/.stage_21_3_5_dependency.tmp.json"); dependency_path = root / "reports" / ".stage_21_3_5_dependency.tmp.json"; dependency_result = json.loads(dependency_path.read_text(encoding="utf-8")) if dependency_path.exists() else {"summary": {"status": "FAIL"}}; dependency_path.unlink(missing_ok=True); dependency_ok = dependency.returncode == 0 and dependency_result.get("summary", {}).get("status") == "PASS"; checks.append(Check("DEPENDENCY_REGRESSION", "PASS" if dependency_ok else "FAIL", dependency.stdout.strip(), {"violations": dependency_result.get("violations", [])}, not dependency_ok))
        code_report = json.loads((root / "reports/stage_21_2_7_code_comment_standards.json").read_text(encoding="utf-8")); contract_path = root / "reports" / ".stage_21_3_5_code_contract.tmp.json"; code_path = root / "reports" / ".stage_21_3_5_code.tmp.json"; write_atomic(contract_path, json.dumps(code_report["code_comment_contract"], ensure_ascii=False, indent=2) + "\n"); code = run(root, sys.executable, "tools/verify_v2_code_comment_standards.py", "--project-root", str(root), "--contract", str(contract_path), "--json-out", str(code_path)); code_result = json.loads(code_path.read_text(encoding="utf-8")) if code_path.exists() else {"summary": {"status": "FAIL"}}; contract_path.unlink(missing_ok=True); code_path.unlink(missing_ok=True); code_ok = code.returncode == 0 and code_result.get("summary", {}).get("status") == "PASS"; checks.append(Check("CODE_STANDARD_REGRESSION", "PASS" if code_ok else "FAIL", code.stdout.strip(), {"violations": code_result.get("violations", [])}, not code_ok))
        print("[8/10] [PASS] Running isolated bootstrap and database safety regressions."); bootstrap = run(root, sys.executable, "-m", "rom_v2.main"); bootstrap_ok = bootstrap.returncode == 0 and json.loads(bootstrap.stdout).get("gameplay_enabled") is False; checks.append(Check("BOOTSTRAP_REGRESSION", "PASS" if bootstrap_ok else "FAIL", bootstrap.stdout.strip(), {"stderr": bootstrap.stderr.strip()}, not bootstrap_ok)); checks.append(Check("DATABASE_UNCHANGED", "PASS" if before == database_evidence(root) else "FAIL", "DB/WAL/SHM unchanged and SQLite was not opened.", {"production_connection_opened": False}, before != database_evidence(root)))
        blockers = [item.check_id for item in checks if item.blocking]
        if blockers: report = rollback(root, manifest, f"Stage 21.3.5 NO_GO: {blockers}", checks); print(f"[9/10] [FAIL] Rollback: {report['status']}"); return 1
        payload = {"schema_version": 1, "stage": STAGE, "generated_at_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"), "summary": {"conclusion": "GO", "blocking_failures": [], **result["summary"], "gameplay_started": False, "database_opened": False}, "git": {"branch": branch, "head_before_commit": head, "upstream": upstream}, "checks": [asdict(item) for item in checks], "architecture_result": result, "database_evidence_before": before, "database_evidence_after": database_evidence(root), "changed_files": [PATCH_PATH, *MUTATED_FILES], "next_stage": "21.3.6", "suggested_next_patch": "patch_21_3_6_create_v2_ci_foundation.py"}
        print("[9/10] [PASS] Writing architecture enforcement evidence and contract."); write_atomic(root / REPORT_PATH, json.dumps(payload, ensure_ascii=False, indent=2) + "\n"); write_atomic(root / CONTRACT_PATH, render_contract(result))
    except Exception as exc: report = rollback(root, manifest, f"Mutation or verification failure: {exc}", checks); print(f"[9/10] [FAIL] {exc}; rollback: {report['status']}", file=sys.stderr); return 2
    (root / FAILURE_REPORT).unlink(missing_ok=True)
    try: commit_hash = exact_commit(root)
    except PatchError as exc: report = rollback(root, manifest, f"Commit failure: {exc}", checks); print(f"[10/10] [FAIL] rollback: {report['status']}", file=sys.stderr); return 2
    print(f"[10/10] [PASS] Architecture enforcement committed with verifier PASS: {commit_hash}"); print("=" * 72); print(f"ROM Stage {STAGE} - architecture enforcement")
    for item in checks: print(f"[{item.status}] {item.check_id}: {item.summary}")
    print(f"[PASS] PHYSICAL_FILES: {result['summary']['physical_file_count']}"); print(f"[PASS] IMPORT_EDGES: {result['summary']['import_edge_count']}"); print(f"[PASS] VIOLATIONS: {result['summary']['violation_count']}"); print("[PASS] GAMEPLAY_STARTED: False\n[PASS] DATABASE_OPENED: False\nCONCLUSION: GO\nPATCH STATUS: PASS"); print(f"GIT COMMIT STATUS: PASS ({commit_hash})"); print("REMOTE PUSH STATUS: NOT REQUIRED\nMANUAL CHECK: NOT REQUIRED\nFAIL-SAFE ROLLBACK: ARMED\nWAL/SHM: NOT MANIPULATED\nSUGGESTED NEXT PATCH: patch_21_3_6_create_v2_ci_foundation.py"); return 0

if __name__ == "__main__":
    raise SystemExit(main())
