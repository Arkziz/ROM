#!/usr/bin/env python3
import ast
from pathlib import Path
p=Path(__file__).resolve().parents[1]/"systems/auction_house_system.py"; tree=ast.parse(p.read_text(encoding="utf-8-sig"))
for name in ("create_auction_lot_record","mark_auction_lot_status"):
 owners=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name==name]; assert len(owners)==1,name
 fn=owners[0]; calls=[ast.unparse(n.func) for n in ast.walk(fn) if isinstance(n,ast.Call)]; assert sum(x.endswith("commit") for x in calls)==1,(name,calls); assert sum(x.endswith("rollback") for x in calls)==1,(name,calls)
 assert any(isinstance(h,ast.ExceptHandler) and any(isinstance(x,ast.Raise) for x in ast.walk(h)) and any(isinstance(x,ast.Call) and ast.unparse(x.func).endswith("rollback") for x in ast.walk(h)) for h in ast.walk(fn)),name
for name in ("create_equipment_auction_lot","purchase_auction_lot"):
 matches=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name==name]
 if matches: assert any(isinstance(n,ast.Call) and ast.unparse(n.func).endswith("rollback") for n in ast.walk(matches[-1])),name
print("PASS: Stage 21.4.7 auction owner rollback invariants")
