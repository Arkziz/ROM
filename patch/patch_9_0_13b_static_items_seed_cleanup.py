#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ROM 9.0.13b: clean legacy static-item seeds and safely retire items 1-26."""
from __future__ import annotations

import ast
import json
import os
import py_compile
import shutil
import sqlite3
import subprocess
import sys
from datetime import datetime
from pathlib import Path

PATCH_ID = "9.0.13b"
LEGACY_EQUIPMENT_IDS = tuple(range(1, 27))
LEGACY_TRASH_IDS = tuple(range(101, 107))
CURRENT_TRASH_IDS = tuple(range(107, 127))
POTION_IDS = (201, 202, 203, 204)
CLASS_RESET_ID = 301
TEST_NAME = "smoke_test_static_item_seed_contracts.py"
TESTS = (
    TEST_NAME,
    "smoke_test_inventory_refine_contracts.py",
    "smoke_test_equipment_readonly_core.py",
    "smoke_test_equipment_trader_contracts.py",
    "smoke_test_auction_lifecycle_contracts.py",
    "smoke_test_rom_core.py",
    "check_imports.py",
)

SEED_ITEMS_SOURCE = '''def seed_items():
    """Seed active consumables only.

    Legacy static equipment 1-26, legacy trash 101-106, and the obsolete
    Rune of Strength definition for ID 301 were retired in ROM 9.0.13b.
    """
    items = [
        (201, "🔴 Мале зілля здоров’я", "potion_hp", "common", "potion", None, 1, 10, 1.00, 0, 0, 0, 0, 0, 0, 0),
        (202, "🔵 Мале зілля мани", "potion_mp", "common", "potion", None, 1, 10, 1.20, 0, 0, 0, 0, 0, 0, 0),
        (203, "🔴 Середнє зілля здоров’я", "potion_hp_medium", "common", "potion", None, 1, 10, 3.00, 0, 0, 0, 0, 0, 0, 0),
        (204, "🔵 Середнє зілля мани", "potion_mp_medium", "common", "potion", None, 1, 10, 3.60, 0, 0, 0, 0, 0, 0, 0),
    ]

    for item in items:
        cursor.execute("""
        INSERT INTO items (
            id, name, type, rarity, category,
            slot_key, weapon_hands,
            max_stack, sell_price,
            bonus_str, bonus_dex, bonus_int, bonus_wis, bonus_sta,
            pdef, mdef
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(id) DO UPDATE SET
            name=excluded.name,
            type=excluded.type,
            rarity=excluded.rarity,
            category=excluded.category,
            slot_key=excluded.slot_key,
            weapon_hands=excluded.weapon_hands,
            max_stack=excluded.max_stack,
            sell_price=excluded.sell_price,
            bonus_str=excluded.bonus_str,
            bonus_dex=excluded.bonus_dex,
            bonus_int=excluded.bonus_int,
            bonus_wis=excluded.bonus_wis,
            bonus_sta=excluded.bonus_sta,
            pdef=excluded.pdef,
            mdef=excluded.mdef
        """, item)

    conn.commit()
'''

UPSERT_SUFFIX = '''
        ON CONFLICT(id) DO UPDATE SET
            name=excluded.name,
            type=excluded.type,
            rarity=excluded.rarity,
            category=excluded.category,
            slot_key=excluded.slot_key,
            weapon_hands=excluded.weapon_hands,
            max_stack=excluded.max_stack,
            sell_price=excluded.sell_price,
            bonus_str=excluded.bonus_str,
            bonus_dex=excluded.bonus_dex,
            bonus_int=excluded.bonus_int,
            bonus_wis=excluded.bonus_wis,
            bonus_sta=excluded.bonus_sta,
            pdef=excluded.pdef,
            mdef=excluded.mdef'''

POST_TEST = r'''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ROM 9.0.13b static-item seed contracts (read-only)."""
from __future__ import annotations
import ast
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "game.db"
LEGACY_EQUIPMENT_IDS = set(range(1, 27))
LEGACY_TRASH_IDS = set(range(101, 107))
CURRENT_TRASH_IDS = set(range(107, 127))
POTION_IDS = {201, 202, 203, 204}


def fail(message):
    print(f"[FAIL] {message}")
    raise SystemExit(1)


def parse_seed_rows(source, tree, name):
    nodes = [node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == name]
    if len(nodes) != 1:
        fail(f"{name} definitions={len(nodes)}, expected 1")
    rows = {}
    for node in ast.walk(nodes[0]):
        if isinstance(node, ast.Tuple):
            try:
                value = ast.literal_eval(node)
            except Exception:
                continue
            if isinstance(value, tuple) and len(value) >= 5 and isinstance(value[0], int):
                rows[value[0]] = value
    return rows, ast.get_source_segment(source, nodes[0]) or ""


def main():
    source = (ROOT / "db.py").read_text(encoding="utf-8-sig")
    tree = ast.parse(source, filename=str(ROOT / "db.py"))
    rows, seed_source = parse_seed_rows(source, tree, "seed_items")
    trash_rows, trash_source = parse_seed_rows(source, tree, "seed_location_trash_items")
    sphere_rows, sphere_source = parse_seed_rows(source, tree, "seed_class_reset_sphere_item")

    if set(rows) != POTION_IDS:
        fail(f"seed_items IDs={sorted(rows)}, expected {sorted(POTION_IDS)}")
    if LEGACY_EQUIPMENT_IDS & set(rows) or LEGACY_TRASH_IDS & set(rows):
        fail("legacy equipment/trash still exists in seed_items")
    if 301 in rows or "Руна Сили I" in seed_source:
        fail("obsolete item 301 Rune of Strength remains in seed_items")
    if not CURRENT_TRASH_IDS.issubset(set(trash_rows)):
        fail("current trash seed 107-126 is incomplete")
    if "Сфера нового шляху" not in sphere_source:
        fail("canonical class-reset sphere seed is missing")
    for name, function_source in (
        ("seed_items", seed_source),
        ("seed_location_trash_items", trash_source),
        ("seed_class_reset_sphere_item", sphere_source),
    ):
        upper = function_source.upper()
        if "INSERT OR REPLACE" in upper:
            fail(f"{name} still uses INSERT OR REPLACE")
        if "ON CONFLICT(ID) DO UPDATE" not in upper:
            fail(f"{name} does not use controlled UPSERT")

    uri = DB_PATH.resolve().as_uri() + "?mode=ro"
    conn = sqlite3.connect(uri, uri=True)
    try:
        conn.execute("PRAGMA query_only=ON")
        legacy_count = int(conn.execute(
            "SELECT COUNT(*) FROM items WHERE id BETWEEN 1 AND 26"
        ).fetchone()[0] or 0)
        if legacy_count:
            fail(f"legacy item rows 1-26 remain: {legacy_count}")
        placeholders = ",".join("?" for _ in POTION_IDS)
        potions = conn.execute(
            f"SELECT id, type FROM items WHERE id IN ({placeholders}) ORDER BY id",
            tuple(sorted(POTION_IDS)),
        ).fetchall()
        if [row[0] for row in potions] != sorted(POTION_IDS):
            fail(f"active potion rows missing: {potions}")
        sphere = conn.execute("SELECT name, type FROM items WHERE id=301").fetchone()
        if not sphere or sphere[1] != "class_reset" or "Сфера нового шляху" not in sphere[0]:
            fail(f"item 301 is not canonical class-reset sphere: {sphere}")
        legacy_trash_count = int(conn.execute(
            "SELECT COUNT(*) FROM items WHERE id BETWEEN 101 AND 106"
        ).fetchone()[0] or 0)
        integrity = conn.execute("PRAGMA quick_check").fetchone()[0]
    finally:
        conn.close()
    if integrity != "ok":
        fail(f"database quick_check={integrity}")

    print("[OK] static item seed post-cleanup contracts")
    print("- seed_items active IDs: [201, 202, 203, 204]")
    print("- legacy equipment seed IDs: 0")
    print("- legacy trash seed IDs: 0")
    print("- obsolete Rune of Strength ID 301: absent")
    print("- canonical class-reset sphere ID 301: OK")
    print("- controlled UPSERT functions: 3")
    print("- physical legacy equipment rows 1-26: 0")
    print(f"- preserved compatibility trash rows 101-106: {legacy_trash_count}")
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
            (root / "db.py").is_file()
            and (root / "game.db").is_file()
            and (root / "tools" / "check_imports.py").is_file()
        ):
            return root
    fail("Не знайдено корінь ROM або game.db.")


def qident(name):
    return '"' + str(name).replace('"', '""') + '"'


def function_map(tree):
    result = {}
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            result.setdefault(node.name, []).append(node)
    return result


def node_start(node):
    decorators = getattr(node, "decorator_list", None) or []
    return min([node.lineno] + [decorator.lineno for decorator in decorators])


def replace_function(source, node, replacement):
    lines = source.splitlines(keepends=True)
    text = replacement.rstrip() + "\n\n"
    lines[node_start(node) - 1:node.end_lineno] = [text]
    return "".join(lines)


def convert_function_to_upsert(source, function_name):
    tree = ast.parse(source)
    nodes = function_map(tree).get(function_name, [])
    if len(nodes) != 1:
        raise RuntimeError(f"{function_name} definitions={len(nodes)}, expected 1")
    node = nodes[0]
    function_source = ast.get_source_segment(source, node) or ""
    if "INSERT OR REPLACE INTO items" not in function_source:
        if "ON CONFLICT(id) DO UPDATE" in function_source:
            return source
        raise RuntimeError(f"{function_name}: INSERT OR REPLACE not found")
    old_values = "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"
    if function_source.count(old_values) != 1:
        raise RuntimeError(f"{function_name}: VALUES signature count={function_source.count(old_values)}")
    updated_function = function_source.replace("INSERT OR REPLACE INTO items", "INSERT INTO items", 1)
    updated_function = updated_function.replace(old_values, old_values + UPSERT_SUFFIX, 1)
    return replace_function(source, node, updated_function)


def table_names(conn):
    return [row[0] for row in conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
    ).fetchall()]


def table_columns(conn, table):
    return [row[1] for row in conn.execute(f"PRAGMA table_info({qident(table)})").fetchall()]


def direct_legacy_references(conn):
    findings = []
    placeholders = ",".join("?" for _ in LEGACY_EQUIPMENT_IDS)
    for table in table_names(conn):
        for column in table_columns(conn, table):
            if column not in {"item_id", "item_ref_id"}:
                continue
            count = int(conn.execute(
                f"SELECT COUNT(*) FROM {qident(table)} WHERE {qident(column)} IN ({placeholders})",
                LEGACY_EQUIPMENT_IDS,
            ).fetchone()[0] or 0)
            if count:
                findings.append((table, column, count))
    return findings


def auction_snapshot_references(conn):
    if "auction_lots" not in table_names(conn):
        return []
    columns = set(table_columns(conn, "auction_lots"))
    if "item_snapshot_json" not in columns:
        return []
    hits = []
    for lot_id, status, raw in conn.execute(
        "SELECT id, status, item_snapshot_json FROM auction_lots"
    ).fetchall():
        try:
            data = json.loads(raw or "{}")
        except Exception:
            continue
        if not isinstance(data, dict):
            continue
        values = []
        for key in ("item_id", "source_item_id", "id"):
            value = data.get(key)
            if isinstance(value, int):
                values.append(value)
        matched = sorted(set(values).intersection(LEGACY_EQUIPMENT_IDS))
        if matched:
            hits.append((lot_id, status, matched))
    return hits


def validate_source(updated):
    tree = ast.parse(updated)
    definitions = function_map(tree)
    for name in ("seed_items", "seed_location_trash_items", "seed_class_reset_sphere_item"):
        if len(definitions.get(name, [])) != 1:
            raise RuntimeError(f"{name}: invalid definition count")
    seed_node = definitions["seed_items"][0]
    seed_source = ast.get_source_segment(updated, seed_node) or ""
    ids = set()
    for node in ast.walk(seed_node):
        if isinstance(node, ast.Tuple):
            try:
                value = ast.literal_eval(node)
            except Exception:
                continue
            if isinstance(value, tuple) and len(value) >= 5 and isinstance(value[0], int):
                ids.add(value[0])
    if ids != set(POTION_IDS):
        raise RuntimeError(f"seed_items IDs={sorted(ids)}, expected {list(POTION_IDS)}")
    if "Руна Сили I" in seed_source:
        raise RuntimeError("obsolete Rune of Strength remains")
    for name in ("seed_items", "seed_location_trash_items", "seed_class_reset_sphere_item"):
        source = ast.get_source_segment(updated, definitions[name][0]) or ""
        if "INSERT OR REPLACE" in source.upper():
            raise RuntimeError(f"{name} still uses INSERT OR REPLACE")
        if "ON CONFLICT(id) DO UPDATE" not in source:
            raise RuntimeError(f"{name} missing controlled UPSERT")


def run_checked(root, path, label, env):
    result = subprocess.run([sys.executable, str(path)], cwd=root, env=env, check=False)
    if result.returncode != 0:
        raise RuntimeError(f"{label} exit code {result.returncode}")


def main():
    root = find_root()
    db_py = root / "db.py"
    game_db = root / "game.db"
    tools = root / "tools"
    test_path = tools / TEST_NAME

    for test_name in TESTS[1:]:
        if not (tools / test_name).is_file():
            fail(f"Відсутній tools/{test_name}.")

    source = db_py.read_text(encoding="utf-8-sig")
    tree = ast.parse(source, filename=str(db_py))
    definitions = function_map(tree)
    seed_nodes = definitions.get("seed_items", [])
    if len(seed_nodes) != 1:
        fail(f"seed_items definitions={len(seed_nodes)}, очікувалося 1.")

    current_seed_source = ast.get_source_segment(source, seed_nodes[0]) or ""
    already_clean = (
        "Руна Сили I" not in current_seed_source
        and "ON CONFLICT(id) DO UPDATE" in current_seed_source
    )
    if already_clean:
        print(f"ℹ️ Патч {PATCH_ID} уже застосовано. Запускаю перевірки.")
        test_path.write_text(POST_TEST, encoding="utf-8")
        env = os.environ.copy()
        env["PYTHONUTF8"] = "1"
        env["PYTHONIOENCODING"] = "utf-8"
        for test_name in TESTS:
            run_checked(root, tools / test_name, test_name, env)
        return

    # Repeat the safety audit immediately before any write.
    conn = sqlite3.connect(str(game_db))
    try:
        direct_refs = direct_legacy_references(conn)
        snapshot_refs = auction_snapshot_references(conn)
        if direct_refs:
            fail(f"Legacy equipment 1-26 now has DB references: {direct_refs}")
        if snapshot_refs:
            fail(f"Legacy equipment 1-26 now appears in Auction snapshots: {snapshot_refs}")
        integrity = conn.execute("PRAGMA quick_check").fetchone()[0]
        if integrity != "ok":
            fail(f"game.db quick_check={integrity}")
    finally:
        conn.close()

    updated = replace_function(source, seed_nodes[0], SEED_ITEMS_SOURCE)
    updated = convert_function_to_upsert(updated, "seed_location_trash_items")
    updated = convert_function_to_upsert(updated, "seed_class_reset_sphere_item")
    validate_source(updated)

    backup_dir = root / "backup"
    backup_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    code_backup = backup_dir / f"db.py_{PATCH_ID}_static_seed_cleanup_{stamp}.bak"
    database_backup = backup_dir / f"game.db_{PATCH_ID}_before_legacy_equipment_delete_{stamp}.bak"
    test_backup = None
    shutil.copy2(db_py, code_backup)
    shutil.copy2(game_db, database_backup)
    if test_path.exists():
        test_backup = backup_dir / f"tools_{TEST_NAME}_{PATCH_ID}_{stamp}.bak"
        shutil.copy2(test_path, test_backup)

    temp = db_py.with_name(".db.9_0_13b.tmp")
    env = os.environ.copy()
    env["PYTHONUTF8"] = "1"
    env["PYTHONIOENCODING"] = "utf-8"

    try:
        temp.write_text(updated, encoding="utf-8")
        os.replace(temp, db_py)
        test_path.write_text(POST_TEST, encoding="utf-8")
        py_compile.compile(str(db_py), doraise=True)
        py_compile.compile(str(test_path), doraise=True)

        conn = sqlite3.connect(str(game_db))
        try:
            conn.execute("BEGIN IMMEDIATE")
            refs_after_lock = direct_legacy_references(conn)
            snapshots_after_lock = auction_snapshot_references(conn)
            if refs_after_lock or snapshots_after_lock:
                raise RuntimeError(
                    f"references appeared before delete: direct={refs_after_lock}, snapshots={snapshots_after_lock}"
                )
            placeholders = ",".join("?" for _ in LEGACY_EQUIPMENT_IDS)
            conn.execute(
                f"DELETE FROM items WHERE id IN ({placeholders})",
                LEGACY_EQUIPMENT_IDS,
            )
            deleted = int(conn.execute("SELECT changes()").fetchone()[0] or 0)
            remaining = int(conn.execute(
                "SELECT COUNT(*) FROM items WHERE id BETWEEN 1 AND 26"
            ).fetchone()[0] or 0)
            if remaining:
                raise RuntimeError(f"legacy equipment rows remain: {remaining}")
            if conn.execute("PRAGMA quick_check").fetchone()[0] != "ok":
                raise RuntimeError("game.db quick_check failed after delete")
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

        for test_name in TESTS:
            run_checked(root, tools / test_name, test_name, env)

        readiness = subprocess.run(
            [sys.executable, str(tools / "db_cleanup_readiness.py")],
            cwd=root, env=env, text=True, encoding="utf-8", errors="replace",
            capture_output=True, check=False,
        )
        print(readiness.stdout, end="")
        if readiness.returncode != 0:
            raise RuntimeError(f"readiness exit code {readiness.returncode}")
        for expected in (
            "duplicates: 0", "legacy_refs: 0", "unsafe_delete: 0", "maybe_cleanup_later: 0",
        ):
            if expected not in readiness.stdout:
                raise RuntimeError(f"readiness missing {expected}")

    except Exception as exc:
        shutil.copy2(code_backup, db_py)
        shutil.copy2(database_backup, game_db)
        if test_backup is not None:
            shutil.copy2(test_backup, test_path)
        elif test_path.exists():
            test_path.unlink()
        if temp.exists():
            temp.unlink()
        fail(f"Перевірка не пройдена; db.py, game.db і тест відновлено: {exc}")

    print(f"✅ Патч {PATCH_ID} успішно застосовано.")
    print("✅ seed_items містить лише активні зілля 201-204.")
    print("✅ Legacy equipment 1-26 прибрано зі seed і фізично видалено з items.")
    print("✅ Legacy trash 101-106 прибрано зі seed, але compatibility rows збережено.")
    print("✅ Конфліктне визначення 301 як Руна Сили I видалено.")
    print("✅ ID 301 належить лише Сфері нового шляху.")
    print("✅ Три seed-функції переведено з INSERT OR REPLACE на контрольований UPSERT.")
    print(f"✅ Фізично видалено legacy equipment rows: {deleted}")
    print("Резервні копії:")
    print(f"   {code_backup.relative_to(root)}")
    print(f"   {database_backup.relative_to(root)}")
    if test_backup is not None:
        print(f"   {test_backup.relative_to(root)}")
    print("Перевірки:")
    print("   python -m py_compile ./db.py")
    for test_name in TESTS:
        print(f"   python ./tools/{test_name}")
    print("   python ./tools/db_cleanup_readiness.py")


if __name__ == "__main__":
    main()
