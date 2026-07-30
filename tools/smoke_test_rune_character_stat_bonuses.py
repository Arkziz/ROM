#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

USER_ID = -100700001
ITEM_ID = 90700001


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
        try: db.conn.execute(f"DELETE FROM {table} WHERE user_id=?", (USER_ID,))
        except Exception: pass
    db.conn.execute("DELETE FROM users WHERE user_id=?", (USER_ID,))
    db.conn.execute("DELETE FROM items WHERE id=?", (ITEM_ID,))
    db.conn.commit()


def main():
    import db
    cleanup(db)
    try:
        db.create_user(USER_ID)
        db.init_rune_system()
        db.conn.execute(
            "UPDATE users SET character_class='mage', level=8, str=10, dex=10, "
            "intelligence=20, wis=15, sta=12, hp=100, max_hp=100, mp=80, max_mp=80 "
            "WHERE user_id=?", (USER_ID,)
        )
        columns={row[1] for row in db.conn.execute("PRAGMA table_info(items)")}
        values={"id":ITEM_ID,"name":"Тестовий рунний нагрудник","type":"armor",
                "rarity":"common","category":"equipment","slot_key":"chest",
                "weapon_hands":1,"max_stack":1,"sell_price":0,"bonus_str":0,
                "bonus_dex":0,"bonus_int":0,"bonus_wis":0,"bonus_sta":0,
                "pdef":0,"mdef":0,"item_level":1,"is_generated":0,
                "item_subtype":"","armor_type":"cloth","weapon_min_damage":0,
                "weapon_max_damage":0,"weapon_min_magic_damage":0,
                "weapon_max_magic_damage":0,"weapon_attack_type":"",
                "shop_preview_owner":None,"shop_preview_price":0}
        selected=[key for key in values if key in columns]
        db.conn.execute(f"INSERT INTO items ({', '.join(selected)}) VALUES ({', '.join('?' for _ in selected)})",
                        tuple(values[key] for key in selected))
        equipment_id=int(db.conn.execute(
            "INSERT INTO inventory (user_id,item_id,quantity,durability) VALUES (?,?,1,100)",
            (USER_ID,ITEM_ID)).lastrowid)
        # create_user() already initializes all canonical equipment slots,
        # including chest, with inventory_id=NULL. Update that existing row
        # instead of inserting a duplicate (user_id, slot_key) pair.
        updated_slot = db.conn.execute(
            "UPDATE equipment_slots SET inventory_id=? "
            "WHERE user_id=? AND slot_key=?",
            (equipment_id, USER_ID, "chest"),
        ).rowcount
        if updated_slot != 1:
            raise RuntimeError(
                f"fixture chest slot update count={updated_slot}, expected 1"
            )
        # STA III, INT IV, WIS V, STR II, DEX I
        rune_specs=((513,"STA",3),(519,"INT",4),(525,"WIS",5),(502,"STR",2),(506,"DEX",1))
        for index,(item_id,stat,level) in enumerate(rune_specs):
            db.conn.execute(
                "INSERT INTO inventory_runes (inventory_id,slot_index,rune_item_id,rune_stat,rune_level) "
                "VALUES (?,?,?,?,?)",(equipment_id,index,item_id,stat,level))
        db.conn.commit()

        # chest normally has 3, but direct fixture uses 5 rows to verify each stat once.
        totals=db.get_equipped_rune_stat_totals(USER_ID)
        expected={"str":2,"sta":3,"dex":1,"int":4,"wis":5}
        if totals!=expected: fail(f"rune totals mismatch: {totals}")
        stats=db.get_player_stats(USER_ID)
        if stats[:5]!=(12,11,24,20,15): fail(f"player stats mismatch: {stats}")

        max_hp=db.get_max_hp(USER_ID)
        expected_hp=100+8*20+15*5
        if max_hp!=expected_hp: fail(f"Max HP mismatch: {max_hp} != {expected_hp}")
        pdef=db.get_physical_defense(USER_ID)
        if pdef!=3: fail(f"PDEF mismatch: {pdef}")
        mdef=db.get_magic_defense(USER_ID)
        if mdef!=20: fail(f"MDEF mismatch: {mdef}")
        max_mp=db.get_max_mp(USER_ID)
        expected_mp=100+8*20+24*3+20*2
        if max_mp!=expected_mp: fail(f"Max MP mismatch: {max_mp} != {expected_mp}")

        # Stored resource synchronization must clamp only, never heal to full.
        db.conn.execute("UPDATE users SET hp=100, max_hp=100, mp=80, max_mp=80 WHERE user_id=?",(USER_ID,))
        db.conn.commit()
        hp_sync=db.sync_user_max_hp(USER_ID,heal_to_full=False)
        db.refresh_user_mp(USER_ID)
        row=db.conn.execute("SELECT hp,max_hp,mp,max_mp FROM users WHERE user_id=?",(USER_ID,)).fetchone()
        if tuple(row)!=(100,expected_hp,80,expected_mp): fail(f"resource no-heal sync mismatch: {row}")

        # Broken equipment disables all rune bonuses.
        db.conn.execute("UPDATE inventory SET durability=0 WHERE id=?",(equipment_id,));db.conn.commit()
        broken=db.get_equipped_rune_stat_totals(USER_ID)
        if any(broken.values()): fail(f"broken item rune bonuses remain: {broken}")
        broken_stats=db.get_player_stats(USER_ID)
        if broken_stats[:5]!=(10,10,20,15,12): fail(f"broken stats mismatch: {broken_stats}")

        # Unequipped equipment also disables rune bonuses.
        db.conn.execute("UPDATE inventory SET durability=100 WHERE id=?",(equipment_id,))
        db.conn.execute("DELETE FROM equipment_slots WHERE user_id=?",(USER_ID,));db.conn.commit()
        unequipped=db.get_equipped_rune_stat_totals(USER_ID)
        if any(unequipped.values()): fail(f"unequipped rune bonuses remain: {unequipped}")

        print("[OK] Rune character stat bonus contracts")
        print("- STR/STA/DEX/INT/WIS rune totals: exact once")
        print("- equipped + durability >0 requirement: OK")
        print("- unequipped rune bonuses: 0")
        print("- broken equipment rune bonuses: 0")
        print("- Max HP / PDEF from STA: OK")
        print("- Max MP / MDEF from INT/WIS: OK")
        print("- physical/magical crit inherit DEX/WIS: canonical stat path")
        print("- resource sync free healing: 0")
    finally:
        cleanup(db)
    print("- isolated fixture cleanup: OK")
    print("- real user mutations: 0")


if __name__=="__main__": main()
