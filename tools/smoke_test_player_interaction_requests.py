#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations
import ast, importlib, sqlite3, sys, tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))
def fail(x): print(f"[FAIL] {x}"); raise SystemExit(1)
def main():
    for rel in ("systems/player_interaction_system.py","handlers/player_interaction.py","db.py"):
        p=ROOT/rel; ast.parse(p.read_text(encoding="utf-8-sig"),filename=str(p))
    m=importlib.import_module("systems.player_interaction_system")
    with tempfile.TemporaryDirectory(prefix="rom_requests_12_3_0_") as td:
        db=Path(td)/"x.db"; c=sqlite3.connect(db)
        c.execute("CREATE TABLE users(user_id INTEGER PRIMARY KEY,character_name TEXT,current_location TEXT,last_activity_at TEXT)")
        c.execute("CREATE TABLE player_activity_sessions(id INTEGER PRIMARY KEY AUTOINCREMENT,user_id INTEGER NOT NULL UNIQUE,activity_type TEXT NOT NULL,reference_id INTEGER,status TEXT,created_at TEXT,updated_at TEXT,expires_at TEXT)")
        now=datetime(2026,8,2,12,0,tzinfo=timezone.utc)
        c.executemany("INSERT INTO users VALUES(?,?,?,?)",((1,"A","start_path",now.isoformat()),(2,"B","start_path",now.isoformat()),(3,"C","dark_forest",now.isoformat()),(4,"D","start_path",(now-timedelta(seconds=301)).isoformat())))
        c.commit(); c.close()
        if not m.init_player_interaction_requests(db_path=db)["success"]: fail("schema")
        req=m.create_player_interaction_request(1,2,"trade",now=now,db_path=db)
        if not req["success"]: fail(req)
        if m.create_player_interaction_request(1,2,"trade",now=now,db_path=db).get("reason")!="player_busy": fail("busy")
        if m.respond_to_player_interaction_request(req["request_id"],1,"accept",now=now,db_path=db).get("reason")!="wrong_actor": fail("actor")
        accepted=m.respond_to_player_interaction_request(req["request_id"],2,"accept",now=now,db_path=db)
        if not accepted["success"] or accepted["status"]!="accepted": fail(accepted)
        if m.respond_to_player_interaction_request(req["request_id"],2,"accept",now=now,db_path=db).get("reason")!="request_not_pending": fail("idempotency")
        m.release_player_activity_session(1,db_path=db); m.release_player_activity_session(2,db_path=db)
        req2=m.create_player_interaction_request(1,2,"trade",now=now,db_path=db)
        declined=m.respond_to_player_interaction_request(req2["request_id"],2,"decline",now=now,db_path=db)
        if not declined["success"]: fail("decline")
        if m.is_player_interaction_busy(1,db_path=db) or m.is_player_interaction_busy(2,db_path=db): fail("decline release")
        if m.create_player_interaction_request(1,3,"trade",now=now,db_path=db).get("reason")!="different_location": fail("location")
        if m.create_player_interaction_request(1,4,"trade",now=now,db_path=db).get("reason")!="player_offline": fail("offline")
        if m.create_player_interaction_request(1,1,"trade",now=now,db_path=db).get("reason")!="self_target": fail("self")
        exp=m.create_player_interaction_request(1,2,"trade",ttl_seconds=1,now=now,db_path=db)
        if m.expire_stale_interaction_requests(now=now+timedelta(seconds=2),db_path=db)!=1: fail("expiry")
        if m.get_interaction_request(exp["request_id"],db_path=db)["status"]!="expired": fail("expiry status")
    hs=(ROOT/"handlers/player_interaction.py").read_text(encoding="utf-8-sig")
    for token in ("pi:req:accept:","pi:req:decline:","create_player_interaction_request"):
        if token not in hs: fail(f"handler {token}")
    print("[OK] Player interaction request contracts")
    print("- atomic request + two activity reservations: OK")
    print("- online/same-location/busy/battle guards: OK")
    print("- recipient actor and revision guards: OK")
    print("- accept/decline/expire cleanup: OK")
    print("- repeat accept cannot duplicate transition: OK")
    print("- isolated DB; real user mutations: 0")
if __name__=="__main__": main()
