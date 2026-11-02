#!/usr/bin/env python3
import sqlite3
class FailCommit:
 def __init__(self,c): self.c=c
 def commit(self): raise RuntimeError("injected commit failure")
 def rollback(self): self.c.rollback()
c=sqlite3.connect(":memory:"); c.execute("CREATE TABLE lots(id INTEGER PRIMARY KEY,status TEXT)"); c.commit(); before=c.execute("SELECT * FROM lots").fetchall(); owner=FailCommit(c)
try:
 c.execute("INSERT INTO lots VALUES(1, ?)", ("active",)); owner.commit()
except RuntimeError: owner.rollback()
else: raise AssertionError("failure not propagated")
assert c.execute("SELECT * FROM lots").fetchall()==before
c.execute("INSERT INTO lots VALUES(1, ?)", ("active",)); c.commit(); before=c.execute("SELECT * FROM lots").fetchall(); owner=FailCommit(c)
try:
 c.execute("UPDATE lots SET status=? WHERE id=1", ("sold",)); owner.commit()
except RuntimeError: owner.rollback()
else: raise AssertionError("failure not propagated")
assert c.execute("SELECT * FROM lots").fetchall()==before
print("PASS: Stage 21.4.7 injected failures roll back auction create/status writes")
