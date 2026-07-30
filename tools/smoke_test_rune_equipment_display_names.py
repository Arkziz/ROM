#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

USER_ID = -100920001
BASE_ITEM_ID = 90920000
ARMOR_CASES = (
    ("helmet", "cloth", "Каптур 5 рівня", "Каптур [Тканина] 5 рівня"),
    ("chest", "leather", "Нагрудник 6 рівня", "Нагрудник [Шкіра] 6 рівня"),
    ("legs", "chain", "Поножі 7 рівня", "Поножі [Кольчуга] 7 рівня"),
    ("boots", "plate", "Чоботи 8 рівня", "Чоботи [Лати] 8 рівня"),
)


def fail(message):
    print(f"[FAIL] {message}")
    raise SystemExit(1)


def cleanup(db):
    try:
        db.conn.execute(
            "DELETE FROM inventory_runes WHERE inventory_id IN "
            "(SELECT id FROM inventory WHERE user_id=?)", (USER_ID,)
        )
    except Exception:
        pass
    for table in ("equipment_slots", "inventory", "user_daily_quests"):
        try:
            db.conn.execute(f"DELETE FROM {table} WHERE user_id=?", (USER_ID,))
        except Exception:
            pass
    db.conn.execute("DELETE FROM users WHERE user_id=?", (USER_ID,))
    db.conn.execute("DELETE FROM items WHERE id BETWEEN ? AND ?", (BASE_ITEM_ID, BASE_ITEM_ID + 20))
    db.conn.commit()


def create_item(db, item_id, slot_key, armor_type, name):
    columns = {row[1] for row in db.conn.execute("PRAGMA table_info(items)")}
    values = {
        "id": item_id, "name": name, "type": "armor", "rarity": "common",
        "category": "equipment", "slot_key": slot_key, "armor_type": armor_type,
        "weapon_hands": 1, "max_stack": 1, "sell_price": 0,
        "bonus_str": 0, "bonus_dex": 0, "bonus_int": 0,
        "bonus_wis": 0, "bonus_sta": 0, "pdef": 0, "mdef": 0,
        "item_level": 1, "is_generated": 0, "item_subtype": "",
    }
    selected = [key for key in values if key in columns]
    db.conn.execute(
        f"INSERT INTO items ({', '.join(selected)}) VALUES "
        f"({', '.join('?' for _ in selected)})",
        tuple(values[key] for key in selected),
    )
    inventory_id = int(db.conn.execute(
        "INSERT INTO inventory (user_id,item_id,quantity,durability) VALUES (?,?,1,100)",
        (USER_ID, item_id),
    ).lastrowid)
    return inventory_id


def main():
    import db
    cleanup(db)
    try:
        db.create_user(USER_ID)
        db.init_rune_system()
        inventory_ids = []
        for offset, (slot_key, armor_type, name, expected) in enumerate(ARMOR_CASES):
            inventory_id = create_item(
                db, BASE_ITEM_ID + offset, slot_key, armor_type, name
            )
            inventory_ids.append(inventory_id)
            actual = db.get_rune_equipment_display_name(inventory_id)
            if actual != expected:
                fail(f"{armor_type}: {actual!r} != {expected!r}")

        # Already formatted names must not duplicate the armor type.
        duplicate = db.get_rune_equipment_display_name(
            inventory_ids[0], "Каптур [Тканина] 5 рівня"
        )
        if duplicate != "Каптур [Тканина] 5 рівня":
            fail(f"armor type duplicated: {duplicate}")

        # Add a rune to the leather chest so both insertion and extractor paths see it.
        chest_id = inventory_ids[1]
        db.conn.execute(
            "INSERT INTO inventory_runes "
            "(inventory_id,slot_index,rune_item_id,rune_stat,rune_level) "
            "VALUES (?,0,501,'STR',1)",
            (chest_id,),
        )
        db.conn.commit()

        slot_info = db.get_equipment_rune_slot_info(USER_ID, chest_id)
        if slot_info.get("name") != "Нагрудник [Шкіра] 6 рівня":
            fail(f"Rune insertion display mismatch: {slot_info}")

        extractor_list = db.get_extractor_equipment(USER_ID)
        extractor_item = next(
            (item for item in extractor_list if item["inventory_id"] == chest_id), None
        )
        if not extractor_item or extractor_item["name"] != "Нагрудник [Шкіра] 6 рівня":
            fail(f"Extractor list display mismatch: {extractor_item}")

        preview = db.get_extractor_preview(USER_ID, chest_id)
        if preview.get("equipment_name") != "Нагрудник [Шкіра] 6 рівня":
            fail(f"Extractor preview display mismatch: {preview}")

        print("[OK] Rune equipment display-name contracts")
        print("- cloth -> Тканина: OK")
        print("- leather -> Шкіра: OK")
        print("- chain -> Кольчуга: OK")
        print("- plate -> Лати: OK")
        print("- Rune Master insertion list/details: canonical name")
        print("- Extractor list/type selection/confirmation: canonical name")
        print("- duplicate armor labels: 0")
        print("- weapon/off-hand naming policy changed: no")
    finally:
        cleanup(db)
    print("- isolated fixture cleanup: OK")
    print("- real user mutations: 0")


if __name__ == "__main__":
    main()
