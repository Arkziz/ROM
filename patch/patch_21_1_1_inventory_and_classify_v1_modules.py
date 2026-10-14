#!/usr/bin/env python3
"""Stage 21.1.1: inventory and classify every tracked ROM V1 Python module.

The patch is read-only for production code and SQLite. It derives classifications
from path, AST structure, imports, duplicate definitions, registration patterns,
SQL/Telegram coupling, and historical markers. It writes JSON to reports and
Markdown to MD, then commits only the patch and both regulated artifacts.
"""
from __future__ import annotations

import ast
import hashlib
import json
import os
import re
import subprocess
import sys
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Sequence

STAGE = "21.1.1"
TARGET_BRANCH = "rewrite/rom-v2"
EXPECTED_PARENT = "b544f2429a1b80e8e3bab1aa05246367f1bc3fab"
V1_BASELINE_TAG = "rom-v1-baseline-stage-20"
V1_BASELINE_COMMIT = "ff9f4920519ca5154ff1238ddaae67cb9ee2ce29"
PATCH_PATH = "patch/patch_21_1_1_inventory_and_classify_v1_modules.py"
JSON_PATH = "reports/stage_21_1_1_v1_module_inventory.json"
MD_PATH = "MD/STAGE_21_1_1_V1_MODULE_INVENTORY.md"
COMMIT_MESSAGE = "Stage 21.1.1: inventory and classify V1 modules"
OWNED_PATHS = {PATCH_PATH, JSON_PATH, MD_PATH}
ALLOWED_DIRTY = {"ROM_FULL_DUMP.txt", "ROM_ADDITIONAL_DUMP.txt"}
DB_FILES = ("game.db", "game.db-wal", "game.db-shm")

CLASS_REWRITE = "REWRITE"
CLASS_CONTENT = "CONTENT_EXTRACT"
CLASS_TEST = "TEST_REFERENCE"
CLASS_SKIP = "DO_NOT_MIGRATE"
CLASS_MANUAL = "NEEDS_MANUAL_REVIEW"
VALID_CLASSES = {CLASS_REWRITE, CLASS_CONTENT, CLASS_TEST, CLASS_SKIP, CLASS_MANUAL}

NON_MODULE_TOP_LEVEL = {
    ".git", ".github", ".runtime", ".venv", "venv", "backup", "MD",
    "patch", "reports", "__pycache__", ".pytest_cache",
}
TEST_NAME_RE = re.compile(r"(?i)(^test_|_test\.py$|smoke|regression|verify|contract|check_)")
HISTORICAL_RE = re.compile(r"(?i)\b(legacy|compat|candidate|shadow|deprecated|superseded|obsolete|fallback)\b")
SQL_RE = re.compile(r"(?i)\b(SELECT|INSERT|UPDATE|DELETE|CREATE TABLE|ALTER TABLE|DROP TABLE|PRAGMA)\b")
CALLBACK_RE = re.compile(r"(?i)(callback|register_.*handler|message_handler|callback_query_handler)")
TELEGRAM_IMPORT_PREFIXES = ("telegram", "aiogram", "telebot")
DATABASE_IMPORT_PREFIXES = ("sqlite3", "db", "db_modules")
MIGRATION_PARTS = {"migration", "migrations"}
DATA_EXTENSIONS = {".json", ".yaml", ".yml", ".toml", ".csv"}


@dataclass(frozen=True)
class Check:
    check_id: str
    status: str
    summary: str
    details: dict[str, Any]
    blocking: bool = False


@dataclass
class ModuleRecord:
    path: str
    sha256: str
    size: int
    classification: str
    confidence: str
    primary_reason: str
    reasons: list[str]
    top_level_functions: list[str]
    top_level_classes: list[str]
    duplicate_functions: list[str]
    duplicate_classes: list[str]
    imports: list[str]
    imports_telegram: bool
    imports_database: bool
    contains_sql: bool
    contains_handler_registration: bool
    historical_markers: list[str]
    exported_symbols: list[str]
    inbound_importers: list[str]
    recommended_v2_destination: str | None
    authoritative_owner_status: str
    unresolved_questions: list[str]


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


def database_evidence(root: Path) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for name in DB_FILES:
        path = root / name
        if not path.exists():
            result[name] = {"exists": False}
            continue
        stat = path.stat()
        result[name] = {
            "exists": True,
            "size": stat.st_size,
            "mtime_ns": stat.st_mtime_ns,
            "sha256": sha256(path),
        }
    return result


def write_atomic(path: Path, content: str) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(content, encoding="utf-8", newline="\n")
    os.replace(temporary, path)


def parse_status(raw: str) -> list[dict[str, str]]:
    result: list[dict[str, str]] = []
    parts = raw.split("\0")
    index = 0
    while index < len(parts):
        item = parts[index]
        if not item:
            index += 1
            continue
        status = item[:2]
        entry = {"status": status, "path": item[3:]}
        if status[0] in {"R", "C"} and index + 1 < len(parts):
            entry["original_path"] = parts[index + 1]
            index += 1
        result.append(entry)
        index += 1
    return result


def tracked_files(root: Path) -> list[str]:
    output = git(root, "ls-files", "-z")
    if output.returncode != 0:
        raise PatchError(output.stderr.strip() or "git ls-files failed")
    return sorted(item for item in output.stdout.split("\0") if item)


def is_v1_module(path: str) -> bool:
    item = Path(path)
    if item.suffix.lower() != ".py" or not item.parts:
        return False
    if item.parts[0] in NON_MODULE_TOP_LEVEL:
        return False
    return True


def module_name(path: str) -> str:
    item = Path(path).with_suffix("")
    parts = list(item.parts)
    if parts and parts[-1] == "__init__":
        parts = parts[:-1]
    return ".".join(parts)


def resolve_import(current_path: str, module: str | None, level: int) -> str | None:
    current_parts = list(Path(current_path).with_suffix("").parts[:-1])
    if level:
        if level > len(current_parts) + 1:
            return None
        base = current_parts[: len(current_parts) - level + 1]
    else:
        base = []
    if module:
        base.extend(module.split("."))
    return ".".join(base) if base else None


def migration_module(path: str) -> bool:
    parts = {part.lower() for part in Path(path).parts}
    return bool(parts & MIGRATION_PARTS)


def test_reference_module(path: str) -> bool:
    item = Path(path)
    parts = {part.lower() for part in item.parts}
    return bool(parts & {"tests", "test", "fixtures"}) or bool(TEST_NAME_RE.search(item.name))


def content_module(path: str) -> bool:
    parts = Path(path).parts
    if not parts:
        return False
    if parts[0] != "data":
        return False
    # Data modules are extracted as content unless their name clearly identifies
    # compatibility, migration or test-only behavior.
    return True


def recommended_destination(path: str, classification: str) -> str | None:
    parts = Path(path).parts
    name = Path(path).stem
    if classification == CLASS_CONTENT:
        if len(parts) > 1 and parts[1] == "story_quests":
            return f"rom_v2/content/quests/{name}.py"
        return f"rom_v2/content/catalogs/{name}.py"
    if classification == CLASS_REWRITE:
        if parts and parts[0] == "handlers":
            return f"rom_v2/infrastructure/telegram/handlers/{name}.py"
        if parts and parts[0] == "db_modules":
            return f"rom_v2/infrastructure/database/repositories/{name}.py"
        if parts and parts[0] == "systems":
            return f"rom_v2/domain/<domain>/{name}.py"
        if name == "main":
            return "rom_v2/main.py"
        return f"rom_v2/application_or_domain/{name}.py"
    if classification == CLASS_TEST:
        return f"tests_v2/reference/{name}.py"
    return None


def classify_module(
    path: str,
    text: str,
    tree: ast.Module,
    imports: set[str],
    duplicate_functions: list[str],
    duplicate_classes: list[str],
    historical_markers: list[str],
    contains_sql: bool,
    contains_registration: bool,
    imports_telegram: bool,
) -> tuple[str, str, str, list[str], str, list[str]]:
    reasons: list[str] = []
    unresolved: list[str] = []
    lower_path = path.lower()

    if migration_module(path):
        classification = CLASS_SKIP
        reasons.append("Historical V1 migration; V2 uses a clean baseline schema.")
        primary = reasons[0]
        confidence = "HIGH"
    elif test_reference_module(path):
        classification = CLASS_TEST
        reasons.append("Test, smoke, regression, verification or fixture module.")
        primary = reasons[0]
        confidence = "HIGH"
    elif content_module(path):
        if historical_markers and any(token in lower_path for token in ("legacy", "compat", "candidate", "shadow", "deprecated")):
            classification = CLASS_MANUAL
            reasons.append("Data module contains an explicit historical/compatibility identity.")
            unresolved.append("Confirm authoritative content owner before extraction.")
            primary = reasons[0]
            confidence = "MEDIUM"
        else:
            classification = CLASS_CONTENT
            reasons.append("Static or catalog-like data belongs in validated V2 content.")
            primary = reasons[0]
            confidence = "HIGH"
    elif Path(path).name == "__init__.py" and len(tree.body) == 0:
        classification = CLASS_SKIP
        reasons.append("Empty package marker; V2 creates its own package boundaries.")
        primary = reasons[0]
        confidence = "HIGH"
    elif duplicate_functions or duplicate_classes:
        classification = CLASS_MANUAL
        reasons.append("Repeated top-level definitions require effective-owner analysis before rewrite.")
        unresolved.append("Determine runtime-effective definition and accepted behavior.")
        primary = reasons[0]
        confidence = "HIGH"
    elif historical_markers and any(token in lower_path for token in ("legacy", "compat", "candidate", "shadow", "deprecated")):
        classification = CLASS_MANUAL
        reasons.append("Module identity indicates legacy/compatibility/shadow behavior.")
        unresolved.append("Decide whether any behavior remains authoritative.")
        primary = reasons[0]
        confidence = "MEDIUM"
    else:
        classification = CLASS_REWRITE
        reasons.append("Runtime behavior must be reimplemented behind clean V2 boundaries.")
        primary = reasons[0]
        confidence = "HIGH"

    if contains_sql:
        reasons.append("Contains SQL and must be isolated behind V2 repositories/Unit of Work.")
    if imports_telegram or contains_registration:
        reasons.append("Contains Telegram/handler coupling and must not enter V2 domain logic.")
    if historical_markers:
        reasons.append("Historical markers: " + ", ".join(historical_markers) + ".")
    if duplicate_functions:
        reasons.append("Duplicate functions: " + ", ".join(duplicate_functions) + ".")
    if duplicate_classes:
        reasons.append("Duplicate classes: " + ", ".join(duplicate_classes) + ".")

    if classification in {CLASS_CONTENT, CLASS_TEST, CLASS_SKIP}:
        owner_status = "NOT_A_V2_RUNTIME_OWNER"
    elif classification == CLASS_REWRITE:
        owner_status = "BEHAVIOR_REFERENCE_ONLY"
    else:
        owner_status = "OWNER_UNRESOLVED"
    return classification, confidence, primary, reasons, owner_status, unresolved


def parse_modules(root: Path, paths: list[str]) -> tuple[list[ModuleRecord], list[dict[str, Any]], dict[str, list[str]]]:
    parsed: dict[str, dict[str, Any]] = {}
    syntax_errors: list[dict[str, Any]] = []
    module_to_path = {module_name(path): path for path in paths}
    inbound: dict[str, set[str]] = defaultdict(set)

    for path in paths:
        full = root / path
        text = full.read_text(encoding="utf-8", errors="replace")
        try:
            tree = ast.parse(text, filename=path)
        except SyntaxError as exc:
            syntax_errors.append({"path": path, "line": exc.lineno, "message": exc.msg})
            continue

        functions = [node.name for node in tree.body if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))]
        classes = [node.name for node in tree.body if isinstance(node, ast.ClassDef)]
        duplicate_functions = sorted(name for name, count in Counter(functions).items() if count > 1)
        duplicate_classes = sorted(name for name, count in Counter(classes).items() if count > 1)
        imports: set[str] = set()
        resolved_internal_imports: set[str] = set()
        exported_symbols: list[str] = []

        for node in tree.body:
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.add(alias.name)
                    if alias.name in module_to_path:
                        resolved_internal_imports.add(alias.name)
            elif isinstance(node, ast.ImportFrom):
                resolved = resolve_import(path, node.module, node.level)
                if node.module:
                    imports.add(("." * node.level) + node.module)
                elif node.level:
                    imports.add("." * node.level)
                if resolved and resolved in module_to_path:
                    resolved_internal_imports.add(resolved)
            elif isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name) and target.id == "__all__":
                        try:
                            values = ast.literal_eval(node.value)
                            if isinstance(values, (list, tuple)):
                                exported_symbols.extend(str(item) for item in values)
                        except (ValueError, TypeError):
                            pass

        current_module = module_name(path)
        for imported in resolved_internal_imports:
            inbound[module_to_path[imported]].add(path)

        markers = sorted(set(match.group(1).lower() for match in HISTORICAL_RE.finditer(text)))
        contains_sql = bool(SQL_RE.search(text)) or "sqlite3" in imports
        contains_registration = bool(CALLBACK_RE.search(text))
        imports_telegram = any(item.lstrip(".").startswith(TELEGRAM_IMPORT_PREFIXES) for item in imports)
        imports_database = any(item.lstrip(".").startswith(DATABASE_IMPORT_PREFIXES) for item in imports)
        classification, confidence, primary, reasons, owner_status, unresolved = classify_module(
            path, text, tree, imports, duplicate_functions, duplicate_classes,
            markers, contains_sql, contains_registration, imports_telegram,
        )
        parsed[path] = {
            "record": ModuleRecord(
                path=path,
                sha256=sha256(full),
                size=full.stat().st_size,
                classification=classification,
                confidence=confidence,
                primary_reason=primary,
                reasons=reasons,
                top_level_functions=functions,
                top_level_classes=classes,
                duplicate_functions=duplicate_functions,
                duplicate_classes=duplicate_classes,
                imports=sorted(imports),
                imports_telegram=imports_telegram,
                imports_database=imports_database,
                contains_sql=contains_sql,
                contains_handler_registration=contains_registration,
                historical_markers=markers,
                exported_symbols=sorted(set(exported_symbols)),
                inbound_importers=[],
                recommended_v2_destination=recommended_destination(path, classification),
                authoritative_owner_status=owner_status,
                unresolved_questions=unresolved,
            ),
            "module": current_module,
        }

    records: list[ModuleRecord] = []
    for path in sorted(parsed):
        record: ModuleRecord = parsed[path]["record"]
        record.inbound_importers = sorted(inbound.get(path, set()))
        records.append(record)
    return records, syntax_errors, {key: sorted(value) for key, value in inbound.items()}


def classify_non_python_content(root: Path, tracked: list[str]) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for path in tracked:
        item = Path(path)
        if item.suffix.lower() not in DATA_EXTENSIONS or not item.parts or item.parts[0] != "data":
            continue
        full = root / path
        records.append({
            "path": path,
            "sha256": sha256(full),
            "size": full.stat().st_size,
            "classification": CLASS_CONTENT,
            "primary_reason": "Non-Python data catalog/content under data/.",
            "recommended_v2_destination": f"rom_v2/content/catalogs/{item.name}",
        })
    return records


def render_markdown(payload: dict[str, Any]) -> str:
    summary = payload["summary"]
    counts = summary["classification_counts"]
    examples = payload["review_queues"]
    lines = [
        "# ROM Stage 21.1.1 - інвентаризація та класифікація модулів V1", "",
        f"- **Статус:** `{summary['conclusion']}`",
        f"- **Гілка:** `{payload['git']['branch']}`",
        f"- **Parent commit:** `{payload['git']['head_before_commit']}`",
        f"- **Python-модулів V1:** `{summary['module_count']}`",
        f"- **Non-Python content records:** `{summary['non_python_content_count']}`",
        f"- **Syntax errors:** `{summary['syntax_error_count']}`", "",
        "## Класифікація", "",
        f"- `REWRITE`: **{counts.get(CLASS_REWRITE, 0)}**",
        f"- `CONTENT_EXTRACT`: **{counts.get(CLASS_CONTENT, 0)}**",
        f"- `TEST_REFERENCE`: **{counts.get(CLASS_TEST, 0)}**",
        f"- `DO_NOT_MIGRATE`: **{counts.get(CLASS_SKIP, 0)}**",
        f"- `NEEDS_MANUAL_REVIEW`: **{counts.get(CLASS_MANUAL, 0)}**", "",
        "## Значення категорій", "",
        "- `REWRITE`: поведінку відтворити через чисті V2 domain/application/infrastructure boundaries; код V1 не імпортувати.",
        "- `CONTENT_EXTRACT`: витягнути лише accepted data/content, пропустити через schema validation і canonical content loader.",
        "- `TEST_REFERENCE`: використати для fixtures, parity та acceptance, але не як production runtime.",
        "- `DO_NOT_MIGRATE`: історичні migrations, порожні package markers або інші артефакти, які V2 створює заново.",
        "- `NEEDS_MANUAL_REVIEW`: effective owner або accepted behavior неможливо безпечно визначити лише статично.", "",
        "## Черги подальшого аудиту", "",
        f"- Повторні top-level definitions: **{len(examples['duplicate_definition_modules'])}** модулів.",
        f"- Telegram + SQL coupling: **{len(examples['telegram_sql_coupled_modules'])}** модулів.",
        f"- Historical/compatibility markers: **{len(examples['historical_marker_modules'])}** модулів.",
        f"- Unresolved owner: **{len(examples['owner_unresolved_modules'])}** модулів.", "",
        "## Правила використання", "",
        "- Класифікація є planning contract, а не дозволом механічно копіювати файл.",
        "- Будь-який `NEEDS_MANUAL_REVIEW` має пройти окремий owner/runtime audit до реалізації V2.",
        "- Уся деталізація по кожному модулю, SHA-256, imports, дублікати, markers, inbound importers і рекомендований destination містяться у JSON.",
        "- Production `game.db`, `game.db-wal` і `game.db-shm` не відкривалися та не змінювалися.", "",
        "## Наступний етап", "",
        "Stage 21.1.2 - AST-аудит повторних визначень, alias chains і runtime overrides.", "",
    ]
    return "\n".join(lines)


def exact_commit(root: Path) -> str:
    paths = [PATCH_PATH, JSON_PATH, MD_PATH]
    add = git(root, "add", "-f", "--", *paths)
    if add.returncode != 0:
        raise PatchError(add.stderr.strip() or "git add failed")
    staged_output = git(root, "diff", "--cached", "--name-only", "-z")
    staged = sorted(item for item in staged_output.stdout.split("\0") if item)
    if staged_output.returncode != 0 or staged != sorted(paths):
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
    tag_target = rev(root, V1_BASELINE_TAG)
    upstream_output = git(root, "rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{u}")
    upstream = upstream_output.stdout.strip() if upstream_output.returncode == 0 else None

    status_output = git(root, "status", "--porcelain=v1", "-z", "--untracked-files=all")
    entries = parse_status(status_output.stdout) if status_output.returncode == 0 else []
    allowed: list[dict[str, str]] = []
    for entry in entries:
        index_status = entry["status"][0]
        path = entry["path"]
        if index_status in {" ", "?"} and (path in OWNED_PATHS or (path in ALLOWED_DIRTY and index_status == " ")):
            allowed.append(entry)
    unexpected = [entry for entry in entries if entry not in allowed]

    checks: list[Check] = [
        Check("TARGET_BRANCH", "PASS" if branch == TARGET_BRANCH else "FAIL", f"Active branch is {branch or 'detached HEAD'}.", {"expected": TARGET_BRANCH}, branch != TARGET_BRANCH),
        Check("EXPECTED_PARENT", "PASS" if head == EXPECTED_PARENT else "FAIL", "HEAD matches accepted Stage 21.0.4 commit." if head == EXPECTED_PARENT else "HEAD differs from accepted Stage 21.0.4 commit.", {"expected": EXPECTED_PARENT, "actual": head}, head != EXPECTED_PARENT),
        Check("UPSTREAM", "PASS" if upstream == f"origin/{TARGET_BRANCH}" else "FAIL", "Rewrite upstream is configured." if upstream == f"origin/{TARGET_BRANCH}" else "Rewrite upstream is missing or incorrect.", {"upstream": upstream}, upstream != f"origin/{TARGET_BRANCH}"),
        Check("V1_BASELINE_TAG", "PASS" if tag_target == V1_BASELINE_COMMIT else "FAIL", "V1 baseline tag resolves to the approved commit." if tag_target == V1_BASELINE_COMMIT else "V1 baseline tag target is missing or incorrect.", {"expected": V1_BASELINE_COMMIT, "actual": tag_target}, tag_target != V1_BASELINE_COMMIT),
        Check("WORKTREE", "PASS" if not unexpected else "FAIL", "Working tree has no unexpected or pre-staged changes." if not unexpected else "Unexpected or pre-staged changes exist.", {"unexpected": unexpected, "allowed": allowed}, bool(unexpected)),
    ]
    blockers = [item.check_id for item in checks if item.blocking]
    if blockers:
        print("[2/8] [FAIL] Preflight returned NO_GO.")
        print("Blocking failures: " + ", ".join(blockers))
        return 1

    print("[2/8] [PASS] Branch, parent, upstream, V1 tag and worktree preflight passed.")
    db_before = database_evidence(root)
    tracked = tracked_files(root)
    module_paths = [path for path in tracked if is_v1_module(path)]

    print(f"[3/8] [PASS] Parsing and classifying {len(module_paths)} tracked V1 Python modules.")
    records, syntax_errors, inbound_graph = parse_modules(root, module_paths)

    print("[4/8] [PASS] Classifying non-Python content and building review queues.")
    non_python_content = classify_non_python_content(root, tracked)
    classification_counts = Counter(record.classification for record in records)
    duplicate_modules = [record.path for record in records if record.duplicate_functions or record.duplicate_classes]
    telegram_sql = [record.path for record in records if record.imports_telegram and record.contains_sql]
    historical = [record.path for record in records if record.historical_markers]
    unresolved = [record.path for record in records if record.authoritative_owner_status == "OWNER_UNRESOLVED"]
    checks.extend([
        Check("PYTHON_SYNTAX", "PASS" if not syntax_errors else "FAIL", "All classified Python modules parse successfully." if not syntax_errors else "Syntax errors were found in V1 modules.", {"errors": syntax_errors}, bool(syntax_errors)),
        Check("MODULE_COVERAGE", "PASS" if len(records) == len(module_paths) else "FAIL", f"Classified all {len(module_paths)} V1 modules." if len(records) == len(module_paths) else "Not all V1 modules were classified.", {"expected": len(module_paths), "actual": len(records)}, len(records) != len(module_paths)),
        Check("CLASSIFICATION_CONTRACT", "PASS" if all(record.classification in VALID_CLASSES for record in records) else "FAIL", "Every module uses an approved classification.", {}, any(record.classification not in VALID_CLASSES for record in records)),
    ])

    print("[5/8] [PASS] Building machine-readable owner and dependency inventory.")
    owner_registry = {
        record.path: {
            "classification": record.classification,
            "owner_status": record.authoritative_owner_status,
            "recommended_v2_destination": record.recommended_v2_destination,
        }
        for record in records
    }
    blockers = [item.check_id for item in checks if item.blocking]
    conclusion = "GO" if not blockers else "NO_GO"

    payload = {
        "schema_version": 1,
        "stage": STAGE,
        "generated_at_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "summary": {
            "conclusion": conclusion,
            "blocking_failures": blockers,
            "module_count": len(records),
            "non_python_content_count": len(non_python_content),
            "syntax_error_count": len(syntax_errors),
            "classification_counts": dict(sorted(classification_counts.items())),
        },
        "git": {
            "branch": branch,
            "head_before_commit": head,
            "upstream": upstream,
            "v1_baseline_tag": V1_BASELINE_TAG,
            "v1_baseline_commit": tag_target,
        },
        "checks": [asdict(item) for item in checks],
        "classification_policy": {
            CLASS_REWRITE: "Reimplement behavior behind clean V2 boundaries; never import V1 runtime.",
            CLASS_CONTENT: "Extract accepted content through schemas and canonical loaders.",
            CLASS_TEST: "Use for fixtures/parity/acceptance only.",
            CLASS_SKIP: "Do not migrate; V2 recreates this concern or the artifact is historical.",
            CLASS_MANUAL: "Resolve effective owner and accepted behavior before V2 implementation.",
        },
        "modules": [asdict(record) for record in records],
        "non_python_content": non_python_content,
        "owner_registry": owner_registry,
        "inbound_import_graph": inbound_graph,
        "review_queues": {
            "duplicate_definition_modules": duplicate_modules,
            "telegram_sql_coupled_modules": telegram_sql,
            "historical_marker_modules": historical,
            "owner_unresolved_modules": unresolved,
        },
        "database_evidence_before": db_before,
        "constraints": {
            "v1_runtime_import_into_v2": "FORBIDDEN",
            "mechanical_file_copy": "FORBIDDEN",
            "manual_review_required_before_rewrite": unresolved,
            "database_strategy": "RESET_FIRST",
        },
        "artifacts": {"patch": PATCH_PATH, "json": JSON_PATH, "markdown": MD_PATH},
        "next_stage": "21.1.2" if conclusion == "GO" else None,
    }

    print("[6/8] [PASS] Writing JSON module registry and Markdown summary.")
    write_atomic(root / JSON_PATH, json.dumps(payload, ensure_ascii=False, indent=2) + "\n")
    write_atomic(root / MD_PATH, render_markdown(payload))

    if conclusion != "GO":
        print("[7/8] [FAIL] Inventory contains blocking failures; commit not created.")
        print("PATCH STATUS: FAIL\nGIT COMMIT STATUS: NOT CREATED\nMANUAL CHECK: NOT REQUIRED\nWAL/SHM: NOT MANIPULATED")
        print("Blocking failures: " + ", ".join(blockers))
        return 1

    try:
        print("[7/8] [PASS] Creating exact-allowlist Stage 21.1.1 commit.")
        commit_hash = exact_commit(root)
    except PatchError as exc:
        print(f"[7/8] [FAIL] {exc}", file=sys.stderr)
        print("PATCH STATUS: FAIL\nGIT COMMIT STATUS: FAIL\nMANUAL CHECK: NOT REQUIRED\nWAL/SHM: NOT MANIPULATED")
        return 2

    db_after = database_evidence(root)
    final_ok = db_before == db_after and git(root, "branch", "--show-current").stdout.strip() == TARGET_BRANCH
    if not final_ok:
        print("[8/8] [FAIL] Post-commit branch or SQLite evidence verification failed.", file=sys.stderr)
        print("PATCH STATUS: FAIL\nGIT COMMIT STATUS: CREATED BUT RECOVERY REVIEW REQUIRED\nMANUAL CHECK: NOT REQUIRED\nWAL/SHM: NOT MANIPULATED")
        return 2

    print(f"[8/8] [PASS] Module inventory committed and SQLite evidence verified: {commit_hash}")
    print("=" * 72)
    print(f"ROM Stage {STAGE} - inventory and classify V1 modules")
    print("=" * 72)
    for item in checks:
        print(f"[{item.status}] {item.check_id}: {item.summary}")
    for name in sorted(VALID_CLASSES):
        print(f"[PASS] {name}: {classification_counts.get(name, 0)}")
    print(f"[PASS] DUPLICATE_DEFINITION_MODULES: {len(duplicate_modules)}")
    print(f"[PASS] TELEGRAM_SQL_COUPLED_MODULES: {len(telegram_sql)}")
    print(f"[PASS] OWNER_UNRESOLVED_MODULES: {len(unresolved)}")
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
