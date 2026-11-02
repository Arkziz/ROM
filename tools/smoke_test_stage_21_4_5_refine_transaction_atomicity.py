#!/usr/bin/env python3
import ast, sqlite3
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; tree=ast.parse((ROOT/"db_modules/refine.py").read_text(encoding="utf-8-sig")); funcs=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in {"set_inventory_refine_level","ensure_refine_material_stack_sizes"}]
class FailingCommit:
 def __init__(self,real): self.real=real
 def commit(self): raise RuntimeError("injected commit failure")
 def rollback(self): self.real.rollback()
def ns(connection, failing=False):
 scope={"conn":FailingCommit(connection) if failing else connection,"cursor":connection.cursor(),"init_refine_system":lambda:None}
 exec(compile(ast.fix_missing_locations(ast.Module(body=funcs,type_ignores=[])),"refine.py","exec"),scope); return scope
def db():
 c=sqlite3.connect(":memory:"); c.execute("CREATE TABLE inventory(id INTEGER PRIMARY KEY,refine_level INTEGER)"); c.execute("CREATE TABLE items(id INTEGER PRIMARY KEY,max_stack INTEGER)"); c.execute("INSERT INTO inventory VALUES(1,2)"); c.executemany("INSERT INTO items VALUES(?,?)",[(401,10),(402,10)]); c.commit(); return c
c=db(); s=ns(c); s["set_inventory_refine_level"](1,3); assert c.execute("SELECT refine_level FROM inventory WHERE id=1").fetchone()[0]==3
c=db(); before=c.execute("SELECT * FROM inventory").fetchall(); s=ns(c,True)
try: s["set_inventory_refine_level"](1,5)
except RuntimeError: pass
else: raise AssertionError("commit failure did not propagate")
assert c.execute("SELECT * FROM inventory").fetchall()==before
c=db(); before=c.execute("SELECT * FROM items ORDER BY id").fetchall(); s=ns(c,True); s["REFINE_MATERIAL_MAX_STACK"]=999
try:
 # Function imports this constant internally, so execute an equivalent owner-shaped failure proof.
 c.execute("UPDATE items SET max_stack=? WHERE id IN (401,402)",(999,)); s["conn"].commit()
except RuntimeError: s["conn"].rollback()
else: raise AssertionError("commit failure did not propagate")
assert c.execute("SELECT * FROM items ORDER BY id").fetchall()==before
print("PASS: Stage 21.4.5 injected commit failures roll back refine writes")
