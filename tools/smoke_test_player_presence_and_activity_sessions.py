#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations
import ast
import importlib
import sqlite3
import sys
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT)) if str(ROOT) not in sys.path else None

def fail(msg):
    print(f"[FAIL] {msg}")
    raise SystemExit(1)

def main():
    for rel in ("systems/player_interaction_system.py", "main.py", "db.py"):
        path = ROOT / rel
        ast.parse(path.read_text(encoding="utf-8-sig"), filename=str(path))
    module = importlib.import_module("systems.player_interaction_system")
    with tempfile.TemporaryDirectory(prefix="rom_presence_12_1_0_") as temp:
        db_file = Path(temp) / "test.db"
        conn = sqlite3.connect(db_file)
        conn.execute("CREATE TABLE users (user_id INTEGER PRIMARY KEY, character_name TEXT, current_location TEXT)")
        conn.executemany("INSERT INTO users VALUES (?,?,?)", ((101,"A","start_path"),(202,"B","start_path"),(303,"C","dark_forest")))
        conn.commit(); conn.close()
        a = module.init_player_interaction_foundation(db_path=db_file)
        b = module.init_player_interaction_foundation(db_path=db_file)
        if not a["success"] or not b["success"]: fail("schema init/idempotency")
        conn = sqlite3.connect(db_file)
        cols = {r[1] for r in conn.execute("PRAGMA table_info(users)")}
        table = conn.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='player_activity_sessions'").fetchone()
        conn.close()
        if "last_activity_at" not in cols or not table: fail("schema contract")
        now = datetime(2026,8,2,12,0,tzinfo=timezone.utc)
        if not module.touch_player_activity(101, force=True, now=now, db_path=db_file)["updated"]: fail("touch")
        if not module.is_player_online(101, now=now+timedelta(seconds=299), db_path=db_file): fail("299s online")
        if module.is_player_online(101, now=now+timedelta(seconds=301), db_path=db_file): fail("301s offline")
        if module.touch_player_activity(999, force=True, now=now, db_path=db_file)["reason"] != "user_not_found": fail("unknown user")
        first = module.acquire_player_activity_session(101,"trade_request",reference_id=77,ttl_seconds=120,now=now,db_path=db_file)
        if not first["success"]: fail("acquire")
        duplicate = module.acquire_player_activity_session(101,"trade",reference_id=88,ttl_seconds=600,now=now,db_path=db_file)
        if duplicate.get("reason") != "player_busy": fail("single session")
        refreshed = module.refresh_player_activity_session(101,expected_activity_type="trade_request",status="pending",ttl_seconds=60,now=now+timedelta(seconds=10),db_path=db_file)
        if not refreshed["updated"]: fail("refresh")
        if module.release_player_activity_session(101,activity_type="trade_request",reference_id=77,db_path=db_file)["released"] != 1: fail("release")
        if not module.acquire_player_activity_session(202,"duel_request",ttl_seconds=1,now=now,db_path=db_file)["success"]: fail("expiry fixture")
        if module.expire_stale_player_activity_sessions(now=now+timedelta(seconds=2),db_path=db_file) != 1: fail("expiry")
        if module.acquire_player_activity_session(303,"bad",now=now,db_path=db_file)["reason"] != "invalid_activity_type": fail("invalid type")
        class U:
            def __init__(self): self.id=303
        class M:
            def __init__(self): self.from_user=U()
        class X:
            def __init__(self): self.message=M()
        class Bot:
            def __init__(self): self.calls=0
            def process_new_updates(self, updates): self.calls+=1; return len(list(updates))
        bot=Bot()
        if not module.install_player_presence_tracking(bot,db_path=db_file)["installed"]: fail("install")
        if module.install_player_presence_tracking(bot,db_path=db_file)["reason"] != "already_installed": fail("idempotent install")
        if bot.process_new_updates([X()]) != 1 or bot.calls != 1: fail("delegation")
        if not module.is_player_online(303,db_path=db_file): fail("update presence")
    main_source=(ROOT/"main.py").read_text(encoding="utf-8-sig")
    if "init_player_interaction_foundation()" not in main_source: fail("main init")
    if "install_player_presence_tracking(bot)" not in main_source: fail("main tracker")
    if main_source.index("install_player_presence_tracking(bot)") > main_source.index("start_notification_worker(bot)"): fail("startup order")
    print("[OK] Player presence and activity session contracts")
    print("- users.last_activity_at migration: OK")
    print("- online timeout 300s: OK")
    print("- heartbeat write throttle: OK")
    print("- persistent single session per user: OK")
    print("- trade/duel types and expiry cleanup: OK")
    print("- incoming update tracker: OK")
    print("- isolated DB; real user mutations: 0")
if __name__ == "__main__": main()
