#!/usr/bin/env python3
import ast, sqlite3
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; tree=ast.parse((ROOT/"db_modules/inventory.py").read_text(encoding="utf-8-sig"))
funcs=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in {"consume_inventory_item","consume_user_item_by_item_id"}]

def namespace(connection, fail_compact=False):
 def count_user_item(user_id,item_id): return connection.execute("SELECT COALESCE(SUM(quantity),0) FROM inventory WHERE user_id=? AND item_id=?",(user_id,item_id)).fetchone()[0]
 def compact(*args,**kwargs):
  if fail_compact: raise RuntimeError("injected compact failure")
 ns={"conn":connection,"cursor":connection.cursor(),"count_user_item":count_user_item,"compact_user_item_stacks":compact}
 exec(compile(ast.fix_missing_locations(ast.Module(body=funcs,type_ignores=[])),"inventory.py","exec"),ns); return ns

def seeded():
 c=sqlite3.connect(":memory:"); c.execute("CREATE TABLE inventory(id INTEGER PRIMARY KEY,user_id INTEGER,item_id INTEGER,quantity INTEGER)"); c.executemany("INSERT INTO inventory VALUES(?,?,?,?)",[(1,7,100,5),(2,7,100,4)]); c.commit(); return c
c=seeded(); ns=namespace(c); assert ns["consume_inventory_item"](7,1,2) is True; assert c.execute("SELECT quantity FROM inventory WHERE id=1").fetchone()[0]==3
c=seeded(); before=c.execute("SELECT * FROM inventory ORDER BY id").fetchall(); ns=namespace(c,True)
try: ns["consume_inventory_item"](7,1,2)
except RuntimeError: pass
else: raise AssertionError("injected failure did not propagate")
assert c.execute("SELECT * FROM inventory ORDER BY id").fetchall()==before
c=seeded(); before=c.execute("SELECT * FROM inventory ORDER BY id").fetchall(); ns=namespace(c,True)
try: ns["consume_user_item_by_item_id"](7,100,6)
except RuntimeError: pass
else: raise AssertionError("injected failure did not propagate")
assert c.execute("SELECT * FROM inventory ORDER BY id").fetchall()==before
print("PASS: Stage 21.4.3 injected-failure rollback leaves isolated inventory unchanged")
