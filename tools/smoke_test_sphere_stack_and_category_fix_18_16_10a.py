#!/usr/bin/env python3
import ast,sqlite3,tempfile,importlib.util,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1]
source=(R/"handlers/inventory.py").read_text(encoding="utf-8-sig");ast.parse(source)
assert "ROM Stage 18.16.10a sphere category exclusivity" in source
assert 'key == "potion"' in source and "not in (501, 504)" in source
assert 'key == "consumable"' in source
spec=importlib.util.spec_from_file_location("m047",R/"migrations/047_sphere_stack_and_category_fix.py");m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
with tempfile.TemporaryDirectory() as d:
 c=sqlite3.connect(str(Path(d)/"t.db"));c.executescript("""CREATE TABLE items(id INTEGER PRIMARY KEY,name TEXT,category TEXT,max_stack INTEGER);CREATE TABLE inventory(id INTEGER PRIMARY KEY,user_id INTEGER,item_id INTEGER,quantity INTEGER);INSERT INTO items VALUES(501,'New','potion',1);INSERT INTO items VALUES(504,'Rebirth','consumable',1);INSERT INTO inventory VALUES(1,7,504,1);INSERT INTO inventory VALUES(2,7,504,1);INSERT INTO inventory VALUES(3,8,504,2);""");result=m.up(c);c.commit();assert c.execute("SELECT category FROM items WHERE id=501").fetchone()[0]=="consumable";assert c.execute("SELECT max_stack FROM items WHERE id=504").fetchone()[0]==99;assert c.execute("SELECT COUNT(*),SUM(quantity) FROM inventory WHERE user_id=7 AND item_id=504").fetchone()==(1,2);assert result["removed_rows"]==1;c.close()
print("[PASS] Stage 18.16.10a sphere stack/category contract")
