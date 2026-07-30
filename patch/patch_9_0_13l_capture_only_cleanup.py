#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ROM 9.0.13l: remove confirmed unused Refine/Inventory base captures."""
from __future__ import annotations

import ast
import os
import py_compile
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

PATCH_ID = "9.0.13l"
TARGET_REL = Path("db.py")
TEST_NAME = "smoke_test_capture_only_cleanup.py"
CAPTURES = (
    "_base_get_inventory_detailed_before_refine_display_v1",
    "_base_get_inventory_entry_before_refine_display_v1",
    "_base_get_item_by_inventory_id_before_refine_display_v1",
    "_base_get_item_by_inventory_id_full_before_refine_display_v1",
    "_base_get_max_hp_before_refine_v1",
    "_base_get_sellable_equipment_items_before_refine_display_v1",
    "_base_get_weapon_damage_by_inventory_id_before_refine_v1",
    "_base_get_weapon_damage_for_refine_hotfix_v1",
)

TEST_SOURCE = r'''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Read-only contracts for removal of obsolete base captures."""
from __future__ import annotations

import ast
import hashlib
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

DB_PATH = ROOT / "game.db"
DB_PY = ROOT / "db.py"
CAPTURES = (
    "_base_get_inventory_detailed_before_refine_display_v1",
    "_base_get_inventory_entry_before_refine_display_v1",
    "_base_get_item_by_inventory_id_before_refine_display_v1",
    "_base_get_item_by_inventory_id_full_before_refine_display_v1",
    "_base_get_max_hp_before_refine_v1",
    "_base_get_sellable_equipment_items_before_refine_display_v1",
    "_base_get_weapon_damage_by_inventory_id_before_refine_v1",
    "_base_get_weapon_damage_for_refine_hotfix_v1",
)
REQUIRED_PUBLIC_APIS = (
    "get_inventory_detailed",
    "get_inventory_entry",
    "get_item_by_inventory_id",
    "get_item_by_inventory_id_full",
    "get_max_hp",
    "get_sellable_equipment_items",
    "get_weapon_damage_by_inventory_id",
)


def fail(message):
    print(f"[FAIL] {message}")
    raise SystemExit(1)


def fingerprint():
    return (
        hashlib.sha256(DB_PATH.read_bytes()).hexdigest(),
        DB_PATH.stat().st_size,
        DB_PATH.stat().st_mtime_ns,
    )


def main():
    before = fingerprint()
    source = DB_PY.read_text(encoding="utf-8-sig")
    tree = ast.parse(source, filename=str(DB_PY))

    residual = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Name) and node.id in CAPTURES:
            residual.append((node.id, node.lineno, "name"))
        elif isinstance(node, ast.Constant) and isinstance(node.value, str) and node.value in CAPTURES:
            residual.append((node.value, node.lineno, "string"))
    if residual:
        fail(f"removed captures still occur in source: {residual}")

    import db

    runtime_residual = [name for name in CAPTURES if hasattr(db, name)]
    if runtime_residual:
        fail(f"removed captures still exist at runtime: {runtime_residual}")

    missing_public = [name for name in REQUIRED_PUBLIC_APIS if not callable(getattr(db, name, None))]
    if missing_public:
        fail(f"public APIs missing after cleanup: {missing_public}")

    # Read-only runtime probes against a real existing user when available.
    row = db.conn.execute("SELECT user_id FROM users ORDER BY user_id LIMIT 1").fetchone()
    user_id = int(row[0]) if row else None
    probes = {}
    if user_id is not None:
        probes["inventory_detailed_type"] = type(db.get_inventory_detailed(user_id)).__name__
        probes["sellable_equipment_type"] = type(db.get_sellable_equipment_items(user_id)).__name__
        probes["max_hp_type"] = type(db.get_max_hp(user_id)).__name__

        inventory_row = db.conn.execute(
            "SELECT id FROM inventory WHERE user_id=? ORDER BY id LIMIT 1",
            (user_id,),
        ).fetchone()
        if inventory_row:
            inventory_id = int(inventory_row[0])
            probes["inventory_entry_type"] = type(
                db.get_inventory_entry(user_id, inventory_id)
            ).__name__
            probes["item_by_inventory_type"] = type(
                db.get_item_by_inventory_id(inventory_id)
            ).__name__
            probes["item_by_inventory_full_type"] = type(
                db.get_item_by_inventory_id_full(inventory_id)
            ).__name__

    if before != fingerprint():
        fail("game.db changed during read-only contracts")

    print("[OK] capture-only cleanup contracts")
    print(f"- removed source captures: {len(CAPTURES)}")
    print("- removed runtime globals: 8")
    print(f"- required public APIs callable: {len(REQUIRED_PUBLIC_APIS)}")
    print(f"- read-only runtime probes: {probes}")
    print("- gameplay functions removed: 0")
    print("- database mutations: 0")


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
            (root / TARGET_REL).is_file()
            and (root / "game.db").is_file()
            and (root / "tools" / "check_imports.py").is_file()
        ):
            return root
    fail("Не знайдено корінь ROM.")


def assigned_names(statement):
    names = set()
    targets = []
    if isinstance(statement, ast.Assign):
        targets = statement.targets
    elif isinstance(statement, ast.AnnAssign):
        targets = [statement.target]
    elif isinstance(statement, ast.AugAssign):
        targets = [statement.target]
    for target in targets:
        for node in ast.walk(target):
            if isinstance(node, ast.Name):
                names.add(node.id)
    return names


def capture_references(source):
    tree = ast.parse(source)
    findings = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Name) and node.id in CAPTURES:
            findings.append((node.id, node.lineno, "name"))
        elif isinstance(node, ast.Constant) and isinstance(node.value, str) and node.value in CAPTURES:
            findings.append((node.value, node.lineno, "string"))
    return findings


def remove_capture_statements(source):
    tree = ast.parse(source)
    removals = []
    removed_names = set()
    parents = {}
    for parent in ast.walk(tree):
        for child in ast.iter_child_nodes(parent):
            parents[child] = parent

    # Captures are not necessarily direct children of Module. Some historical
    # assignments live inside top-level try/compatibility blocks, so inspect the
    # complete AST rather than tree.body only.
    for statement in ast.walk(tree):
        if not isinstance(statement, (ast.Assign, ast.AnnAssign, ast.AugAssign)):
            continue
        names = assigned_names(statement).intersection(CAPTURES)
        if names:
            removals.append(statement)
            removed_names.update(names)

    if removed_names != set(CAPTURES):
        missing = sorted(set(CAPTURES) - removed_names)
        extra = sorted(removed_names - set(CAPTURES))
        raise RuntimeError(
            f"capture assignment set mismatch: missing={missing}, extra={extra}"
        )

    lines = source.splitlines(keepends=True)
    edits = []
    for statement in removals:
        parent = parents.get(statement)
        must_keep_suite = False
        if parent is not None:
            for field_name in ("body", "orelse", "finalbody"):
                suite = getattr(parent, field_name, None)
                if isinstance(suite, list) and statement in suite and len(suite) == 1:
                    must_keep_suite = True
                    break
            if isinstance(parent, ast.Try):
                for handler in parent.handlers:
                    if statement in handler.body and len(handler.body) == 1:
                        must_keep_suite = True
                        break

        start = statement.lineno - 1
        end = statement.end_lineno
        if must_keep_suite:
            indent = " " * statement.col_offset
            replacement = indent + "pass  # removed obsolete compatibility capture\n"
        else:
            replacement = ""
            if end < len(lines) and not lines[end].strip():
                end += 1
        edits.append((start, end, replacement))

    for start, end, replacement in sorted(edits, key=lambda item: item[0], reverse=True):
        lines[start:end] = [replacement] if replacement else []

    updated = "".join(lines)
    ast.parse(updated, filename="db.py")
    residual = capture_references(updated)
    if residual:
        raise RuntimeError(f"capture references remain after removal: {residual}")
    return updated, len(removals)


def run_checked(root, path, label, env):
    result = subprocess.run([sys.executable, str(path)], cwd=root, env=env, check=False)
    if result.returncode != 0:
        raise RuntimeError(f"{label} exit code {result.returncode}")


def main():
    root = find_root()
    target = root / TARGET_REL
    tools = root / "tools"
    test_path = tools / TEST_NAME

    tests = [
        TEST_NAME,
        "smoke_test_inventory_refine_contracts.py",
        "smoke_test_equipment_readonly_core.py",
        "smoke_test_equipment_trader_contracts.py",
        "smoke_test_player_combat_stats.py",
        "smoke_test_rom_core.py",
        "check_imports.py",
    ]
    for name in tests[1:]:
        if not (tools / name).is_file():
            fail(f"Відсутній tools/{name}.")

    source = target.read_text(encoding="utf-8-sig")
    existing = capture_references(source)
    env = os.environ.copy()
    env["PYTHONUTF8"] = "1"
    env["PYTHONIOENCODING"] = "utf-8"

    if not existing:
        print(f"ℹ️ Патч {PATCH_ID} уже застосовано. Запускаю перевірки.")
        test_path.write_text(TEST_SOURCE, encoding="utf-8")
        for name in tests:
            run_checked(root, tools / name, name, env)
        return

    updated, removed_statements = remove_capture_statements(source)

    backup_dir = root / "backup"
    backup_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    code_backup = backup_dir / f"db.py_{PATCH_ID}_{stamp}.bak"
    test_backup = None
    shutil.copy2(target, code_backup)
    if test_path.exists():
        test_backup = backup_dir / f"tools_{TEST_NAME}_{PATCH_ID}_{stamp}.bak"
        shutil.copy2(test_path, test_backup)

    try:
        target.write_text(updated, encoding="utf-8")
        test_path.write_text(TEST_SOURCE, encoding="utf-8")
        py_compile.compile(str(target), doraise=True)
        py_compile.compile(str(test_path), doraise=True)

        for name in tests:
            run_checked(root, tools / name, name, env)

        readiness = subprocess.run(
            [sys.executable, str(tools / "db_cleanup_readiness.py")],
            cwd=root,
            env=env,
            text=True,
            encoding="utf-8",
            errors="replace",
            capture_output=True,
            check=False,
        )
        print(readiness.stdout, end="")
        if readiness.returncode != 0:
            raise RuntimeError(f"readiness exit code {readiness.returncode}")
        for marker in (
            "duplicates: 0",
            "legacy_refs: 0",
            "unsafe_delete: 0",
            "maybe_cleanup_later: 0",
        ):
            if marker not in readiness.stdout:
                raise RuntimeError(f"readiness missing {marker}")

    except Exception as exc:
        shutil.copy2(code_backup, target)
        if test_backup is not None:
            shutil.copy2(test_backup, test_path)
        elif test_path.exists():
            test_path.unlink()
        fail(f"Перевірка не пройдена; db.py і тест відновлено: {exc}")

    print(f"✅ Патч {PATCH_ID} успішно застосовано.")
    print(f"✅ Видалено capture statements: {removed_statements}")
    print("✅ Видалено 8 невикористаних runtime `_base_*` globals.")
    print("✅ Актуальні public Inventory/Refine/Equipment API збережено.")
    print("✅ Gameplay-код функцій і game.db не змінено.")
    print("Резервні копії:")
    print(f"   {code_backup.relative_to(root)}")
    if test_backup is not None:
        print(f"   {test_backup.relative_to(root)}")
    print("Перевірки:")
    for name in tests:
        print(f"   python ./tools/{name}")
    print("   python ./tools/db_cleanup_readiness.py")


if __name__ == "__main__":
    main()
