# -*- coding: utf-8 -*-
import sqlite3,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from events.test_event_2026.items import get_item_definitions
items={int(x["id"]):x for x in get_item_definitions()}
assert items[4000]["category"]=="material"
assert items[4001]["category"]=="material"
assert items[4001]["type"]=="test_event_reward"
assert items[4001]["tradeable"] is False
assert items[4001]["sellable"] is False
assert items[4001]["auctionable"] is False
conn=sqlite3.connect(f"file:{(ROOT/'game.db').as_posix()}?mode=ro",uri=True)
try:
 row=conn.execute("SELECT name,type,category,max_stack FROM items WHERE id=4001").fetchone()
finally:conn.close()
assert row==("🎁 Пам’ятний знак випробування","test_event_reward","material",10),row
print("TEST_EVENT_REWARD_MATERIAL_18_29_4P_OK")
