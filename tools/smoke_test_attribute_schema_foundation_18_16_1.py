#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sqlite3
from pathlib import Path
R=Path(__file__).resolve().parents[1]
N=("free_attribute_points","total_attribute_points_earned","allocated_strength","allocated_dexterity","allocated_intelligence","allocated_wisdom","allocated_stamina")
A=N+("attribute_points_migrated_at",)
c=sqlite3.connect((R/"game.db").resolve().as_uri()+"?mode=ro",uri=True)
try:
 d={str(r[1]):r for r in c.execute("PRAGMA table_info(users)")}
 assert not sorted(set(A)-set(d)),sorted(set(A)-set(d))
 for n in N:
  assert str(d[n][2]).upper()=="INTEGER" and int(d[n][3])==1 and str(d[n][4]) in ("0","'0'",'"0"'),(n,d[n])
  assert c.execute(f'SELECT COUNT(*) FROM users WHERE "{n}" IS NULL OR "{n}"<0 OR "{n}"<>0').fetchone()[0]==0,n
 assert c.execute("PRAGMA quick_check").fetchone()[0]=="ok"
 assert not list(c.execute("PRAGMA foreign_key_check"))
 assert c.execute("SELECT COUNT(*) FROM schema_migrations WHERE migration_name=?",("042_attribute_points_foundation.py",)).fetchone()[0]==1
finally:c.close()
print("[PASS] Stage 18.16.1 attribute schema foundation contract")
