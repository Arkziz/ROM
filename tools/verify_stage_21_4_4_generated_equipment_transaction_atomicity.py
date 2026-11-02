#!/usr/bin/env python3
import ast
from pathlib import Path
p=Path(__file__).resolve().parents[1]/"db_modules/generated_equipment.py"; tree=ast.parse(p.read_text(encoding="utf-8-sig")); owners=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=="create_generated_equipment_item"]; assert len(owners)==1
fn=owners[0]; calls=[ast.unparse(n.func) for n in ast.walk(fn) if isinstance(n,ast.Call)]; assert sum(x.endswith("commit") for x in calls)==1; assert sum(x.endswith("rollback") for x in calls)==1
handlers=[n for n in ast.walk(fn) if isinstance(n,ast.ExceptHandler)]; assert any(any(isinstance(x,ast.Raise) for x in ast.walk(h)) and any(isinstance(x,ast.Call) and ast.unparse(x.func).endswith("rollback") for x in ast.walk(h)) for h in handlers)
print("PASS: Stage 21.4.4 generated equipment commit/rollback ownership")
