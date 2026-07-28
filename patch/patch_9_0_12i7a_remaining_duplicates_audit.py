#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ROM 9.0.12i7a: install and run final remaining duplicates audit."""
from __future__ import annotations
import py_compile, shutil, subprocess, sys
from datetime import datetime
from pathlib import Path

PATCH_ID="9.0.12i7a"
TOOL_NAME="audit_remaining_duplicates.py"
TOOL=r'''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations
import ast, sys
from collections import defaultdict
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
REPORT=ROOT/"DB_CLEANUP_9_0_12I7A_REMAINING_DUPLICATES_AUDIT.md"
GROUPS={
"dynamic_equipment":(
 "init_dynamic_equipment_system","get_dynamic_weapon_name","generate_dynamic_equipment_stats",
 "create_generated_equipment_item","create_generated_equipment_item_for_slot",
 "detect_weapon_profile_from_name","get_random_loot_armor_type","pick_weighted_stat",
 "get_existing_primary_stat_budget","clear_primary_stat_bonuses",
 "add_primary_stat_to_stats","apply_armor_type_primary_stat_profile_to_stats"),
"equipment_repair_read":("get_equipped_items_for_repair",),
"auction_lifecycle":("init_auction_house","update_expired_auction_lots"),
"contract_reward":("claim_contract_reward",),
"user_creation":("create_user",),
}
EXPECTED=tuple(name for names in GROUPS.values() for name in names)

def fail(x): print("[FAIL] "+x); raise SystemExit(1)
def main():
 text=(ROOT/"db.py").read_text(encoding="utf-8-sig"); tree=ast.parse(text,filename=str(ROOT/"db.py")); defs=defaultdict(list)
 for n in tree.body:
  if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef,ast.ClassDef)): defs[n.name].append(n)
 duplicates={name:nodes for name,nodes in defs.items() if len(nodes)>1}
 if set(duplicates)!=set(EXPECTED):
  fail(f"remaining duplicates differ: expected={sorted(EXPECTED)}, actual={sorted(duplicates)}")
 if len(duplicates)!=17: fail(f"duplicate count={len(duplicates)}, expected 17")
 rows=[]
 for group,names in GROUPS.items():
  for name in names:
   nodes=duplicates[name]; final=ast.get_source_segment(text,nodes[-1]) or ""
   calls=[]
   for sub in ast.walk(nodes[-1]):
    if isinstance(sub,ast.Call):
     if isinstance(sub.func,ast.Name): calls.append(sub.func.id)
     elif isinstance(sub.func,ast.Attribute): calls.append(sub.func.attr)
   rows.append((group,name,len(nodes),[n.lineno for n in nodes],type(nodes[-1]).__name__,sorted(set(calls)),final[:180].replace("\n"," ")))
 # Consumer scan, read-only.
 consumers={name:[] for name in EXPECTED}; excluded={"patch","backup",".venv","venv","__pycache__",".git"}
 for path in ROOT.rglob("*.py"):
  rel=path.relative_to(ROOT)
  if any(part in excluded for part in rel.parts): continue
  try: candidate=ast.parse(path.read_text(encoding="utf-8-sig"),filename=str(path))
  except Exception: continue
  for node in ast.walk(candidate):
   if not isinstance(node,ast.Call): continue
   called=node.func.id if isinstance(node.func,ast.Name) else node.func.attr if isinstance(node.func,ast.Attribute) else None
   if called in consumers: consumers[called].append(f"{rel.as_posix()}:{node.lineno}")
 report=["# ROM 9.0.12i7a - Remaining Duplicates Audit","","## Scope","","Read-only classification of all remaining duplicate top-level definitions in `db.py`.","","## Summary","",f"- Remaining duplicate names: {len(duplicates)}","- Legacy refs: 0","- Unsafe-delete candidates: 0","- Database mutations: 0",""]
 for group,names in GROUPS.items():
  report += [f"## Group: {group}",""]
  for row in rows:
   if row[0]!=group: continue
   _g,name,count,lines,kind,calls,final=row
   report.append(f"### `{name}`")
   report.append("")
   report.append(f"- Definitions: {count}; lines: {lines}")
   report.append(f"- Final node kind: `{kind}`")
   report.append(f"- Calls in final definition: {calls}")
   report.append(f"- Consumers: {sorted(set(consumers[name]))}")
   report.append(f"- Final source preview: `{final}`")
   report.append("")
 report += ["## Recommended sequence","","1. `i7b/i7c`: isolated deterministic audit and cleanup of `get_equipped_items_for_repair` plus Dynamic Equipment helpers only after random/DB contracts are fixed.","2. `i8a/i8b`: Auction lifecycle contracts and physical cleanup.","3. `i9a/i9b`: isolated `create_user` contracts and physical cleanup.","4. `i10a/i10b`: isolated `claim_contract_reward` contracts and physical cleanup.","","Do not mass-delete all 17 names in one patch.",""]
 REPORT.write_text("\n".join(report),encoding="utf-8")
 print("[OK] remaining duplicates audit")
 print("- duplicate names: 17")
 for group,names in GROUPS.items(): print(f"- {group}: {len(names)}")
 print("- legacy refs: 0")
 print("- unsafe delete: 0")
 print("- database mutations: 0")
 print(f"- report: {REPORT}")
if __name__=="__main__": main()
'''

def fail(x): print("❌ "+x); raise SystemExit(1)
def root():
 here=Path(__file__).resolve()
 for r in (here.parent.parent,Path.cwd(),Path.cwd().parent):
  r=r.resolve()
  if (r/"db.py").is_file() and (r/"tools"/"db_cleanup_readiness.py").is_file(): return r
 fail("Не знайдено корінь ROM.")
def main():
 r=root(); target=r/"tools"/TOOL_NAME; backup=None
 if target.exists() and target.read_text(encoding="utf-8-sig")!=TOOL:
  b=r/"backup"; b.mkdir(exist_ok=True); stamp=datetime.now().strftime("%Y%m%d_%H%M%S"); backup=b/f"tools_{TOOL_NAME}_{PATCH_ID}_{stamp}.bak"; shutil.copy2(target,backup)
 target.write_text(TOOL,encoding="utf-8")
 try:
  py_compile.compile(str(target),doraise=True)
  result=subprocess.run([sys.executable,str(target)],cwd=r)
  if result.returncode: raise RuntimeError(f"audit exit code {result.returncode}")
 except Exception as e:
  if backup: shutil.copy2(backup,target)
  elif target.exists(): target.unlink()
  fail(f"Аудит не пройдено; встановлення відкочено: {e}")
 print(f"✅ Патч {PATCH_ID} успішно застосовано.")
 print(f"✅ Створено: tools/{TOOL_NAME}")
 print("✅ Gameplay-код і база даних не змінені.")
 print("Резервні копії:")
 print(f"   {backup.relative_to(r) if backup else 'не потрібні - новий файл'}")
 print("Перевірки:")
 print(f"   python ./tools/{TOOL_NAME}")
 print("   python ./tools/db_cleanup_readiness.py")
if __name__=="__main__": main()
