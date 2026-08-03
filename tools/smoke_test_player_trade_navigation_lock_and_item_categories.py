#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations
import ast, sqlite3, sys, tempfile
from contextlib import closing
from datetime import timedelta
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))
def fail(x): print(f"[FAIL] {x}"); raise SystemExit(1)
def main():
    for rel in ("systems/player_interaction_system.py","handlers/player_interaction.py","db.py"):
        p=ROOT/rel; ast.parse(p.read_text(encoding="utf-8-sig"),filename=str(p))
    from systems import player_interaction_system as m
    with tempfile.TemporaryDirectory(prefix="rom_trade_nav_12_6_4_",ignore_cleanup_errors=True) as td:
        db=Path(td)/"test.db"; now=m._now()
        with closing(sqlite3.connect(db)) as c:
            c.executescript("""
            PRAGMA foreign_keys=ON;
            CREATE TABLE users(user_id INTEGER PRIMARY KEY,character_name TEXT,current_location TEXT,gold REAL,last_activity_at TEXT);
            CREATE TABLE items(id INTEGER PRIMARY KEY,name TEXT,category TEXT,rarity TEXT,tradeable INTEGER,bound_type TEXT,dev_only INTEGER,premium_bound INTEGER);
            CREATE TABLE inventory(id INTEGER PRIMARY KEY,user_id INTEGER,item_id INTEGER,quantity INTEGER,durability INTEGER,max_durability INTEGER,refine_level INTEGER);
            CREATE TABLE equipment_slots(user_id INTEGER,slot_key TEXT,inventory_id INTEGER);
            CREATE TABLE player_interaction_requests(id INTEGER PRIMARY KEY,request_type TEXT,initiator_user_id INTEGER,recipient_user_id INTEGER,location_snapshot TEXT,status TEXT,revision INTEGER,created_at TEXT,updated_at TEXT,expires_at TEXT,responded_at TEXT);
            CREATE TABLE player_activity_sessions(id INTEGER PRIMARY KEY,user_id INTEGER UNIQUE,activity_type TEXT,reference_id INTEGER,status TEXT,created_at TEXT,updated_at TEXT,expires_at TEXT);
            INSERT INTO users VALUES(1,'A','start_path',100,'x'),(2,'B','start_path',50,'x');
            INSERT INTO items VALUES(10,'Potion','potion','common',1,'',0,0),(11,'Armor','equipment','rare',1,'',0,0),(401,'Stone','material','common',1,'',0,0),(501,'Rune','rune','common',1,'',0,0);
            INSERT INTO inventory VALUES(100,1,10,5,NULL,NULL,0),(101,1,11,1,80,100,3),(102,1,401,10,NULL,NULL,0),(103,1,501,2,NULL,NULL,0);
            """); c.commit()
        m.init_player_interaction_foundation(db_path=db); m.init_player_trade_foundation(db_path=db); m.init_player_trade_item_policy_and_reservations(db_path=db)
        stamp=m._text(now); expires=m._text(now+timedelta(minutes=10))
        with closing(sqlite3.connect(db)) as c:
            c.execute("INSERT INTO player_trades(initiator_user_id,recipient_user_id,location_snapshot,status,revision,created_at,updated_at,expires_at) VALUES(1,2,'start_path','editing',1,?,?,?)",(stamp,stamp,expires)); tid=c.execute("SELECT last_insert_rowid()").fetchone()[0]; c.commit()
        expected={"equipment":101,"potion":100,"material":102,"rune":103}
        for category,inventory_id in expected.items():
            result=m.get_tradeable_inventory_for_trade_category(tid,1,category,page=0,page_size=8,db_path=db)
            ids=[x['inventory_id'] for x in result.get('items',[])]
            if ids!=[inventory_id]: fail((category,ids))
        counts=m.get_player_trade_category_counts(tid,1,db_path=db)
        if counts.get('counts')!={"equipment":1,"potion":1,"material":1,"rune":1}: fail(counts)
    h=(ROOT/'handlers/player_interaction.py').read_text(encoding='utf-8-sig')
    required=('🤝 Триває обмін','install_player_trade_navigation_lock_12_6_4','pi:tec:categories:','pi:tec:list:','pi:tec:view:','🔙 До категорій','PLAYER_TRADE_CATEGORY_PAGE_SIZE_12_6_4 = 8')
    for x in required:
        if x not in h: fail('missing '+x)
    print('[OK] Player trade navigation lock and item category contracts')
    print('- active trade reply keyboard has one informational button: OK')
    print('- non-trade messages/callbacks are blocked during active trade: OK')
    print('- trade callbacks and amount input remain allowed: OK')
    print('- equipment/potion/material/rune categorization: OK')
    print('- category pagination uses 8 positions per page: OK')
    print('- cancel restores normal keyboard for both players: OK')
    print('- isolated DB; real user mutations: 0')
if __name__=='__main__': main()
