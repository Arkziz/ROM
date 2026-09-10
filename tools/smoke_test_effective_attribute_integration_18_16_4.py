#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations
import ast, sqlite3
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
path=ROOT/"systems/player_system.py"
source=path.read_text(encoding="utf-8-sig")
tree=ast.parse(source)
defs=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=="_player_base_row_9_0_12g"]
assert len(defs)==1,len(defs)
segment=ast.get_source_segment(source,defs[0]) or ""
expected=(
 "COALESCE(str,0) + COALESCE(allocated_strength,0)",
 "COALESCE(dex,0) + COALESCE(allocated_dexterity,0)",
 "COALESCE(intelligence,0) + COALESCE(allocated_intelligence,0)",
 "COALESCE(wis,0) + COALESCE(allocated_wisdom,0)",
 "COALESCE(sta,0) + COALESCE(allocated_stamina,0)",
)
for expression in expected: assert expression in segment,expression
for column in ("allocated_strength","allocated_dexterity","allocated_intelligence","allocated_wisdom","allocated_stamina"):
 assert segment.count(column)==1,(column,segment.count(column))
stats=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=="get_player_stats"]
assert len(stats)==1
stats_segment=ast.get_source_segment(source,stats[0]) or ""
assert stats_segment.count("_player_base_row_9_0_12g(user_id)")==1
conn=sqlite3.connect((ROOT/"game.db").resolve().as_uri()+"?mode=ro",uri=True)
try:
 assert conn.execute("PRAGMA quick_check").fetchone()[0]=="ok"
 assert not list(conn.execute("PRAGMA foreign_key_check"))
finally:conn.close()
print("[PASS] Stage 18.16.4 exact-once aggregation structure")
