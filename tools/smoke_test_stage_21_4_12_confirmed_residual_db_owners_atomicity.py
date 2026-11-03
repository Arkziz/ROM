#!/usr/bin/env python3
import sqlite3
class FailCommit:
 def __init__(self,c): self.c=c
 def commit(self): raise RuntimeError("injected commit failure")
 def rollback(self): self.c.rollback()
c=sqlite3.connect(":memory:"); c.execute("CREATE TABLE inventory(id INTEGER PRIMARY KEY,durability INTEGER,quantity INTEGER)"); c.execute("INSERT INTO inventory VALUES(1,100,3)"); c.commit(); before=c.execute("SELECT * FROM inventory").fetchall(); owner=FailCommit(c)
try:
 c.execute("UPDATE inventory SET durability=durability-1,quantity=quantity-1 WHERE id=1"); owner.commit()
except RuntimeError: owner.rollback()
else: raise AssertionError("failure not propagated")
assert c.execute("SELECT * FROM inventory").fetchall()==before
print("PASS: Stage 21.4.12 injected failure rolls back residual DB-owner-shaped writes")
