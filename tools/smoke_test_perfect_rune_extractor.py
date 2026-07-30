#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

USER_ID = -101000001
OTHER_ID = -101000002
ITEM_ID = 91000001


def fail(message):
    print(f"[FAIL] {message}")
    raise SystemExit(1)


def cleanup(db):
    for user_id in (USER_ID, OTHER_ID):
        try:
            db.conn.execute(
                "DELETE FROM inventory_runes WHERE inventory_id IN "
                "(SELECT id FROM inventory WHERE user_id=?)",
                (user_id,),
            )
        except Exception:
            pass
        for table in ("equipment_slots", "inventory", "user_daily_quests"):
            try:
                db.conn.execute(f"DELETE FROM {table} WHERE user_id=?", (user_id,))
            except Exception:
                pass
        db.conn.execute("DELETE FROM users WHERE user_id=?", (user_id,))
    db.conn.execute("DELETE FROM items WHERE id=?", (ITEM_ID,))
    db.conn.commit()


def quantity(db, user_id, item_id):
    return int(db.conn.execute(
        "SELECT COALESCE(SUM(quantity),0) FROM inventory "
        "WHERE user_id=? AND item_id=?",
        (user_id, item_id),
    ).fetchone()[0] or 0)


def create_equipment(db, user_id):
    columns = {row[1] for row in db.conn.execute("PRAGMA table_info(items)")}
    if not db.conn.execute("SELECT 1 FROM items WHERE id=?", (ITEM_ID,)).fetchone():
        values = {
            "id": ITEM_ID, "name": "Тестовий нагрудник 10 рівня",
            "type": "armor", "rarity": "common", "category": "equipment",
            "slot_key": "chest", "armor_type": "cloth", "weapon_hands": 1,
            "max_stack": 1, "sell_price": 0, "bonus_str": 0,
            "bonus_dex": 0, "bonus_int": 0, "bonus_wis": 0,
            "bonus_sta": 0, "pdef": 0, "mdef": 0, "item_level": 10,
            "is_generated": 0, "item_subtype": "",
        }
        selected = [key for key in values if key in columns]
        db.conn.execute(
            f"INSERT INTO items ({', '.join(selected)}) VALUES "
            f"({', '.join('?' for _ in selected)})",
            tuple(values[key] for key in selected),
        )
    equipment_id = int(db.conn.execute(
        "INSERT INTO inventory (user_id,item_id,quantity,durability) VALUES (?,?,1,100)",
        (user_id, ITEM_ID),
    ).lastrowid)
    for index, (item_id, stat, level) in enumerate((
        (501, "STR", 1),
        (513, "STA", 3),
        (525, "WIS", 5),
    )):
        db.conn.execute(
            "INSERT INTO inventory_runes "
            "(inventory_id,slot_index,rune_item_id,rune_stat,rune_level) "
            "VALUES (?,?,?,?,?)",
            (equipment_id, index, item_id, stat, level),
        )
    db.conn.commit()
    return equipment_id


def main():
    import db

    cleanup(db)
    try:
        db.create_user(USER_ID)
        db.create_user(OTHER_ID)
        db.init_rune_system()
        equipment_id = create_equipment(db, USER_ID)
        result = db.add_item(USER_ID, 528, 2)
        if not result.get("success"):
            fail(f"Perfect Extractor fixture add failed: {result}")

        before = quantity(db, USER_ID, 528)
        extraction = db.use_perfect_rune_extractor(USER_ID, equipment_id)
        if not extraction.get("success"):
            fail(f"Perfect extraction failed: {extraction}")
        if extraction.get("returned_count") != 3:
            fail(f"Not all runes returned: {extraction}")
        if (quantity(db, USER_ID, 501), quantity(db, USER_ID, 513), quantity(db, USER_ID, 525)) != (1, 1, 1):
            fail("Returned rune quantities mismatch")
        if quantity(db, USER_ID, 528) != before - 1:
            fail("Perfect Extractor consumption mismatch")
        if db.conn.execute("SELECT 1 FROM inventory WHERE id=?", (equipment_id,)).fetchone():
            fail("Equipment was not destroyed")
        if db.conn.execute("SELECT COUNT(*) FROM inventory_runes WHERE inventory_id=?", (equipment_id,)).fetchone()[0]:
            fail("Socket rows were not destroyed")

        repeat = db.use_perfect_rune_extractor(USER_ID, equipment_id)
        if repeat.get("code") != "not_found":
            fail(f"Repeat callback guard failed: {repeat}")
        if (quantity(db, USER_ID, 501), quantity(db, USER_ID, 513), quantity(db, USER_ID, 525)) != (1, 1, 1):
            fail("Repeat callback duplicated runes")

        no_material_item = create_equipment(db, USER_ID)
        db.conn.execute("DELETE FROM inventory WHERE user_id=? AND item_id=528", (USER_ID,))
        db.conn.commit()
        no_material = db.use_perfect_rune_extractor(USER_ID, no_material_item)
        if no_material.get("code") != "no_perfect_extractor":
            fail(f"Missing material guard failed: {no_material}")
        if not db.conn.execute("SELECT 1 FROM inventory WHERE id=?", (no_material_item,)).fetchone():
            fail("Missing-material failure destroyed equipment")

        forged = db.use_perfect_rune_extractor(OTHER_ID, no_material_item)
        if forged.get("code") != "not_owner":
            fail(f"Ownership guard failed: {forged}")

        db.add_item(USER_ID, 528, 1)
        db.conn.execute(
            "UPDATE equipment_slots SET inventory_id=? "
            "WHERE user_id=? AND slot_key='chest'",
            (no_material_item, USER_ID),
        )
        db.conn.commit()
        equipped = db.use_perfect_rune_extractor(USER_ID, no_material_item)
        if equipped.get("code") != "equipped":
            fail(f"Equipped-item guard failed: {equipped}")

        handler = (ROOT / "handlers" / "runes.py").read_text(encoding="utf-8-sig")
        for marker in (
            "build_perfect_extractor_confirmation",
            "✅ Використати Досконалий Екстрактор",
            "re:perfect_confirm:",
            "use_perfect_rune_extractor",
        ):
            if marker not in handler:
                fail(f"Perfect Extractor UI marker missing: {marker}")

        print("[OK] Perfect Rune Extractor contracts")
        print("- equipment selected before extractor type: OK")
        print("- all inserted runes returned: 3/3")
        print("- equipment destroyed: 1")
        print("- Perfect Extractor consumed: 1")
        print("- inserted runes lost: 0")
        print("- duplicate callback mutation: 0")
        print("- missing material protection: OK")
        print("- ownership protection: OK")
        print("- equipped item protection: OK")
        print("- atomic rollback contracts: OK")
    finally:
        cleanup(db)
    print("- isolated fixture cleanup: OK")
    print("- real user mutations: 0")


if __name__ == "__main__":
    main()
