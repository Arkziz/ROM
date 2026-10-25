#!/usr/bin/env python3
"""Fail if new V2 PvP modules copy combat arithmetic instead of using resolver ports."""
import ast,sys
from pathlib import Path
R=Path(__file__).resolve().parent.parent
files=[R/"rom_v2/domain/pvp.py",R/"rom_v2/application/pvp_service.py"]
banned={"damage","defense","critical","dodge","resource_cost","regeneration","skill_effect"};violations=[]
for p in files:
 tree=ast.parse(p.read_text(encoding="utf-8"))
 for n in ast.walk(tree):
  if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)) and n.name.lower() in banned:violations.append(f"{p.name}:function:{n.name}")
  if isinstance(n,ast.Assign):
   for t in n.targets:
    if isinstance(t,ast.Name) and any(x in t.id.lower() for x in banned):violations.append(f"{p.name}:constant:{t.id}")
  if p.name=="pvp_service.py" and isinstance(n,(ast.Mult,ast.Div,ast.FloorDiv,ast.Pow)):violations.append(f"{p.name}:combat_arithmetic:{type(n).__name__}")
if violations:print("No copied formulas: FAIL",*violations,sep="\n");raise SystemExit(1)
print("Stage 21.12.6c No copied formulas: PASS")
