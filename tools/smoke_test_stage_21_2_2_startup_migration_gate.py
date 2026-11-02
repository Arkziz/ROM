#!/usr/bin/env python3
import ast
from pathlib import Path
p=Path(__file__).resolve().parents[1]/"main.py"; t=ast.parse(p.read_text(encoding="utf-8-sig")); fn=next(n for n in t.body if isinstance(n,ast.FunctionDef) and n.name=="_validate_startup_migration_result"); ns={}; exec(compile(ast.fix_missing_locations(ast.Module(body=[fn],type_ignores=[])),"main.py","exec"),ns); v=ns["_validate_startup_migration_result"]
good={"success":True,"applied":["001.py"],"skipped":["002.py"],"failed":None,"total_files":2}; assert v(good) is good
bad=[None,{}, {"success":False,"applied":[],"skipped":[],"failed":{"migration":"001.py"},"total_files":1},{"success":True,"applied":[],"skipped":[],"failed":None,"total_files":1},{"success":True,"applied":(),"skipped":[],"failed":None,"total_files":0}]
for value in bad:
 try: v(value)
 except RuntimeError: pass
 else: raise AssertionError(f"invalid migration result accepted: {value!r}")
print("PASS: Stage 21.2.2 isolated migration-result contract smoke")
