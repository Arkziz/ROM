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
    hp=ROOT/"handlers/player_interaction.py"; sp=ROOT/"systems/player_interaction_system.py"; mp=ROOT/"main.py"
    hs=hp.read_text(encoding="utf-8-sig"); ss=sp.read_text(encoding="utf-8-sig"); ms=mp.read_text(encoding="utf-8-sig")
    ht=ast.parse(hs,filename=str(hp)); ast.parse(ss,filename=str(sp)); ast.parse(ms,filename=str(mp))
    locks=[n for n in ht.body if isinstance(n,ast.FunctionDef) and n.name=="install_player_trade_navigation_lock_12_6_4"]
    if len(locks)!=1: fail(f"expected one canonical lock installer, found {len(locks)}")
    obsolete=[n.name for n in ht.body if isinstance(n,ast.FunctionDef) and (n.name.startswith("_trade_reopen_directly_") or n.name.startswith("_trade_status_button_stub_") or n.name.startswith("_trade_update_is_duplicate_") or n.name.startswith("_trade_reopen_allowed_"))]
    if obsolete: fail(f"obsolete lock helpers remain: {obsolete}")
    reopen_handlers=[n for n in ast.walk(ht) if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)) and n.name=="reopen_active_trade"]
    if reopen_handlers: fail("obsolete reopen_active_trade handler remains registered")
    lock_src=ast.get_source_segment(hs,locks[0]) or ""
    branches=[n for n in ast.walk(locks[0]) if isinstance(n,ast.If) and "PLAYER_TRADE_ACTIVE_REPLY_BUTTON_12_6_4" in (ast.get_source_segment(hs,n.test) or "")]
    if len(branches)!=1: fail("canonical no-op button branch missing")
    body=ast.Module(body=branches[0].body,type_ignores=[])
    if any(isinstance(n,ast.Call) for n in ast.walk(body)): fail("status no-op branch contains calls")
    if "_trade_lock_allowed_callback_12_6_4" not in lock_src: fail("callback whitelist missing")
    if "_trade_is_amount_input_active_12_6_4(user_id)" not in lock_src: fail("amount-input pass-through missing")
    amount_handlers=[n for n in ast.walk(ht) if isinstance(n,ast.FunctionDef) and n.name=="amount_message"]
    if not amount_handlers: fail("amount_message handler missing")
    amount_src=ast.get_source_segment(hs,amount_handlers[-1]) or ""
    if "Скасувати введення" not in amount_src: fail("amount-input cancel branch missing")
    if "player_trade_active_reply_kb_12_6_4" not in amount_src: fail("amount cancel does not restore trade keyboard")
    if "_send_trade_editor" not in amount_src: fail("amount cancel does not restore trade editor")
    for contract in ("recover_active_player_trades_after_restart","server_restart","_PLAYER_TRADE_RESTART_RECOVERY","participant_user_ids","_player_trade_recovery_main_kb"):
        if contract not in ss+ms: fail("missing startup contract: "+contract)
    from systems import player_interaction_system as m
    with tempfile.TemporaryDirectory(prefix="rom_trade_restart_12_6_5_",ignore_cleanup_errors=True) as td:
        db=Path(td)/"test.db"; now=m._now(); stamp=m._text(now); expires=m._text(now+timedelta(minutes=20))
        with closing(sqlite3.connect(db)) as c:
            c.executescript("""
            PRAGMA foreign_keys=ON;
            CREATE TABLE users(user_id INTEGER PRIMARY KEY,character_name TEXT,current_location TEXT,gold REAL,last_activity_at TEXT);
            CREATE TABLE inventory(id INTEGER PRIMARY KEY,user_id INTEGER,item_id INTEGER,quantity INTEGER);
            CREATE TABLE player_interaction_requests(id INTEGER PRIMARY KEY,request_type TEXT,initiator_user_id INTEGER,recipient_user_id INTEGER,location_snapshot TEXT,status TEXT,revision INTEGER,created_at TEXT,updated_at TEXT,expires_at TEXT,responded_at TEXT);
            CREATE TABLE player_activity_sessions(id INTEGER PRIMARY KEY,user_id INTEGER UNIQUE,activity_type TEXT,reference_id INTEGER,status TEXT,created_at TEXT,updated_at TEXT,expires_at TEXT);
            INSERT INTO users VALUES(1,'A','start_path',0,'x'),(2,'B','start_path',0,'x');
            """); c.commit()
        m.init_player_interaction_foundation(db_path=db); m.init_player_trade_foundation(db_path=db); m.init_player_trade_item_policy_and_reservations(db_path=db)
        with closing(sqlite3.connect(db)) as c:
            c.execute("INSERT INTO player_trades(initiator_user_id,recipient_user_id,location_snapshot,status,revision,created_at,updated_at,expires_at) VALUES(1,2,'start_path','editing',3,?,?,?)",(stamp,stamp,expires)); tid=c.execute("SELECT last_insert_rowid()").fetchone()[0]
            c.executemany("INSERT INTO player_activity_sessions(user_id,activity_type,reference_id,status,created_at,updated_at,expires_at) VALUES(?,'trade',?,'editing',?,?,?)",((1,tid,stamp,stamp,expires),(2,tid,stamp,stamp,expires))); c.commit()
        result=m.recover_active_player_trades_after_restart(now=now,db_path=db)
        if result.get("cancelled_trades")!=1 or result.get("participant_user_ids")!=[1,2]: fail(result)
        with closing(sqlite3.connect(db)) as c:
            status=c.execute("SELECT status,cancel_reason FROM player_trades WHERE id=?",(tid,)).fetchone(); sessions=c.execute("SELECT COUNT(*) FROM player_activity_sessions WHERE reference_id=?",(tid,)).fetchone()[0]
        if status!=("cancelled","server_restart") or sessions!=0: fail((status,sessions))
    print("[OK] Player trade lock consolidation and startup recovery contracts")
    print("- exactly one canonical navigation lock: OK")
    print("- obsolete reopen/status/dedupe helpers removed: OK")
    print("- obsolete persistent-button message handler removed: OK")
    print("- status button is a strict no-op: OK")
    print("- amount-input cancel recovery remains covered: OK")
    print("- restart cancels active trades and releases sessions: OK")
    print("- startup restores normal keyboards for both participants: OK")
    print("- isolated DB; real user mutations: 0")
if __name__=="__main__": main()
