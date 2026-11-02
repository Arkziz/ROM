#!/usr/bin/env python3
import sqlite3
class FailCommit:
 def __init__(self,c): self.c=c
 def commit(self): raise RuntimeError("injected commit failure")
 def rollback(self): self.c.rollback()
c=sqlite3.connect(":memory:"); c.execute("CREATE TABLE wallet(user_id INTEGER PRIMARY KEY,balance INTEGER)"); c.execute("INSERT INTO wallet VALUES(7,10)"); c.commit(); before=c.execute("SELECT * FROM wallet").fetchall(); owner=FailCommit(c)
try:
 c.execute("UPDATE wallet SET balance=balance+5 WHERE user_id=7"); owner.commit()
except RuntimeError: owner.rollback()
else: raise AssertionError("failure not propagated")
assert c.execute("SELECT * FROM wallet").fetchall()==before
print("PASS: Stage 21.4.6 injected commit failure leaves isolated currency state unchanged")
