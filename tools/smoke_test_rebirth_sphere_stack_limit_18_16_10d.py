#!/usr/bin/env python3
import importlib.util,sqlite3,tempfile
from pathlib import Path
R=Path(__file__).resolve().parents[1]
s=importlib.util.spec_from_file_location("m048",R/"migrations/048_rebirth_sphere_stack_limit.py");m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
with tempfile.TemporaryDirectory() as d:
 c=sqlite3.connect(str(Path(d)/"t.db"));c.executescript("""CREATE TABLE items(id INTEGER PRIMARY KEY,name TEXT,max_stack INTEGER);CREATE TABLE inventory(id INTEGER PRIMARY KEY AUTOINCREMENT,user_id INTEGER,item_id INTEGER,quantity INTEGER);INSERT INTO items VALUES(504,'Sphere',99);INSERT INTO inventory(user_id,item_id,quantity) VALUES(1,504,23);INSERT INTO inventory(user_id,item_id,quantity) VALUES(2,504,2);""");r=m.up(c);c.commit();assert c.execute("SELECT max_stack FROM items WHERE id=504").fetchone()[0]==10;assert [x[0] for x in c.execute("SELECT quantity FROM inventory WHERE user_id=1 ORDER BY id")]==[10,10,3];assert [x[0] for x in c.execute("SELECT quantity FROM inventory WHERE user_id=2 ORDER BY id")]==[2];before=list(c.execute("SELECT user_id,quantity FROM inventory ORDER BY user_id,id"));m.up(c);c.commit();after=list(c.execute("SELECT user_id,quantity FROM inventory ORDER BY user_id,id"));assert before==after;c.close()
print("[PASS] Stage 18.16.10d Rebirth Sphere stack limit contract")
