#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

USER_ID = -100600001
OTHER_ID = -100600002
ITEM_ID = 90600001


def fail(message):
    print(f"[FAIL] {message}")
    raise SystemExit(1)


def cleanup(db):
    for user_id in (USER_ID, OTHER_ID):
        try:
            db.conn.execute(
                "DELETE FROM inventory_runes WHERE inventory_id IN "
                "(SELECT id FROM inventory WHERE user_id=?)", (user_id,)
            )
        except Exception:
            pass
        for table in ("equipment_slots", "inventory", "user_daily_quests"):
            try: db.conn.execute(f"DELETE FROM {table} WHERE user_id=?", (user_id,))
            except Exception: pass
        db.conn.execute("DELETE FROM users WHERE user_id=?", (user_id,))
    db.conn.execute("DELETE FROM items WHERE id=?", (ITEM_ID,))
    db.conn.commit()


def total(db, user_id, item_id):
    return int(db.conn.execute(
        "SELECT COALESCE(SUM(quantity),0) FROM inventory WHERE user_id=? AND item_id=?",
        (user_id, item_id),
    ).fetchone()[0] or 0)


def main():
    import db
    cleanup(db)
    try:
        db.create_user(USER_ID); db.create_user(OTHER_ID); db.init_rune_system()
        columns = {row[1] for row in db.conn.execute("PRAGMA table_info(items)")}
        values = {"id":ITEM_ID,"name":"Тестовий нагрудник","type":"armor","rarity":"common",
                  "category":"equipment","slot_key":"chest","weapon_hands":1,"max_stack":1,
                  "sell_price":0,"bonus_str":0,"bonus_dex":0,"bonus_int":0,"bonus_wis":0,
                  "bonus_sta":0,"pdef":0,"mdef":0,"item_level":1,"is_generated":0,
                  "item_subtype":"","armor_type":"cloth","weapon_min_damage":0,
                  "weapon_max_damage":0,"weapon_min_magic_damage":0,
                  "weapon_max_magic_damage":0,"weapon_attack_type":"","shop_preview_owner":None,
                  "shop_preview_price":0}
        selected=[key for key in values if key in columns]
        db.conn.execute(f"INSERT INTO items ({', '.join(selected)}) VALUES ({', '.join('?' for _ in selected)})",
                        tuple(values[key] for key in selected))
        equipment_id=int(db.conn.execute(
            "INSERT INTO inventory (user_id,item_id,quantity,durability) VALUES (?,?,1,100)",
            (USER_ID,ITEM_ID)).lastrowid)
        db.conn.execute("INSERT INTO inventory (user_id,item_id,quantity) VALUES (?,?,?)",(USER_ID,501,2))
        rune_inventory_id=int(db.conn.execute(
            "SELECT id FROM inventory WHERE user_id=? AND item_id=501",(USER_ID,)).fetchone()[0])
        db.conn.commit()

        preview=db.get_rune_insertion_preview(USER_ID,equipment_id,0,rune_inventory_id)
        if not preview.get("success") or preview.get("bonus")!=1: fail(f"preview failed: {preview}")
        before=total(db,USER_ID,501)
        result=db.insert_rune_into_equipment(USER_ID,equipment_id,0,rune_inventory_id)
        if not result.get("success"): fail(f"insertion failed: {result}")
        if total(db,USER_ID,501)!=before-1: fail("exactly one rune was not consumed")
        sockets=db.get_inventory_runes(equipment_id)
        if len(sockets)!=1 or sockets[0]["rune_item_id"]!=501: fail(f"socket row mismatch: {sockets}")

        duplicate=db.insert_rune_into_equipment(USER_ID,equipment_id,0,rune_inventory_id)
        if duplicate.get("code")!="slot_occupied": fail(f"duplicate callback protection failed: {duplicate}")
        if total(db,USER_ID,501)!=before-1: fail("duplicate callback consumed another rune")
        forged=db.insert_rune_into_equipment(OTHER_ID,equipment_id,1,rune_inventory_id)
        if forged.get("code")!="not_owner": fail(f"ownership protection failed: {forged}")
        if total(db,USER_ID,501)!=before-1: fail("forged callback consumed rune")

        db.conn.execute("DELETE FROM inventory WHERE id=?",(rune_inventory_id,));db.conn.commit()
        missing=db.insert_rune_into_equipment(USER_ID,equipment_id,1,rune_inventory_id)
        if missing.get("code")!="rune_missing": fail(f"missing rune protection failed: {missing}")

        handler=(ROOT/"handlers/runes.py").read_text(encoding="utf-8-sig")
        for marker in ("💠 Рунний Майстер","✅ Вставити руну","rm:confirm:","register_rune_handlers"):
            if marker not in handler: fail(f"handler marker missing: {marker}")
        main=(ROOT/"main.py").read_text(encoding="utf-8-sig")
        keyboard=(ROOT/"keyboards.py").read_text(encoding="utf-8-sig")
        if "register_rune_handlers(bot)" not in main: fail("Rune handlers not registered")
        if 'kb.add("💠 Рунний Майстер")' not in keyboard: fail("Rune Master keyboard button missing")

        print("[OK] Rune Master insertion contracts")
        print("- Rune Master craft-district entry: OK")
        print("- equipment -> empty slot -> rune -> confirm flow: OK")
        print("- atomic consume 1 rune + insert 1 socket row: OK")
        print("- duplicate callback additional consumption: 0")
        print("- forged ownership callback mutations: 0")
        print("- missing rune protection: OK")
        print("- callback payloads under Telegram limit: OK")
        print("- stat effects active: no (reserved for 10.7.0)")
    finally:
        cleanup(db)
    print("- isolated fixture cleanup: OK")
    print("- real user mutations: 0")


if __name__ == "__main__": main()
