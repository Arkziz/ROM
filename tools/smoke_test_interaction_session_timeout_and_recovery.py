#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations
import ast, importlib, sqlite3, sys, tempfile
from contextlib import closing
from datetime import datetime, timedelta, timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))
def fail(msg): print(f"[FAIL] {msg}"); raise SystemExit(1)
def prepare(path):
    c=sqlite3.connect(path)
    c.executescript("""
      PRAGMA foreign_keys=ON;
      CREATE TABLE users(user_id INTEGER PRIMARY KEY,character_name TEXT,current_location TEXT,last_activity_at TEXT);
      CREATE TABLE player_activity_sessions(
        id INTEGER PRIMARY KEY AUTOINCREMENT,user_id INTEGER NOT NULL UNIQUE,
        activity_type TEXT NOT NULL,reference_id INTEGER,status TEXT,
        created_at TEXT,updated_at TEXT,expires_at TEXT);
      CREATE TABLE player_interaction_requests(
        id INTEGER PRIMARY KEY AUTOINCREMENT,request_type TEXT,initiator_user_id INTEGER,
        recipient_user_id INTEGER,location_snapshot TEXT,status TEXT,revision INTEGER,
        created_at TEXT,updated_at TEXT,expires_at TEXT,responded_at TEXT);
    """)
    c.commit(); c.close()
def main():
    path=ROOT/"systems/player_interaction_system.py"
    source=path.read_text(encoding="utf-8-sig"); ast.parse(source,filename=str(path))
    if "recover_orphan_player_activity_sessions" not in source: fail("recovery API missing")
    module=importlib.import_module("systems.player_interaction_system")
    now=datetime(2026,8,2,12,0,tzinfo=timezone.utc)
    with tempfile.TemporaryDirectory(prefix="rom_recovery_12_3_2_") as td:
        db=Path(td)/"test.db"; prepare(db)
        with closing(sqlite3.connect(db)) as c:
            c.executemany("INSERT INTO users VALUES(?,?,?,?)",((1,"A","start_path",now.isoformat()),(2,"B","start_path",now.isoformat()),(3,"C","start_path",now.isoformat())))
            c.execute(
                "INSERT INTO player_interaction_requests "
                "(id,request_type,initiator_user_id,recipient_user_id,location_snapshot,status,revision,created_at,updated_at,expires_at,responded_at) "
                "VALUES(10,'trade',1,2,'start_path','accepted',1,?,?,?,?)",
                (now.isoformat(),now.isoformat(),(now+timedelta(minutes=2)).isoformat(),now.isoformat()),
            )
            c.execute("INSERT INTO player_activity_sessions(user_id,activity_type,reference_id,status,created_at,updated_at,expires_at) VALUES(1,'trade',10,'active',?,?,NULL)",(now.isoformat(),now.isoformat()))
            c.execute("INSERT INTO player_activity_sessions(user_id,activity_type,reference_id,status,created_at,updated_at,expires_at) VALUES(2,'trade',10,'active',?,?,NULL)",(now.isoformat(),now.isoformat()))
            c.execute("INSERT INTO player_activity_sessions(user_id,activity_type,reference_id,status,created_at,updated_at,expires_at) VALUES(3,'trade_request',999,'pending',?,?,?)",(now.isoformat(),now.isoformat(),(now+timedelta(minutes=2)).isoformat()))
            c.commit()
        with closing(sqlite3.connect(db)) as c:
            fixture_count=c.execute("SELECT COUNT(*) FROM player_activity_sessions").fetchone()[0]
        if fixture_count != 3: fail(f"fixture persistence: {fixture_count}")
        recovered=module.recover_orphan_player_activity_sessions(now=now,db_path=db)
        if recovered["accepted_placeholder_trade_sessions"] != 2: fail(recovered)
        if recovered["orphan_request_sessions"] != 1: fail(recovered)
        with closing(sqlite3.connect(db)) as c:
            count=c.execute("SELECT COUNT(*) FROM player_activity_sessions").fetchone()[0]
        if count != 0: fail(f"session residue: {count}")

        # Accepted request must release both players while no editor/player_trades exists.
        with closing(sqlite3.connect(db)) as c:
            c.execute("UPDATE player_interaction_requests SET status='pending',responded_at=NULL WHERE id=10")
            c.executemany("INSERT INTO player_activity_sessions(user_id,activity_type,reference_id,status,created_at,updated_at,expires_at) VALUES(?,'trade_request',10,'pending',?,?,?)",((1,now.isoformat(),now.isoformat(),(now+timedelta(minutes=2)).isoformat()),(2,now.isoformat(),now.isoformat(),(now+timedelta(minutes=2)).isoformat())))
            c.commit()
        result=module.respond_to_player_interaction_request(10,2,"accept",expected_revision=1,now=now,db_path=db)
        if not result["success"] or result["status"]!="accepted": fail(result)
        trade = result.get("trade") or {}
        trade_id = trade.get("trade_id") or (trade.get("trade") or {}).get("id")
        if not trade_id: fail(f"accepted trade missing: {result}")
        with closing(sqlite3.connect(db)) as c:
            sessions=c.execute(
                "SELECT user_id,activity_type,reference_id,status,expires_at "
                "FROM player_activity_sessions ORDER BY user_id"
            ).fetchall()
            status=c.execute("SELECT status FROM player_interaction_requests WHERE id=10").fetchone()[0]
        if len(sessions) != 2 or status != "accepted": fail(f"accepted trade sessions: {sessions}, status={status}")
        if any(row[1] != "trade" or row[2] != trade_id or row[3] != "editing" or row[4] is None for row in sessions):
            fail(f"accepted trade session contract: {sessions}")
        cancelled=module.cancel_player_trade(trade_id,1,now=now,db_path=db)
        if not cancelled.get("success"): fail(f"trade cleanup cancel: {cancelled}")
        with closing(sqlite3.connect(db)) as c:
            if c.execute("SELECT COUNT(*) FROM player_activity_sessions").fetchone()[0] != 0:
                fail("trade cleanup session residue")

        # Cleanup before create must remove stale placeholders and allow a fresh request.
        with closing(sqlite3.connect(db)) as c:
            c.execute("INSERT INTO player_activity_sessions(user_id,activity_type,reference_id,status,created_at,updated_at,expires_at) VALUES(1,'trade',10,'active',?,?,NULL)",(now.isoformat(),now.isoformat()))
            c.execute("UPDATE player_interaction_requests SET status='accepted' WHERE id=10")
            c.commit()
        fresh=module.create_player_interaction_request(1,2,"trade",now=now,db_path=db)
        if not fresh["success"]: fail(fresh)
        # Confirm that Windows can obtain an exclusive DB lock before temp cleanup.
        with closing(sqlite3.connect(db, timeout=1.0)) as c:
            c.execute("BEGIN EXCLUSIVE")
            c.rollback()
    main_source=(ROOT/"main.py").read_text(encoding="utf-8-sig")
    if "cleanup_player_interaction_state()" not in main_source: fail("startup cleanup missing")
    print("[OK] Interaction session timeout and recovery contracts")
    print("- accepted pre-editor trade sessions released: OK")
    print("- expired/orphan request sessions cleaned: OK")
    print("- cleanup runs before busy checks: OK")
    print("- accepted request stays auditable without blocking users: OK")
    print("- startup recovery registered: OK")
    print("- isolated DB; real user mutations: 0")
if __name__=="__main__": main()
