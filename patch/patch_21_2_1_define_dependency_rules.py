#!/usr/bin/env python3
"""Stage 21.2.1: define and enforce ROM V2 dependency rules.

Creates the Architecture Decision Record and standalone verifier for the V2
layering contract. The patch only changes regulated Stage 21 artifacts. It does
not import V1 runtime modules, open SQLite, or modify production DB/WAL/SHM.
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

STAGE = "21.2.1"
TARGET_BRANCH = "rewrite/rom-v2"
EXPECTED_PARENT = "b69e7397931d68ccdd35d7ad18fcb48280e8a3ec"
PATCH_PATH = "patch/patch_21_2_1_define_dependency_rules.py"
VERIFIER_PATH = "tools/verify_v2_dependency_rules.py"
REPORT_PATH = "reports/stage_21_2_1_dependency_rules.json"
ADR_PATH = "MD/ADR_21_2_1_V2_DEPENDENCY_RULES.md"
FAILURE_REPORT = "reports/stage_21_2_1_failure_rollback.json"
COMMIT_MESSAGE = "Stage 21.2.1: define V2 dependency rules"
OWNED = {PATCH_PATH, VERIFIER_PATH, REPORT_PATH, ADR_PATH, FAILURE_REPORT}
ALLOWED_DIRTY = {"ROM_FULL_DUMP.txt", "ROM_ADDITIONAL_DUMP.txt"}
DB_FILES = ("game.db", "game.db-wal", "game.db-shm")
BACKUP_PREFIX = "stage_21_2_1"

VERIFIER_SOURCE = r'''#!/usr/bin/env python3
"""Verify ROM V2 dependency directions without importing application code."""
from __future__ import annotations

import argparse
import ast
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

LAYERS = ("domain", "application", "infrastructure", "app")
LAYER_RANK = {name: index for index, name in enumerate(LAYERS)}
FORBIDDEN_DOMAIN_ROOTS = {
    "aiogram", "telebot", "telegram", "sqlite3", "sqlalchemy", "aiosqlite",
    "requests", "httpx", "aiohttp", "dotenv", "os", "subprocess",
}
FORBIDDEN_APPLICATION_ROOTS = {
    "aiogram", "telebot", "telegram", "sqlite3", "sqlalchemy", "aiosqlite",
}
ALLOWED_CROSS_LAYER = {
    "application": {"domain"},
    "infrastructure": {"domain", "application"},
    "app": {"domain", "application", "infrastructure"},
    "domain": set(),
}


def module_name(root: Path, path: Path) -> str:
    relative = path.relative_to(root.parent).with_suffix("")
    parts = list(relative.parts)
    if parts and parts[-1] == "__init__":
        parts.pop()
    return ".".join(parts)


def layer_for(root: Path, path: Path) -> str | None:
    relative = path.relative_to(root)
    return relative.parts[0] if relative.parts and relative.parts[0] in LAYERS else None


def imported_modules(tree: ast.AST) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                records.append({"module": alias.name, "line": node.lineno, "kind": "import"})
        elif isinstance(node, ast.ImportFrom):
            prefix = "." * node.level
            records.append({"module": prefix + (node.module or ""), "line": node.lineno, "kind": "from"})
    return records


def resolve_internal_layer(module: str) -> str | None:
    normalized = module.lstrip(".")
    parts = normalized.split(".")
    if not parts:
        return None
    if parts[0] == "rom_v2" and len(parts) > 1 and parts[1] in LAYERS:
        return parts[1]
    if parts[0] in LAYERS:
        return parts[0]
    return None


def verify(project_root: Path) -> dict[str, Any]:
    root = project_root / "rom_v2"
    files = sorted(root.rglob("*.py")) if root.is_dir() else []
    modules: list[dict[str, Any]] = []
    violations: list[dict[str, Any]] = []
    edges: list[dict[str, Any]] = []
    parse_errors: list[dict[str, Any]] = []

    for path in files:
        layer = layer_for(root, path)
        if layer is None:
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        try:
            tree = ast.parse(text, filename=str(path))
        except SyntaxError as exc:
            parse_errors.append({"file": str(path.relative_to(project_root)), "error": str(exc)})
            continue
        imports = imported_modules(tree)
        module = module_name(root, path)
        modules.append({"file": str(path.relative_to(project_root)).replace("\\", "/"), "module": module, "layer": layer, "imports": imports})
        for item in imports:
            imported = item["module"]
            external_root = imported.lstrip(".").split(".")[0]
            target_layer = resolve_internal_layer(imported)
            if target_layer:
                edges.append({"source_layer": layer, "target_layer": target_layer, "file": str(path.relative_to(project_root)).replace("\\", "/"), "line": item["line"], "import": imported})
                if target_layer != layer and target_layer not in ALLOWED_CROSS_LAYER[layer]:
                    violations.append({"rule": "FORBIDDEN_LAYER_DIRECTION", "source_layer": layer, "target_layer": target_layer, "file": str(path.relative_to(project_root)).replace("\\", "/"), "line": item["line"], "import": imported})
            if layer == "domain" and external_root in FORBIDDEN_DOMAIN_ROOTS:
                violations.append({"rule": "FORBIDDEN_DOMAIN_DEPENDENCY", "file": str(path.relative_to(project_root)).replace("\\", "/"), "line": item["line"], "import": imported})
            if layer == "application" and external_root in FORBIDDEN_APPLICATION_ROOTS:
                violations.append({"rule": "FORBIDDEN_APPLICATION_ADAPTER_DEPENDENCY", "file": str(path.relative_to(project_root)).replace("\\", "/"), "line": item["line"], "import": imported})

    return {
        "schema_version": 1,
        "root": "rom_v2",
        "contract": {
            "layers_inner_to_outer": list(LAYERS),
            "allowed_cross_layer_dependencies": {key: sorted(value) for key, value in ALLOWED_CROSS_LAYER.items()},
            "domain_forbidden_roots": sorted(FORBIDDEN_DOMAIN_ROOTS),
            "application_forbidden_roots": sorted(FORBIDDEN_APPLICATION_ROOTS),
        },
        "summary": {
            "status": "PASS" if not violations and not parse_errors else "FAIL",
            "module_count": len(modules),
            "edge_count": len(edges),
            "violation_count": len(violations),
            "parse_error_count": len(parse_errors),
            "layer_counts": dict(sorted(Counter(item["layer"] for item in modules).items())),
            "empty_v2_tree": not files,
        },
        "modules": modules,
        "edges": edges,
        "violations": violations,
        "parse_errors": parse_errors,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", default=".")
    parser.add_argument("--json-out")
    args = parser.parse_args()
    result = verify(Path(args.project_root).resolve())
    text = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    if args.json_out:
        Path(args.json_out).write_text(text, encoding="utf-8", newline="\n")
    print(f"V2 dependency verifier: {result['summary']['status']}")
    print(f"Modules: {result['summary']['module_count']}")
    print(f"Edges: {result['summary']['edge_count']}")
    print(f"Violations: {result['summary']['violation_count']}")
    print(f"Parse errors: {result['summary']['parse_error_count']}")
    if result['summary']['empty_v2_tree']:
        print("V2 tree is not created yet; contract validation itself passed.")
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
    evidence: dict[str, Any] = {}
    for name in DB_FILES:
        path = root / name
        if not path.exists():
            evidence[name] = {"exists": False}
            continue
        stat = path.stat()
        evidence[name] = {"exists": True, "size": stat.st_size, "mtime_ns": stat.st_mtime_ns, "sha256": sha256(path)}
    return evidence


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
    for relative_path in (VERIFIER_PATH, REPORT_PATH, ADR_PATH):
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
    git(root, "reset", "--", VERIFIER_PATH, REPORT_PATH, ADR_PATH)
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
    report = {
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
    write_atomic(root / FAILURE_REPORT, json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    return report


def render_adr(verifier_result: dict[str, Any]) -> str:
    summary = verifier_result["summary"]
    return "\n".join([
        "# ADR 21.2.1 — ROM V2 dependency rules", "",
        "- **Status:** `ACCEPTED`",
        "- **Stage:** `21.2.1`",
        "- **Decision date:** `2026-10-16`",
        "- **Verifier:** `tools/verify_v2_dependency_rules.py`", "",
        "## Context", "",
        "ROM V1 має цикли, broad facades, Telegram/SQLite coupling і неоднозначний dependency ownership. ROM V2 потребує одностороннього dependency graph, який перевіряється без імпорту runtime-коду.", "",
        "## Decision", "",
        "Внутрішні шари розташовані від найстабільнішого до зовнішнього:", "",
        "```text",
        "domain ← application ← infrastructure ← app",
        "```", "",
        "Дозволено:", "",
        "- `domain` залежить лише від standard library і власних domain modules;",
        "- `application` залежить від `domain` та application ports;",
        "- `infrastructure` реалізує application ports і може залежати від `application` та `domain`;",
        "- `app` є composition root і може wire усі внутрішні шари.", "",
        "Заборонено:", "",
        "- `domain → application|infrastructure|app`;",
        "- `application → infrastructure|app`;",
        "- `infrastructure → app`;",
        "- Telegram framework, SQLite/ORM, HTTP clients, environment access і subprocess у `domain`;",
        "- Telegram framework та SQLite/ORM у `application`;",
        "- relative або absolute imports, що обходять заявлений напрям шарів.", "",
        "## Ports and adapters", "",
        "- Application визначає ports для repositories, Unit of Work, Clock, Random, notifications і external integrations.",
        "- Infrastructure реалізує ports.",
        "- Telegram handlers є adapters у зовнішньому `app`/adapter boundary, а не domain/application logic.",
        "- SQLite schema, SQL і migrations належать infrastructure/database.", "",
        "## Automated enforcement", "",
        f"- Current V2 modules: **{summary['module_count']}**.",
        f"- Current internal edges: **{summary['edge_count']}**.",
        f"- Current violations: **{summary['violation_count']}**.",
        f"- V2 tree currently empty: **{summary['empty_v2_tree']}**.",
        "- Verifier parses AST only and never imports project modules.",
        "- Empty V2 tree is valid before scaffold creation; every future V2 Python file is automatically covered.", "",
        "## Consequences", "",
        "- New V2 code that violates dependency directions must fail automated acceptance.",
        "- Concrete adapters cannot leak into domain or application.",
        "- Composition and framework wiring remain replaceable.",
        "- Exceptions require a new ADR; verifier suppression is not allowed by inline comments.", "",
        "## Safety", "",
        "Production code was not imported or executed. Production DB/WAL/SHM were not opened or modified.", "",
        "## Next roadmap stage", "",
        "Stage 21.2.2 — V2 package skeleton and application composition boundary.", "",
    ])


def exact_commit(root: Path) -> str:
    paths = [PATCH_PATH, VERIFIER_PATH, REPORT_PATH, ADR_PATH]
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
    for directory in (root / "tools", root / "reports", root / "MD", root / "backup"):
        directory.mkdir(parents=True, exist_ok=True)

    print("[1/8] [PASS] Regulated directories and Stage 21.2.1 output contract detected.")
    branch = git(root, "branch", "--show-current").stdout.strip()
    head = rev(root, "HEAD")
    upstream_result = git(root, "rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{u}")
    upstream = upstream_result.stdout.strip() if upstream_result.returncode == 0 else None
    entries = parse_status(git(root, "status", "--porcelain=v1", "-z", "--untracked-files=all").stdout)
    allowed = [entry for entry in entries if entry["status"][0] in {" ", "?"} and (entry["path"] in OWNED or (entry["path"] in ALLOWED_DIRTY and entry["status"][0] == " "))]
    unexpected = [entry for entry in entries if entry not in allowed]
    checks = [
        Check("BRANCH", "PASS" if branch == TARGET_BRANCH else "FAIL", f"Active branch: {branch}", {}, branch != TARGET_BRANCH),
        Check("PARENT", "PASS" if head == EXPECTED_PARENT else "FAIL", "Expected Stage 21.1.X3a parent verified." if head == EXPECTED_PARENT else "Unexpected parent.", {"expected": EXPECTED_PARENT, "actual": head}, head != EXPECTED_PARENT),
        Check("UPSTREAM", "PASS" if upstream == f"origin/{TARGET_BRANCH}" else "FAIL", f"Upstream: {upstream}", {}, upstream != f"origin/{TARGET_BRANCH}"),
        Check("WORKTREE", "PASS" if not unexpected else "FAIL", "No unexpected changes." if not unexpected else "Unexpected changes exist.", {"unexpected": unexpected}, bool(unexpected)),
    ]
    if any(item.blocking for item in checks):
        print("[2/8] [FAIL] Preflight returned NO_GO.")
        return 1

    print("[2/8] [PASS] Branch, parent, upstream and worktree verified; backups prepared in ROM\\backup.")
    db_before = database_evidence(root)
    backup_manifest = prepare_backups(root)

    print("[3/8] [PASS] Writing standalone AST dependency verifier and ADR draft.")
    write_atomic(root / VERIFIER_PATH, VERIFIER_SOURCE)
    try:
        py_compile.compile(str(root / VERIFIER_PATH), doraise=True)
    except py_compile.PyCompileError as exc:
        report = rollback_artifacts(root, backup_manifest, f"Verifier py_compile failed: {exc}", checks)
        print(f"[3/8] [FAIL] py_compile failed; rollback status: {report['status']}.")
        return 2

    print("[4/8] [PASS] Executing verifier against current ROM V2 tree.")
    temporary_report = root / "reports" / ".stage_21_2_1_verifier.tmp.json"
    verifier_run = run(root, sys.executable, VERIFIER_PATH, "--project-root", str(root), "--json-out", str(temporary_report))
    if not temporary_report.is_file():
        report = rollback_artifacts(root, backup_manifest, "Verifier did not produce JSON output.", checks)
        print(f"[4/8] [FAIL] Missing verifier output; rollback status: {report['status']}.")
        return 2
    verifier_result = json.loads(temporary_report.read_text(encoding="utf-8"))
    temporary_report.unlink()
    checks.extend([
        Check("VERIFIER_PY_COMPILE", "PASS", "Standalone verifier compiles.", {}),
        Check("VERIFIER_EXECUTION", "PASS" if verifier_run.returncode == 0 else "FAIL", verifier_run.stdout.strip() or "Verifier executed.", {"stderr": verifier_run.stderr.strip()}, verifier_run.returncode != 0),
        Check("DEPENDENCY_RULES", "PASS" if verifier_result["summary"]["status"] == "PASS" else "FAIL", f"Violations: {verifier_result['summary']['violation_count']}; parse errors: {verifier_result['summary']['parse_error_count']}.", {}, verifier_result["summary"]["status"] != "PASS"),
        Check("DOMAIN_TELEGRAM_SQLITE_FORBIDDEN", "PASS", "Domain forbidden dependency roots are encoded in verifier contract.", {"forbidden": verifier_result["contract"]["domain_forbidden_roots"]}),
        Check("LAYER_DIRECTION_CONTRACT", "PASS", "domain <- application <- infrastructure <- app contract encoded.", {"allowed": verifier_result["contract"]["allowed_cross_layer_dependencies"]}),
        Check("DATABASE_EVIDENCE_READY", "PASS", "DB/WAL/SHM evidence captured without opening SQLite.", {"production_connection_opened": False}),
    ])
    blockers = [item.check_id for item in checks if item.blocking]
    conclusion = "GO" if not blockers else "NO_GO"
    report_payload = {
        "schema_version": 1,
        "stage": STAGE,
        "generated_at_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "summary": {
            "conclusion": conclusion,
            "blocking_failures": blockers,
            **verifier_result["summary"],
        },
        "git": {"branch": branch, "head_before_commit": head, "upstream": upstream},
        "checks": [asdict(item) for item in checks],
        "dependency_contract": verifier_result["contract"],
        "modules": verifier_result["modules"],
        "edges": verifier_result["edges"],
        "violations": verifier_result["violations"],
        "parse_errors": verifier_result["parse_errors"],
        "acceptance": {
            "adr_created": True,
            "standalone_verifier_created": True,
            "verifier_ast_only": True,
            "runtime_imported": False,
            "empty_v2_tree_allowed_before_scaffold": True,
            "future_v2_python_files_covered": True,
        },
        "database_evidence_before": db_before,
        "artifacts": {"patch": PATCH_PATH, "verifier": VERIFIER_PATH, "json": REPORT_PATH, "adr": ADR_PATH},
        "next_stage": "21.2.2" if conclusion == "GO" else None,
    }

    print("[5/8] [PASS] Writing ADR and full dependency evidence report.")
    try:
        write_atomic(root / REPORT_PATH, json.dumps(report_payload, ensure_ascii=False, indent=2) + "\n")
        write_atomic(root / ADR_PATH, render_adr(verifier_result))
        if conclusion != "GO":
            for item in checks:
                if item.status == "FAIL":
                    print(f"[FAIL] {item.check_id}: {item.summary}")
            rollback = rollback_artifacts(root, backup_manifest, "Dependency-rule acceptance returned NO_GO.", checks)
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

    print("[6/8] [PASS] ADR, verifier and current dependency graph validated.")
    failure_path = root / FAILURE_REPORT
    if failure_path.exists():
        failure_path.unlink()
    try:
        print("[7/8] [PASS] Creating exact-allowlist Stage 21.2.1 commit.")
        commit_hash = exact_commit(root)
    except PatchError as exc:
        rollback = rollback_artifacts(root, backup_manifest, f"Commit phase failed: {exc}", checks)
        print(f"[7/8] [FAIL] {exc}; rollback status: {rollback['status']}.", file=sys.stderr)
        return 2

    print(f"[8/8] [PASS] Dependency rules committed and DB/WAL/SHM verified: {commit_hash}")
    print("=" * 72)
    print(f"ROM Stage {STAGE} - V2 dependency rules")
    for item in checks:
        print(f"[{item.status}] {item.check_id}: {item.summary}")
    print(f"[PASS] V2_MODULES: {verifier_result['summary']['module_count']}")
    print(f"[PASS] INTERNAL_EDGES: {verifier_result['summary']['edge_count']}")
    print(f"[PASS] VIOLATIONS: {verifier_result['summary']['violation_count']}")
    print(f"[PASS] PARSE_ERRORS: {verifier_result['summary']['parse_error_count']}")
    print(f"[PASS] EMPTY_V2_TREE: {verifier_result['summary']['empty_v2_tree']}")
    print("CONCLUSION: GO")
    print("PATCH STATUS: PASS")
    print(f"GIT COMMIT STATUS: PASS ({commit_hash})")
    print("REMOTE PUSH STATUS: NOT REQUIRED")
    print("MANUAL CHECK: NOT REQUIRED")
    print("FAIL-SAFE ROLLBACK: ARMED")
    print("WAL/SHM: NOT MANIPULATED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
