#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations
import ast, importlib, sqlite3, sys, tempfile
from contextlib import closing
from datetime import datetime, timedelta, timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))
def fail(x): print(f"[FAIL] {x}"); raise SystemExit(1)
def main():
    for rel in ("systems/player_interaction_system.py","db.py","main.py"):
        p=ROOT/rel; ast.parse(p.read_text(encoding="utf-8-sig"),filename=str(p))
    m=importlib.import_module("systems.player_interaction_system")
    now=datetime(2026,8,3,12,0,tzinfo=timezone.utc)
    with tempfile.TemporaryDirectory(prefix="rom_policy_12_5_0_",ignore_cleanup_errors=True) as td:
        db=Path(td)/"test.db"
        with closing(sqlite3.connect(db)) as c:
            c.executescript("""
            PRAGMA foreign_keys=ON;
            CREATE TABLE users(user_id INTEGER PRIMARY KEY,character_name TEXT,current_location TEXT,last_activity_at TEXT);
            CREATE TABLE items(id INTEGER PRIMARY KEY,name TEXT,category TEXT,tradeable INTEGER,bound_type TEXT,dev_only INTEGER,premium_bound INTEGER);
            CREATE TABLE inventory(id INTEGER PRIMARY KEY,user_id INTEGER,item_id INTEGER,quantity INTEGER,durability INTEGER,max_durability INTEGER,refine_level INTEGER);
            CREATE TABLE equipment_slots(user_id INTEGER,slot_key TEXT,inventory_id INTEGER);
            CREATE TABLE inventory_runes(id INTEGER PRIMARY KEY,inventory_id INTEGER,rune_item_id INTEGER,slot_index INTEGER);
            CREATE TABLE player_interaction_requests(id INTEGER PRIMARY KEY,request_type TEXT,initiator_user_id INTEGER,recipient_user_id INTEGER,location_snapshot TEXT,status TEXT,revision INTEGER,created_at TEXT,updated_at TEXT,expires_at TEXT,responded_at TEXT);
            CREATE TABLE player_activity_sessions(id INTEGER PRIMARY KEY,user_id INTEGER UNIQUE,activity_type TEXT,reference_id INTEGER,status TEXT,created_at TEXT,updated_at TEXT,expires_at TEXT);
            CREATE TABLE player_trades(id INTEGER PRIMARY KEY,request_id INTEGER,initiator_user_id INTEGER,recipient_user_id INTEGER,location_snapshot TEXT,status TEXT,revision INTEGER,initiator_ready INTEGER,recipient_ready INTEGER,initiator_confirmed INTEGER,recipient_confirmed INTEGER,created_at TEXT,updated_at TEXT,expires_at TEXT,completed_at TEXT,cancelled_at TEXT,cancel_reason TEXT);
            CREATE TABLE auction_lots(id INTEGER PRIMARY KEY,item_ref_id INTEGER,item_source TEXT,quantity INTEGER,status TEXT);
            """)
            c.executemany("INSERT INTO users VALUES(?,?,?,?,?)",()) if False else None
            c.executemany("INSERT INTO users VALUES(?,?,?,?)",((1,"A","start_path",now.isoformat()),(2,"B","start_path",now.isoformat())))
            items=((301,"Sphere","material",0,"",0,0),(401,"Stone","material",1,"",0,0),(402,"Success","material",1,"",0,0),(501,"Rune","rune",1,"",0,0),(526,"Token","material",1,"",0,0),(527,"Simple","material",1,"",0,0),(528,"Perfect","material",1,"",0,0),(900,"Trash","trash",1,"",0,0),(901,"Potion","potion",1,"",0,0),(902,"Sword","equipment",1,"",0,0),(903,"Bound","material",0,"quest",0,0),(904,"ChildRune","rune",1,"",0,0),(905,"GenericBlocked","material",0,"",0,0))
            c.executemany("INSERT INTO items VALUES(?,?,?,?,?,?,?)",items)
            inventory=((10,1,301,1,None,None,0),(11,1,401,20,None,None,0),(12,1,402,1,None,None,0),(13,1,501,3,None,None,0),(14,1,526,2,None,None,0),(15,1,527,1,None,None,0),(16,1,528,1,None,None,0),(17,1,900,5,None,None,0),(18,1,901,10,None,None,0),(19,1,902,1,50,100,3),(20,1,902,1,0,100,0),(21,1,903,1,None,None,0),(22,1,902,1,80,100,1),(23,1,905,1,None,None,0))
            c.executemany("INSERT INTO inventory VALUES(?,?,?,?,?,?,?)",inventory)
            c.execute("INSERT INTO equipment_slots VALUES(1,'main_hand',22)")
            c.execute("INSERT INTO inventory_runes VALUES(1,19,501,0)")
            expires=(now+timedelta(minutes=10)).isoformat()
            c.execute("INSERT INTO player_trades VALUES(1,1,1,2,'start_path','editing',1,0,0,0,0,?,?,?,NULL,NULL,NULL)",(now.isoformat(),now.isoformat(),expires))
            c.commit()
        if not m.init_player_trade_item_policy_and_reservations(db_path=db)["success"]: fail("init")
        allowed=(11,13,15,18,19)
        for inv in allowed:
            result=m.get_item_trade_policy(1,inv,1,trade_id=1,db_path=db)
            if not result["tradeable"]: fail((inv,result))
        blocked={10:"protected_item",12:"protected_item",14:"protected_item",16:"protected_item",17:"gray_loot",20:"broken",21:"bound_item",22:"equipped",23:"tradeable_false"}
        for inv,reason in blocked.items():
            result=m.get_item_trade_policy(1,inv,1,trade_id=1,db_path=db)
            if result["tradeable"] or result["reason"]!=reason: fail((inv,result))
        snapshot=m.build_trade_item_snapshot(1,19,db_path=db)
        if not snapshot or len(snapshot["runes"])!=1: fail(snapshot)
        first=m.reserve_inventory_for_trade(1,1,11,7,now=now,db_path=db)
        if not first["success"]: fail(first)
        if m.get_inventory_available_quantity(1,11,db_path=db)!=13: fail("available quantity")
        second=m.reserve_inventory_for_trade(1,1,11,21,now=now,db_path=db)
        if second["success"]: fail("quantity overflow")
        if not m.assert_inventory_not_reserved(11,requested_quantity=1,db_path=db)["success"] is False: fail("reservation guard")
        released=m.release_trade_inventory_reservations(1,db_path=db)
        if released!=1: fail(released)
        if m.get_inventory_available_quantity(1,11,db_path=db)!=20: fail("release")
        # Re-reserve and verify cancel_player_trade clears Stage 12.5 rows.
        again=m.reserve_inventory_for_trade(1,1,11,2,now=now,db_path=db)
        if not again["success"]: fail(again)
        cancelled=m.cancel_player_trade(1,1,now=now,db_path=db)
        if not cancelled["success"]: fail(cancelled)
        with closing(sqlite3.connect(db)) as c:
            if c.execute("SELECT COUNT(*) FROM inventory_reservations").fetchone()[0] != 0:
                fail("cancel reservation residue")
            c.execute("UPDATE player_trades SET status='cancelled' WHERE id=1")
        with closing(sqlite3.connect(db)) as c:
            c.execute(
                "INSERT INTO inventory_reservations "
                "(inventory_id,user_id,quantity,reservation_type,reference_id,created_at,expires_at) "
                "VALUES(11,1,2,'player_trade',1,?,?)",
                (now.isoformat(),(now+timedelta(minutes=1)).isoformat()),
            )
            c.commit()
        with closing(sqlite3.connect(db)) as c:
            fixture_count=c.execute("SELECT COUNT(*) FROM inventory_reservations").fetchone()[0]
        if fixture_count != 1: fail(f"reservation fixture persistence: {fixture_count}")
        recovery=m.recover_orphan_inventory_reservations(now=now,db_path=db)
        if recovery["orphan_or_terminal"]!=1: fail(recovery)
    main=(ROOT/"main.py").read_text(encoding="utf-8-sig")
    if "init_player_trade_item_policy_and_reservations()" not in main: fail("startup init")
    print("[OK] Player trade item policy and reservation contracts")
    print("- allowed stone/runes/potions/simple extractor/equipment: OK")
    print("- blocked sphere/success rune/token/perfect extractor/trash: OK")
    print("- equipped/broken/bound policy: OK")
    print("- quantity-aware stack reservation: OK")
    print("- socketed-equipment snapshot: OK")
    print("- release and orphan recovery: OK")
    print("- isolated DB; real user mutations: 0")
if __name__=="__main__": main()
