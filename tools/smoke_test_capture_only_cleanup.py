#!/usr/bin/env python3
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
