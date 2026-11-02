#!/usr/bin/env python3
import sqlite3
class FailCommit:
 def __init__(self,c): self.c=c
 def commit(self): raise RuntimeError("injected commit failure")
 def rollback(self): self.c.rollback()
c=sqlite3.connect(":memory:"); c.execute("CREATE TABLE applications(id INTEGER PRIMARY KEY,status TEXT)"); c.execute("CREATE TABLE guilds(id INTEGER PRIMARY KEY,progress INTEGER,level INTEGER)"); c.execute("INSERT INTO applications VALUES(1, ?)",("pending",)); c.execute("INSERT INTO guilds VALUES(1,10,1)"); c.commit(); before_a=c.execute("SELECT * FROM applications").fetchall(); before_g=c.execute("SELECT * FROM guilds").fetchall(); owner=FailCommit(c)
try:
 c.execute("UPDATE applications SET status=? WHERE id=1",("rejected",)); c.execute("UPDATE guilds SET progress=progress+5,level=2 WHERE id=1"); owner.commit()
except RuntimeError: owner.rollback()
else: raise AssertionError("failure not propagated")
assert c.execute("SELECT * FROM applications").fetchall()==before_a
assert c.execute("SELECT * FROM guilds").fetchall()==before_g
print("PASS: Stage 21.4.8 injected failure rolls back guild application/progress writes")
