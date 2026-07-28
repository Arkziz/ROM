#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Isolated mutation contracts for ROM Character System."""
from __future__ import annotations
import inspect
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))

import db
from data.classes import CLASS_CONFIGS
from systems import character_system as cs

TEST_USER_ID=-90120501
SECOND_USER_ID=-90120502


def fail(message):
    print(f"[FAIL] {message}")
    raise SystemExit(1)


def cleanup():
    for uid in (TEST_USER_ID,SECOND_USER_ID):
        for table in ("equipment_slots","inventory","user_active_contracts","user_daily_quests"):
            try: db.cursor.execute(f"DELETE FROM {table} WHERE user_id=?",(uid,))
            except Exception: pass
        db.cursor.execute("DELETE FROM users WHERE user_id=?",(uid,))
    db.conn.commit()


def insert_user(uid):
    db.cursor.execute(
        """
        INSERT INTO users (
            user_id,hp,max_hp,level,exp,gold,kills,bag_slots,current_location,
            str,dex,intelligence,wis,sta,daily_hunts,character_name,
            character_class,class_change_available,mp,max_mp
        ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """,
        (uid,170,170,3,0,0,0,40,"start_path",10,10,12,11,10,0,"","",0,0,0),
    )
    db.conn.commit()


def state(uid):
    row=db.cursor.execute(
        "SELECT character_name,character_class,class_change_available,mp,max_mp FROM users WHERE user_id=?",
        (uid,),
    ).fetchone()
    return tuple(row) if row else None


def main():
    real_before=db.cursor.execute(
        "SELECT user_id,character_name,character_class,class_change_available,mp,max_mp FROM users WHERE user_id>=0 ORDER BY user_id"
    ).fetchall()
    cleanup()
    insert_user(TEST_USER_ID)
    insert_user(SECOND_USER_ID)
    checks=0
    try:
        # No literal character-name example is embedded: derive a valid unique value from the fixture ID.
        generated_name=str(abs(TEST_USER_ID))
        normalized=db.normalize_character_name("  "+generated_name+"  ")
        if normalized!=generated_name: fail("name normalization contract failed")
        valid,message=db.validate_character_name(generated_name)
        if valid is not True or message!="": fail("valid name contract failed")
        checks+=2

        result=db.set_character_name(TEST_USER_ID,"  "+generated_name+"  ")
        if not isinstance(result,dict) or result.get("success") is not True: fail("set_character_name success contract failed")
        if db.get_character_name(TEST_USER_ID)!=generated_name: fail("character name persistence failed")
        if cs.is_character_name_taken(generated_name,exclude_user_id=TEST_USER_ID): fail("exclude_user_id uniqueness contract failed")
        duplicate=db.set_character_name(SECOND_USER_ID,generated_name)
        if not isinstance(duplicate,dict) or duplicate.get("success") is not False: fail("duplicate name rejection failed")
        invalid=db.set_character_name(TEST_USER_ID,"")
        if not isinstance(invalid,dict) or invalid.get("success") is not False: fail("invalid name rejection failed")
        checks+=5

        mana_classes=[key for key,cfg in CLASS_CONFIGS.items() if cfg.get("resource")=="mana"]
        non_mana_classes=[key for key,cfg in CLASS_CONFIGS.items() if cfg.get("resource")!="mana"]
        if not mana_classes or not non_mana_classes: fail("required class fixtures not available")
        mana_key=mana_classes[0]; non_mana_key=non_mana_classes[0]

        class_result=db.set_character_class(TEST_USER_ID,mana_key)
        if not isinstance(class_result,dict) or class_result.get("success") is not True: fail("set mana class contract failed")
        if db.get_character_class(TEST_USER_ID)!=mana_key: fail("class persistence failed")
        if db.get_character_class_display(TEST_USER_ID)!=CLASS_CONFIGS[mana_key]["name"]: fail("class display contract failed")
        if db.get_character_resource_type(TEST_USER_ID)!="mana": fail("resource type contract failed")
        unknown=db.set_character_class(TEST_USER_ID,"__invalid_class_key__")
        if not isinstance(unknown,dict) or unknown.get("success") is not False: fail("unknown class rejection failed")
        checks+=5

        maximum=db.get_max_mp(TEST_USER_ID)
        if not isinstance(maximum,int) or maximum<=0: fail("mana max MP contract failed")
        # Public keyword contract uses mp=; system implementation uses amount=.
        if db.set_user_mp(TEST_USER_ID,mp=maximum+100)!=maximum: fail("public mp keyword/clamp contract failed")
        mp_info=db.get_user_mp(TEST_USER_ID)
        required={"mp","max_mp","current_mp"}
        if not isinstance(mp_info,dict) or not required.issubset(mp_info): fail("get_user_mp dictionary contract failed")
        if mp_info["mp"]!=maximum or mp_info["max_mp"]!=maximum: fail("get_user_mp values failed")
        if cs.set_user_mp(TEST_USER_ID,amount=-10)!=0: fail("system amount keyword/lower clamp failed")
        refreshed=db.refresh_user_mp(TEST_USER_ID)
        if not isinstance(refreshed,int): fail("refresh_user_mp return contract failed")
        checks+=5

        non_mana=db.set_character_class(TEST_USER_ID,non_mana_key)
        if non_mana.get("success") is not True: fail("set non-mana class failed")
        if db.get_max_mp(TEST_USER_ID)!=0: fail("non-mana max MP contract failed")
        info=db.get_user_mp(TEST_USER_ID)
        if info.get("mp")!=0 or info.get("max_mp")!=0: fail("non-mana MP contract failed")
        checks+=3

        if db.get_class_change_available(TEST_USER_ID)!=0 or db.has_class_change_available(TEST_USER_ID): fail("initial class-change contract failed")
        if db.grant_class_change_available(TEST_USER_ID)!=1: fail("single grant failed")
        if db.grant_class_change_available(TEST_USER_ID,amount=2)!=3: fail("multi grant failed")
        if not db.has_class_change_available(TEST_USER_ID): fail("availability boolean failed")
        if db.consume_class_change_available(TEST_USER_ID) is not True: fail("consume available failed")
        if db.get_class_change_available(TEST_USER_ID)!=2: fail("consume count failed")
        db.consume_class_change_available(TEST_USER_ID); db.consume_class_change_available(TEST_USER_ID)
        if db.consume_class_change_available(TEST_USER_ID) is not False: fail("consume at zero failed")
        checks+=7

        # Public and system signatures intentionally differ only in the second parameter name for set_user_mp.
        public_sig=str(inspect.signature(db.set_user_mp)); system_sig=str(inspect.signature(cs.set_user_mp))
        if public_sig!="(user_id, mp)" or system_sig!="(user_id, amount)": fail("set_user_mp signature contract changed")

    finally:
        cleanup()

    leftovers=db.cursor.execute("SELECT COUNT(*) FROM users WHERE user_id IN (?,?)",(TEST_USER_ID,SECOND_USER_ID)).fetchone()[0]
    if int(leftovers or 0)!=0: fail("isolated fixture cleanup failed")
    real_after=db.cursor.execute(
        "SELECT user_id,character_name,character_class,class_change_available,mp,max_mp FROM users WHERE user_id>=0 ORDER BY user_id"
    ).fetchall()
    if [tuple(r) for r in real_before] != [tuple(r) for r in real_after]: fail("real user rows changed")

    print("[OK] character isolated mutation contracts")
    print(f"- mutation contract checks: {checks}")
    print("- name validation/uniqueness: OK")
    print("- class selection/display/resource: OK")
    print("- MP dictionary/clamp/keyword contracts: OK")
    print("- class-change grant/consume contracts: OK")
    print("- isolated fixtures cleanup: OK")
    print("- real user mutations: 0")

if __name__=="__main__": main()
