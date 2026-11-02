#!/usr/bin/env python3
import ast
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; SPECS={'systems/admin_crystal_credit_system.py': ['preview_admin_adjustment'], 'systems/crystal_wallet_system.py': ['compensate_crystal_transaction']}
for rel,names in SPECS.items():
 tree=ast.parse((ROOT/rel).read_text(encoding="utf-8-sig"))
 for name in names:
  fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name==name); calls=[ast.unparse(n.func) for n in ast.walk(fn) if isinstance(n,ast.Call)]
  assert sum(x.endswith("commit") for x in calls)==1,(rel,name); assert sum(x.endswith("rollback") for x in calls)==1,(rel,name)
  assert any(isinstance(h,ast.ExceptHandler) and any(isinstance(x,ast.Raise) for x in ast.walk(h)) for h in ast.walk(fn)),(rel,name)
# Preserve already-atomic business owners and caller-owned _stack helper.
shop=ast.parse((ROOT/"systems/crystal_shop_system.py").read_text(encoding="utf-8-sig")); stack=next(n for n in shop.body if isinstance(n,ast.FunctionDef) and n.name=="_stack"); assert not any(isinstance(n,ast.Call) and ast.unparse(n.func).endswith("commit") for n in ast.walk(stack))
print("PASS: Stage 21.4.6 crystal/currency owners rollback; caller-owned helper preserved")
