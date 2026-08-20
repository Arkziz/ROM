#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import ast
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
source = (ROOT / "db_modules/connection.py").read_text(encoding="utf-8")
ast.parse(source)
assert source.count("ROM 17.8.1.1 PARAMETERIZED BAG DEFAULT") == 1
assert 'UPDATE users SET bag_slots = DEFAULT_BAG_SLOTS' not in source
assert '"UPDATE users SET bag_slots = ? WHERE bag_slots IS NULL"' in source
assert '(DEFAULT_BAG_SLOTS,)' in source

conn = sqlite3.connect(":memory:")
conn.execute("CREATE TABLE users(user_id INTEGER PRIMARY KEY, bag_slots INTEGER)")
conn.executemany("INSERT INTO users(user_id,bag_slots) VALUES(?,?)", [(1,None),(2,40),(3,80)])
DEFAULT_BAG_SLOTS = 60
conn.execute("UPDATE users SET bag_slots = ? WHERE bag_slots IS NULL", (DEFAULT_BAG_SLOTS,))
rows = conn.execute("SELECT user_id,bag_slots FROM users ORDER BY user_id").fetchall()
assert rows == [(1,60),(2,40),(3,80)], rows
print("[PASS] Stage 17.8.1.1 parameterized bag default SQL recovery")
