#!/usr/bin/env python3
import ast
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; p=ROOT/"db_modules/inventory.py"; tree=ast.parse(p.read_text(encoding="utf-8-sig"))
for name in ("consume_inventory_item","consume_user_item_by_item_id"):
 fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name==name)
 calls=[ast.unparse(n.func) for n in ast.walk(fn) if isinstance(n,ast.Call)]
 assert any(x.endswith("commit") for x in calls), name
 assert any(x.endswith("rollback") for x in calls), name
 handlers=[n for n in ast.walk(fn) if isinstance(n,ast.ExceptHandler)]
 assert any(any(isinstance(x,ast.Raise) for x in ast.walk(h)) for h in handlers), name
print("PASS: Stage 21.4.3 inventory transaction ownership and rollback invariants")
