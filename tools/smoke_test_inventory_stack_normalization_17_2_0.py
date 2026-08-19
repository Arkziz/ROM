#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import ast
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
source=(ROOT/"db_modules"/"inventory.py").read_text(encoding="utf-8")
tree=ast.parse(source)
def req(v,m):
    if not v: raise AssertionError(m)
req(source.count("# ROM 17.2.0 CANONICAL STACK NORMALIZATION")==1,"marker")
req(len([n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=="add_item"])==1,"add_item must be unique")
req("SAVEPOINT rom_add_item_17_2_0" not in source,"savepoint must be dynamic SQL")
req("ORDER BY id ASC" in source,"oldest stack order")
req("while quantity > 0" in source,"multi-stack creation")
req("_inventory_reserved_ids_for_item" in source,"reservation guard")
print("[PASS] Stage 17.2.0 canonical inventory stack runtime")
