#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ROM 9.0.13a: install and run a read-only static-items/DB-init audit."""
from __future__ import annotations

import os
import py_compile
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

PATCH_ID = "9.0.13a"
TOOL_NAME = "audit_static_items_and_db_init.py"

TOOL = r'''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Read-only audit of ROM static item seeds and DB initialization side effects."""
from __future__ import annotations

import ast
import hashlib
import json
import os
import re
import sqlite3
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "game.db"
REPORT = ROOT / "DB_CLEANUP_9_0_13A_STATIC_ITEMS_AND_DB_INIT_AUDIT.md"

LEGACY_EQUIPMENT_IDS = tuple(range(1, 27))
LEGACY_TRASH_IDS = tuple(range(101, 107))
CURRENT_TRASH_IDS = tuple(range(107, 127))
POTION_IDS = (201, 202, 203, 204)
CLASS_RESET_ID = 301
REFINE_IDS = (401, 402)
AUDIT_IDS = tuple(sorted(set(
    LEGACY_EQUIPMENT_IDS + LEGACY_TRASH_IDS + CURRENT_TRASH_IDS +
    POTION_IDS + (CLASS_RESET_ID,) + REFINE_IDS
)))
EXCLUDED_DIRS = {"patch", "backup", ".venv", "venv", "__pycache__", ".git"}


def fail(message):
    print(f"[FAIL] {message}")
    raise SystemExit(1)


def qident(name):
    return '"' + str(name).replace('"', '""') + '"'


def file_sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def parse(path):
    text = path.read_text(encoding="utf-8-sig")
    return text, ast.parse(text, filename=str(path))


def function_nodes(tree, name):
    return [
        node for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == name
    ]


def literal_seed_rows(text, tree, function_name):
    nodes = function_nodes(tree, function_name)
    if len(nodes) != 1:
        fail(f"{function_name}: definitions={len(nodes)}, expected 1")
    node = nodes[0]
    rows = []
    for sub in ast.walk(node):
        if not isinstance(sub, (ast.List, ast.Tuple)):
            continue
        for element in sub.elts:
            if not isinstance(element, ast.Tuple):
                continue
            try:
                value = ast.literal_eval(element)
            except Exception:
                continue
            if isinstance(value, tuple) and len(value) >= 5 and isinstance(value[0], int):
                rows.append(value)
    unique = {}
    for row in rows:
        unique[int(row[0])] = row
    return unique, ast.get_source_segment(text, node) or ""


def top_level_sql_side_effects(tree):
    findings = []
    mutating_methods = {"execute", "executemany", "executescript", "commit", "rollback"}
    mutating_names = {
        "ensure_refine_material_stack_sizes",
        "migrate_active_contracts_target_kills_to_5",
        "run_pending_migrations",
        "seed_items",
        "seed_location_trash_items",
        "seed_class_reset_sphere_item",
    }
    for statement in tree.body:
        if isinstance(statement, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef,
                                  ast.Import, ast.ImportFrom)):
            continue
        for node in ast.walk(statement):
            if not isinstance(node, ast.Call):
                continue
            name = None
            if isinstance(node.func, ast.Name):
                name = node.func.id
            elif isinstance(node.func, ast.Attribute):
                name = node.func.attr
            if name in mutating_methods or name in mutating_names:
                findings.append({"line": node.lineno, "call": name})
    return findings


def project_code_references():
    references = defaultdict(list)
    semantic_names = defaultdict(list)
    tracked_names = {
        "CLASS_RESET_SPHERE_ITEM_ID", "REFINE_STONE_ITEM_ID",
        "SUCCESS_RUNE_ITEM_ID", "DAILY_QUEST_REWARD_ITEM_ID",
    }
    for path in ROOT.rglob("*.py"):
        rel = path.relative_to(ROOT)
        if any(part in EXCLUDED_DIRS for part in rel.parts):
            continue
        try:
            _text, tree = parse(path)
        except Exception:
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.Constant) and type(node.value) is int and node.value in AUDIT_IDS:
                references[int(node.value)].append(f"{rel.as_posix()}:{node.lineno}")
            elif isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load) and node.id in tracked_names:
                semantic_names[node.id].append(f"{rel.as_posix()}:{node.lineno}")
    return references, semantic_names


def table_names(conn):
    return [
        row[0] for row in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name"
        ).fetchall()
    ]


def table_columns(conn, table):
    return [row[1] for row in conn.execute(f"PRAGMA table_info({qident(table)})").fetchall()]


def count_by_column(conn, table, column, ids):
    placeholders = ",".join("?" for _ in ids)
    rows = conn.execute(
        f"SELECT {qident(column)}, COUNT(*) FROM {qident(table)} "
        f"WHERE {qident(column)} IN ({placeholders}) GROUP BY {qident(column)} ORDER BY {qident(column)}",
        tuple(ids),
    ).fetchall()
    return {int(row[0]): int(row[1]) for row in rows}


def database_references(conn):
    refs = defaultdict(dict)
    for table in table_names(conn):
        columns = table_columns(conn, table)
        for column in columns:
            if column in {"item_id", "item_ref_id"}:
                counts = count_by_column(conn, table, column, AUDIT_IDS)
                if counts:
                    refs[f"{table}.{column}"].update(counts)
    return refs


def item_rows(conn):
    if "items" not in table_names(conn):
        fail("items table not found")
    columns = table_columns(conn, "items")
    wanted = [
        name for name in (
            "id", "name", "type", "rarity", "category", "slot_key",
            "max_stack", "sell_price", "item_level", "is_generated",
            "item_subtype", "armor_type", "weapon_attack_type",
            "shop_preview_owner", "shop_preview_price",
        ) if name in columns
    ]
    placeholders = ",".join("?" for _ in AUDIT_IDS)
    select_list = ",".join(qident(name) for name in wanted)
    rows = conn.execute(
        f"SELECT {select_list} FROM items WHERE id IN ({placeholders}) ORDER BY id",
        AUDIT_IDS,
    ).fetchall()
    return wanted, [dict(zip(wanted, row)) for row in rows]


def equipped_legacy_counts(conn):
    tables = set(table_names(conn))
    if not {"equipment_slots", "inventory"}.issubset(tables):
        return {}
    slot_cols = set(table_columns(conn, "equipment_slots"))
    inv_cols = set(table_columns(conn, "inventory"))
    if not {"inventory_id", "user_id"}.issubset(slot_cols) or not {"id", "item_id"}.issubset(inv_cols):
        return {}
    placeholders = ",".join("?" for _ in LEGACY_EQUIPMENT_IDS)
    rows = conn.execute(
        f"""SELECT i.item_id, COUNT(*)
            FROM equipment_slots es
            JOIN inventory i ON i.id=es.inventory_id
            WHERE i.item_id IN ({placeholders})
            GROUP BY i.item_id ORDER BY i.item_id""",
        LEGACY_EQUIPMENT_IDS,
    ).fetchall()
    return {int(row[0]): int(row[1]) for row in rows}


def auction_snapshot_hits(conn):
    if "auction_lots" not in table_names(conn):
        return []
    columns = set(table_columns(conn, "auction_lots"))
    snapshot_column = "item_snapshot_json" if "item_snapshot_json" in columns else None
    if not snapshot_column:
        return []
    hits = []
    rows = conn.execute(
        f"SELECT id, status, {qident(snapshot_column)} FROM auction_lots"
    ).fetchall()
    for lot_id, status, raw in rows:
        try:
            data = json.loads(raw or "{}")
        except Exception:
            continue
        candidates = []
        if isinstance(data, dict):
            for key in ("item_id", "source_item_id", "id"):
                value = data.get(key)
                if isinstance(value, int):
                    candidates.append(value)
        matched = sorted(set(candidates).intersection(AUDIT_IDS))
        if matched:
            hits.append({"lot_id": lot_id, "status": status, "item_ids": matched})
    return hits


def group_counts(mapping, ids):
    total = 0
    details = {}
    for source, counts in mapping.items():
        selected = {item_id: count for item_id, count in counts.items() if item_id in ids}
        if selected:
            details[source] = selected
            total += sum(selected.values())
    return total, details


def main():
    db_py = ROOT / "db.py"
    main_py = ROOT / "main.py"
    if not db_py.is_file() or not main_py.is_file():
        fail("db.py or main.py not found")
    if not DB_PATH.is_file():
        fail("game.db not found; DB reference audit cannot be completed")

    db_hash_before = file_sha256(DB_PATH)
    db_size_before = DB_PATH.stat().st_size
    db_mtime_before = DB_PATH.stat().st_mtime_ns

    db_text, db_tree = parse(db_py)
    main_text, main_tree = parse(main_py)

    seed_rows, seed_source = literal_seed_rows(db_text, db_tree, "seed_items")
    trash_rows, trash_source = literal_seed_rows(db_text, db_tree, "seed_location_trash_items")
    sphere_rows, sphere_source = literal_seed_rows(db_text, db_tree, "seed_class_reset_sphere_item")

    expected_seed_ids = set(LEGACY_EQUIPMENT_IDS + LEGACY_TRASH_IDS + POTION_IDS + (CLASS_RESET_ID,))
    actual_seed_ids = set(seed_rows)
    if not expected_seed_ids.issubset(actual_seed_ids):
        fail(f"seed_items missing expected IDs: {sorted(expected_seed_ids - actual_seed_ids)}")
    if not set(CURRENT_TRASH_IDS).issubset(set(trash_rows)):
        fail("seed_location_trash_items does not contain all IDs 107-126")

    conflict_301 = {
        "seed_items": seed_rows.get(CLASS_RESET_ID),
        "seed_class_reset_sphere_item": sphere_rows.get(CLASS_RESET_ID),
    }
    if conflict_301["seed_items"] is None:
        fail("expected historical item 301 collision was not found in seed_items")
    if "Сфера нового шляху" not in sphere_source:
        fail("canonical class-reset sphere seed not found")

    seed_replace = "INSERT OR REPLACE" in seed_source.upper()
    trash_replace = "INSERT OR REPLACE" in trash_source.upper()
    sphere_replace = "INSERT OR REPLACE" in sphere_source.upper()

    main_calls = []
    for node in ast.walk(main_tree):
        if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Name):
            continue
        if node.func.id in {"seed_items", "seed_location_trash_items", "seed_class_reset_sphere_item"}:
            main_calls.append((node.lineno, node.func.id))
    main_calls.sort()

    code_refs, semantic_refs = project_code_references()
    import_side_effects = top_level_sql_side_effects(db_tree)

    uri = DB_PATH.resolve().as_uri() + "?mode=ro"
    conn = sqlite3.connect(uri, uri=True)
    try:
        conn.execute("PRAGMA query_only=ON")
        refs = database_references(conn)
        item_columns, items = item_rows(conn)
        equipped = equipped_legacy_counts(conn)
        auction_hits = auction_snapshot_hits(conn)
        integrity = conn.execute("PRAGMA quick_check").fetchone()[0]
    finally:
        conn.close()

    db_hash_after = file_sha256(DB_PATH)
    if (
        db_hash_before != db_hash_after or
        db_size_before != DB_PATH.stat().st_size or
        db_mtime_before != DB_PATH.stat().st_mtime_ns
    ):
        fail("game.db changed during read-only audit")

    legacy_equipment_ref_total, legacy_equipment_refs = group_counts(refs, LEGACY_EQUIPMENT_IDS)
    legacy_trash_ref_total, legacy_trash_refs = group_counts(refs, LEGACY_TRASH_IDS)
    current_trash_ref_total, current_trash_refs = group_counts(refs, CURRENT_TRASH_IDS)
    potion_ref_total, potion_refs = group_counts(refs, POTION_IDS)
    sphere_ref_total, sphere_refs = group_counts(refs, (CLASS_RESET_ID,))
    refine_ref_total, refine_refs = group_counts(refs, REFINE_IDS)

    present_ids = {int(row["id"]) for row in items}
    missing_current = sorted(set(CURRENT_TRASH_IDS + POTION_IDS + (CLASS_RESET_ID,) + REFINE_IDS) - present_ids)

    recommendations = []
    recommendations.append("Remove IDs 1-26 from startup seed; keep existing DB rows until reference migration is decided.")
    recommendations.append("Remove IDs 101-106 from startup seed; current mobs use IDs 107-126.")
    recommendations.append("Remove the obsolete ID 301 Rune of Strength definition immediately; reserve 301 only for the class-reset sphere.")
    recommendations.append("Keep potions 201-204, current trash 107-126, class-reset sphere 301, and refine materials 401-402.")
    recommendations.append("Replace INSERT OR REPLACE seed writes with controlled UPSERT/INSERT OR IGNORE to avoid resetting modern item columns.")
    recommendations.append("Move import-time maintenance calls into explicit startup initialization/migrations.")
    if legacy_equipment_ref_total or equipped:
        recommendations.append("Do not DELETE legacy equipment item rows yet: real DB references/equipped rows exist.")
    else:
        recommendations.append("Legacy equipment rows have no direct inventory/equipment references in the audited DB; physical deletion is possible only after auction snapshot review and backup.")
    if legacy_trash_ref_total:
        recommendations.append("Do not DELETE legacy trash rows yet: existing inventories or other tables still reference them; allow players to sell them naturally.")
    else:
        recommendations.append("Legacy trash IDs 101-106 have no direct DB references in the audited DB and can become physical-cleanup candidates after backup.")

    report = [
        "# ROM 9.0.13a — Static Items and DB Initialization Audit",
        "",
        f"Generated: `{datetime.now().isoformat(timespec='seconds')}`",
        "",
        "## Safety",
        "",
        f"- Database opened with SQLite read-only URI: **yes**",
        f"- `PRAGMA query_only`: **enabled**",
        f"- Database SHA-256 unchanged: **{db_hash_before == db_hash_after}**",
        f"- Database integrity (`PRAGMA quick_check`): **{integrity}**",
        "- Gameplay files changed by audit: **0**",
        "- Database rows changed by audit: **0**",
        "",
        "## Seed ownership",
        "",
        f"- `seed_items()` IDs: `{sorted(actual_seed_ids)}`",
        f"- Legacy equipment IDs in seed: `{sorted(set(LEGACY_EQUIPMENT_IDS) & actual_seed_ids)}`",
        f"- Legacy trash IDs in seed: `{sorted(set(LEGACY_TRASH_IDS) & actual_seed_ids)}`",
        f"- Current trash IDs in dedicated seed: `{sorted(set(CURRENT_TRASH_IDS) & set(trash_rows))}`",
        f"- Potion IDs in seed: `{sorted(set(POTION_IDS) & actual_seed_ids)}`",
        f"- Refine IDs are owned by refine seed: `{list(REFINE_IDS)}`",
        "",
        "## Critical ID collision",
        "",
        f"- `seed_items()` ID 301: `{conflict_301['seed_items']}`",
        "- Canonical ID 301 owner: `seed_class_reset_sphere_item()` / `CLASS_RESET_SPHERE_ITEM_ID`.",
        "- Result: **confirmed semantic collision**.",
        "",
        "## Seed write policy",
        "",
        f"- `seed_items()` uses `INSERT OR REPLACE`: **{seed_replace}**",
        f"- `seed_location_trash_items()` uses `INSERT OR REPLACE`: **{trash_replace}**",
        f"- `seed_class_reset_sphere_item()` uses `INSERT OR REPLACE`: **{sphere_replace}**",
        f"- Current `items` columns: `{item_columns}`",
        "",
        "## Startup call order",
        "",
        f"- Calls found in `main.py`: `{main_calls}`",
        "",
        "## Real database references",
        "",
        f"- Legacy equipment 1-26 direct references: **{legacy_equipment_ref_total}** — `{legacy_equipment_refs}`",
        f"- Legacy equipment currently equipped: **{sum(equipped.values())}** — `{equipped}`",
        f"- Legacy trash 101-106 direct references: **{legacy_trash_ref_total}** — `{legacy_trash_refs}`",
        f"- Current trash 107-126 direct references: **{current_trash_ref_total}** — `{current_trash_refs}`",
        f"- Potions 201-204 direct references: **{potion_ref_total}** — `{potion_refs}`",
        f"- Class reset sphere 301 direct references: **{sphere_ref_total}** — `{sphere_refs}`",
        f"- Refine materials 401-402 direct references: **{refine_ref_total}** — `{refine_refs}`",
        f"- Auction snapshot hits: `{auction_hits}`",
        f"- Missing active static item rows: `{missing_current}`",
        "",
        "## Static code references",
        "",
    ]
    for item_id in AUDIT_IDS:
        locations = sorted(set(code_refs.get(item_id, [])))
        if locations:
            report.append(f"- `{item_id}`: `{locations}`")
    report.extend(["", "## Semantic constant references", ""])
    for name, locations in sorted(semantic_refs.items()):
        report.append(f"- `{name}`: `{sorted(set(locations))}`")
    report.extend(["", "## Top-level/import-time DB mutation candidates", ""])
    if import_side_effects:
        for finding in import_side_effects:
            report.append(f"- `db.py:{finding['line']}` calls `{finding['call']}()` at module scope.")
    else:
        report.append("- None detected by the structural rule set.")
    report.extend(["", "## Recommendations", ""])
    for index, recommendation in enumerate(recommendations, start=1):
        report.append(f"{index}. {recommendation}")
    report.extend(["", "## Suggested next patch", "", "`patch_9_0_13b_static_items_seed_cleanup.py`", ""])
    REPORT.write_text("\n".join(report), encoding="utf-8")

    print("[OK] static items and DB initialization audit")
    print(f"- seed_items IDs: {len(actual_seed_ids)}")
    print("- legacy equipment seed IDs: 26")
    print("- legacy trash seed IDs: 6")
    print("- current trash seed IDs: 20")
    print("- item 301 semantic collision: CONFIRMED")
    print(f"- legacy equipment DB refs: {legacy_equipment_ref_total}")
    print(f"- legacy equipment equipped: {sum(equipped.values())}")
    print(f"- legacy trash DB refs: {legacy_trash_ref_total}")
    print(f"- startup seed call count: {len(main_calls)}")
    print(f"- import-time mutation candidates: {len(import_side_effects)}")
    print("- database mutations: 0")
    print(f"- report: {REPORT}")


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
        if (root / "db.py").is_file() and (root / "main.py").is_file():
            return root
    fail("Не знайдено корінь ROM.")


def main():
    root = find_root()
    target = root / "tools" / TOOL_NAME
    backup = None

    if target.exists() and target.read_text(encoding="utf-8-sig") != TOOL:
        backup_dir = root / "backup"
        backup_dir.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup = backup_dir / f"tools_{TOOL_NAME}_{PATCH_ID}_{stamp}.bak"
        shutil.copy2(target, backup)

    target.write_text(TOOL, encoding="utf-8")

    env = os.environ.copy()
    env["PYTHONUTF8"] = "1"
    env["PYTHONIOENCODING"] = "utf-8"

    try:
        py_compile.compile(str(target), doraise=True)
        result = subprocess.run([sys.executable, str(target)], cwd=root, env=env, check=False)
        if result.returncode != 0:
            raise RuntimeError(f"audit exit code {result.returncode}")
    except Exception as exc:
        if backup is not None:
            shutil.copy2(backup, target)
        elif target.exists():
            target.unlink()
        fail(f"Аудит не пройдено; встановлення відкочено: {exc}")

    print(f"✅ Патч {PATCH_ID} успішно застосовано.")
    print(f"✅ Створено: tools/{TOOL_NAME}")
    print("✅ Створено: DB_CLEANUP_9_0_13A_STATIC_ITEMS_AND_DB_INIT_AUDIT.md")
    print("✅ Gameplay-код і game.db не змінені.")
    print("Резервні копії:")
    print(f"   {backup.relative_to(root) if backup else 'не потрібні - новий файл'}")
    print("Повторний запуск:")
    print(f"   python ./tools/{TOOL_NAME}")


if __name__ == "__main__":
    main()
