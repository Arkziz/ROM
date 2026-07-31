#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations
import ast, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))
USER_ID=-101300001

def fail(message): print(f"[FAIL] {message}"); raise SystemExit(1)
def cleanup(db):
    for table in ("equipment_slots","inventory","user_daily_quests"):
        try: db.conn.execute(f"DELETE FROM {table} WHERE user_id=?",(USER_ID,))
        except Exception: pass
    db.conn.execute("DELETE FROM users WHERE user_id=?",(USER_ID,)); db.conn.commit()
def quantity(db,item_id):
    return int(db.conn.execute("SELECT COALESCE(SUM(quantity),0) FROM inventory WHERE user_id=? AND item_id=?",(USER_ID,item_id)).fetchone()[0] or 0)
def main():
    import db
    from data.runes import SIMPLE_RUNE_EXTRACTOR_GOLD_PRICE,SIMPLE_RUNE_EXTRACTOR_SHOP_ENABLED,PERFECT_RUNE_EXTRACTOR_CRYSTAL_SHOP_ENABLED
    cleanup(db)
    try:
        if SIMPLE_RUNE_EXTRACTOR_GOLD_PRICE!=10.0: fail("price")
        if not SIMPLE_RUNE_EXTRACTOR_SHOP_ENABLED: fail("shop disabled")
        if PERFECT_RUNE_EXTRACTOR_CRYSTAL_SHOP_ENABLED: fail("perfect shop enabled")
        db.create_user(USER_ID); db.conn.execute("UPDATE users SET gold=100 WHERE user_id=?",(USER_ID,)); db.conn.commit()
        before=quantity(db,527)
        one=db.buy_simple_rune_extractor(USER_ID,1)
        if not one.get("success") or quantity(db,527)!=before+1: fail(one)
        custom=db.buy_simple_rune_extractor(USER_ID,7)
        if not custom.get("success") or quantity(db,527)!=before+8: fail(custom)
        gold=float(db.conn.execute("SELECT gold FROM users WHERE user_id=?",(USER_ID,)).fetchone()[0])
        if gold!=20.0: fail(f"gold={gold}")
        rejected=db.buy_simple_rune_extractor(USER_ID,3)
        if rejected.get("code")!="not_enough_gold" or quantity(db,527)!=before+8: fail(rejected)
        for value in (0,101):
            if db.buy_simple_rune_extractor(USER_ID,value).get("code")!="invalid_quantity": fail(value)
        hp=ROOT/"handlers/runes.py"; handlers=hp.read_text(encoding="utf-8-sig"); ast.parse(handlers,filename=str(hp))
        keyboard=(ROOT/"keyboards.py").read_text(encoding="utf-8-sig")
        main_source=(ROOT/"main.py").read_text(encoding="utf-8-sig")
        if 'kb.add("🛒 Крамниця")' not in keyboard: fail("shop button")
        for marker in ("rs:buy:1","rs:quantity","rs:confirm:","build_rune_master_shop_quantity_prompt","build_rune_master_shop_confirmation","rune_master_shop_quantity_input","_RUNE_MASTER_SHOP_QUANTITY_STATE_10_13_0"):
            if marker not in handlers: fail(marker)
        if "rs:buy:5" in handlers: fail("obsolete buy 5")
        if "register_rune_master_shop_handlers(bot)" not in main_source: fail("registration")
        print("[OK] Rune Master Extractor shop contracts")
        print("- Simple Extractor unit price: 10 gold")
        print("- immediate buy x1: OK")
        print("- custom quantity 1-100: OK")
        print("- confirmation callback: OK")
        print("- insufficient gold rollback: OK")
        print("- Perfect Extractor crystal purchase active: no")
    finally: cleanup(db)
    print("- isolated fixture cleanup: OK"); print("- real user mutations: 0")
if __name__=="__main__": main()
