#!/usr/bin/env python3
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
