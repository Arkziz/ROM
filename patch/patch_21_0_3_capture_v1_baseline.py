#!/usr/bin/env python3
"""Stage 21.0.3: capture the authoritative ROM V1 baseline.

The patch must run on rewrite/rom-v2 at the accepted Stage 21.0.2 commit. It
creates a machine-readable V1 baseline manifest and a detailed Markdown
summary, verifies that production SQLite/WAL/SHM bytes remain unchanged, and
commits only this patch plus its two regulated artifacts.
"""
from __future__ import annotations

import ast
import hashlib
import json
import os
import re
import shutil
import sqlite3
import subprocess
import sys
import tempfile
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Sequence

STAGE = "21.0.3"
TARGET_BRANCH = "rewrite/rom-v2"
EXPECTED_PARENT = "2ba3cbb3aa25f196cb740df093dcfd0c397d25c2"
PATCH_PATH = "patch/patch_21_0_3_capture_v1_baseline.py"
JSON_PATH = "reports/stage_21_0_3_v1_baseline.json"
MD_PATH = "MD/STAGE_21_0_3_V1_BASELINE.md"
COMMIT_MESSAGE = "Stage 21.0.3: capture ROM V1 baseline"
OWNED_PATHS = {PATCH_PATH, JSON_PATH, MD_PATH}
ALLOWED_DIRTY = {"ROM_FULL_DUMP.txt", "ROM_ADDITIONAL_DUMP.txt"}
DB_FILES = ("game.db", "game.db-wal", "game.db-shm")
NON_PRODUCTION_TOP_LEVEL = {
    ".git", ".github", ".runtime", ".venv", "venv", "backup", "MD",
    "patch", "reports", "tools", "__pycache__", ".pytest_cache",
}
TEXT_SUFFIXES = {
    ".py", ".md", ".txt", ".json", ".toml", ".ini", ".cfg", ".yaml",
    ".yml", ".ps1", ".sh", ".sql", ".example",
}
CONFIG_NAME_PATTERN = re.compile(
    r"(?P<kind>getenv|environ_get|environ_index)\s*[:(\[]?\s*[\"'](?P<name>[A-Z][A-Z0-9_]{2,})[\"']"
)
DIRECT_ENV_PATTERNS = (
    re.compile(r"os\.getenv\(\s*[\"']([A-Z][A-Z0-9_]{2,})[\"']"),
    re.compile(r"os\.environ\.get\(\s*[\"']([A-Z][A-Z0-9_]{2,})[\"']"),
    re.compile(r"os\.environ\[\s*[\"']([A-Z][A-Z0-9_]{2,})[\"']\s*\]"),
)
REFERENCE_MARKERS = re.compile(
    r"(?i)\b(legacy|compat|candidate|shadow|deprecated|superseded|fallback|migration)\b"
)


@dataclass(frozen=True)
class Check:
    check_id: str
    status: str
    summary: str
    details: dict[str, Any]
    blocking: bool = False


class PatchError(RuntimeError):
    """Expected fail-safe patch failure."""


def run(root: Path, *command: str, timeout: int = 120) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        cwd=root,
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
        timeout=timeout,
        check=False,
    )


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


def file_evidence(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"exists": False}
    stat = path.stat()
    return {
        "exists": True,
        "size": stat.st_size,
        "mtime_ns": stat.st_mtime_ns,
        "sha256": sha256(path),
    }


def database_evidence(root: Path) -> dict[str, Any]:
    return {name: file_evidence(root / name) for name in DB_FILES}


def tracked_files(root: Path) -> list[str]:
    result = git(root, "ls-files", "-z")
    if result.returncode != 0:
        raise PatchError(result.stderr.strip() or "git ls-files failed")
    return sorted(item for item in result.stdout.split("\0") if item)


def parse_status(raw: str) -> list[dict[str, str]]:
    entries: list[dict[str, str]] = []
    parts = raw.split("\0")
    index = 0
    while index < len(parts):
        item = parts[index]
        if not item:
            index += 1
            continue
        status = item[:2]
        path = item[3:]
        entry = {"status": status, "path": path}
        if status[0] in {"R", "C"} and index + 1 < len(parts):
            entry["original_path"] = parts[index + 1]
            index += 1
        entries.append(entry)
        index += 1
    return entries


def write_atomic(path: Path, content: str) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(content, encoding="utf-8", newline="\n")
    os.replace(temporary, path)


def is_production_path(relative_path: str) -> bool:
    path = Path(relative_path)
    if not path.parts or path.parts[0] in NON_PRODUCTION_TOP_LEVEL:
        return False
    if path.name.startswith("ROM_") and path.suffix.lower() in {".txt", ".md", ".json"}:
        return False
    if path.name in {"game.db", "game.db-wal", "game.db-shm", ".env"}:
        return False
    return path.suffix.lower() in TEXT_SUFFIXES or path.name in {
        "main.py", "requirements.txt", "pyproject.toml", "poetry.lock", "Pipfile",
    }


def inventory_files(root: Path, paths: Iterable[str]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    production: list[dict[str, Any]] = []
    support: list[dict[str, Any]] = []
    for relative_path in paths:
        path = root / relative_path
        if not path.is_file():
            continue
        item = {
            "path": relative_path,
            "size": path.stat().st_size,
            "sha256": sha256(path),
            "suffix": path.suffix.lower(),
        }
        (production if is_production_path(relative_path) else support).append(item)
    return production, support


def python_inventory(root: Path, production: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    modules: list[dict[str, Any]] = []
    syntax_errors: list[dict[str, Any]] = []
    marker_files: list[dict[str, Any]] = []
    for item in production:
        if item["suffix"] != ".py":
            continue
        path = root / item["path"]
        text = path.read_text(encoding="utf-8", errors="replace")
        try:
            tree = ast.parse(text, filename=item["path"])
        except SyntaxError as exc:
            syntax_errors.append({"path": item["path"], "line": exc.lineno, "message": exc.msg})
            continue
        imports: set[str] = set()
        functions = 0
        classes = 0
        duplicate_top_level: list[str] = []
        seen: set[tuple[str, str]] = set()
        env_names: set[str] = set()
        for node in tree.body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                functions += 1
                token = ("function", node.name)
                if token in seen:
                    duplicate_top_level.append(node.name)
                seen.add(token)
            elif isinstance(node, ast.ClassDef):
                classes += 1
                token = ("class", node.name)
                if token in seen:
                    duplicate_top_level.append(node.name)
                seen.add(token)
            elif isinstance(node, ast.Import):
                imports.update(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imports.add(node.module)
        for pattern in DIRECT_ENV_PATTERNS:
            env_names.update(pattern.findall(text))
        markers = sorted(set(match.group(1).lower() for match in REFERENCE_MARKERS.finditer(text)))
        if markers or duplicate_top_level:
            marker_files.append({
                "path": item["path"],
                "markers": markers,
                "duplicate_top_level_symbols": sorted(set(duplicate_top_level)),
                "classification": "REFERENCE_REVIEW_REQUIRED",
            })
        modules.append({
            "path": item["path"],
            "functions": functions,
            "classes": classes,
            "imports": sorted(imports),
            "environment_variables": sorted(env_names),
            "duplicate_top_level_symbols": sorted(set(duplicate_top_level)),
        })
    return modules, syntax_errors, marker_files


def migration_inventory(root: Path, paths: list[str]) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for relative_path in paths:
        path = Path(relative_path)
        if "migrations" not in path.parts or path.suffix.lower() not in {".py", ".sql"}:
            continue
        full = root / relative_path
        numbers = re.findall(r"(?<!\d)(\d{3})(?!\d)", path.name)
        result.append({
            "path": relative_path,
            "migration_number_candidates": numbers,
            "sha256": sha256(full),
            "size": full.stat().st_size,
        })
    return sorted(result, key=lambda item: item["path"])


def dependency_inventory(root: Path, paths: list[str]) -> list[dict[str, Any]]:
    names = {"requirements.txt", "requirements-dev.txt", "pyproject.toml", "poetry.lock", "Pipfile", "Pipfile.lock"}
    return [
        {"path": item, "sha256": sha256(root / item), "size": (root / item).stat().st_size}
        for item in paths if Path(item).name in names and (root / item).is_file()
    ]


def verification_inventory(paths: list[str]) -> list[str]:
    result = []
    for item in paths:
        path = Path(item)
        lower = path.name.lower()
        if path.suffix.lower() == ".py" and path.parts and path.parts[0] == "tools" and any(
            token in lower for token in ("test", "verify", "regression", "contract", "check", "smoke")
        ):
            result.append(item)
    return sorted(result)


def content_inventory(paths: list[str]) -> dict[str, list[str]]:
    groups = {"data": [], "story_quests": [], "systems": [], "handlers": [], "db_modules": []}
    for item in paths:
        parts = Path(item).parts
        if not parts:
            continue
        if parts[0] == "data":
            groups["data"].append(item)
        if len(parts) > 1 and parts[0] == "data" and parts[1] == "story_quests":
            groups["story_quests"].append(item)
        if parts[0] in {"systems", "handlers", "db_modules"}:
            groups[parts[0]].append(item)
    return {name: sorted(values) for name, values in groups.items()}


def collect_database_schema(root: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    before = database_evidence(root)
    result: dict[str, Any] = {
        "production_connection_opened": False,
        "query_target": "isolated_snapshot",
        "production_evidence_before": before,
        "wal_shm_status": "NOT MANIPULATED",
    }
    database = root / "game.db"
    if not database.exists():
        result.update({"status": "ABSENT", "production_evidence_after": database_evidence(root)})
        return result, before
    with tempfile.TemporaryDirectory(prefix="rom_21_0_3_db_") as temp_name:
        snapshot_root = Path(temp_name)
        for name in DB_FILES:
            source = root / name
            if source.exists():
                shutil.copy2(source, snapshot_root / name)
        connection = sqlite3.connect((snapshot_root / "game.db").resolve().as_uri() + "?mode=ro", uri=True, timeout=5)
        connection.row_factory = sqlite3.Row
        try:
            quick_check = [row[0] for row in connection.execute("PRAGMA quick_check").fetchall()]
            foreign_key_violations = [dict(row) for row in connection.execute("PRAGMA foreign_key_check").fetchall()]
            user_version = connection.execute("PRAGMA user_version").fetchone()[0]
            objects = []
            for row in connection.execute(
                "SELECT type, name, tbl_name, sql FROM sqlite_master "
                "WHERE name NOT LIKE 'sqlite_%' ORDER BY type, name"
            ).fetchall():
                objects.append({
                    "type": row["type"], "name": row["name"], "table": row["tbl_name"],
                    "sql": row["sql"],
                })
            tables = []
            table_names = [item["name"] for item in objects if item["type"] == "table"]
            for table in table_names:
                quoted = table.replace('"', '""')
                columns = [dict(row) for row in connection.execute(f'PRAGMA table_info("{quoted}")').fetchall()]
                foreign_keys = [dict(row) for row in connection.execute(f'PRAGMA foreign_key_list("{quoted}")').fetchall()]
                indexes = [dict(row) for row in connection.execute(f'PRAGMA index_list("{quoted}")').fetchall()]
                tables.append({"name": table, "columns": columns, "foreign_keys": foreign_keys, "indexes": indexes})
        finally:
            connection.close()
    after = database_evidence(root)
    result.update({
        "status": "PASS" if quick_check == ["ok"] and not foreign_key_violations and before == after else "FAIL",
        "quick_check": quick_check,
        "foreign_key_violations": foreign_key_violations,
        "user_version": user_version,
        "objects": objects,
        "tables": tables,
        "counts": {
            "tables": sum(item["type"] == "table" for item in objects),
            "indexes": sum(item["type"] == "index" for item in objects),
            "triggers": sum(item["type"] == "trigger" for item in objects),
            "views": sum(item["type"] == "view" for item in objects),
        },
        "production_evidence_after": after,
        "production_bytes_unchanged": before == after,
    })
    return result, after


def render_markdown(payload: dict[str, Any]) -> str:
    inv = payload["inventory"]
    db = payload["database"]
    checks = payload["checks"]
    rows = [
        f"| `{item['check_id']}` | **{item['status']}** | {'так' if item['blocking'] else 'ні'} | {item['summary'].replace('|', '/')} |"
        for item in checks
    ]
    return "\n".join([
        "# ROM Stage 21.0.3 - baseline ROM V1", "",
        f"- **Статус:** `{payload['summary']['conclusion']}`",
        f"- **Гілка:** `{payload['git']['branch']}`",
        f"- **Parent commit:** `{payload['git']['head_before_commit']}`",
        f"- **Production-файлів:** `{len(inv['production_files'])}`",
        f"- **Python-модулів:** `{len(inv['python_modules'])}`",
        f"- **Міграційних файлів:** `{len(inv['migrations'])}`",
        f"- **Verifier/test-файлів:** `{len(inv['verification_files'])}`",
        f"- **Таблиць БД:** `{db.get('counts', {}).get('tables', 0)}`", "",
        "## Перевірки", "", "| ID | Статус | Blocking | Результат |", "|---|---:|---:|---|", *rows, "",
        "## Зафіксовані категорії", "",
        "- Повний SHA-256 inventory tracked production і support files міститься у JSON.",
        "- Python AST inventory містить imports, environment variable names, top-level functions/classes і повторні top-level symbols.",
        "- Database schema зібрана тільки з isolated snapshot і містить tables, columns, foreign keys, indexes, triggers та views.",
        "- Окремо зафіксовані migrations, dependencies, tools/verifiers і content packages.",
        "- Файли з legacy/compat/candidate/shadow/deprecated/superseded/fallback markers позначено `REFERENCE_REVIEW_REQUIRED`.", "",
        "## Правило використання baseline", "",
        "- V1 є джерелом підтвердженої поведінки, контенту та parity fixtures.",
        "- V1 runtime modules не можна імпортувати у майбутній `rom_v2` production runtime.",
        "- Позначені reference-файли не переносяться механічно; authoritative owner визначається окремим контрактним аудитом Stage 21.1.",
        "- Старі Stage 19-20 MD/JSON не відновлюються у робоче дерево; Git history залишається джерелом історичних артефактів.", "",
        "## SQLite safety", "",
        "- Production `game.db` не відкривалася через SQLite.",
        "- `quick_check` і schema inventory виконано на isolated snapshot.",
        "- `game.db-wal` і `game.db-shm` не видалялися, не очищувалися та не використовувалися для rollback.",
        f"- Побайтова незмінність production DB/WAL/SHM: `{db.get('production_bytes_unchanged')}`.", "",
        "## Наступний етап", "",
        "Stage 21.0.4 - створення анотованого Git tag фінального baseline Stage 20/V1.", "",
    ])


def exact_commit(root: Path) -> str:
    paths = [PATCH_PATH, JSON_PATH, MD_PATH]
    add = git(root, "add", "-f", "--", *paths)
    if add.returncode != 0:
        raise PatchError(add.stderr.strip() or "git add failed")
    staged_result = git(root, "diff", "--cached", "--name-only", "-z")
    if staged_result.returncode != 0:
        raise PatchError(staged_result.stderr.strip() or "cannot inspect staged files")
    staged = sorted(item for item in staged_result.stdout.split("\0") if item)
    if staged != sorted(paths):
        git(root, "reset", "--", *paths)
        raise PatchError(f"staging allowlist mismatch: {staged}")
    commit = git(root, "commit", "-m", COMMIT_MESSAGE)
    if commit.returncode != 0:
        git(root, "reset", "--", *paths)
        raise PatchError(commit.stderr.strip() or commit.stdout.strip() or "git commit failed")
    commit_hash = rev(root, "HEAD")
    if not commit_hash:
        raise PatchError("commit created but HEAD cannot be resolved")
    return commit_hash


def main() -> int:
    root = Path(__file__).resolve().parent.parent
    if not (root / ".git").exists():
        print("[FAIL] Run this file from ROM\\patch.", file=sys.stderr)
        return 2
    if not (root / "reports").is_dir() or not (root / "MD").is_dir():
        print("[FAIL] Required reports and MD directories are missing.", file=sys.stderr)
        return 2

    print("[1/8] [PASS] ROM root and regulated artifact directories detected.")
    branch = git(root, "branch", "--show-current").stdout.strip()
    head = rev(root, "HEAD")
    upstream = git(root, "rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{u}")
    upstream_name = upstream.stdout.strip() if upstream.returncode == 0 else None
    upstream_head = rev(root, upstream_name) if upstream_name else None

    status_result = git(root, "status", "--porcelain=v1", "-z", "--untracked-files=all")
    entries = parse_status(status_result.stdout) if status_result.returncode == 0 else []
    allowed: list[dict[str, str]] = []
    for entry in entries:
        index_status = entry["status"][0]
        path = entry["path"]
        if index_status in {" ", "?"} and (path in OWNED_PATHS or (path in ALLOWED_DIRTY and index_status == " ")):
            allowed.append(entry)
    unexpected = [entry for entry in entries if entry not in allowed]

    checks: list[Check] = [
        Check("TARGET_BRANCH", "PASS" if branch == TARGET_BRANCH else "FAIL", f"Active branch is {branch or 'detached HEAD'}.", {"expected": TARGET_BRANCH}, branch != TARGET_BRANCH),
        Check("EXPECTED_PARENT", "PASS" if head == EXPECTED_PARENT else "FAIL", "HEAD matches accepted Stage 21.0.2 commit." if head == EXPECTED_PARENT else "HEAD differs from accepted Stage 21.0.2 commit.", {"expected": EXPECTED_PARENT, "actual": head}, head != EXPECTED_PARENT),
        Check("UPSTREAM", "PASS" if upstream_name == f"origin/{TARGET_BRANCH}" and upstream_head == head else "FAIL", "Rewrite branch upstream is configured and synchronized." if upstream_name == f"origin/{TARGET_BRANCH}" and upstream_head == head else "Rewrite branch upstream is missing or not synchronized.", {"upstream": upstream_name, "local": head, "remote": upstream_head}, not (upstream_name == f"origin/{TARGET_BRANCH}" and upstream_head == head)),
        Check("WORKTREE", "PASS" if not unexpected else "FAIL", "Working tree has no unexpected or pre-staged changes." if not unexpected else "Unexpected or pre-staged changes exist.", {"unexpected": unexpected, "allowed": allowed}, bool(unexpected)),
    ]
    blockers = [item.check_id for item in checks if item.blocking]
    if blockers:
        print("[2/8] [FAIL] Preflight returned NO_GO.")
        print("Blocking failures: " + ", ".join(blockers))
        return 1

    print("[2/8] [PASS] Branch, parent, upstream and worktree preflight passed.")
    db_before = database_evidence(root)
    paths = tracked_files(root)

    print("[3/8] [PASS] Building tracked production/support file inventory and SHA-256 manifest.")
    production_files, support_files = inventory_files(root, paths)

    print("[4/8] [PASS] Parsing Python modules, imports, environment names and reference markers.")
    python_modules, syntax_errors, reference_review = python_inventory(root, production_files)
    checks.append(Check("PYTHON_SYNTAX", "PASS" if not syntax_errors else "FAIL", "All tracked production Python modules parse successfully." if not syntax_errors else "Production Python syntax errors were found.", {"errors": syntax_errors}, bool(syntax_errors)))

    print("[5/8] [PASS] Capturing migration, dependency, verifier and content inventories.")
    migrations = migration_inventory(root, paths)
    dependencies = dependency_inventory(root, paths)
    verifiers = verification_inventory(paths)
    content = content_inventory(paths)
    checks.extend([
        Check("PRODUCTION_INVENTORY", "PASS" if production_files else "FAIL", f"Captured {len(production_files)} production files.", {}, not production_files),
        Check("MIGRATION_INVENTORY", "PASS" if migrations else "WARN", f"Captured {len(migrations)} migration files.", {}, False),
        Check("VERIFIER_INVENTORY", "PASS" if verifiers else "WARN", f"Captured {len(verifiers)} verifier/test files.", {}, False),
    ])

    print("[6/8] [PASS] Capturing complete SQLite schema from an isolated snapshot.")
    try:
        database, db_after_schema = collect_database_schema(root)
    except (OSError, sqlite3.Error) as exc:
        print(f"[FAIL] Database snapshot inventory failed: {exc}", file=sys.stderr)
        return 2
    db_ok = database.get("status") in {"PASS", "ABSENT"} and db_before == db_after_schema
    checks.append(Check("DATABASE_SCHEMA", "PASS" if db_ok else "FAIL", "Database schema captured safely and production bytes are unchanged." if db_ok else "Database schema capture or byte preservation failed.", {"status": database.get("status")}, not db_ok))

    blockers = [item.check_id for item in checks if item.blocking]
    conclusion = "GO" if not blockers else "NO_GO"
    print("[7/8] [PASS] Writing authoritative V1 baseline artifacts.")
    payload = {
        "schema_version": 1,
        "stage": STAGE,
        "generated_at_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "summary": {
            "conclusion": conclusion,
            "blocking_failures": blockers,
            "production_file_count": len(production_files),
            "python_module_count": len(python_modules),
            "migration_count": len(migrations),
            "verification_file_count": len(verifiers),
            "reference_review_file_count": len(reference_review),
        },
        "git": {
            "branch": branch,
            "head_before_commit": head,
            "upstream": upstream_name,
            "upstream_head": upstream_head,
            "stage_20_closure_ancestor": git(root, "merge-base", "--is-ancestor", "bd6880020d3918d2ca3c071950975826dc69320c", "HEAD").returncode == 0,
        },
        "checks": [asdict(item) for item in checks],
        "inventory": {
            "production_files": production_files,
            "support_files": support_files,
            "python_modules": python_modules,
            "migrations": migrations,
            "dependencies": dependencies,
            "verification_files": verifiers,
            "content_groups": content,
            "reference_review_required": reference_review,
        },
        "database": database,
        "constraints": {
            "v1_runtime_import_into_v2": "FORBIDDEN",
            "historical_stage_19_20_artifacts_restored": False,
            "database_migration_required_now": False,
            "v2_database_strategy": "RESET_FIRST",
        },
        "artifacts": {"patch": PATCH_PATH, "json": JSON_PATH, "markdown": MD_PATH},
        "next_stage": "21.0.4" if conclusion == "GO" else None,
    }
    write_atomic(root / JSON_PATH, json.dumps(payload, ensure_ascii=False, indent=2) + "\n")
    write_atomic(root / MD_PATH, render_markdown(payload))

    if conclusion != "GO":
        print("[8/8] [FAIL] Baseline contains blocking failures; commit not created.")
        print("PATCH STATUS: FAIL\nGIT COMMIT STATUS: NOT CREATED\nMANUAL CHECK: NOT REQUIRED\nWAL/SHM: NOT MANIPULATED")
        print("Blocking failures: " + ", ".join(blockers))
        return 1

    try:
        commit_hash = exact_commit(root)
    except PatchError as exc:
        print(f"[8/8] [FAIL] {exc}", file=sys.stderr)
        print("PATCH STATUS: FAIL\nGIT COMMIT STATUS: FAIL\nMANUAL CHECK: NOT REQUIRED\nWAL/SHM: NOT MANIPULATED")
        return 2

    db_final = database_evidence(root)
    final_ok = db_before == db_final and git(root, "branch", "--show-current").stdout.strip() == TARGET_BRANCH
    if not final_ok:
        print("[8/8] [FAIL] Post-commit branch or SQLite evidence verification failed.", file=sys.stderr)
        print("PATCH STATUS: FAIL\nGIT COMMIT STATUS: CREATED BUT RECOVERY REVIEW REQUIRED\nMANUAL CHECK: NOT REQUIRED\nWAL/SHM: NOT MANIPULATED")
        return 2

    print(f"[8/8] [PASS] Baseline committed and post-commit evidence verified: {commit_hash}")
    print("=" * 72)
    print(f"ROM Stage {STAGE} - capture V1 baseline")
    print("=" * 72)
    for item in checks:
        print(f"[{item.status}] {item.check_id}: {item.summary}")
    print(f"[PASS] PRODUCTION_FILES: {len(production_files)}")
    print(f"[PASS] PYTHON_MODULES: {len(python_modules)}")
    print(f"[PASS] MIGRATIONS: {len(migrations)}")
    print(f"[PASS] VERIFIERS: {len(verifiers)}")
    print(f"[PASS] REFERENCE_REVIEW_REQUIRED: {len(reference_review)}")
    print("-" * 72)
    print("CONCLUSION: GO")
    print("PATCH STATUS: PASS")
    print(f"GIT COMMIT STATUS: PASS ({commit_hash})")
    print("REMOTE PUSH STATUS: NOT REQUIRED")
    print("MANUAL CHECK: NOT REQUIRED")
    print("WAL/SHM: NOT MANIPULATED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
