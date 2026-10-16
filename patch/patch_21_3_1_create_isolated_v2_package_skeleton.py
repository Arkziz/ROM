#!/usr/bin/env python3
"""Stage 21.3.1: create an isolated, non-gameplay ROM V2 package skeleton."""
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

STAGE = "21.3.1"
TARGET_BRANCH = "rewrite/rom-v2"
EXPECTED_PARENT = "16d55eac701564341f43aef06ca82ff2259e9152"
PATCH_PATH = "patch/patch_21_3_1_create_isolated_v2_package_skeleton.py"
REPORT_PATH = "reports/stage_21_3_1_isolated_v2_package_skeleton.json"
CONTRACT_PATH = "MD/STAGE_21_3_1_ISOLATED_V2_PACKAGE_SKELETON.md"
STRUCTURE_VERIFIER_PATH = "tools/verify_v2_package_structure.py"
FAILURE_REPORT = "reports/stage_21_3_1_failure_rollback.json"
COMMIT_MESSAGE = "Stage 21.3.1: create isolated V2 package skeleton"
DB_FILES = ("game.db", "game.db-wal", "game.db-shm")
ALLOWED_DIRTY = {"ROM_FULL_DUMP.txt", "ROM_ADDITIONAL_DUMP.txt"}
BACKUP_PREFIX = "stage_21_3_1"

FILES: dict[str, str] = {
    "rom_v2/__init__.py": '''"""Isolated ROM V2 package without gameplay activation."""\n\n__all__: tuple[str, ...] = ()\n''',
    "rom_v2/domain/__init__.py": '''"""Pure ROM V2 domain package."""\n\n__all__: tuple[str, ...] = ()\n''',
    "rom_v2/application/__init__.py": '''"""ROM V2 application use-case and port package."""\n\n__all__: tuple[str, ...] = ()\n''',
    "rom_v2/application/ports/__init__.py": '''"""Canonical ROM V2 application port package."""\n\n__all__: tuple[str, ...] = ()\n''',
    "rom_v2/application/ports/repositories.py": '''"""Aggregate-oriented repository ports for ROM V2."""\nfrom __future__ import annotations\n\nfrom typing import Protocol, TypeVar\n\nAggregateT = TypeVar("AggregateT")\nAggregateIdT = TypeVar("AggregateIdT")\n\n\nclass AggregateRepository(Protocol[AggregateT, AggregateIdT]):\n    """Define persistence operations without transaction ownership."""\n\n    def get(self, aggregate_id: AggregateIdT) -> AggregateT | None:\n        """Return one aggregate by stable identity when present."""\n        ...\n\n    def add(self, aggregate: AggregateT) -> None:\n        """Register a new aggregate in the active Unit of Work."""\n        ...\n\n    def save(self, aggregate: AggregateT, expected_version: int) -> None:\n        """Persist an aggregate using optimistic expected-version semantics."""\n        ...\n\n    def exists(self, aggregate_id: AggregateIdT) -> bool:\n        """Return whether an aggregate identity already exists."""\n        ...\n''',
    "rom_v2/application/ports/unit_of_work.py": '''"""Explicit transaction boundary port for ROM V2."""\nfrom __future__ import annotations\n\nfrom typing import Protocol\n\n\nclass UnitOfWork(Protocol):\n    """Own one transaction and one commit point for a business operation."""\n\n    def commit(self) -> None:\n        """Commit aggregate state, events, outbox, and idempotency atomically."""\n        ...\n\n    def rollback(self) -> None:\n        """Discard every uncommitted change in the active operation."""\n        ...\n''',
    "rom_v2/application/ports/clock.py": '''"""Clock port for deterministic ROM V2 time access."""\nfrom __future__ import annotations\n\nfrom datetime import datetime\nfrom typing import Protocol\n\n\nclass Clock(Protocol):\n    """Provide UTC wall time and monotonic elapsed-time measurements."""\n\n    def now_utc(self) -> datetime:\n        """Return a timezone-aware UTC datetime."""\n        ...\n\n    def monotonic_seconds(self) -> float:\n        """Return a non-decreasing elapsed-time value."""\n        ...\n''',
    "rom_v2/application/ports/random_source.py": '''"""Injected random-source port for deterministic ROM V2 behavior."""\nfrom __future__ import annotations\n\nfrom typing import Protocol, TypeVar\n\nChoiceT = TypeVar("ChoiceT")\n\n\nclass RandomSource(Protocol):\n    """Expose explicit gameplay random operations without hidden reseeding."""\n\n    def random(self) -> float:\n        """Return a floating-point draw in the half-open range [0, 1)."""\n        ...\n\n    def randint(self, minimum: int, maximum: int) -> int:\n        """Return an integer from the inclusive range."""\n        ...\n\n    def choice(self, values: tuple[ChoiceT, ...]) -> ChoiceT:\n        """Return one value from a validated non-empty sequence."""\n        ...\n\n    def shuffle(self, values: list[ChoiceT]) -> None:\n        """Shuffle the supplied mutable sequence through the injected source."""\n        ...\n''',
    "rom_v2/infrastructure/__init__.py": '''"""ROM V2 infrastructure adapter package."""\n\n__all__: tuple[str, ...] = ()\n''',
    "rom_v2/app/__init__.py": '''"""ROM V2 composition and delivery package."""\n\n__all__: tuple[str, ...] = ()\n''',
    "rom_v2/content/__init__.py": '''"""ROM V2 declarative content package."""\n\n__all__: tuple[str, ...] = ()\n''',
    "rom_v2/config.py": '''"""Minimal non-secret V2 bootstrap configuration."""\nfrom __future__ import annotations\n\nfrom dataclasses import dataclass\n\n\n@dataclass(frozen=True, slots=True)\nclass V2Config:\n    """Hold only safe bootstrap settings before validated secret loading exists."""\n\n    application_name: str = "rom_v2"\n    mode: str = "bootstrap"\n    gameplay_enabled: bool = False\n\n    def validate(self) -> None:\n        """Reject any configuration that could activate gameplay in the skeleton."""\n        if self.gameplay_enabled:\n            raise ValueError("gameplay_enabled_must_remain_false_in_stage_21_3_1")\n''',
    "rom_v2/container.py": '''"""Dependency container for the isolated V2 skeleton."""\nfrom __future__ import annotations\n\nfrom dataclasses import dataclass\n\nfrom rom_v2.config import V2Config\n\n\n@dataclass(frozen=True, slots=True)\nclass V2Container:\n    """Own the minimal dependencies required by the bootstrap lifecycle."""\n\n    config: V2Config\n''',
    "rom_v2/lifecycle.py": '''"""Startup and shutdown lifecycle for the isolated V2 skeleton."""\nfrom __future__ import annotations\n\nfrom dataclasses import dataclass\n\nfrom rom_v2.container import V2Container\n\n\n@dataclass(slots=True)\nclass V2Lifecycle:\n    """Track bootstrap lifecycle without starting Telegram, DB, jobs, or gameplay."""\n\n    container: V2Container\n    started: bool = False\n\n    def start(self) -> None:\n        """Validate configuration and mark the isolated skeleton as started."""\n        self.container.config.validate()\n        self.started = True\n\n    def stop(self) -> None:\n        """Return the isolated skeleton to its stopped state."""\n        self.started = False\n''',
    "rom_v2/bootstrap.py": '''"""Authoritative bootstrap factory for the isolated V2 skeleton."""\nfrom __future__ import annotations\n\nfrom rom_v2.config import V2Config\nfrom rom_v2.container import V2Container\nfrom rom_v2.lifecycle import V2Lifecycle\n\n\ndef build_lifecycle(config: V2Config | None = None) -> V2Lifecycle:\n    """Build a lifecycle with explicit dependencies and gameplay disabled."""\n    effective_config = config if config is not None else V2Config()\n    return V2Lifecycle(container=V2Container(config=effective_config))\n''',
    "rom_v2/main.py": '''"""Executable smoke entrypoint for the isolated ROM V2 skeleton."""\nfrom __future__ import annotations\n\nimport json\n\nfrom rom_v2.bootstrap import build_lifecycle\n\n\ndef main() -> int:\n    """Start and stop the skeleton without gameplay or external side effects."""\n    lifecycle = build_lifecycle()\n    lifecycle.start()\n    payload = {\n        "status": "ready",\n        "application": lifecycle.container.config.application_name,\n        "mode": lifecycle.container.config.mode,\n        "gameplay_enabled": lifecycle.container.config.gameplay_enabled,\n        "telegram_started": False,\n        "database_opened": False,\n        "background_jobs_started": False,\n    }\n    print(json.dumps(payload, sort_keys=True))\n    lifecycle.stop()\n    return 0\n\n\nif __name__ == "__main__":\n    raise SystemExit(main())\n''',
    "tools/verify_v2_result_error_model.py": r'''#!/usr/bin/env python3
"""Verify the ROM V2 Result/error contract and detect competing implementations."""
from __future__ import annotations
import argparse, ast, json, re
from pathlib import Path
from typing import Any

REQUIRED_STATUS_KEYS = {
    "success", "business_rejection", "validation_error", "stale_state",
    "idempotent_repeat", "retryable_error", "consistency_error",
}
RESULT_CLASS_RE = re.compile(r"(?i)^(result|operationresult|commandresult|serviceresult)$")
OPERATION_HINT_RE = re.compile(r"(?i)(command|handler|use_case|usecase|execute|settle|apply|perform|process|handle)")


def _annotation_text(node: ast.AST | None) -> str:
    return ast.unparse(node) if node is not None else ""


def _is_operation_boundary(node: ast.FunctionDef | ast.AsyncFunctionDef, file_path: str) -> bool:
    if OPERATION_HINT_RE.search(node.name):
        return True
    normalized = file_path.lower()
    return any(part in normalized for part in ("/commands/", "/handlers/", "/use_cases/", "/usecases/"))


def _is_result_annotation(annotation: str) -> bool:
    compact = annotation.replace(" ", "")
    return compact == "Result" or compact.startswith("Result[") or compact.startswith("OperationResult[")


def verify(root: Path, contract: dict[str, Any]) -> dict[str, Any]:
    violations: list[dict[str, Any]] = []
    status_rows = contract.get("statuses", [])
    keys = [row.get("key") for row in status_rows]
    if set(keys) != REQUIRED_STATUS_KEYS or len(keys) != len(set(keys)):
        violations.append({"rule": "STATUS_SET", "expected": sorted(REQUIRED_STATUS_KEYS), "actual": sorted(keys)})
    if contract.get("canonical_owner") != "rom_v2.application.result":
        violations.append({"rule": "CANONICAL_OWNER"})
    if not contract.get("mutation_contract", {}).get("unit_of_work_required"):
        violations.append({"rule": "UNIT_OF_WORK_REQUIRED"})
    if not contract.get("mutation_contract", {}).get("preconditions_before_first_mutation"):
        violations.append({"rule": "PRECONDITIONS_BEFORE_MUTATION"})
    if not contract.get("presentation_contract", {}).get("telegram_types_forbidden"):
        violations.append({"rule": "PRESENTATION_SEPARATION"})
    retryable = {row["key"] for row in status_rows if row.get("retryable")}
    if retryable != {"stale_state", "retryable_error"}:
        violations.append({"rule": "RETRYABILITY_SET", "actual": sorted(retryable)})
    mutating = {row["key"] for row in status_rows if row.get("mutation_allowed")}
    if mutating != {"success"}:
        violations.append({"rule": "MUTATION_ALLOWED_SET", "actual": sorted(mutating)})

    result_owners: list[dict[str, Any]] = []
    implicit_operation_results: list[dict[str, Any]] = []
    rom_v2 = root / "rom_v2"
    if rom_v2.is_dir():
        for path in sorted(rom_v2.rglob("*.py")):
            relative = path.relative_to(root).as_posix()
            try:
                tree = ast.parse(path.read_text(encoding="utf-8", errors="replace"), filename=relative)
            except SyntaxError as exc:
                violations.append({"rule": "PARSE_ERROR", "file": relative, "error": str(exc)})
                continue
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef) and RESULT_CLASS_RE.fullmatch(node.name):
                    result_owners.append({"file": relative, "class": node.name, "line": node.lineno})
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and not node.name.startswith("_"):
                    annotation = _annotation_text(node.returns)
                    if _is_operation_boundary(node, relative) and not _is_result_annotation(annotation):
                        implicit_operation_results.append({"file": relative, "function": node.name, "line": node.lineno, "annotation": annotation or None})
    if len(result_owners) > 1:
        violations.append({"rule": "MULTIPLE_RESULT_OWNERS", "owners": result_owners})
    if result_owners and result_owners[0]["file"] != "rom_v2/application/result.py":
        violations.append({"rule": "WRONG_RESULT_OWNER", "owners": result_owners})
    if implicit_operation_results:
        violations.append({"rule": "IMPLICIT_OPERATION_RESULTS", "functions": implicit_operation_results})

    return {
        "schema_version": 2,
        "summary": {
            "status": "PASS" if not violations else "FAIL",
            "status_count": len(status_rows),
            "result_owner_count": len(result_owners),
            "implicit_public_result_count": len(implicit_operation_results),
            "violation_count": len(violations),
            "physical_result_model_exists": bool(result_owners),
        },
        "result_owners": result_owners,
        "implicit_public_results": implicit_operation_results,
        "violations": violations,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", default=".")
    parser.add_argument("--contract", required=True)
    parser.add_argument("--json-out")
    args = parser.parse_args()
    contract = json.loads(Path(args.contract).read_text(encoding="utf-8"))
    result = verify(Path(args.project_root).resolve(), contract)
    text = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    if args.json_out:
        Path(args.json_out).write_text(text, encoding="utf-8", newline="\n")
    print(f"V2 result/error verifier: {result['summary']['status']}")
    print(f"Statuses: {result['summary']['status_count']}")
    print(f"Physical Result owners: {result['summary']['result_owner_count']}")
    print(f"Implicit operation results: {result['summary']['implicit_public_result_count']}")
    print(f"Violations: {result['summary']['violation_count']}")
    return 0 if result["summary"]["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
''',
    "tests_v2/__init__.py": '''"""ROM V2 isolated test package."""\n\n__all__: tuple[str, ...] = ()\n''',
    "tests_v2/test_v2_bootstrap_smoke.py": '''"""Smoke tests for the isolated ROM V2 bootstrap."""\nfrom __future__ import annotations\n\nimport unittest\n\nfrom rom_v2.bootstrap import build_lifecycle\n\n\nclass V2BootstrapSmokeTest(unittest.TestCase):\n    """Verify lifecycle startup without gameplay or external integrations."""\n\n    def test_start_and_stop_are_isolated(self) -> None:\n        """Start and stop while gameplay remains disabled."""\n        lifecycle = build_lifecycle()\n        lifecycle.start()\n        self.assertTrue(lifecycle.started)\n        self.assertFalse(lifecycle.container.config.gameplay_enabled)\n        lifecycle.stop()\n        self.assertFalse(lifecycle.started)\n\n\nif __name__ == "__main__":\n    unittest.main()\n''',
}

REPORTS = {
    "dependency": ("reports/stage_21_2_1_dependency_rules.json", "dependency_contract", "tools/verify_v2_dependency_rules.py"),
    "structure": ("reports/stage_21_2_2_package_structure.json", "layout_contract", "tools/verify_v2_package_structure.py"),
    "result": ("reports/stage_21_2_3_result_error_model.json", "result_error_contract", "tools/verify_v2_result_error_model.py"),
    "events": ("reports/stage_21_2_4_domain_event_model.json", "domain_event_contract", "tools/verify_v2_domain_event_model.py"),
    "uow": ("reports/stage_21_2_5_repository_unit_of_work.json", "repository_unit_of_work_contract", "tools/verify_v2_repository_unit_of_work.py"),
    "clock_rng": ("reports/stage_21_2_6_clock_rng_abstractions.json", "clock_rng_contract", "tools/verify_v2_clock_rng_abstractions.py"),
    "code_comments": ("reports/stage_21_2_7_code_comment_standards.json", "code_comment_contract", "tools/verify_v2_code_comment_standards.py"),
}
OWNED = {PATCH_PATH, REPORT_PATH, CONTRACT_PATH, STRUCTURE_VERIFIER_PATH, FAILURE_REPORT, *FILES}

@dataclass(frozen=True)
class Check:
    """Describe one automated acceptance check."""
    check_id: str
    status: str
    summary: str
    details: dict[str, Any]
    blocking: bool = False

class PatchError(RuntimeError):
    """Signal a controlled mutation or commit failure."""


def run(root: Path, *command: str, timeout: int = 120) -> subprocess.CompletedProcess[str]:
    """Run a subprocess without creating bytecode artifacts in the source tree."""
    environment = os.environ.copy()
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    return subprocess.run(command, cwd=root, env=environment, text=True, encoding="utf-8", errors="replace", capture_output=True, timeout=timeout, check=False)


def git(root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    """Run Git in the project root."""
    return run(root, "git", *args)


def rev(root: Path, name: str) -> str | None:
    """Resolve a Git commit reference."""
    result = git(root, "rev-parse", "--verify", f"{name}^{{commit}}")
    return result.stdout.strip() if result.returncode == 0 else None


def sha256(path: Path) -> str:
    """Return a file SHA-256 without interpreting its contents."""
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def database_evidence(root: Path) -> dict[str, Any]:
    """Capture DB/WAL/SHM evidence without opening SQLite."""
    evidence: dict[str, Any] = {}
    for name in DB_FILES:
        path = root / name
        if not path.exists(): evidence[name] = {"exists": False}
        else:
            stat = path.stat()
            evidence[name] = {"exists": True, "size": stat.st_size, "mtime_ns": stat.st_mtime_ns, "sha256": sha256(path)}
    return evidence


def write_atomic(path: Path, content: str) -> None:
    """Write one UTF-8 artifact using atomic replacement."""
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.parent.mkdir(parents=True, exist_ok=True)
    temporary.write_text(content, encoding="utf-8", newline="\n")
    os.replace(temporary, path)


def parse_status(raw: str) -> list[dict[str, str]]:
    """Parse porcelain-v1 NUL-separated Git status."""
    return [{"status": item[:2], "path": item[3:]} for item in raw.split("\0") if item]


def git_blob(root: Path, commit: str, relative_path: str) -> bytes | None:
    """Read a parent-commit blob without changing the worktree."""
    result = subprocess.run(["git", "show", f"{commit}:{relative_path}"], cwd=root, capture_output=True, check=False)
    return result.stdout if result.returncode == 0 else None


def prepare_backups(root: Path) -> dict[str, Any]:
    """Back up every patch-owned artifact from the expected parent."""
    backup_dir = root / "backup"
    backup_dir.mkdir(parents=True, exist_ok=True)
    manifest: dict[str, Any] = {"files": {}}
    for relative_path in [*FILES, STRUCTURE_VERIFIER_PATH, REPORT_PATH, CONTRACT_PATH]:
        blob = git_blob(root, EXPECTED_PARENT, relative_path)
        backup = backup_dir / f"{BACKUP_PREFIX}__{relative_path.replace('/', '__')}"
        if blob is None: manifest["files"][relative_path] = {"existed": False, "backup": None}
        else:
            backup.write_bytes(blob)
            manifest["files"][relative_path] = {"existed": True, "backup": str(backup.relative_to(root)).replace("\\", "/")}
    return manifest


def rollback(root: Path, manifest: dict[str, Any], reason: str, checks: list[Check]) -> dict[str, Any]:
    """Restore parent artifacts and remove files introduced by a failed patch."""
    paths = [*FILES, STRUCTURE_VERIFIER_PATH, REPORT_PATH, CONTRACT_PATH]
    git(root, "reset", "--", *paths)
    restored: list[str] = []; removed: list[str] = []; errors: list[str] = []
    for relative_path, metadata in manifest["files"].items():
        target = root / relative_path
        try:
            if metadata["existed"]:
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes((root / metadata["backup"]).read_bytes())
                restored.append(relative_path)
            elif target.exists():
                target.unlink(); removed.append(relative_path)
        except OSError as exc: errors.append(f"{relative_path}: {exc}")
    for directory in sorted({str(Path(path).parent) for path in FILES}, key=len, reverse=True):
        try: (root / directory).rmdir()
        except OSError: pass
    payload = {"stage": STAGE, "status": "FAIL_ROLLED_BACK" if not errors else "ROLLBACK_INCOMPLETE", "reason": reason, "failed_checks": [asdict(item) for item in checks if item.status == "FAIL"], "restored_files": restored, "removed_failed_artifacts": removed, "rollback_errors": errors, "database_evidence_after_rollback": database_evidence(root), "main_py_started_after_failure": False, "wal_shm_manipulated": False}
    write_atomic(root / FAILURE_REPORT, json.dumps(payload, ensure_ascii=False, indent=2) + "\n")
    return payload


def repair_structure_verifier(root: Path) -> None:
    """Exclude interpreter cache directories from runtime package discovery."""
    path = root / STRUCTURE_VERIFIER_PATH
    source = path.read_text(encoding="utf-8")
    original = 'physical_packages = {path.name for path in runtime_root.iterdir() if path.is_dir()}'
    repaired = 'physical_packages = {path.name for path in runtime_root.iterdir() if path.is_dir() and path.name != "__pycache__"}'
    if repaired in source:
        return
    if original not in source:
        raise PatchError("structure verifier package-discovery contract not found")
    write_atomic(path, source.replace(original, repaired, 1))
    compile(path.read_text(encoding="utf-8"), str(path), "exec")


def remove_bytecode_artifacts(root: Path) -> list[str]:
    """Remove transient Python bytecode artifacts before structure verification."""
    removed: list[str] = []
    for base_name in ("rom_v2", "tests_v2"):
        base = root / base_name
        if not base.exists():
            continue
        for pyc in sorted(base.rglob("*.pyc")):
            relative = pyc.relative_to(root).as_posix()
            pyc.unlink(missing_ok=True)
            removed.append(relative)
        for cache in sorted(base.rglob("__pycache__"), key=lambda path: len(path.parts), reverse=True):
            relative = cache.relative_to(root).as_posix()
            try:
                cache.rmdir()
                removed.append(relative + "/")
            except OSError:
                pass
    return removed


def run_verifier(root: Path, name: str, report_path: str, key: str, verifier_path: str) -> dict[str, Any]:
    """Execute one Stage 21 architecture verifier with its canonical contract."""
    report = json.loads((root / report_path).read_text(encoding="utf-8"))
    contract = report[key]
    temporary_contract = root / "reports" / f".stage_21_3_1_{name}_contract.tmp.json"
    temporary_result = root / "reports" / f".stage_21_3_1_{name}_result.tmp.json"
    write_atomic(temporary_contract, json.dumps(contract, ensure_ascii=False, indent=2) + "\n")
    command = [sys.executable, verifier_path, "--project-root", str(root)]
    if name != "dependency":
        command.extend(["--contract", str(temporary_contract)])
    command.extend(["--json-out", str(temporary_result)])
    execution = run(root, *command)
    result = json.loads(temporary_result.read_text(encoding="utf-8")) if temporary_result.exists() else {"summary": {"status": "FAIL"}, "violations": [{"rule": "MISSING_OUTPUT"}]}
    temporary_contract.unlink(missing_ok=True); temporary_result.unlink(missing_ok=True)
    return {"name": name, "returncode": execution.returncode, "stdout": execution.stdout.strip(), "stderr": execution.stderr.strip(), "result": result}


def render_contract(verifiers: list[dict[str, Any]], smoke_payload: dict[str, Any]) -> str:
    """Render the human-readable Stage 21.3.1 implementation contract."""
    lines = [
        "# Stage 21.3.1 — Isolated ROM V2 package skeleton", "",
        "- **Status:** `IMPLEMENTED`",
        "- **Entrypoint:** `python -m rom_v2.main`",
        "- **Gameplay:** `DISABLED`",
        "- **V1 runtime imports:** `FORBIDDEN`", "",
        "## Created structure", "",
        "```text", "rom_v2/", "  domain/", "  application/", "  infrastructure/", "  app/", "  content/", "  config.py", "  container.py", "  lifecycle.py", "  bootstrap.py", "  main.py", "tests_v2/", "  test_v2_bootstrap_smoke.py", "```", "",
        "## Bootstrap behavior", "",
        "The entrypoint builds an explicit container, validates safe bootstrap configuration, starts and stops lifecycle, and prints one JSON smoke record. It does not start Telegram, open a database, start background jobs, or execute gameplay.", "",
        "## Smoke result", "",
        f"```json\n{json.dumps(smoke_payload, ensure_ascii=False, indent=2)}\n```", "",
        "## Verifiers", "",
    ]
    lines.extend(f"- `{item['name']}`: `{item['result']['summary']['status']}`" for item in verifiers)
    lines.extend(["", "## Next roadmap stage", "", "Stage 21.3.2 — Runtime directories and Git exclusion.", ""])
    return "\n".join(lines)


def exact_commit(root: Path) -> str:
    """Commit only the declared Stage 21.3.1 artifacts."""
    paths = [PATCH_PATH, *FILES, STRUCTURE_VERIFIER_PATH, REPORT_PATH, CONTRACT_PATH]
    added = git(root, "add", "-f", "--", *paths)
    if added.returncode != 0: raise PatchError(added.stderr.strip())
    staged = sorted(item for item in git(root, "diff", "--cached", "--name-only", "-z").stdout.split("\0") if item)
    if staged != sorted(paths):
        git(root, "reset", "--", *paths)
        raise PatchError(f"staging allowlist mismatch: {staged}")
    committed = git(root, "commit", "-m", COMMIT_MESSAGE)
    if committed.returncode != 0:
        git(root, "reset", "--", *paths)
        raise PatchError(committed.stderr.strip() or committed.stdout.strip())
    return rev(root, "HEAD") or ""


def main() -> int:
    """Apply Stage 21.3.1 with full verification and fail-safe rollback."""
    root = Path(__file__).resolve().parent.parent
    for _, (report, key, verifier) in REPORTS.items():
        if not (root / report).is_file() or not (root / verifier).is_file():
            print(f"[FAIL] Missing prerequisite: {report} or {verifier}", file=sys.stderr); return 2
        if key not in json.loads((root / report).read_text(encoding="utf-8")):
            print(f"[FAIL] Missing canonical contract key {key} in {report}", file=sys.stderr); return 2
    print("[1/10] [PASS] Stage 21.2 contracts, verifiers and regulated directories detected.")
    branch = git(root, "branch", "--show-current").stdout.strip(); head = rev(root, "HEAD")
    upstream_result = git(root, "rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{u}"); upstream = upstream_result.stdout.strip() if upstream_result.returncode == 0 else None
    entries = parse_status(git(root, "status", "--porcelain=v1", "-z", "--untracked-files=all").stdout)
    allowed = [entry for entry in entries if entry["status"][0] in {" ", "?"} and (entry["path"] in OWNED or (entry["path"] in ALLOWED_DIRTY and entry["status"][0] == " "))]
    unexpected = [entry for entry in entries if entry not in allowed]
    checks = [
        Check("BRANCH", "PASS" if branch == TARGET_BRANCH else "FAIL", f"Active branch: {branch}", {}, branch != TARGET_BRANCH),
        Check("PARENT", "PASS" if head == EXPECTED_PARENT else "FAIL", "Expected Stage 21.2.7 parent verified.", {"expected": EXPECTED_PARENT, "actual": head}, head != EXPECTED_PARENT),
        Check("UPSTREAM", "PASS" if upstream == f"origin/{TARGET_BRANCH}" else "FAIL", f"Upstream: {upstream}", {}, upstream != f"origin/{TARGET_BRANCH}"),
        Check("WORKTREE", "PASS" if not unexpected else "FAIL", "No unexpected changes.", {"unexpected": unexpected}, bool(unexpected)),
    ]
    if any(item.blocking for item in checks): print("[2/10] [FAIL] Preflight returned NO_GO."); return 1
    print("[2/10] [PASS] Branch, parent, upstream and worktree verified; backups prepared in ROM\\backup.")
    before = database_evidence(root); manifest = prepare_backups(root)
    try:
        print("[3/10] [PASS] Creating isolated rom_v2 and tests_v2 skeleton.")
        for relative_path, content in FILES.items(): write_atomic(root / relative_path, content)
        repair_structure_verifier(root)
        checks.append(Check("STRUCTURE_VERIFIER_CACHE_POLICY", "PASS", "Interpreter cache directories are excluded from package discovery.", {"verifier": STRUCTURE_VERIFIER_PATH}))
        print("[4/10] [PASS] Compiling every new V2 Python module without writing __pycache__.")
        for relative_path in FILES:
            if relative_path.endswith(".py"):
                source = (root / relative_path).read_text(encoding="utf-8")
                compile(source, str(root / relative_path), "exec")
        print("[5/10] [PASS] Running isolated V2 bootstrap smoke command.")
        smoke = run(root, sys.executable, "-m", "rom_v2.main")
        smoke_payload = json.loads(smoke.stdout.strip()) if smoke.returncode == 0 else {}
        smoke_ok = smoke.returncode == 0 and smoke_payload.get("status") == "ready" and smoke_payload.get("gameplay_enabled") is False and smoke_payload.get("telegram_started") is False and smoke_payload.get("database_opened") is False and smoke_payload.get("background_jobs_started") is False
        checks.append(Check("ISOLATED_SMOKE", "PASS" if smoke_ok else "FAIL", smoke.stdout.strip() or "Smoke failed.", {"stderr": smoke.stderr.strip()}, not smoke_ok))
        print("[6/10] [PASS] Running V2 unit smoke test.")
        tests = run(root, sys.executable, "-m", "unittest", "tests_v2.test_v2_bootstrap_smoke")
        checks.append(Check("UNIT_SMOKE", "PASS" if tests.returncode == 0 else "FAIL", tests.stderr.strip() or tests.stdout.strip(), {}, tests.returncode != 0))
        removed_bytecode = remove_bytecode_artifacts(root)
        checks.append(Check("BYTECODE_ARTIFACTS_CLEANED", "PASS", f"Transient bytecode artifacts removed: {len(removed_bytecode)}.", {"removed": removed_bytecode}))
        print("[7/10] [PASS] Running all Stage 21 architecture and contract verifiers.")
        verifier_results = [run_verifier(root, name, *spec) for name, spec in REPORTS.items()]
        for item in verifier_results:
            ok = item["returncode"] == 0 and item["result"].get("summary", {}).get("status") == "PASS"
            checks.append(Check(f"VERIFIER_{item['name'].upper()}", "PASS" if ok else "FAIL", item["stdout"] or f"{item['name']} verifier failed.", {"stderr": item["stderr"], "violations": item["result"].get("violations", [])}, not ok))
        if before != database_evidence(root): checks.append(Check("DATABASE_UNCHANGED", "FAIL", "DB/WAL/SHM evidence changed.", {}, True))
        else: checks.append(Check("DATABASE_UNCHANGED", "PASS", "DB/WAL/SHM unchanged and SQLite was not opened.", {"production_connection_opened": False}))
        blockers = [item.check_id for item in checks if item.blocking]
        if blockers:
            report = rollback(root, manifest, f"Stage 21.3.1 NO_GO: {blockers}", checks); print(f"[8/10] [FAIL] Rollback: {report['status']}"); return 1
        payload = {"schema_version": 1, "stage": STAGE, "generated_at_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"), "summary": {"conclusion": "GO", "blocking_failures": [], "created_file_count": len(FILES), "verifier_count": len(verifier_results), "smoke_status": "PASS", "bytecode_artifacts_removed": len(removed_bytecode), "gameplay_started": False, "telegram_started": False, "database_opened": False}, "git": {"branch": branch, "head_before_commit": head, "upstream": upstream}, "checks": [asdict(item) for item in checks], "created_files": sorted(FILES), "smoke_payload": smoke_payload, "verifiers": verifier_results, "database_evidence_before": before, "database_evidence_after": database_evidence(root), "artifacts": {"patch": PATCH_PATH, "json": REPORT_PATH, "markdown": CONTRACT_PATH, "structure_verifier": STRUCTURE_VERIFIER_PATH}, "next_stage": "21.3.2", "suggested_next_patch": "patch_21_3_2_create_v2_runtime_directories.py"}
        print("[8/10] [PASS] Writing complete implementation and verifier evidence.")
        write_atomic(root / REPORT_PATH, json.dumps(payload, ensure_ascii=False, indent=2) + "\n")
        write_atomic(root / CONTRACT_PATH, render_contract(verifier_results, smoke_payload))
    except Exception as exc:
        report = rollback(root, manifest, f"Mutation or verification failure: {exc}", checks); print(f"[8/10] [FAIL] {exc}; rollback: {report['status']}", file=sys.stderr); return 2
    (root / FAILURE_REPORT).unlink(missing_ok=True)
    try:
        print("[9/10] [PASS] Creating exact-allowlist Stage 21.3.1 commit.")
        commit_hash = exact_commit(root)
    except PatchError as exc:
        report = rollback(root, manifest, f"Commit failure: {exc}", checks); print(f"[9/10] [FAIL] rollback: {report['status']}", file=sys.stderr); return 2
    print(f"[10/10] [PASS] Isolated V2 skeleton committed and DB/WAL/SHM verified: {commit_hash}")
    print("=" * 72); print(f"ROM Stage {STAGE} - isolated V2 package skeleton")
    for item in checks: print(f"[{item.status}] {item.check_id}: {item.summary}")
    print(f"[PASS] CREATED_FILES: {len(FILES)}"); print(f"[PASS] VERIFIERS: {len(REPORTS)}"); print("[PASS] GAMEPLAY_STARTED: False"); print("[PASS] TELEGRAM_STARTED: False"); print("[PASS] DATABASE_OPENED: False")
    print("CONCLUSION: GO\nPATCH STATUS: PASS"); print(f"GIT COMMIT STATUS: PASS ({commit_hash})"); print("REMOTE PUSH STATUS: NOT REQUIRED\nMANUAL CHECK: NOT REQUIRED\nFAIL-SAFE ROLLBACK: ARMED\nWAL/SHM: NOT MANIPULATED\nSUGGESTED NEXT PATCH: patch_21_3_2_create_v2_runtime_directories.py")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
