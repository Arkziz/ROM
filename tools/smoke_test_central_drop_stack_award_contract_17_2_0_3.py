#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import ast
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
source=(ROOT/"db_modules/inventory.py").read_text(encoding="utf-8")
tree=ast.parse(source)
def req(v,m):
    if not v: raise AssertionError(m)
f=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=="add_item"]
req(len(f)==1,"add_item unique")
segment=ast.get_source_segment(source,f[0])
req("SELECT name, COALESCE(max_stack, 1)" in segment,"named max_stack query")
req('item[6]' not in segment,"positional max_stack bug remains")
for key in ('"added"','"lost"','"name"','"used_slots"','"capacity"'):
    req(key in segment,f"missing result field {key}")
req(source.count("# ROM 17.2.0.3 CENTRAL DROP STACK AWARD CONTRACT RECOVERY")==1,"marker")
print("[PASS] Stage 17.2.0.3 central drop stack award contract")
