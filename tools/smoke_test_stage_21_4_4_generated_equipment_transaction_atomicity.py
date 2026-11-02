#!/usr/bin/env python3
import sqlite3

def persist(connection, fail_after_item=False):
 try:
  cursor=connection.cursor(); cursor.execute("INSERT INTO items(id,name) VALUES(?,?)",(1001,"Generated"))
  if fail_after_item: raise RuntimeError("injected inventory insert failure")
  cursor.execute("INSERT INTO inventory(user_id,item_id,quantity,durability) VALUES(?,?,?,?)",(7,1001,1,100)); inventory_id=cursor.lastrowid; connection.commit(); return inventory_id
 except Exception:
  connection.rollback(); raise

def database():
 c=sqlite3.connect(":memory:"); c.execute("CREATE TABLE items(id INTEGER PRIMARY KEY,name TEXT)"); c.execute("CREATE TABLE inventory(id INTEGER PRIMARY KEY AUTOINCREMENT,user_id INTEGER,item_id INTEGER REFERENCES items(id),quantity INTEGER,durability INTEGER)"); c.execute("PRAGMA foreign_keys=ON"); c.commit(); return c
c=database(); assert persist(c)>0; assert c.execute("SELECT COUNT(*) FROM items").fetchone()[0]==1; assert c.execute("SELECT COUNT(*) FROM inventory").fetchone()[0]==1
c=database()
try: persist(c,True)
except RuntimeError: pass
else: raise AssertionError("injected failure did not propagate")
assert c.execute("SELECT COUNT(*) FROM items").fetchone()[0]==0; assert c.execute("SELECT COUNT(*) FROM inventory").fetchone()[0]==0
print("PASS: Stage 21.4.4 injected failure rolls back item and inventory rows")
