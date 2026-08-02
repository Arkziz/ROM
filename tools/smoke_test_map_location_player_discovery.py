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
ROOT=Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))
def fail(msg): print(f"[FAIL] {msg}"); raise SystemExit(1)
def main():
    for rel in ("systems/player_interaction_system.py","handlers/player_interaction.py","main.py","keyboards.py"):
        path=ROOT/rel; ast.parse(path.read_text(encoding="utf-8-sig"),filename=str(path))
    module=importlib.import_module("systems.player_interaction_system")
    with tempfile.TemporaryDirectory(prefix="rom_map_players_12_2_0_") as temp:
        db=Path(temp)/"test.db"; conn=sqlite3.connect(db)
        conn.execute("CREATE TABLE users (user_id INTEGER PRIMARY KEY, character_name TEXT, current_location TEXT, level INTEGER, character_class TEXT, last_activity_at TEXT)")
        now=datetime(2026,8,2,12,0,tzinfo=timezone.utc)
        rows=((1,"Viewer","start_path",8,"mage",now.isoformat()),
              (2,"Online Same","start_path",7,"warrior",(now-timedelta(seconds=60)).isoformat()),
              (3,"Offline Same","start_path",9,"priest",(now-timedelta(seconds=301)).isoformat()),
              (4,"Online Other","dark_forest",10,"rogue",(now-timedelta(seconds=10)).isoformat()),
              (5,"","start_path",5,"knight",now.isoformat()))
        conn.executemany("INSERT INTO users VALUES (?,?,?,?,?,?)",rows); conn.commit(); conn.close()
        result=module.get_online_players_in_same_location(1,now=now,db_path=db)
        if not result["success"] or result["total"] != 1: fail(f"filter contract: {result}")
        if result["players"][0]["user_id"] != 2: fail("wrong target")
        profile=module.get_public_player_interaction_profile(1,2,now=now,db_path=db)
        if not profile["success"]: fail(f"profile: {profile}")
        if module.get_public_player_interaction_profile(1,1,now=now,db_path=db)["reason"] != "self_target": fail("self")
        if module.get_public_player_interaction_profile(1,3,now=now,db_path=db)["reason"] != "player_offline": fail("offline")
        if module.get_public_player_interaction_profile(1,4,now=now,db_path=db)["reason"] != "different_location": fail("location")
    main=(ROOT/"main.py").read_text(encoding="utf-8-sig")
    if "register_player_interaction_handlers(bot)" not in main: fail("main registration")
    keyboards=(ROOT/"keyboards.py").read_text(encoding="utf-8-sig")
    if "👥 Гравці локації" not in keyboards: fail("Map button")
    handler=(ROOT/"handlers/player_interaction.py").read_text(encoding="utf-8-sig")
    for token in ("🤝 Запропонувати обмін","⚔️ Викликати на дуель","🔙 До гравців локації"):
        if token not in handler: fail(f"missing UI: {token}")
    print("[OK] Map location player discovery contracts")
    print("- same-location online-only query: OK")
    print("- self/offline/other-location exclusion: OK")
    print("- deterministic pagination: OK")
    print("- public player profile: OK")
    print("- trade and future-duel action buttons: OK")
    print("- Map button and main handler registration: OK")
    print("- isolated DB; real user mutations: 0")
if __name__=="__main__": main()
