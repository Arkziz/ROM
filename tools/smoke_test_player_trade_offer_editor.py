#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ROM 12.6.0 isolated runtime and integration contracts."""
from __future__ import annotations
import ast, sqlite3, sys, tempfile
from contextlib import closing
from datetime import timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

def fail(message):
    print(f"[FAIL] {message}")
    raise SystemExit(1)

def main():
    for rel in ("systems/player_interaction_system.py", "handlers/player_interaction.py", "db.py"):
        path = ROOT / rel
        ast.parse(path.read_text(encoding="utf-8-sig"), filename=str(path))
    from systems import player_interaction_system as m
    with tempfile.TemporaryDirectory(prefix="rom_trade_editor_12_6_0_", ignore_cleanup_errors=True) as td:
        db = Path(td) / "test.db"
        now = m._now()
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
            INSERT INTO items VALUES(10,'Potion','potion','common',1,'',0,0),(11,'Sword','equipment','rare',1,'',0,0),(301,'Sphere','material','common',0,'',0,0);
            INSERT INTO inventory VALUES(100,1,10,5,NULL,NULL,0),(101,1,11,1,80,100,3),(102,1,301,1,NULL,NULL,0);
            """)
            c.commit()
        m.init_player_interaction_foundation(db_path=db)
        m.init_player_trade_foundation(db_path=db)
        m.init_player_trade_item_policy_and_reservations(db_path=db)
        stamp=m._text(now); expires=m._text(now+timedelta(minutes=10))
        with closing(sqlite3.connect(db)) as c:
            c.execute("INSERT INTO player_trades(initiator_user_id,recipient_user_id,location_snapshot,status,revision,created_at,updated_at,expires_at) VALUES(1,2,'start_path','editing',1,?,?,?)",(stamp,stamp,expires))
            trade_id=c.execute("SELECT last_insert_rowid()").fetchone()[0]; c.commit()
        first=m.set_player_trade_item_offer(trade_id,1,100,1,now=now,db_path=db)
        if not first.get('success') or first.get('revision') != 2: fail(first)
        changed=m.set_player_trade_item_offer(trade_id,1,100,3,now=now,db_path=db)
        if not changed.get('success') or changed.get('revision') != 3: fail(changed)
        if m.get_inventory_reserved_quantity(100,db_path=db) != 3: fail('reservation quantity')
        equipment=m.set_player_trade_item_offer(trade_id,1,101,1,now=now,db_path=db)
        if not equipment.get('success'): fail(equipment)
        blocked=m.set_player_trade_item_offer(trade_id,1,102,1,now=now,db_path=db)
        if blocked.get('success') or blocked.get('reason') != 'protected_item': fail(blocked)
        gold=m.set_player_trade_gold_offer(trade_id,1,25,now=now,db_path=db)
        if not gold.get('success') or gold.get('gold_amount') != 25: fail(gold)
        overflow=m.set_player_trade_gold_offer(trade_id,1,101,now=now,db_path=db)
        if overflow.get('success') or overflow.get('reason') != 'insufficient_gold': fail(overflow)
        state=m.get_player_trade_editor_state(trade_id,1,now=now,db_path=db)
        if not state.get('success') or len(state.get('own_offers',[])) != 3: fail(state)
        removed=m.remove_player_trade_item_offer(trade_id,1,100,now=now,db_path=db)
        if not removed.get('success') or m.get_inventory_reserved_quantity(100,db_path=db) != 0: fail(removed)
        cancelled=m.cancel_player_trade(trade_id,1,now=now,db_path=db)
        if not cancelled.get('success'): fail(cancelled)
        with closing(sqlite3.connect(db)) as c:
            residue=c.execute("SELECT COUNT(*) FROM inventory_reservations").fetchone()[0]
            if residue != 0: fail(f'reservation residue: {residue}')
    handler=(ROOT/'handlers/player_interaction.py').read_text(encoding='utf-8-sig')
    for callback in ('pi:te:open:','pi:te:list:','pi:te:item:','pi:te:set:','pi:te:remove:','pi:te:gold:','pi:te:gold0:'):
        if callback not in handler: fail(f'missing callback {callback}')
    print('[OK] Player trade offer editor contracts')
    print('- item add/update/remove and quantity reservations: OK')
    print('- equipment and protected-item policy integration: OK')
    print('- gold offer and wallet limit: OK')
    print('- revision increment and editor state: OK')
    print('- cancel releases all reservations: OK')
    print('- Telegram callback routing contracts: OK')
    print('- isolated DB; real user mutations: 0')
if __name__ == '__main__': main()
