#!/usr/bin/env python3
import ast
from pathlib import Path
p=Path(__file__).resolve().parents[1]/"main.py"; t=ast.parse(p.read_text(encoding="utf-8-sig"))
defs=[n for n in ast.walk(t) if isinstance(n,ast.FunctionDef) and n.name=="run_bot_polling_resilient"]
assert len(defs)==1
assert not [x for x in ast.walk(defs[0]) if isinstance(x,ast.Call) and ast.unparse(x.func)=="run_bot_polling_resilient"]
assert len([x for x in ast.walk(t) if isinstance(x,ast.Call) and ast.unparse(x.func).endswith("infinity_polling")])==1
assert len([x for x in ast.walk(t) if isinstance(x,ast.Call) and ast.unparse(x.func)=="run_bot_polling_resilient"])==1
print("PASS: Stage 21.1.2 single polling owner")
