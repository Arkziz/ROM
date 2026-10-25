#!/usr/bin/env python3
"""Fail when reusable Quest Engine modules contain concrete quest content."""
import ast,re
from pathlib import Path
R=Path(__file__).resolve().parent.parent
files=[R/"rom_v2/domain/quest_engine.py",R/"rom_v2/application/quest_engine_service.py"]
violations=[]
for p in files:
 text=p.read_text(encoding="utf-8");tree=ast.parse(text)
 for n in ast.walk(tree):
  if isinstance(n,ast.Constant) and isinstance(n.value,str):
   v=n.value
   if re.search(r"(?i)quest[_ -]?\d+",v) or any(ch in v for ch in "АБВГҐДЕЄЖЗИІЇЙКЛМНОПРСТУФХЦЧШЩЬЮЯ"):violations.append(f"{p.name}:content_literal:{v}")
  if isinstance(n,ast.Compare) and any(isinstance(x,ast.Constant) and isinstance(x.value,int) and x.value>=100 for x in [n.left,*n.comparators]):violations.append(f"{p.name}:concrete_id_branch")
if violations:print("Quest content independence: FAIL",*violations,sep="\n");raise SystemExit(1)
print("Stage 21.13.1c Quest content independence: PASS")
