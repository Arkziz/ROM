# -*- coding: utf-8 -*-
import sqlite3,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))
from systems.event_statistics_system import record_event_mob_victory,get_event_kill_leaderboard
import importlib.util
spec=importlib.util.spec_from_file_location("migration",ROOT/"migrations"/"050_event_kill_statistics.py"); mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
c=sqlite3.connect(":memory:"); c.execute("PRAGMA foreign_keys=ON"); c.execute("CREATE TABLE users(user_id INTEGER PRIMARY KEY)"); c.executemany("INSERT INTO users VALUES(?)",[(1,),(2,),(3,)]); mod.up(c)
assert record_event_mob_victory(c,"test_event_2026",1,"test_slime","battle:a")["recorded"] is True
assert record_event_mob_victory(c,"test_event_2026",1,"test_slime","battle:a")["duplicate"] is True
assert record_event_mob_victory(c,"test_event_2026",1,"test_slime","battle:b")["kills"]==2
assert record_event_mob_victory(c,"test_event_2026",2,"test_slime","battle:c")["kills"]==1
board=get_event_kill_leaderboard(c,"test_event_2026","test_slime",user_id=2)
assert [x["user_id"] for x in board["entries"]]==[1,2] and board["own"]["rank"]==2
assert c.execute("SELECT COUNT(*) FROM event_kill_receipts").fetchone()[0]==3
print("EVENT_KILL_STATISTICS_18_29_3B_OK")
