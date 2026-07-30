#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ROM 9.0.13j: move DB maintenance from import-time to explicit startup."""
from __future__ import annotations

import ast
import os
import py_compile
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

PATCH_ID = "9.0.13j"
DB_REL = Path("db.py")
MAIN_REL = Path("main.py")
TEST_NAME = "smoke_test_explicit_db_startup_maintenance.py"
TARGETS = (
    "ensure_refine_material_stack_sizes",
    "migrate_active_contracts_target_kills_to_5",
)

STARTUP_FUNCTION = '''def run_db_startup_maintenance():
    """Run idempotent database maintenance explicitly during application startup.

    This function is intentionally not called while importing db.py.  main.py
    owns the startup call after schema migrations and before item seeding and
    handler registration.
    """
    result = {
        "success": False,
        "refine_material_stack_sizes": None,
        "contract_target_kills": None,
    }

    result["refine_material_stack_sizes"] = ensure_refine_material_stack_sizes()
    result["contract_target_kills"] = migrate_active_contracts_target_kills_to_5()
    result["success"] = True
    return result
'''

TEST_SOURCE = r'''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Contracts for explicit DB startup maintenance ownership."""
from __future__ import annotations

import ast
import hashlib
import os
import shutil
import sqlite3
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

DB_PATH = ROOT / "game.db"
DB_PY = ROOT / "db.py"
MAIN_PY = ROOT / "main.py"
TARGETS = (
    "ensure_refine_material_stack_sizes",
    "migrate_active_contracts_target_kills_to_5",
)


def fail(message):
    print(f"[FAIL] {message}")
    raise SystemExit(1)


def fingerprint(path):
    return (
        hashlib.sha256(path.read_bytes()).hexdigest(),
        path.stat().st_size,
        path.stat().st_mtime_ns,
    )


def call_name(node):
    if isinstance(node.func, ast.Name):
        return node.func.id
    if isinstance(node.func, ast.Attribute):
        return node.func.attr
    return ""


def module_scope_target_calls(tree):
    findings = []
    for statement in tree.body:
        if isinstance(statement, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef,
                                  ast.Import, ast.ImportFrom)):
            continue
        for node in ast.walk(statement):
            if isinstance(node, ast.Call) and call_name(node) in TARGETS:
                findings.append((call_name(node), node.lineno))
    return findings


def run_import(temp_dir):
    probe = temp_dir / "probe.py"
    probe.write_text(
        "import sys\n"
        f"sys.path.insert(0, {str(ROOT)!r})\n"
        "import db\n"
        "print('[OK] import db without explicit maintenance')\n",
        encoding="utf-8",
    )
    env = os.environ.copy()
    env["PYTHONUTF8"] = "1"
    env["PYTHONIOENCODING"] = "utf-8"
    result = subprocess.run(
        [sys.executable, str(probe)], cwd=temp_dir, env=env,
        text=True, encoding="utf-8", errors="replace",
        capture_output=True, check=False,
    )
    return result


def main():
    real_before = fingerprint(DB_PATH)
    db_source = DB_PY.read_text(encoding="utf-8-sig")
    db_tree = ast.parse(db_source, filename=str(DB_PY))
    main_source = MAIN_PY.read_text(encoding="utf-8-sig")
    main_tree = ast.parse(main_source, filename=str(MAIN_PY))

    hidden = module_scope_target_calls(db_tree)
    if hidden:
        fail(f"module-scope maintenance calls remain: {hidden}")

    runners = [
        node for node in db_tree.body
        if isinstance(node, ast.FunctionDef)
        and node.name == "run_db_startup_maintenance"
    ]
    if len(runners) != 1:
        fail(f"run_db_startup_maintenance definitions={len(runners)}, expected 1")
    runner_source = ast.get_source_segment(db_source, runners[0]) or ""
    positions = [runner_source.find(name + "()") for name in TARGETS]
    if min(positions) < 0 or positions != sorted(positions):
        fail(f"maintenance call order invalid: {positions}")
    if 'result["success"] = True' not in runner_source or "return result" not in runner_source:
        fail("structured startup summary contract missing")

    imports = [
        node for node in main_tree.body
        if isinstance(node, ast.ImportFrom) and node.module == "db"
    ]
    imported = {
        alias.asname or alias.name for node in imports for alias in node.names
    }
    if "run_db_startup_maintenance" not in imported:
        fail("main.py does not import run_db_startup_maintenance")

    startup_calls = [
        node for node in main_tree.body
        if isinstance(node, ast.Assign)
        and any(isinstance(target, ast.Name) and target.id == "_db_startup_maintenance_result" for target in node.targets)
        and isinstance(node.value, ast.Call)
        and call_name(node.value) == "run_db_startup_maintenance"
    ]
    if len(startup_calls) != 1:
        fail(f"explicit startup calls={len(startup_calls)}, expected 1")
    startup_line = startup_calls[0].lineno
    seed_lines = [
        node.lineno for node in main_tree.body
        if isinstance(node, ast.Expr) and isinstance(node.value, ast.Call)
        and call_name(node.value) in {"seed_items", "seed_location_trash_items"}
    ]
    migration_lines = [
        node.lineno for node in ast.walk(main_tree)
        if isinstance(node, ast.Call) and call_name(node) == "run_pending_migrations"
    ]
    if not seed_lines or startup_line >= min(seed_lines):
        fail("explicit maintenance is not before item seeding")
    if migration_lines and startup_line <= max(migration_lines):
        fail("explicit maintenance is not after migration execution")

    # Import must not invoke either maintenance function.  A byte-for-byte copy
    # is used so all writes, if any, stay outside the real project database.
    with tempfile.TemporaryDirectory(prefix="rom_9_0_13j_") as temp_name:
        temp_dir = Path(temp_name)
        sandbox_db = temp_dir / "game.db"
        shutil.copy2(DB_PATH, sandbox_db)
        sandbox_before = fingerprint(sandbox_db)
        imported_result = run_import(temp_dir)
        sandbox_after = fingerprint(sandbox_db)
        if imported_result.returncode != 0:
            fail(f"sandbox import failed: {imported_result.stderr or imported_result.stdout}")
        if sandbox_before != sandbox_after:
            fail("plain import db changed the sandbox database file")

    # Pure call-order and structured-result probe.  The real implementations are
    # temporarily replaced, so no real database mutation is possible here.
    import db
    original_refine = db.ensure_refine_material_stack_sizes
    original_contract = db.migrate_active_contracts_target_kills_to_5
    calls = []
    try:
        db.ensure_refine_material_stack_sizes = lambda: calls.append("refine") or {"updated": 0}
        db.migrate_active_contracts_target_kills_to_5 = lambda: calls.append("contract") or {"updated": 0}
        first = db.run_db_startup_maintenance()
        second = db.run_db_startup_maintenance()
    finally:
        db.ensure_refine_material_stack_sizes = original_refine
        db.migrate_active_contracts_target_kills_to_5 = original_contract

    if calls != ["refine", "contract", "refine", "contract"]:
        fail(f"explicit maintenance order/idempotent invocation failed: {calls}")
    for result in (first, second):
        if result.get("success") is not True:
            fail(f"startup summary success contract failed: {result}")
        if set(result) != {"success", "refine_material_stack_sizes", "contract_target_kills"}:
            fail(f"startup summary keys changed: {result}")

    if real_before != fingerprint(DB_PATH):
        fail("real game.db changed during tests")

    print("[OK] explicit DB startup maintenance contracts")
    print("- module-scope target calls: 0")
    print("- plain import db database changes: 0")
    print("- explicit startup owner in main.py: exactly 1")
    print("- startup order: migrations -> maintenance -> seeds")
    print("- maintenance order: refine stacks -> contract targets")
    print("- structured summary contract: OK")
    print("- repeated explicit invocation contract: OK")
    print("- real database mutations during tests: 0")


if __name__ == "__main__":
    main()
'''


def fail(message):
    print(f"❌ {message}")
    raise SystemExit(1)


def find_root():
    here = Path(__file__).resolve()
    for root in (here.parent.parent, Path.cwd(), Path.cwd().parent):
        root = root.resolve()
        if (
            (root / DB_REL).is_file()
            and (root / MAIN_REL).is_file()
            and (root / "tools" / "check_imports.py").is_file()
        ):
            return root
    fail("Не знайдено корінь ROM.")


def parse(source, filename="<source>"):
    return ast.parse(source, filename=filename)


def call_name(call):
    if isinstance(call.func, ast.Name):
        return call.func.id
    if isinstance(call.func, ast.Attribute):
        return call.func.attr
    return ""


def module_statements_with_target_calls(source):
    tree = parse(source)
    findings = []
    for statement in tree.body:
        if isinstance(statement, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef,
                                  ast.Import, ast.ImportFrom)):
            continue
        names = {
            call_name(node) for node in ast.walk(statement)
            if isinstance(node, ast.Call) and call_name(node) in TARGETS
        }
        if names:
            findings.append((statement, names))
    return findings


def remove_module_calls(source):
    findings = module_statements_with_target_calls(source)
    names = set().union(*(names for _statement, names in findings)) if findings else set()
    if names != set(TARGETS):
        raise RuntimeError(f"module-scope target set={sorted(names)}, expected={sorted(TARGETS)}")
    lines = source.splitlines(keepends=True)
    for statement, _names in sorted(findings, key=lambda item: item[0].lineno, reverse=True):
        start = statement.lineno - 1
        end = statement.end_lineno
        # Consume one immediately following blank line for a clean result.
        if end < len(lines) and not lines[end].strip():
            end += 1
        lines[start:end] = []
    return "".join(lines)


def insert_startup_function(source):
    if "def run_db_startup_maintenance(" in source:
        return source
    tree = parse(source)
    definitions = {
        node.name: node for node in tree.body if isinstance(node, ast.FunctionDef)
    }
    anchors = [definitions.get(name) for name in TARGETS]
    if any(anchor is None for anchor in anchors):
        raise RuntimeError("maintenance function definition missing")
    insert_after = max(anchor.end_lineno for anchor in anchors)
    lines = source.splitlines(keepends=True)
    lines[insert_after:insert_after] = ["\n" + STARTUP_FUNCTION.rstrip() + "\n"]
    return "".join(lines)


def add_main_import(source):
    tree = parse(source)
    db_imports = [
        node for node in tree.body
        if isinstance(node, ast.ImportFrom) and node.module == "db"
    ]
    if not db_imports:
        raise RuntimeError("main.py from db import block not found")
    if any(
        alias.name == "run_db_startup_maintenance"
        for node in db_imports
        for alias in node.names
    ):
        return source

    # Add a separate import statement instead of rewriting the existing large
    # multi-line import block. This is stable for parenthesized, single-line,
    # and backslash-continued imports.
    insert_after = max(node.end_lineno for node in db_imports)
    lines = source.splitlines(keepends=True)
    lines[insert_after:insert_after] = [
        "from db import run_db_startup_maintenance\n"
    ]
    updated = "".join(lines)
    parse(updated, "main.py")
    return updated


def add_main_startup_call(source):
    if "_db_startup_maintenance_result = run_db_startup_maintenance()" in source:
        return source
    tree = parse(source)
    seed_nodes = [
        node for node in tree.body
        if isinstance(node, ast.Expr) and isinstance(node.value, ast.Call)
        and call_name(node.value) in {"seed_items", "seed_location_trash_items"}
    ]
    if not seed_nodes:
        raise RuntimeError("main.py seed startup anchor not found")
    first_seed = min(seed_nodes, key=lambda node: node.lineno)
    block = '''_db_startup_maintenance_result = run_db_startup_maintenance()
if _db_startup_maintenance_result.get("success"):
    print(f"✅ DB STARTUP MAINTENANCE: {_db_startup_maintenance_result}")

'''
    lines = source.splitlines(keepends=True)
    lines[first_seed.lineno - 1:first_seed.lineno - 1] = [block]
    return "".join(lines)


def validate_updated(db_source, main_source):
    db_tree = parse(db_source, "db.py")
    main_tree = parse(main_source, "main.py")
    hidden = []
    for statement in db_tree.body:
        if isinstance(statement, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef,
                                  ast.Import, ast.ImportFrom)):
            continue
        for node in ast.walk(statement):
            if isinstance(node, ast.Call) and call_name(node) in TARGETS:
                hidden.append((call_name(node), node.lineno))
    if hidden:
        raise RuntimeError(f"module-scope target calls remain: {hidden}")
    runners = [node for node in db_tree.body if isinstance(node, ast.FunctionDef) and node.name == "run_db_startup_maintenance"]
    if len(runners) != 1:
        raise RuntimeError(f"startup runner definitions={len(runners)}")
    import_ok = any(
        isinstance(node, ast.ImportFrom) and node.module == "db"
        and any(alias.name == "run_db_startup_maintenance" for alias in node.names)
        for node in main_tree.body
    )
    if not import_ok:
        raise RuntimeError("main.py startup runner import missing")
    calls = [
        node for node in ast.walk(main_tree)
        if isinstance(node, ast.Call) and call_name(node) == "run_db_startup_maintenance"
    ]
    if len(calls) != 1:
        raise RuntimeError(f"main.py startup runner calls={len(calls)}, expected 1")


def run_checked(root, path, label, env):
    result = subprocess.run([sys.executable, str(path)], cwd=root, env=env, check=False)
    if result.returncode != 0:
        raise RuntimeError(f"{label} exit code {result.returncode}")


def main():
    root = find_root()
    db_path = root / DB_REL
    main_path = root / MAIN_REL
    tools = root / "tools"
    test_path = tools / TEST_NAME

    required_tests = [
        "smoke_test_rom_core.py",
        "check_imports.py",
        "db_cleanup_readiness.py",
    ]
    for name in required_tests:
        if not (tools / name).is_file():
            fail(f"Відсутній tools/{name}.")

    db_source = db_path.read_text(encoding="utf-8-sig")
    main_source = main_path.read_text(encoding="utf-8-sig")
    already = (
        "def run_db_startup_maintenance(" in db_source
        and not module_statements_with_target_calls(db_source)
        and "_db_startup_maintenance_result = run_db_startup_maintenance()" in main_source
    )

    env = os.environ.copy()
    env["PYTHONUTF8"] = "1"
    env["PYTHONIOENCODING"] = "utf-8"

    if already:
        print(f"ℹ️ Патч {PATCH_ID} уже застосовано. Запускаю перевірки.")
        test_path.write_text(TEST_SOURCE, encoding="utf-8")
        for name in (TEST_NAME, "smoke_test_rom_core.py", "check_imports.py"):
            run_checked(root, tools / name, name, env)
        return

    updated_db = remove_module_calls(db_source)
    updated_db = insert_startup_function(updated_db)
    updated_main = add_main_import(main_source)
    updated_main = add_main_startup_call(updated_main)
    validate_updated(updated_db, updated_main)

    backup_dir = root / "backup"
    backup_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    db_backup = backup_dir / f"db.py_{PATCH_ID}_{stamp}.bak"
    main_backup = backup_dir / f"main.py_{PATCH_ID}_{stamp}.bak"
    test_backup = None
    shutil.copy2(db_path, db_backup)
    shutil.copy2(main_path, main_backup)
    if test_path.exists():
        test_backup = backup_dir / f"tools_{TEST_NAME}_{PATCH_ID}_{stamp}.bak"
        shutil.copy2(test_path, test_backup)

    try:
        db_path.write_text(updated_db, encoding="utf-8")
        main_path.write_text(updated_main, encoding="utf-8")
        test_path.write_text(TEST_SOURCE, encoding="utf-8")
        py_compile.compile(str(db_path), doraise=True)
        py_compile.compile(str(main_path), doraise=True)
        py_compile.compile(str(test_path), doraise=True)
        for name in (TEST_NAME, "smoke_test_rom_core.py", "check_imports.py"):
            run_checked(root, tools / name, name, env)
        readiness = subprocess.run(
            [sys.executable, str(tools / "db_cleanup_readiness.py")],
            cwd=root, env=env, text=True, encoding="utf-8", errors="replace",
            capture_output=True, check=False,
        )
        print(readiness.stdout, end="")
        if readiness.returncode != 0:
            raise RuntimeError(f"readiness exit code {readiness.returncode}")
        for marker in ("duplicates: 0", "legacy_refs: 0", "unsafe_delete: 0", "maybe_cleanup_later: 0"):
            if marker not in readiness.stdout:
                raise RuntimeError(f"readiness missing {marker}")
    except Exception as exc:
        shutil.copy2(db_backup, db_path)
        shutil.copy2(main_backup, main_path)
        if test_backup is not None:
            shutil.copy2(test_backup, test_path)
        elif test_path.exists():
            test_path.unlink()
        fail(f"Перевірка не пройдена; db.py, main.py і тест відновлено: {exc}")

    print(f"✅ Патч {PATCH_ID} успішно застосовано.")
    print("✅ Приховані maintenance-виклики прибрано з import db.")
    print("✅ Додано run_db_startup_maintenance() зі структурованим результатом.")
    print("✅ main.py явно запускає maintenance після міграцій і до seed-функцій.")
    print("✅ Бізнес-правила refine stack і contract target migration не змінено.")
    print("Резервні копії:")
    print(f"   {db_backup.relative_to(root)}")
    print(f"   {main_backup.relative_to(root)}")
    if test_backup is not None:
        print(f"   {test_backup.relative_to(root)}")
    print("Перевірки:")
    print(f"   python ./tools/{TEST_NAME}")
    print("   python ./tools/smoke_test_rom_core.py")
    print("   python ./tools/check_imports.py")
    print("   python ./tools/db_cleanup_readiness.py")


if __name__ == "__main__":
    main()
