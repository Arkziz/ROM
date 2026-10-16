#!/usr/bin/env python3
"""Stage 21.2.2: define the unambiguous ROM V2 package and runtime layout.

This stage approves the future package map without prematurely creating the
rom_v2 runtime skeleton reserved for Stage 21.3.1. It creates a machine layout
contract, a standalone structure verifier, an ADR, and manual acceptance
checklist. Production V1 and DB/WAL/SHM are not opened or modified.
"""
from __future__ import annotations

import hashlib
import json
import os
import py_compile
import subprocess
import sys
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

STAGE = "21.2.2"
TARGET_BRANCH = "rewrite/rom-v2"
EXPECTED_PARENT = "17aaae53828eeee7b731e92277ae191282ee77dd"
DEPENDENCY_REPORT = "reports/stage_21_2_1_dependency_rules.json"
DEPENDENCY_ADR = "MD/ADR_21_2_1_V2_DEPENDENCY_RULES.md"
DEPENDENCY_VERIFIER = "tools/verify_v2_dependency_rules.py"
PATCH_PATH = "patch/patch_21_2_2_define_v2_package_structure.py"
VERIFIER_PATH = "tools/verify_v2_package_structure.py"
REPORT_PATH = "reports/stage_21_2_2_package_structure.json"
CONTRACT_PATH = "MD/ADR_21_2_2_V2_PACKAGE_STRUCTURE.md"
CHECKLIST_PATH = "MD/STAGE_21_2_2_MANUAL_ACCEPTANCE_CHECKLIST.md"
FAILURE_REPORT = "reports/stage_21_2_2_failure_rollback.json"
COMMIT_MESSAGE = "Stage 21.2.2: define V2 package structure"
OWNED = {PATCH_PATH, VERIFIER_PATH, REPORT_PATH, CONTRACT_PATH, CHECKLIST_PATH, FAILURE_REPORT}
ALLOWED_DIRTY = {"ROM_FULL_DUMP.txt", "ROM_ADDITIONAL_DUMP.txt"}
DB_FILES = ("game.db", "game.db-wal", "game.db-shm")
BACKUP_PREFIX = "stage_21_2_2"

LAYOUT_CONTRACT: dict[str, Any] = {
    "schema_version": 1,
    "runtime_root": "rom_v2",
    "runtime_packages": {
        "rom_v2/domain": {
            "kind": "python_package",
            "owner": "domain_model",
            "purpose": "Pure entities, value objects, policies, invariants and domain events.",
            "may_depend_on": ["rom_v2/domain"],
            "forbidden": ["Telegram", "SQLite", "ORM", "HTTP", ".env", "filesystem", "subprocess"],
        },
        "rom_v2/application": {
            "kind": "python_package",
            "owner": "use_cases_and_ports",
            "purpose": "Commands, queries, use cases, ports, orchestration and transaction boundaries.",
            "may_depend_on": ["rom_v2/domain", "rom_v2/application"],
            "forbidden": ["Telegram", "SQLite", "ORM", "concrete infrastructure adapters"],
        },
        "rom_v2/infrastructure": {
            "kind": "python_package",
            "owner": "adapters_and_persistence",
            "purpose": "Database, repository, external integration and technical adapter implementations.",
            "may_depend_on": ["rom_v2/domain", "rom_v2/application", "rom_v2/infrastructure"],
            "forbidden": ["app composition imports", "business policy ownership"],
        },
        "rom_v2/app": {
            "kind": "python_package",
            "owner": "composition_and_delivery",
            "purpose": "Composition root, lifecycle and delivery adapters including future Telegram wiring.",
            "may_depend_on": ["rom_v2/domain", "rom_v2/application", "rom_v2/infrastructure", "rom_v2/app"],
            "forbidden": ["business formulas", "SQL", "duplicate domain policies"],
        },
        "rom_v2/content": {
            "kind": "python_package",
            "owner": "validated_content_catalogs",
            "purpose": "Declarative stable-key content and schema-validated catalogs without runtime mutation.",
            "may_depend_on": ["rom_v2/domain", "rom_v2/content"],
            "forbidden": ["Telegram", "SQLite", "repositories", "application services", "runtime mutation"],
        },
    },
    "support_roots": {
        "tests_v2": "V2 unit, contract, integration, parity and architecture tests only.",
        "tools": "Executable audit, verifier, bootstrap and maintenance tools.",
        "reports": "Machine-readable generated evidence and acceptance reports.",
        "MD": "Human-readable ADRs, contracts, runbooks and acceptance documents.",
        ".runtime/v2": "Ignored local DB, logs, exports and temporary runtime artifacts; created in Stage 21.3.2.",
    },
    "reserved_future_paths": {
        "rom_v2/main.py": "Stage 21.3.1 entrypoint; must start without gameplay.",
        "rom_v2/bootstrap.py": "Stage 21.3.1 composition bootstrap.",
        "rom_v2/config.py": "Stage 21.3.3 validated V2-prefixed configuration.",
        "rom_v2/container.py": "Stage 21.3.1 dependency container/composition owner.",
        "rom_v2/lifecycle.py": "Stage 21.3.1 startup/shutdown lifecycle.",
    },
    "forbidden_catch_all_names": [
        "common.py", "helpers.py", "helper.py", "utils.py", "utility.py", "misc.py",
        "manager.py", "service.py", "services.py", "base.py", "core.py", "shared.py",
    ],
    "naming_contract": {
        "package_and_module_names": "lowercase_snake_case_english",
        "stable_keys": "english_machine_keys",
        "user_facing_text": "localized_outside_identifiers",
        "one_authoritative_owner": True,
        "public_api_type_hints": True,
        "public_api_docstrings": True,
    },
    "stage_boundary": {
        "21.2.2": "Approve layout contract and verifier only.",
        "21.3.1": "Create physical rom_v2 package skeleton, bootstrap, container, lifecycle and smoke test.",
        "21.3.2": "Create and ignore .runtime/v2 directories.",
    },
}

VERIFIER_SOURCE = r'''#!/usr/bin/env python3
"""Verify the ROM V2 package-layout contract without importing runtime code."""
from __future__ import annotations

import argparse
import ast
import json
import re
from pathlib import Path
from typing import Any

EXPECTED_RUNTIME_PACKAGES = {"domain", "application", "infrastructure", "app", "content"}
EXPECTED_SUPPORT_ROOTS = {"tests_v2", "tools", "reports", "MD"}
FORBIDDEN_CATCH_ALL = {
    "common.py", "helpers.py", "helper.py", "utils.py", "utility.py", "misc.py",
    "manager.py", "service.py", "services.py", "base.py", "core.py", "shared.py",
}
VALID_NAME = re.compile(r"^[a-z][a-z0-9_]*$")


def verify(project_root: Path, contract: dict[str, Any]) -> dict[str, Any]:
    violations: list[dict[str, Any]] = []
    observations: list[dict[str, Any]] = []
    runtime_root = project_root / contract["runtime_root"]
    physical_runtime_exists = runtime_root.is_dir()

    declared_runtime = {Path(path).name for path in contract["runtime_packages"]}
    declared_support = set(contract["support_roots"])
    if declared_runtime != EXPECTED_RUNTIME_PACKAGES:
        violations.append({"rule": "RUNTIME_PACKAGE_SET", "expected": sorted(EXPECTED_RUNTIME_PACKAGES), "actual": sorted(declared_runtime)})
    if not EXPECTED_SUPPORT_ROOTS.issubset(declared_support):
        violations.append({"rule": "SUPPORT_ROOT_SET", "missing": sorted(EXPECTED_SUPPORT_ROOTS - declared_support)})

    duplicate_owners: dict[str, list[str]] = {}
    owners: dict[str, list[str]] = {}
    for path, metadata in contract["runtime_packages"].items():
        owners.setdefault(metadata["owner"], []).append(path)
        name = Path(path).name
        if not VALID_NAME.fullmatch(name):
            violations.append({"rule": "PACKAGE_NAMING", "path": path})
        if Path(path).name + ".py" in FORBIDDEN_CATCH_ALL:
            violations.append({"rule": "CATCH_ALL_PACKAGE_NAME", "path": path})
    duplicate_owners = {owner: paths for owner, paths in owners.items() if len(paths) > 1}
    if duplicate_owners:
        violations.append({"rule": "DUPLICATE_OWNER", "owners": duplicate_owners})

    files: list[Path] = []
    if physical_runtime_exists:
        files = sorted(runtime_root.rglob("*.py"))
        for path in files:
            relative = path.relative_to(project_root).as_posix()
            if path.name in FORBIDDEN_CATCH_ALL:
                violations.append({"rule": "FORBIDDEN_CATCH_ALL_MODULE", "file": relative})
            if path.name != "__init__.py" and not VALID_NAME.fullmatch(path.stem):
                violations.append({"rule": "MODULE_NAMING", "file": relative})
            try:
                ast.parse(path.read_text(encoding="utf-8", errors="replace"), filename=relative)
            except SyntaxError as exc:
                violations.append({"rule": "PYTHON_PARSE_ERROR", "file": relative, "error": str(exc)})
        physical_packages = {path.name for path in runtime_root.iterdir() if path.is_dir()}
        unknown = sorted(physical_packages - EXPECTED_RUNTIME_PACKAGES)
        missing = sorted(EXPECTED_RUNTIME_PACKAGES - physical_packages)
        if unknown:
            violations.append({"rule": "UNDECLARED_RUNTIME_PACKAGE", "packages": unknown})
        if missing:
            violations.append({"rule": "MISSING_RUNTIME_PACKAGE_AFTER_SCAFFOLD", "packages": missing})
    else:
        observations.append({"kind": "STAGE_BOUNDARY", "message": "Physical rom_v2 skeleton is intentionally reserved for Stage 21.3.1."})

    return {
        "schema_version": 1,
        "summary": {
            "status": "PASS" if not violations else "FAIL",
            "physical_runtime_exists": physical_runtime_exists,
            "physical_python_file_count": len(files),
            "declared_runtime_package_count": len(declared_runtime),
            "declared_support_root_count": len(declared_support),
            "violation_count": len(violations),
        },
        "declared_runtime_packages": sorted(declared_runtime),
        "declared_support_roots": sorted(declared_support),
        "observations": observations,
        "violations": violations,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", default=".")
    parser.add_argument("--contract", required=True)
    parser.add_argument("--json-out")
    args = parser.parse_args()
    root = Path(args.project_root).resolve()
    contract = json.loads(Path(args.contract).read_text(encoding="utf-8"))
    result = verify(root, contract)
    text = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    if args.json_out:
        Path(args.json_out).write_text(text, encoding="utf-8", newline="\n")
    print(f"V2 package structure verifier: {result['summary']['status']}")
    print(f"Declared runtime packages: {result['summary']['declared_runtime_package_count']}")
    print(f"Declared support roots: {result['summary']['declared_support_root_count']}")
    print(f"Physical V2 tree exists: {result['summary']['physical_runtime_exists']}")
    print(f"Violations: {result['summary']['violation_count']}")
    return 0 if result["summary"]["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
'''


@dataclass(frozen=True)
class Check:
    check_id: str
    status: str
    summary: str
    details: dict[str, Any]
    blocking: bool = False


class PatchError(RuntimeError):
    pass


def run(root: Path, *command: str, timeout: int = 120) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, cwd=root, text=True, encoding="utf-8", errors="replace", capture_output=True, timeout=timeout, check=False)


def git(root: Path, *args: str, timeout: int = 120) -> subprocess.CompletedProcess[str]:
    return run(root, "git", *args, timeout=timeout)


def rev(root: Path, name: str) -> str | None:
    result = git(root, "rev-parse", "--verify", f"{name}^{{commit}}")
    return result.stdout.strip() if result.returncode == 0 else None


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def database_evidence(root: Path) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for name in DB_FILES:
        path = root / name
        if not path.exists():
            result[name] = {"exists": False}
            continue
        stat = path.stat()
        result[name] = {"exists": True, "size": stat.st_size, "mtime_ns": stat.st_mtime_ns, "sha256": sha256(path)}
    return result


def write_atomic(path: Path, content: str) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.parent.mkdir(parents=True, exist_ok=True)
    temporary.write_text(content, encoding="utf-8", newline="\n")
    os.replace(temporary, path)


def parse_status(raw: str) -> list[dict[str, str]]:
    return [{"status": item[:2], "path": item[3:]} for item in raw.split("\0") if item]


def git_blob(root: Path, commit: str, relative_path: str) -> bytes | None:
    result = subprocess.run(["git", "show", f"{commit}:{relative_path}"], cwd=root, capture_output=True, check=False)
    return result.stdout if result.returncode == 0 else None


def prepare_backups(root: Path) -> dict[str, Any]:
    backup_dir = root / "backup"
    backup_dir.mkdir(parents=True, exist_ok=True)
    manifest: dict[str, Any] = {"parent": EXPECTED_PARENT, "files": {}}
    for relative_path in (VERIFIER_PATH, REPORT_PATH, CONTRACT_PATH, CHECKLIST_PATH):
        blob = git_blob(root, EXPECTED_PARENT, relative_path)
        backup_path = backup_dir / f"{BACKUP_PREFIX}__{relative_path.replace('/', '__')}"
        if blob is None:
            manifest["files"][relative_path] = {"existed": False, "backup": None}
        else:
            backup_path.write_bytes(blob)
            manifest["files"][relative_path] = {"existed": True, "backup": str(backup_path.relative_to(root)).replace("\\", "/"), "sha256": hashlib.sha256(blob).hexdigest()}
    return manifest


def rollback_artifacts(root: Path, manifest: dict[str, Any], reason: str, checks: list[Check]) -> dict[str, Any]:
    restored: list[str] = []
    removed: list[str] = []
    errors: list[str] = []
    paths = [VERIFIER_PATH, REPORT_PATH, CONTRACT_PATH, CHECKLIST_PATH]
    git(root, "reset", "--", *paths)
    for relative_path, metadata in manifest["files"].items():
        target = root / relative_path
        try:
            if metadata["existed"]:
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes((root / metadata["backup"]).read_bytes())
                restored.append(relative_path)
            elif target.exists():
                target.unlink()
                removed.append(relative_path)
        except OSError as exc:
            errors.append(f"{relative_path}: {exc}")
    verification = {path: metadata["existed"] == (root / path).exists() for path, metadata in manifest["files"].items()}
    payload = {
        "stage": STAGE,
        "status": "FAIL_ROLLED_BACK" if not errors and all(verification.values()) else "ROLLBACK_INCOMPLETE",
        "reason": reason,
        "failed_checks": [asdict(item) for item in checks if item.status == "FAIL"],
        "restored_files": restored,
        "removed_failed_artifacts": removed,
        "rollback_errors": errors,
        "post_rollback_verification": verification,
        "database_evidence_after_rollback": database_evidence(root),
        "main_py_started": False,
        "wal_shm_manipulated": False,
    }
    write_atomic(root / FAILURE_REPORT, json.dumps(payload, ensure_ascii=False, indent=2) + "\n")
    return payload


def render_contract() -> str:
    return "\n".join([
        "# ADR 21.2.2 — ROM V2 package structure", "",
        "- **Status:** `PROPOSED_FOR_MANUAL_ACCEPTANCE`",
        "- **Stage:** `21.2.2`",
        "- **Parent ADR:** `ADR_21_2_1_V2_DEPENDENCY_RULES.md`", "",
        "## Decision", "",
        "Затвердити однозначний майбутній layout:", "",
        "```text",
        "rom_v2/",
        "  domain/          # pure domain model and policy",
        "  application/     # use cases, commands, queries and ports",
        "  infrastructure/  # persistence and external adapters",
        "  app/             # composition root and delivery adapters",
        "  content/         # declarative validated catalogs",
        "tests_v2/          # V2-only tests",
        "tools/             # executable verification and maintenance tools",
        "reports/           # machine evidence",
        "MD/                # ADRs, contracts and runbooks",
        ".runtime/v2/       # ignored runtime data, created in Stage 21.3.2",
        "```", "",
        "## Stage boundary", "",
        "Stage 21.2.2 затверджує layout, ownership, naming і verifier. Фізичний `rom_v2` skeleton, bootstrap, dependency container, lifecycle та smoke test створюються тільки у Stage 21.3.1. Runtime directories створюються у Stage 21.3.2.", "",
        "## Ownership", "",
        "- `domain`: entities, value objects, policies, invariants, domain events.",
        "- `application`: commands, queries, use cases, ports and transaction orchestration.",
        "- `infrastructure`: repository/database/external adapter implementations.",
        "- `app`: composition root, lifecycle and delivery adapters.",
        "- `content`: declarative stable-key catalogs and validation-ready content.", "",
        "## Prohibitions", "",
        "- Catch-all modules such as `utils.py`, `helpers.py`, `common.py`, `service.py`, `manager.py`, `base.py`, `core.py` or `shared.py`.",
        "- Business rules in `app`, SQL outside infrastructure, runtime mutation in content.",
        "- Multiple package owners for the same responsibility.",
        "- User-facing text as a technical identifier.", "",
        "## Acceptance", "",
        "Automated verifier must PASS. Manual acceptance must confirm that a new developer can unambiguously place representative files and that no catch-all package is required.", "",
        "## Next roadmap stage", "",
        "Stage 21.2.3 — Result and error model.", "",
    ])


def render_checklist() -> str:
    return "\n".join([
        "# Stage 21.2.2 — manual acceptance checklist", "",
        "Status before review: `AWAITING_MANUAL_ACCEPTANCE`", "",
        "Позначте PASS лише після формального огляду:", "",
        "- [ ] П'ять runtime packages мають однозначне призначення: domain, application, infrastructure, app, content.",
        "- [ ] Для entity/value object/policy очевидний owner: `domain`.",
        "- [ ] Для command/query/use case/port очевидний owner: `application`.",
        "- [ ] Для SQLite repository або зовнішнього adapter очевидний owner: `infrastructure`.",
        "- [ ] Для composition, lifecycle або Telegram delivery очевидний owner: `app`.",
        "- [ ] Для declarative catalog очевидний owner: `content`.",
        "- [ ] `tests_v2`, `tools`, `reports`, `MD` і `.runtime/v2` не змішані з runtime package.",
        "- [ ] Не потрібні catch-all модулі `utils`, `helpers`, `common`, `service`, `manager`, `base`, `core`, `shared`.",
        "- [ ] Межа Stage 21.2.2/21.3.1 зрозуміла: зараз contract; physical skeleton наступного блоку.",
        "- [ ] Назви package/module англійською snake_case; presentation text не є stable key.", "",
        "## Result", "",
        "- Manual result: `PENDING`",
        "- Reviewer: `Oleh`",
        "- Date: `PENDING`",
        "- Notes: `PENDING`", "",
    ])


def exact_commit(root: Path) -> str:
    paths = [PATCH_PATH, VERIFIER_PATH, REPORT_PATH, CONTRACT_PATH, CHECKLIST_PATH]
    result = git(root, "add", "-f", "--", *paths)
    if result.returncode != 0:
        raise PatchError(result.stderr.strip() or "git add failed")
    staged_result = git(root, "diff", "--cached", "--name-only", "-z")
    staged = sorted(item for item in staged_result.stdout.split("\0") if item)
    if staged_result.returncode != 0 or staged != sorted(paths):
        git(root, "reset", "--", *paths)
        raise PatchError(f"staging allowlist mismatch: {staged}")
    committed = git(root, "commit", "-m", COMMIT_MESSAGE)
    if committed.returncode != 0:
        git(root, "reset", "--", *paths)
        raise PatchError(committed.stderr.strip() or committed.stdout.strip() or "git commit failed")
    commit_hash = rev(root, "HEAD")
    if not commit_hash:
        raise PatchError("commit created but HEAD cannot be resolved")
    return commit_hash


def main() -> int:
    root = Path(__file__).resolve().parent.parent
    for required in (DEPENDENCY_REPORT, DEPENDENCY_ADR, DEPENDENCY_VERIFIER):
        if not (root / required).is_file():
            print(f"[FAIL] Missing Stage 21.2.1 prerequisite artifact: {required}", file=sys.stderr)
            return 2

    print("[1/8] [PASS] Stage 21.2.1 prerequisites and regulated directories detected.")
    branch = git(root, "branch", "--show-current").stdout.strip()
    head = rev(root, "HEAD")
    upstream_result = git(root, "rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{u}")
    upstream = upstream_result.stdout.strip() if upstream_result.returncode == 0 else None
    entries = parse_status(git(root, "status", "--porcelain=v1", "-z", "--untracked-files=all").stdout)
    allowed = [entry for entry in entries if entry["status"][0] in {" ", "?"} and (entry["path"] in OWNED or (entry["path"] in ALLOWED_DIRTY and entry["status"][0] == " "))]
    unexpected = [entry for entry in entries if entry not in allowed]
    checks = [
        Check("BRANCH", "PASS" if branch == TARGET_BRANCH else "FAIL", f"Active branch: {branch}", {}, branch != TARGET_BRANCH),
        Check("PARENT", "PASS" if head == EXPECTED_PARENT else "FAIL", "Expected Stage 21.2.1 parent verified." if head == EXPECTED_PARENT else "Unexpected parent.", {"expected": EXPECTED_PARENT, "actual": head}, head != EXPECTED_PARENT),
        Check("UPSTREAM", "PASS" if upstream == f"origin/{TARGET_BRANCH}" else "FAIL", f"Upstream: {upstream}", {}, upstream != f"origin/{TARGET_BRANCH}"),
        Check("WORKTREE", "PASS" if not unexpected else "FAIL", "No unexpected changes." if not unexpected else "Unexpected changes exist.", {"unexpected": unexpected}, bool(unexpected)),
    ]
    if any(item.blocking for item in checks):
        print("[2/8] [FAIL] Preflight returned NO_GO.")
        return 1

    print("[2/8] [PASS] Branch, parent, upstream and worktree verified; backups prepared in ROM\\backup.")
    db_before = database_evidence(root)
    backup_manifest = prepare_backups(root)
    dependency_report = json.loads((root / DEPENDENCY_REPORT).read_text(encoding="utf-8"))
    prerequisite_failures: list[str] = []
    if dependency_report.get("stage") != "21.2.1":
        prerequisite_failures.append("dependency report stage is not 21.2.1")
    if dependency_report.get("summary", {}).get("conclusion") != "GO":
        prerequisite_failures.append("dependency report conclusion is not GO")
    if dependency_report.get("summary", {}).get("status") != "PASS":
        prerequisite_failures.append("dependency verifier status is not PASS")
    if dependency_report.get("summary", {}).get("violation_count") != 0:
        prerequisite_failures.append("dependency report contains violations")
    if dependency_report.get("summary", {}).get("parse_error_count") != 0:
        prerequisite_failures.append("dependency report contains parse errors")
    if prerequisite_failures:
        print("[FAIL] Stage 21.2.1 prerequisite is not canonical: " + "; ".join(prerequisite_failures), file=sys.stderr)
        return 2
    checks.append(Check(
        "STAGE_21_2_1_PREREQUISITE",
        "PASS",
        "Stage 21.2.1 report, ADR and dependency verifier are canonical PASS.",
        {
            "report": DEPENDENCY_REPORT,
            "adr": DEPENDENCY_ADR,
            "verifier": DEPENDENCY_VERIFIER,
            "dependency_commit": EXPECTED_PARENT,
        },
    ))

    print("[3/8] [PASS] Writing package-layout verifier, ADR and manual acceptance checklist.")
    write_atomic(root / VERIFIER_PATH, VERIFIER_SOURCE)
    try:
        py_compile.compile(str(root / VERIFIER_PATH), doraise=True)
    except py_compile.PyCompileError as exc:
        rollback = rollback_artifacts(root, backup_manifest, f"Structure verifier py_compile failed: {exc}", checks)
        print(f"[3/8] [FAIL] py_compile failed; rollback status: {rollback['status']}.")
        return 2

    print("[4/8] [PASS] Executing structure verifier against proposed contract and current tree.")
    temporary_contract = root / "reports" / ".stage_21_2_2_contract.tmp.json"
    temporary_result = root / "reports" / ".stage_21_2_2_verifier.tmp.json"
    write_atomic(temporary_contract, json.dumps(LAYOUT_CONTRACT, ensure_ascii=False, indent=2) + "\n")
    verifier_run = run(root, sys.executable, VERIFIER_PATH, "--project-root", str(root), "--contract", str(temporary_contract), "--json-out", str(temporary_result))
    if not temporary_result.is_file():
        temporary_contract.unlink(missing_ok=True)
        rollback = rollback_artifacts(root, backup_manifest, "Structure verifier did not create output.", checks)
        print(f"[4/8] [FAIL] Missing verifier output; rollback status: {rollback['status']}.")
        return 2
    verifier_result = json.loads(temporary_result.read_text(encoding="utf-8"))
    temporary_contract.unlink(missing_ok=True)
    temporary_result.unlink(missing_ok=True)
    checks.extend([
        Check("VERIFIER_PY_COMPILE", "PASS", "Standalone package-structure verifier compiles.", {}),
        Check("VERIFIER_EXECUTION", "PASS" if verifier_run.returncode == 0 else "FAIL", verifier_run.stdout.strip() or "Verifier executed.", {"stderr": verifier_run.stderr.strip()}, verifier_run.returncode != 0),
        Check("UNAMBIGUOUS_RUNTIME_PACKAGES", "PASS" if verifier_result["summary"]["declared_runtime_package_count"] == 5 else "FAIL", "Five canonical runtime packages declared.", {"packages": verifier_result["declared_runtime_packages"]}, verifier_result["summary"]["declared_runtime_package_count"] != 5),
        Check("NO_CATCH_ALL_MODULES", "PASS" if not verifier_result["violations"] else "FAIL", f"Structure violations: {verifier_result['summary']['violation_count']}.", {"violations": verifier_result["violations"]}, bool(verifier_result["violations"])),
        Check("STAGE_BOUNDARY_PRESERVED", "PASS" if not verifier_result["summary"]["physical_runtime_exists"] else "FAIL", "Physical rom_v2 skeleton remains reserved for Stage 21.3.1.", {}, verifier_result["summary"]["physical_runtime_exists"]),
        Check("SUPPORT_ROOTS_DECLARED", "PASS" if verifier_result["summary"]["declared_support_root_count"] >= 5 else "FAIL", f"Support roots declared: {verifier_result['summary']['declared_support_root_count']}.", {}, verifier_result["summary"]["declared_support_root_count"] < 5),
        Check("MANUAL_ACCEPTANCE_REQUIRED", "PASS", "Roadmap requires formal manual acceptance after automated PASS.", {"status_after_patch": "AWAITING_MANUAL_ACCEPTANCE"}),
        Check("DATABASE_EVIDENCE_READY", "PASS", "DB/WAL/SHM evidence captured without opening SQLite.", {"production_connection_opened": False}),
    ])
    blockers = [item.check_id for item in checks if item.blocking]
    conclusion = "GO_AUTOMATED_AWAITING_MANUAL_ACCEPTANCE" if not blockers else "NO_GO"
    payload = {
        "schema_version": 1,
        "stage": STAGE,
        "generated_at_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "summary": {
            "conclusion": conclusion,
            "blocking_failures": blockers,
            "automated_status": "PASS" if not blockers else "FAIL",
            "manual_status": "PENDING",
            **verifier_result["summary"],
        },
        "git": {"branch": branch, "head_before_commit": head, "upstream": upstream},
        "checks": [asdict(item) for item in checks],
        "layout_contract": LAYOUT_CONTRACT,
        "verifier_result": verifier_result,
        "manual_acceptance": {
            "required": True,
            "status": "PENDING",
            "checklist": CHECKLIST_PATH,
            "acceptance_criterion": "Однозначна структура без catch-all модулів.",
        },
        "stage_boundary": {
            "physical_rom_v2_created": False,
            "reason": "Physical skeleton belongs to Stage 21.3.1; Stage 21.2.2 approves structure only.",
        },
        "database_evidence_before": db_before,
        "artifacts": {"patch": PATCH_PATH, "verifier": VERIFIER_PATH, "json": REPORT_PATH, "adr": CONTRACT_PATH, "manual_checklist": CHECKLIST_PATH},
        "next_stage_after_manual_acceptance": "21.2.3",
        "suggested_next_patch": "patch_21_2_3_define_result_error_model.py",
    }

    print("[5/8] [PASS] Writing full package contract and automated acceptance evidence.")
    try:
        write_atomic(root / REPORT_PATH, json.dumps(payload, ensure_ascii=False, indent=2) + "\n")
        write_atomic(root / CONTRACT_PATH, render_contract())
        write_atomic(root / CHECKLIST_PATH, render_checklist())
        if blockers:
            rollback = rollback_artifacts(root, backup_manifest, "Package-structure acceptance returned NO_GO.", checks)
            print(f"[6/8] [FAIL] NO_GO; rollback status: {rollback['status']}; commit not created.")
            return 1
        if db_before != database_evidence(root):
            rollback = rollback_artifacts(root, backup_manifest, "DB/WAL/SHM evidence changed before commit.", checks)
            print(f"[6/8] [FAIL] DB evidence changed; rollback status: {rollback['status']}.")
            return 2
    except Exception as exc:
        rollback = rollback_artifacts(root, backup_manifest, f"Unexpected mutation-phase failure: {exc}", checks)
        print(f"[6/8] [FAIL] {exc}; rollback status: {rollback['status']}.", file=sys.stderr)
        return 2

    print("[6/8] [PASS] Package ownership, naming, stage boundary and catch-all safeguards validated.")
    failure_path = root / FAILURE_REPORT
    if failure_path.exists():
        failure_path.unlink()
    try:
        print("[7/8] [PASS] Creating exact-allowlist Stage 21.2.2 automated-evidence commit.")
        commit_hash = exact_commit(root)
    except PatchError as exc:
        rollback = rollback_artifacts(root, backup_manifest, f"Commit phase failed: {exc}", checks)
        print(f"[7/8] [FAIL] {exc}; rollback status: {rollback['status']}.", file=sys.stderr)
        return 2

    print(f"[8/8] [PASS] Package structure evidence committed and DB/WAL/SHM verified: {commit_hash}")
    print("=" * 72)
    print(f"ROM Stage {STAGE} - V2 package structure")
    for item in checks:
        print(f"[{item.status}] {item.check_id}: {item.summary}")
    print(f"[PASS] DECLARED_RUNTIME_PACKAGES: {verifier_result['summary']['declared_runtime_package_count']}")
    print(f"[PASS] DECLARED_SUPPORT_ROOTS: {verifier_result['summary']['declared_support_root_count']}")
    print(f"[PASS] STRUCTURE_VIOLATIONS: {verifier_result['summary']['violation_count']}")
    print(f"[PASS] PHYSICAL_ROM_V2_CREATED: {verifier_result['summary']['physical_runtime_exists']}")
    print("CONCLUSION: GO_AUTOMATED_AWAITING_MANUAL_ACCEPTANCE")
    print("PATCH STATUS: PASS")
    print(f"GIT COMMIT STATUS: PASS ({commit_hash})")
    print("REMOTE PUSH STATUS: NOT REQUIRED")
    print("MANUAL CHECK: REQUIRED - formal review of MD/STAGE_21_2_2_MANUAL_ACCEPTANCE_CHECKLIST.md")
    print("FAIL-SAFE ROLLBACK: ARMED")
    print("WAL/SHM: NOT MANIPULATED")
    print("SUGGESTED NEXT PATCH AFTER MANUAL PASS: patch_21_2_3_define_result_error_model.py")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
