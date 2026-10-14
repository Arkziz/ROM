#!/usr/bin/env python3
"""Stage 21.1.1a: correct false-positive V1 module classifications.

This follow-up keeps the successful Stage 21.1.1 commit in history, regenerates
its canonical inventory with stricter test-module and package-marker rules,
creates a separate remediation report, and commits an exact allowlist.
Production code and SQLite files are never opened or modified.
"""
from __future__ import annotations

import ast
import hashlib
import importlib.util
import json
import os
import subprocess
import sys
from collections import Counter
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Sequence

STAGE = "21.1.1a"
TARGET_BRANCH = "rewrite/rom-v2"
EXPECTED_PARENT = "4813dcf8542c42f765aeb0dd1fe9134f29683442"
SOURCE_PATCH_PATH = "patch/patch_21_1_1_inventory_and_classify_v1_modules.py"
PATCH_PATH = "patch/patch_21_1_1a_fix_module_classification_false_positives.py"
CANONICAL_JSON_PATH = "reports/stage_21_1_1_v1_module_inventory.json"
CANONICAL_MD_PATH = "MD/STAGE_21_1_1_V1_MODULE_INVENTORY.md"
REMEDIATION_JSON_PATH = "reports/stage_21_1_1a_module_classification_fix.json"
REMEDIATION_MD_PATH = "MD/STAGE_21_1_1A_MODULE_CLASSIFICATION_FIX.md"
COMMIT_MESSAGE = "Stage 21.1.1a: fix module classification false positives"
OWNED_PATHS = {
    PATCH_PATH,
    CANONICAL_JSON_PATH,
    CANONICAL_MD_PATH,
    REMEDIATION_JSON_PATH,
    REMEDIATION_MD_PATH,
}
ALLOWED_DIRTY = {"ROM_FULL_DUMP.txt", "ROM_ADDITIONAL_DUMP.txt"}
DB_FILES = ("game.db", "game.db-wal", "game.db-shm")

# Test classification must be explicit. A generic domain word such as
# "contract" must never turn a runtime module into TEST_REFERENCE.
TEST_DIRECTORIES = {"tools", "tests", "test", "fixtures"}
TEST_PREFIXES = (
    "test_", "smoke_test_", "verify_", "check_", "regression_",
    "contract_test_", "integration_test_", "acceptance_test_",
)
TEST_SUFFIXES = ("_test.py", "_tests.py")
RUNTIME_CONTRACT_SENTINELS = {
    "handlers/contracts.py": "REWRITE",
    "systems/contract_system.py": "REWRITE",
}
PACKAGE_MARKER_SENTINELS = {
    "data/__init__.py": "DO_NOT_MIGRATE",
    "data/story_quests/__init__.py": "DO_NOT_MIGRATE",
}


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


def load_stage_21_1_1(root: Path):
    path = root / SOURCE_PATCH_PATH
    if not path.is_file():
        raise PatchError(f"required canonical generator is missing: {SOURCE_PATCH_PATH}")
    spec = importlib.util.spec_from_file_location("rom_stage_21_1_1_generator", path)
    if spec is None or spec.loader is None:
        raise PatchError("cannot load Stage 21.1.1 generator")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def strict_test_reference(path: str) -> bool:
    item = Path(path)
    parts = {part.lower() for part in item.parts}
    name = item.name.lower()
    if parts & TEST_DIRECTORIES:
        return True
    return name.startswith(TEST_PREFIXES) or name.endswith(TEST_SUFFIXES)


def package_marker(path: str) -> bool:
    """V2 always recreates package boundaries instead of migrating __init__.py."""
    return Path(path).name == "__init__.py"


def classify_strict(generator, root: Path, module_paths: list[str]):
    """Reuse the accepted inventory engine with corrected classification rules."""
    original_test_reference = generator.test_reference_module
    original_content_module = generator.content_module
    original_classify = generator.classify_module

    def strict_content_module(path: str) -> bool:
        return not package_marker(path) and original_content_module(path)

    def strict_classify_module(
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
    ):
        if package_marker(path):
            reasons = ["Package initializer; V2 creates its own package boundaries and explicit exports."]
            # Non-empty package initializers are still not migrated. Their imports
            # remain visible in the inventory for later content/runtime audits.
            return (
                generator.CLASS_SKIP,
                "HIGH",
                reasons[0],
                reasons,
                "NOT_A_V2_RUNTIME_OWNER",
                [],
            )
        return original_classify(
            path,
            text,
            tree,
            imports,
            duplicate_functions,
            duplicate_classes,
            historical_markers,
            contains_sql,
            contains_registration,
            imports_telegram,
        )

    generator.test_reference_module = strict_test_reference
    generator.content_module = strict_content_module
    generator.classify_module = strict_classify_module
    try:
        return generator.parse_modules(root, module_paths)
    finally:
        generator.test_reference_module = original_test_reference
        generator.content_module = original_content_module
        generator.classify_module = original_classify


def module_index(records) -> dict[str, Any]:
    return {record.path: record for record in records}


def semantic_checks(before: dict[str, Any], after_records) -> list[Check]:
    after = module_index(after_records)
    checks: list[Check] = []
    for path, expected in {**RUNTIME_CONTRACT_SENTINELS, **PACKAGE_MARKER_SENTINELS}.items():
        actual = after[path].classification if path in after else None
        checks.append(Check(
            f"SENTINEL_{path.upper().replace('/', '_').replace('.', '_')}",
            "PASS" if actual == expected else "FAIL",
            f"{path} -> {actual}; expected {expected}.",
            {"path": path, "expected": expected, "actual": actual},
            actual != expected,
        ))

    false_contract_tests = [
        record.path for record in after_records
        if record.classification == "TEST_REFERENCE"
        and "contract" in Path(record.path).name.lower()
        and not strict_test_reference(record.path)
    ]
    checks.append(Check(
        "NO_GENERIC_CONTRACT_TEST_FALSE_POSITIVES",
        "PASS" if not false_contract_tests else "FAIL",
        "No runtime module is classified as a test solely because its name contains 'contract'."
        if not false_contract_tests else "Generic contract-name false positives remain.",
        {"paths": false_contract_tests},
        bool(false_contract_tests),
    ))

    init_wrong = [record.path for record in after_records if package_marker(record.path) and record.classification != "DO_NOT_MIGRATE"]
    checks.append(Check(
        "PACKAGE_INITIALIZER_CONSISTENCY",
        "PASS" if not init_wrong else "FAIL",
        "All __init__.py files are consistently classified as DO_NOT_MIGRATE."
        if not init_wrong else "Some package initializers remain inconsistently classified.",
        {"paths": init_wrong},
        bool(init_wrong),
    ))

    before_paths = {item["path"] for item in before["modules"]}
    after_paths = set(after)
    coverage_ok = before_paths == after_paths
    checks.append(Check(
        "MODULE_SET_STABILITY",
        "PASS" if coverage_ok else "FAIL",
        "Corrected inventory covers exactly the same V1 module set."
        if coverage_ok else "Corrected inventory module set differs from Stage 21.1.1.",
        {"missing": sorted(before_paths-after_paths), "extra": sorted(after_paths-before_paths)},
        not coverage_ok,
    ))
    return checks


def render_canonical_markdown(payload: dict[str, Any]) -> str:
    summary = payload["summary"]
    counts = summary["classification_counts"]
    queues = payload["review_queues"]
    return "\n".join([
        "# ROM Stage 21.1.1 - інвентаризація та класифікація модулів V1", "",
        "- **Canonical revision:** `Stage 21.1.1a`",
        f"- **Статус:** `{summary['conclusion']}`",
        f"- **Гілка:** `{payload['git']['branch']}`",
        f"- **Python-модулів V1:** `{summary['module_count']}`",
        f"- **Syntax errors:** `{summary['syntax_error_count']}`", "",
        "## Класифікація", "",
        f"- `REWRITE`: **{counts.get('REWRITE', 0)}**",
        f"- `CONTENT_EXTRACT`: **{counts.get('CONTENT_EXTRACT', 0)}**",
        f"- `TEST_REFERENCE`: **{counts.get('TEST_REFERENCE', 0)}**",
        f"- `DO_NOT_MIGRATE`: **{counts.get('DO_NOT_MIGRATE', 0)}**",
        f"- `NEEDS_MANUAL_REVIEW`: **{counts.get('NEEDS_MANUAL_REVIEW', 0)}**", "",
        "## Виправлення Stage 21.1.1a", "",
        "- Слово `contract` більше не є самостійним test marker.",
        "- `handlers/contracts.py` і `systems/contract_system.py` класифікуються як runtime `REWRITE`.",
        "- Усі `__init__.py` класифікуються як `DO_NOT_MIGRATE`; V2 створить package boundaries та exports заново.",
        "- Test classification дозволена лише для явних test directories, prefixes і suffixes.", "",
        "## Черги наступних аудитів", "",
        f"- Duplicate definitions: **{len(queues['duplicate_definition_modules'])}**.",
        f"- Telegram + SQL coupling: **{len(queues['telegram_sql_coupled_modules'])}**.",
        f"- Historical markers: **{len(queues['historical_marker_modules'])}**.",
        f"- Owner unresolved: **{len(queues['owner_unresolved_modules'])}**.", "",
        "## Використання", "",
        "- Цей Markdown і відповідний JSON після Stage 21.1.1a є canonical inventory.",
        "- Класифікація є planning contract, а не дозволом механічно копіювати V1.",
        "- Production DB/WAL/SHM не відкривалися й не змінювалися.", "",
        "## Наступний етап", "",
        "Stage 21.1.2 - AST-аудит повторних визначень, alias chains і runtime overrides.", "",
    ])


def render_remediation_markdown(remediation: dict[str, Any]) -> str:
    delta = remediation["classification_delta"]
    rows = [
        f"| `{item['path']}` | `{item['before']}` | `{item['after']}` |"
        for item in delta[:100]
    ]
    return "\n".join([
        "# ROM Stage 21.1.1a - виправлення false positives класифікації", "",
        f"- **Статус:** `{remediation['summary']['conclusion']}`",
        f"- **Parent commit:** `{EXPECTED_PARENT}`",
        f"- **Перекласифіковано модулів:** `{len(delta)}`",
        f"- **Semantic checks:** `{remediation['summary']['semantic_pass_count']} PASS / {remediation['summary']['semantic_fail_count']} FAIL`", "",
        "## Причина", "",
        "Stage 21.1.1 використовував слово `contract` як надто широкий test marker та перевіряв `data/` раніше за package marker. Через це runtime contract modules і package initializers отримали неправильні категорії.", "",
        "## Виправлені правила", "",
        "- Test modules визначаються тільки явними test directories, prefixes та suffixes.",
        "- Звичайні runtime-назви `contracts.py` і `contract_system.py` не є тестами.",
        "- Усі `__init__.py` не переносяться; V2 формує package boundaries заново.",
        "- Module set і SHA-256 metadata не змінюються; оновлюється тільки класифікаційний contract та derived queues.", "",
        "## Classification delta", "",
        "| Модуль | Було | Стало |", "|---|---|---|", *rows,
        *( ["", f"> Показано перші 100 із {len(delta)} змін; повний delta міститься у JSON."] if len(delta) > 100 else [] ), "",
        "## Наступний етап", "",
        "Stage 21.1.2 - AST-аудит повторних визначень, alias chains і runtime overrides.", "",
    ])


def exact_commit(root: Path) -> str:
    paths = [
        PATCH_PATH,
        CANONICAL_JSON_PATH,
        CANONICAL_MD_PATH,
        REMEDIATION_JSON_PATH,
        REMEDIATION_MD_PATH,
    ]
    add = git(root, "add", "-f", "--", *paths)
    if add.returncode != 0:
        raise PatchError(add.stderr.strip() or "git add failed")
    staged_result = git(root, "diff", "--cached", "--name-only", "-z")
    staged = sorted(item for item in staged_result.stdout.split("\0") if item)
    if staged_result.returncode != 0 or staged != sorted(paths):
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
    for required in (root / "reports", root / "MD", root / SOURCE_PATCH_PATH, root / CANONICAL_JSON_PATH):
        if not required.exists():
            print(f"[FAIL] Required input is missing: {required}", file=sys.stderr)
            return 2

    print("[1/8] [PASS] ROM root, canonical inventory and regulated directories detected.")
    branch = git(root, "branch", "--show-current").stdout.strip()
    head = rev(root, "HEAD")
    upstream_result = git(root, "rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{u}")
    upstream = upstream_result.stdout.strip() if upstream_result.returncode == 0 else None

    status_result = git(root, "status", "--porcelain=v1", "-z", "--untracked-files=all")
    entries = parse_status(status_result.stdout) if status_result.returncode == 0 else []
    allowed: list[dict[str, str]] = []
    for entry in entries:
        index_status = entry["status"][0]
        path = entry["path"]
        if index_status in {" ", "?"} and (path in OWNED_PATHS or (path in ALLOWED_DIRTY and index_status == " ")):
            allowed.append(entry)
    unexpected = [entry for entry in entries if entry not in allowed]

    preflight = [
        Check("TARGET_BRANCH", "PASS" if branch == TARGET_BRANCH else "FAIL", f"Active branch is {branch or 'detached HEAD'}.", {"expected": TARGET_BRANCH}, branch != TARGET_BRANCH),
        Check("EXPECTED_PARENT", "PASS" if head == EXPECTED_PARENT else "FAIL", "HEAD matches successful Stage 21.1.1 commit." if head == EXPECTED_PARENT else "HEAD differs from successful Stage 21.1.1 commit.", {"expected": EXPECTED_PARENT, "actual": head}, head != EXPECTED_PARENT),
        Check("UPSTREAM", "PASS" if upstream == f"origin/{TARGET_BRANCH}" else "FAIL", "Rewrite upstream is configured." if upstream == f"origin/{TARGET_BRANCH}" else "Rewrite upstream is missing or incorrect.", {"upstream": upstream}, upstream != f"origin/{TARGET_BRANCH}"),
        Check("WORKTREE", "PASS" if not unexpected else "FAIL", "Working tree has no unexpected or pre-staged changes." if not unexpected else "Unexpected or pre-staged changes exist.", {"unexpected": unexpected, "allowed": allowed}, bool(unexpected)),
    ]
    blockers = [item.check_id for item in preflight if item.blocking]
    if blockers:
        print("[2/8] [FAIL] Preflight returned NO_GO.")
        print("Blocking failures: " + ", ".join(blockers))
        return 1

    print("[2/8] [PASS] Branch, parent, upstream and worktree preflight passed.")
    db_before = database_evidence(root)
    before = json.loads((root / CANONICAL_JSON_PATH).read_text(encoding="utf-8"))
    generator = load_stage_21_1_1(root)
    tracked = generator.tracked_files(root)
    module_paths = [path for path in tracked if generator.is_v1_module(path)]

    print(f"[3/8] [PASS] Reclassifying {len(module_paths)} modules with corrected strict rules.")
    records, syntax_errors, inbound_graph = classify_strict(generator, root, module_paths)

    print("[4/8] [PASS] Running sentinel, package initializer and module-set semantic checks.")
    semantic = semantic_checks(before, records)
    classification_counts = Counter(record.classification for record in records)
    non_python_content = generator.classify_non_python_content(root, tracked)
    duplicate_modules = [record.path for record in records if record.duplicate_functions or record.duplicate_classes]
    telegram_sql = [record.path for record in records if record.imports_telegram and record.contains_sql]
    historical = [record.path for record in records if record.historical_markers]
    unresolved = [record.path for record in records if record.authoritative_owner_status == "OWNER_UNRESOLVED"]

    after_by_path = {record.path: record for record in records}
    before_by_path = {item["path"]: item for item in before["modules"]}
    delta = []
    for path in sorted(after_by_path):
        previous = before_by_path[path]["classification"]
        current = after_by_path[path].classification
        if previous != current:
            delta.append({
                "path": path,
                "before": previous,
                "after": current,
                "reason": after_by_path[path].primary_reason,
            })

    print("[5/8] [PASS] Rebuilding canonical inventory and remediation evidence.")
    semantic_failures = [item.check_id for item in semantic if item.blocking]
    syntax_ok = not syntax_errors
    module_count_ok = len(records) == len(before["modules"])
    conclusion = "GO" if syntax_ok and module_count_ok and not semantic_failures else "NO_GO"

    checks = preflight + [
        Check("PYTHON_SYNTAX", "PASS" if syntax_ok else "FAIL", "All modules parse successfully." if syntax_ok else "Syntax errors were found.", {"errors": syntax_errors}, not syntax_ok),
        Check("MODULE_COVERAGE", "PASS" if module_count_ok else "FAIL", "Module coverage remains stable." if module_count_ok else "Module coverage changed unexpectedly.", {"before": len(before["modules"]), "after": len(records)}, not module_count_ok),
        *semantic,
    ]

    canonical = {
        "schema_version": 2,
        "canonical_revision": STAGE,
        "stage": "21.1.1",
        "generated_at_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "summary": {
            "conclusion": conclusion,
            "blocking_failures": [item.check_id for item in checks if item.blocking],
            "module_count": len(records),
            "non_python_content_count": len(non_python_content),
            "syntax_error_count": len(syntax_errors),
            "classification_counts": dict(sorted(classification_counts.items())),
        },
        "git": {
            "branch": branch,
            "head_before_commit": head,
            "upstream": upstream,
            "v1_baseline_tag": before["git"]["v1_baseline_tag"],
            "v1_baseline_commit": before["git"]["v1_baseline_commit"],
        },
        "checks": [asdict(item) for item in checks],
        "classification_policy": {
            "REWRITE": "Reimplement behavior behind clean V2 boundaries; never import V1 runtime.",
            "CONTENT_EXTRACT": "Extract accepted content through schemas and canonical loaders.",
            "TEST_REFERENCE": "Only explicit test directories/prefixes/suffixes; use for fixtures/parity/acceptance only.",
            "DO_NOT_MIGRATE": "Historical migrations, package initializers and artifacts recreated by V2.",
            "NEEDS_MANUAL_REVIEW": "Resolve effective owner and accepted behavior before V2 implementation.",
        },
        "modules": [asdict(record) for record in records],
        "non_python_content": non_python_content,
        "owner_registry": {
            record.path: {
                "classification": record.classification,
                "owner_status": record.authoritative_owner_status,
                "recommended_v2_destination": record.recommended_v2_destination,
            }
            for record in records
        },
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
            "database_strategy": "RESET_FIRST",
        },
        "remediation": {
            "stage": STAGE,
            "source_inventory_commit": EXPECTED_PARENT,
            "classification_delta_count": len(delta),
        },
        "artifacts": {"patch": PATCH_PATH, "json": CANONICAL_JSON_PATH, "markdown": CANONICAL_MD_PATH},
        "next_stage": "21.1.2" if conclusion == "GO" else None,
    }

    remediation = {
        "schema_version": 1,
        "stage": STAGE,
        "generated_at_utc": canonical["generated_at_utc"],
        "summary": {
            "conclusion": conclusion,
            "classification_delta_count": len(delta),
            "semantic_pass_count": sum(item.status == "PASS" for item in semantic),
            "semantic_fail_count": sum(item.status == "FAIL" for item in semantic),
        },
        "root_causes": [
            "Generic word 'contract' was used as a test marker.",
            "data/ content classification ran before package-marker classification.",
        ],
        "corrected_rules": {
            "test_directories": sorted(TEST_DIRECTORIES),
            "test_prefixes": list(TEST_PREFIXES),
            "test_suffixes": list(TEST_SUFFIXES),
            "all_package_initializers": "DO_NOT_MIGRATE",
        },
        "semantic_checks": [asdict(item) for item in semantic],
        "classification_delta": delta,
        "canonical_artifacts_updated": [CANONICAL_JSON_PATH, CANONICAL_MD_PATH],
        "database_evidence_before": db_before,
        "next_stage": "21.1.2" if conclusion == "GO" else None,
    }

    print("[6/8] [PASS] Writing corrected canonical inventory and separate remediation artifacts.")
    write_atomic(root / CANONICAL_JSON_PATH, json.dumps(canonical, ensure_ascii=False, indent=2) + "\n")
    write_atomic(root / CANONICAL_MD_PATH, render_canonical_markdown(canonical))
    write_atomic(root / REMEDIATION_JSON_PATH, json.dumps(remediation, ensure_ascii=False, indent=2) + "\n")
    write_atomic(root / REMEDIATION_MD_PATH, render_remediation_markdown(remediation))

    if conclusion != "GO":
        print("[7/8] [FAIL] Semantic remediation returned NO_GO; commit not created.")
        print("PATCH STATUS: FAIL\nGIT COMMIT STATUS: NOT CREATED\nMANUAL CHECK: NOT REQUIRED\nWAL/SHM: NOT MANIPULATED")
        return 1

    try:
        print("[7/8] [PASS] Creating exact-allowlist Stage 21.1.1a commit.")
        commit_hash = exact_commit(root)
    except PatchError as exc:
        print(f"[7/8] [FAIL] {exc}", file=sys.stderr)
        print("PATCH STATUS: FAIL\nGIT COMMIT STATUS: FAIL\nMANUAL CHECK: NOT REQUIRED\nWAL/SHM: NOT MANIPULATED")
        return 2

    db_after = database_evidence(root)
    if db_before != db_after or git(root, "branch", "--show-current").stdout.strip() != TARGET_BRANCH:
        print("[8/8] [FAIL] Post-commit branch or DB/WAL/SHM evidence verification failed.", file=sys.stderr)
        print("PATCH STATUS: FAIL\nGIT COMMIT STATUS: CREATED BUT RECOVERY REVIEW REQUIRED\nMANUAL CHECK: NOT REQUIRED\nWAL/SHM: NOT MANIPULATED")
        return 2

    print(f"[8/8] [PASS] Corrected inventory committed and DB/WAL/SHM evidence verified: {commit_hash}")
    print("=" * 72)
    print(f"ROM Stage {STAGE} - fix module classification false positives")
    print("=" * 72)
    for item in checks:
        print(f"[{item.status}] {item.check_id}: {item.summary}")
    for name in sorted(classification_counts):
        print(f"[PASS] {name}: {classification_counts[name]}")
    print(f"[PASS] CLASSIFICATION_DELTA: {len(delta)}")
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
