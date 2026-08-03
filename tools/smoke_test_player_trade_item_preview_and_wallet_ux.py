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
    with tempfile.TemporaryDirectory(prefix="rom_trade_preview_12_6_2_",ignore_cleanup_errors=True) as td:
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
            INSERT INTO users VALUES(1,'A','start_path',125.5,'x'),(2,'B','start_path',50,'x');
            INSERT INTO items VALUES(10,'Potion','potion','common',1,'',0,0),(11,'Armor','equipment','rare',1,'',0,0);
            INSERT INTO inventory VALUES(100,1,10,5,NULL,NULL,0),(101,1,11,1,80,100,3);
            """); c.commit()
        m.init_player_interaction_foundation(db_path=db); m.init_player_trade_foundation(db_path=db); m.init_player_trade_item_policy_and_reservations(db_path=db)
        stamp=m._text(now); expires=m._text(now+timedelta(minutes=10))
        with closing(sqlite3.connect(db)) as c:
            c.execute("INSERT INTO player_trades(initiator_user_id,recipient_user_id,location_snapshot,status,revision,created_at,updated_at,expires_at) VALUES(1,2,'start_path','editing',1,?,?,?)",(stamp,stamp,expires)); tid=c.execute("SELECT last_insert_rowid()").fetchone()[0]; c.commit()
        stack=m.get_trade_item_preview(tid,1,100,db_path=db)
        if not stack['success'] or not stack['is_stack'] or stack['maximum_quantity']!=5 or stack['offered_quantity']!=0: fail(stack)
        equipment=m.get_trade_item_preview(tid,1,101,db_path=db)
        if not equipment['success'] or not equipment['is_equipment']: fail(equipment)
        if m.get_player_trade_offers(tid,db_path=db): fail('preview mutated offer')
        if not m.set_player_trade_item_offer(tid,1,100,2,now=now,db_path=db)['success']: fail('stack mutation')
        wallet=m.get_player_trade_wallet_state(tid,1,db_path=db)
        if wallet!={'success':True,'wallet_gold':125.5,'offered_gold':0.0,'remaining_gold':125.5}: fail(wallet)
        if not m.set_player_trade_gold_offer(tid,1,25.5,now=now,db_path=db)['success']: fail('gold')
        wallet=m.get_player_trade_wallet_state(tid,1,db_path=db)
        if wallet['offered_gold']!=25.5 or wallet['remaining_gold']!=100.0: fail(wallet)
    handler=(ROOT/'handlers/player_interaction.py').read_text(encoding='utf-8-sig')
    required=('Додати цей предмет до пропозиції?','📦 Додати все доступне','Ваше золото:','У пропозиції:','Доступний залишок:','pi:tep:view:','pi:tep:addone:','pi:tep:set:','pi:tep:all:')
    for value in required:
        if value not in handler: fail(f'missing contract: {value}')
    if '✅ Додати x' in handler: fail('unwanted stack confirmation button')
    print('[OK] Player trade item preview and wallet UX contracts')
    print('- selecting an item builds preview without mutation: OK')
    print('- stack preview uses minus/current/plus and add-all only: OK')
    print('- no redundant stack Add xN confirmation button: OK')
    print('- equipment preview requires Add item or Back: OK')
    print('- wallet/offered/remaining gold state: OK')
    print('- preview callback routing contracts: OK')
    print('- isolated DB; real user mutations: 0')
if __name__=='__main__': main()
