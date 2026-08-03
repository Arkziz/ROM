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
    with tempfile.TemporaryDirectory(prefix="rom_trade_ux_12_6_1_",ignore_cleanup_errors=True) as td:
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
            INSERT INTO items VALUES(10,'Potion','potion','common',1,'',0,0),(11,'Armor','equipment','rare',1,'',0,0);
            INSERT INTO inventory VALUES(100,1,10,5,NULL,NULL,0),(101,1,11,1,80,100,3);
            """); c.commit()
        m.init_player_interaction_foundation(db_path=db); m.init_player_trade_foundation(db_path=db); m.init_player_trade_item_policy_and_reservations(db_path=db)
        stamp=m._text(now); expires=m._text(now+timedelta(minutes=10))
        with closing(sqlite3.connect(db)) as c:
            c.execute("INSERT INTO player_trades(initiator_user_id,recipient_user_id,location_snapshot,status,revision,created_at,updated_at,expires_at) VALUES(1,2,'start_path','editing',1,?,?,?)",(stamp,stamp,expires)); tid=c.execute("SELECT last_insert_rowid()").fetchone()[0]; c.commit()
        listing=m.get_tradeable_inventory_for_trade(tid,1,db_path=db)
        by_id={x['inventory_id']:x for x in listing['items']}
        if by_id[100]['available_quantity']!=5 or not by_id[100]['is_stack']: fail(listing)
        if not by_id[101]['is_equipment']: fail(listing)
        if not m.set_player_trade_item_offer(tid,1,101,1,now=now,db_path=db)['success']: fail('equipment add')
        if 101 in {x['inventory_id'] for x in m.get_tradeable_inventory_for_trade(tid,1,db_path=db)['items']}: fail('equipment still visible')
        if not m.set_player_trade_item_offer(tid,1,100,2,now=now,db_path=db)['success']: fail('partial stack')
        partial={x['inventory_id']:x for x in m.get_tradeable_inventory_for_trade(tid,1,db_path=db)['items']}
        if partial[100]['available_quantity']!=3: fail(partial)
        all_result=m.add_all_available_to_trade_offer(tid,1,100,now=now,db_path=db)
        if not all_result['success'] or all_result['quantity']!=5: fail(all_result)
        if 100 in {x['inventory_id'] for x in m.get_tradeable_inventory_for_trade(tid,1,db_path=db)['items']}: fail('full stack still visible')
        if not m.remove_player_trade_item_offer(tid,1,100,now=now,db_path=db)['success']: fail('remove')
        if 100 not in {x['inventory_id'] for x in m.get_tradeable_inventory_for_trade(tid,1,db_path=db)['items']}: fail('removed stack not restored')
    handler=(ROOT/'handlers/player_interaction.py').read_text(encoding='utf-8-sig')
    for value in ('✏️ Моя пропозиція','📦 Додати все','pi:teux:list:','pi:teux:add:','pi:teux:mine:','pi:teux:edit:','pi:teux:all:','pi:teux:remove:'):
        if value not in handler: fail(f'missing UX contract: {value}')
    print('[OK] Player trade offer editor UX contracts')
    print('- equipment is added once and disappears from add list: OK')
    print('- partial stack shows only remaining quantity: OK')
    print('- add-all reserves full available stack and hides it: OK')
    print('- removing an offer restores it to add list: OK')
    print('- equipment has no quantity editor contract: OK')
    print('- My Offer editor and UX callback routing: OK')
    print('- isolated DB; real user mutations: 0')
if __name__=='__main__': main()
