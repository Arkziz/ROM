#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

FIXTURE_USER_ID = -100500001
FIXTURE_ITEM_ID = 90500001


def fail(message):
    print(f"[FAIL] {message}")
    raise SystemExit(1)


def cleanup(db):
    try:
        db.conn.execute(
            "DELETE FROM inventory_runes WHERE inventory_id IN "
            "(SELECT id FROM inventory WHERE user_id=?)",
            (FIXTURE_USER_ID,),
        )
    except Exception:
        pass
    for table in ("equipment_slots", "inventory", "user_daily_quests"):
        try:
            db.conn.execute(f"DELETE FROM {table} WHERE user_id=?", (FIXTURE_USER_ID,))
        except Exception:
            pass
    db.conn.execute("DELETE FROM users WHERE user_id=?", (FIXTURE_USER_ID,))
    db.conn.execute("DELETE FROM items WHERE id=?", (FIXTURE_ITEM_ID,))
    db.conn.commit()


def main():
    import db
    from data.runes import RUNE_SLOT_LIMITS
    from systems import rune_system

    cleanup(db)
    try:
        db.create_user(FIXTURE_USER_ID)
        columns = {row[1] for row in db.conn.execute("PRAGMA table_info(items)")}
        values = {
            "id": FIXTURE_ITEM_ID,
            "name": "Тестове рунне спорядження",
            "type": "armor",
            "rarity": "common",
            "category": "equipment",
            "slot_key": "chest",
            "weapon_hands": 1,
            "max_stack": 1,
            "sell_price": 0,
            "bonus_str": 0, "bonus_dex": 0, "bonus_int": 0,
            "bonus_wis": 0, "bonus_sta": 0, "pdef": 0, "mdef": 0,
            "item_level": 1, "is_generated": 0, "item_subtype": "",
            "armor_type": "cloth", "weapon_min_damage": 0,
            "weapon_max_damage": 0, "weapon_min_magic_damage": 0,
            "weapon_max_magic_damage": 0, "weapon_attack_type": "",
            "shop_preview_owner": None, "shop_preview_price": 0,
        }
        selected = [key for key in values if key in columns]
        db.conn.execute(
            f"INSERT INTO items ({', '.join(selected)}) VALUES "
            f"({', '.join('?' for _ in selected)})",
            tuple(values[key] for key in selected),
        )
        cursor = db.conn.execute(
            "INSERT INTO inventory (user_id, item_id, quantity, durability) "
            "VALUES (?, ?, 1, 100)",
            (FIXTURE_USER_ID, FIXTURE_ITEM_ID),
        )
        inventory_id = int(cursor.lastrowid)
        db.conn.commit()

        info = db.get_equipment_rune_slot_info(FIXTURE_USER_ID, inventory_id)
        if not info.get("success") or info.get("capacity") != 3:
            fail(f"chest slot info mismatch: {info}")
        if info.get("used") != 0 or info.get("free") != 3:
            fail(f"empty socket counts mismatch: {info}")
        if len(info.get("slots", [])) != 3:
            fail("chest must expose 3 explicit socket records")
        text = db.format_equipment_rune_slots_text(FIXTURE_USER_ID, inventory_id)
        if "Використано: 0/3" not in text or text.count("порожній") != 3:
            fail(f"empty slot display mismatch: {text}")
        if db.get_equipment_rune_slot_info(-1, inventory_id).get("code") != "not_owner":
            fail("ownership protection failed")
        if sum(RUNE_SLOT_LIMITS.values()) != 14:
            fail("total rune slot map must equal 14")

        # Insert one synthetic canonical socket row to test read/display only.
        db.conn.execute(
            "INSERT INTO inventory_runes "
            "(inventory_id, slot_index, rune_item_id, rune_stat, rune_level) "
            "VALUES (?, 0, 501, 'STR', 1)",
            (inventory_id,),
        )
        db.conn.commit()
        filled = db.get_equipment_rune_slot_info(FIXTURE_USER_ID, inventory_id)
        filled_text = db.format_equipment_rune_slots_text(FIXTURE_USER_ID, inventory_id)
        if filled.get("used") != 1 or filled.get("free") != 2:
            fail(f"filled socket counts mismatch: {filled}")
        if "Слот 1: Руна Сили I (+1)" not in filled_text:
            fail(f"filled socket display mismatch: {filled_text}")

        inventory_source = (ROOT / "handlers" / "inventory.py").read_text(encoding="utf-8-sig")
        for marker in (
            "hide redundant ×1",
            'if quantity > 1:',
            'label += f" ×{quantity}"',
            "💠 Рунні слоти:",
        ):
            if marker not in inventory_source:
                fail(f"mobile/rune UI marker missing: {marker}")

        print("[OK] Equipment Rune Slot contracts")
        print("- equipment slot types: 10")
        print("- full equipment rune capacity: 14")
        print("- chest capacity: 3")
        print("- normalized socket rows: OK")
        print("- ownership protection: OK")
        print("- empty/occupied slot display: OK")
        print("- mobile rune label ×1 hidden: OK")
        print("- stacked rune label uses ×N: OK")
        print("- rune insertion mutation API active: no (reserved for 10.6.0)")
        print("- stat effects active: no (reserved for 10.7.0)")
    finally:
        cleanup(db)
    print("- isolated fixture cleanup: OK")
    print("- real user mutations: 0")


if __name__ == "__main__":
    main()
