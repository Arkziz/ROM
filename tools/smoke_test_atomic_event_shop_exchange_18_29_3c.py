# -*- coding: utf-8 -*-
import importlib.util,sqlite3,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))
from systems.event_shop_system import exchange_event_shop_offer
spec=importlib.util.spec_from_file_location("m",ROOT/"migrations"/"051_event_shop_exchange.py"); m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
c=sqlite3.connect(":memory:"); c.execute("PRAGMA foreign_keys=ON"); c.executescript("CREATE TABLE users(user_id INTEGER PRIMARY KEY,bag_slots INTEGER);CREATE TABLE items(id INTEGER PRIMARY KEY,max_stack INTEGER);CREATE TABLE inventory(id INTEGER PRIMARY KEY AUTOINCREMENT,user_id INTEGER,item_id INTEGER,quantity INTEGER,durability INTEGER);")
c.execute("INSERT INTO users VALUES(1,2)"); c.executemany("INSERT INTO items VALUES(?,?)",[(4000,999),(4001,10)]); c.execute("INSERT INTO inventory(user_id,item_id,quantity) VALUES(1,4000,6)"); m.up(c)
import events.test_event_2026.config as cfg; cfg.ENABLED=True
r=exchange_event_shop_offer(c,"test_event_2026",1,"test_reward_exchange","idem:1",event_active=True); assert r["success"] and not r["duplicate"]
r2=exchange_event_shop_offer(c,"test_event_2026",1,"test_reward_exchange","idem:1",event_active=True); assert r2["duplicate"]
assert c.execute("SELECT SUM(quantity) FROM inventory WHERE user_id=1 AND item_id=4000").fetchone()[0]==3
assert c.execute("SELECT SUM(quantity) FROM inventory WHERE user_id=1 AND item_id=4001").fetchone()[0]==1
assert c.execute("SELECT COUNT(*) FROM event_shop_transactions").fetchone()[0]==1
cfg.ENABLED=False; assert exchange_event_shop_offer(c,"test_event_2026",1,"test_reward_exchange","idem:2",event_active=True)["reason"]=="event_inactive"
print("ATOMIC_EVENT_SHOP_EXCHANGE_18_29_3C_OK")
