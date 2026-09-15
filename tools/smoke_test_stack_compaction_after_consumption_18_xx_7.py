#!/usr/bin/env python3
import sqlite3,tempfile
from pathlib import Path
from db_modules.inventory import compact_user_item_stacks
with tempfile.TemporaryDirectory() as tmp:
 c=sqlite3.connect(Path(tmp)/"x.db")
 c.executescript("CREATE TABLE items(id INTEGER PRIMARY KEY,max_stack INTEGER);CREATE TABLE inventory(id INTEGER PRIMARY KEY,user_id INTEGER,item_id INTEGER,quantity INTEGER);CREATE TABLE inventory_reservations(id INTEGER PRIMARY KEY,inventory_id INTEGER,user_id INTEGER,quantity INTEGER);INSERT INTO items VALUES(601,50);INSERT INTO inventory VALUES(125,1,601,42);INSERT INTO inventory VALUES(140,1,601,6);")
 before=c.execute("SELECT SUM(quantity) FROM inventory").fetchone()[0];r=compact_user_item_stacks(1,601,connection=c);after=c.execute("SELECT SUM(quantity) FROM inventory").fetchone()[0]
 assert before==after==48 and r["freed_rows"]==1
 assert c.execute("SELECT id,quantity FROM inventory").fetchall()==[(125,48)]
 assert compact_user_item_stacks(1,601,connection=c)["changed"] is False
 c.execute("DELETE FROM inventory");c.execute("INSERT INTO inventory VALUES(1,1,601,47)");c.execute("INSERT INTO inventory VALUES(2,1,601,2)");c.execute("INSERT INTO inventory_reservations VALUES(1,2,1,1)")
 compact_user_item_stacks(1,601,connection=c)
 assert c.execute("SELECT quantity FROM inventory WHERE id=2").fetchone()[0]==2
 c.commit()
 c.close()
print("STACK_COMPACTION_AFTER_CONSUMPTION_18_XX_7_OK")
