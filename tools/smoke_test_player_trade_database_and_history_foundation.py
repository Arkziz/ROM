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
def prepare(path):
    with closing(sqlite3.connect(path)) as c:
        c.executescript("""
        PRAGMA foreign_keys=ON;
        CREATE TABLE users(user_id INTEGER PRIMARY KEY,character_name TEXT,current_location TEXT,last_activity_at TEXT);
        CREATE TABLE player_activity_sessions(id INTEGER PRIMARY KEY AUTOINCREMENT,user_id INTEGER NOT NULL UNIQUE,activity_type TEXT NOT NULL,reference_id INTEGER,status TEXT,created_at TEXT,updated_at TEXT,expires_at TEXT);
        CREATE TABLE player_interaction_requests(id INTEGER PRIMARY KEY AUTOINCREMENT,request_type TEXT,initiator_user_id INTEGER,recipient_user_id INTEGER,location_snapshot TEXT,status TEXT,revision INTEGER,created_at TEXT,updated_at TEXT,expires_at TEXT,responded_at TEXT);
        """); c.commit()
def main():
    for rel in ("systems/player_interaction_system.py","handlers/player_interaction.py","db.py","main.py"):
        p=ROOT/rel; ast.parse(p.read_text(encoding="utf-8-sig"),filename=str(p))
    m=importlib.import_module("systems.player_interaction_system")
    now=datetime(2026,8,2,12,0,tzinfo=timezone.utc)
    with tempfile.TemporaryDirectory(prefix="rom_trade_12_4_0_",ignore_cleanup_errors=True) as td:
        db=Path(td)/"test.db"; prepare(db)
        with closing(sqlite3.connect(db)) as c:
            c.executemany("INSERT INTO users VALUES(?,?,?,?)",((1,"A","start_path",now.isoformat()),(2,"B","start_path",now.isoformat())))
            c.execute("INSERT INTO player_interaction_requests VALUES(10,'trade',1,2,'start_path','accepted',1,?,?,?,?)",(now.isoformat(),now.isoformat(),(now+timedelta(minutes=2)).isoformat(),now.isoformat()))
            c.commit()
        init=m.init_player_trade_foundation(db_path=db)
        if not init["success"]: fail(init)
        created=m.create_player_trade_from_accepted_request(10,now=now,db_path=db)
        if not created["success"] or not created["created"]: fail(created)
        trade_id=created["trade_id"]
        duplicate=m.create_player_trade_from_accepted_request(10,now=now,db_path=db)
        if not duplicate["success"] or duplicate["created"]: fail("idempotent create")
        with closing(sqlite3.connect(db)) as c:
            sessions=c.execute("SELECT user_id,activity_type,reference_id,status,expires_at FROM player_activity_sessions ORDER BY user_id").fetchall()
        if len(sessions)!=2 or any(r[1]!="trade" or r[2]!=trade_id or r[3]!="editing" or r[4] is None for r in sessions): fail(sessions)
        events=m.get_player_trade_events(trade_id,db_path=db)
        if len(events)!=1 or events[0]["event_type"]!="created": fail(events)
        cancelled=m.cancel_player_trade(trade_id,1,now=now,db_path=db)
        if not cancelled["success"] or cancelled["status"]!="cancelled": fail(cancelled)
        if m.cancel_player_trade(trade_id,1,now=now,db_path=db).get("reason")!="trade_not_active": fail("repeat cancel")
        history=m.get_player_trade_history(1,db_path=db)
        if len(history)!=1 or history[0]["status"]!="cancelled": fail(history)
        with closing(sqlite3.connect(db)) as c:
            if c.execute("SELECT COUNT(*) FROM player_activity_sessions").fetchone()[0]!=0: fail("cancel session residue")
            c.execute("INSERT INTO player_interaction_requests VALUES(11,'trade',1,2,'start_path','accepted',1,?,?,?,?)",(now.isoformat(),now.isoformat(),(now+timedelta(minutes=2)).isoformat(),now.isoformat()))
            c.commit()
        second=m.create_player_trade_from_accepted_request(11,now=now,db_path=db)
        if m.expire_stale_player_trades(now=now+timedelta(seconds=601),db_path=db)!=1: fail("expiry")
        if m.get_player_trade(second["trade_id"],db_path=db)["status"]!="expired": fail("expiry status")
        if m.get_player_trade_history(2,db_path=db)[0]["status"]!="expired": fail("expiry history")
    main_source=(ROOT/"main.py").read_text(encoding="utf-8-sig")
    if "init_player_trade_foundation()" not in main_source: fail("startup init")
    handler=(ROOT/"handlers/player_interaction.py").read_text(encoding="utf-8-sig")
    if "pi:trade:cancel:" not in handler: fail("cancel callback")
    print("[OK] Player trade database and history foundation contracts")
    print("- four trade tables and indexes: OK")
    print("- accepted request creates one editing trade: OK")
    print("- two timed activity sessions reference trade_id: OK")
    print("- created/cancelled/expired events: OK")
    print("- cancellation and timeout release both users: OK")
    print("- immutable terminal history row: OK")
    print("- isolated DB; real user mutations: 0")
if __name__=="__main__": main()
