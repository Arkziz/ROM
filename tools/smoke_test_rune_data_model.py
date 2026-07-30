#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import hashlib
import importlib
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def fail(message):
    print(f"[FAIL] {message}")
    raise SystemExit(1)


def main():
    import db
    from data import runes
    from systems import rune_system

    result = db.init_rune_system()
    if result.get("success") is not True or result.get("seeded") != 28:
        fail(f"init contract failed: {result}")

    columns = {row[1] for row in db.conn.execute("PRAGMA table_info(inventory_runes)")}
    required = {"id", "inventory_id", "slot_index", "rune_item_id", "rune_stat", "rune_level", "inserted_at"}
    if not required.issubset(columns):
        fail(f"inventory_runes columns missing: {required - columns}")

    rows = db.conn.execute(
        "SELECT id, type, category, max_stack, sell_price FROM items "
        "WHERE id BETWEEN 501 AND 528 ORDER BY id"
    ).fetchall()
    if len(rows) != 28:
        fail(f"rune-system seed rows={len(rows)}, expected 28")
    if len({row[1] for row in rows}) != 28:
        fail("rune-system item types are not unique")
    if any(int(row[3] or 0) != 999 for row in rows):
        fail("rune-system max_stack contract failed")
    if any(float(row[4] or 0) != 0.0 for row in rows):
        fail("rune-system items must not be sellable")

    if len(runes.RUNE_ITEM_DEFINITIONS) != 25:
        fail("expected 25 canonical rune definitions")
    if sum(runes.RUNE_SLOT_LIMITS.values()) != 14:
        fail("expected 14 total equipment rune slots")
    if runes.FIRIUS_TOKENS_PER_DAILY_REWARD != 10:
        fail("daily Firius token reward must be 10")

    same = db.validate_rune_fusion_selection([501, 501, 501])
    mixed_type = db.validate_rune_fusion_selection([501, 506, 501])
    mixed_level = db.validate_rune_fusion_selection([501, 502, 501])
    wrong_count = db.validate_rune_fusion_selection([501, 501])
    max_level = db.validate_rune_fusion_selection([505, 505, 505])
    if not same.get("success") or same.get("result_item_id") != 502:
        fail(f"same-rune fusion selection failed: {same}")
    for result in (mixed_type, mixed_level):
        if result.get("code") != "different_runes" or "3 однакові руни" not in result.get("message", ""):
            fail(f"mixed rune validation message failed: {result}")
    if wrong_count.get("code") != "wrong_quantity":
        fail(f"wrong quantity contract failed: {wrong_count}")
    if max_level.get("code") != "max_level":
        fail(f"max-level contract failed: {max_level}")

    if db.get_equipped_rune_stat_totals(-999999999) != {"str": 0, "sta": 0, "dex": 0, "int": 0, "wis": 0}:
        fail("missing-user rune totals contract failed")

    quick = db.conn.execute("PRAGMA quick_check").fetchone()[0]
    if quick != "ok":
        fail(f"quick_check={quick}")

    print("[OK] Rune/Firius data model contracts")
    print("- canonical rune definitions: 25")
    print("- utility item definitions: 3")
    print("- seeded item rows 501-528: 28")
    print("- normalized inventory_runes schema: OK")
    print("- equipment rune slots total: 14")
    print("- Firius Tokens per daily reward: 10")
    print("- mixed rune type/level validation: OK")
    print("- user message: Потрібно вибрати 3 однакові руни одного типу й рівня.")
    print("- Rune V fusion rejection: OK")
    print("- stat integration active: no (reserved for 10.7.0)")
    print("- database quick_check: ok")


if __name__ == "__main__":
    main()
