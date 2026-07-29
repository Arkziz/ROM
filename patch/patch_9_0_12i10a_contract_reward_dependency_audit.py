#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ROM 9.0.12i10a: install Contract Reward dependency audit."""
from __future__ import annotations
import py_compile, shutil, subprocess, sys
from datetime import datetime
from pathlib import Path

PATCH_ID="9.0.12i10a"
TOOL_NAME="audit_contract_reward_dependency.py"
TOOL=r'''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Read-only audit of the final claim_contract_reward duplicate/capture chain."""
from __future__ import annotations
import ast
import inspect
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))
REPORT=ROOT/"DB_CLEANUP_9_0_12I10A_CONTRACT_REWARD_DEPENDENCY_AUDIT.md"
CAPTURE="_base_claim_contract_reward_before_guild_reward_v1"

def fail(message): print(f"[FAIL] {message}"); raise SystemExit(1)
def parse(path):
 text=path.read_text(encoding="utf-8-sig"); tree=ast.parse(text,filename=str(path)); defs={}
 for node in tree.body:
  if isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef)): defs.setdefault(node.name,[]).append(node)
 return text,tree,defs
def safe(fn,*args,**kwargs):
 try:return True,fn(*args,**kwargs)
 except Exception as exc:return False,f"{type(exc).__name__}: {exc}"
def calls(node):
 result=[]
 for sub in ast.walk(node):
  if isinstance(sub,ast.Call):
   if isinstance(sub.func,ast.Name): result.append(sub.func.id)
   elif isinstance(sub.func,ast.Attribute): result.append(sub.func.attr)
 return sorted(set(result))
def main():
 db_text,db_tree,db_defs=parse(ROOT/"db.py")
 sys_text,sys_tree,sys_defs=parse(ROOT/"systems"/"contract_system.py")
 nodes=db_defs.get("claim_contract_reward",[])
 if len(nodes)!=2: fail(f"db.py claim_contract_reward definitions={len(nodes)}, expected 2")
 if len(sys_defs.get("claim_contract_reward",[]))!=1: fail("contract_system claim_contract_reward definition count is not 1")
 base_source=ast.get_source_segment(db_text,nodes[0]) or ""
 final_source=ast.get_source_segment(db_text,nodes[-1]) or ""
 system_source=ast.get_source_segment(sys_text,sys_defs["claim_contract_reward"][0]) or ""
 if CAPTURE not in final_source: fail("final db override does not use expected capture")
 if "_claim_contract_reward_base" not in system_source: fail("system direct claim path missing _claim_contract_reward_base")
 if "award_guild_contract_completion" not in system_source: fail("system claim path missing Guild reward hook")
 capture_blocks=[]
 for node in db_tree.body:
  if isinstance(node,ast.Try) and CAPTURE in {x.id for x in ast.walk(node) if isinstance(x,ast.Name)}: capture_blocks.append(node)
 if len(capture_blocks)!=1: fail(f"capture blocks={len(capture_blocks)}, expected 1")
 import db
 from systems import contract_system as contract
 capture=getattr(db,CAPTURE,None)
 if not callable(capture): fail("base claim capture is not callable")
 # Strictly read-only comparisons: absent user IDs only.
 comparisons=[]
 for uid in (-90121001,-90121002):
  public=safe(db.claim_contract_reward,uid)
  system=safe(contract.claim_contract_reward,uid)
  base=safe(capture,uid)
  if public!=system or public!=base: fail(f"missing-user mismatch uid={uid}: public={public!r}, system={system!r}, base={base!r}")
  comparisons.append(uid)
 # Confirm no fixture rows were created by missing-user paths.
 for uid in comparisons:
  if db.cursor.execute("SELECT COUNT(*) FROM users WHERE user_id=?",(uid,)).fetchone()[0]: fail(f"missing-user path created users row: {uid}")
  try:
   if db.cursor.execute("SELECT COUNT(*) FROM user_active_contracts WHERE user_id=?",(uid,)).fetchone()[0]: fail(f"missing-user path created contract row: {uid}")
  except Exception: pass
 consumers=[]
 excluded={"patch","backup",".venv","venv","__pycache__",".git"}
 for path in ROOT.rglob("*.py"):
  rel=path.relative_to(ROOT)
  if any(part in excluded for part in rel.parts): continue
  try: tree=ast.parse(path.read_text(encoding="utf-8-sig"),filename=str(path))
  except Exception: continue
  for node in ast.walk(tree):
   if isinstance(node,ast.Call):
    name=node.func.id if isinstance(node.func,ast.Name) else node.func.attr if isinstance(node.func,ast.Attribute) else None
    if name=="claim_contract_reward": consumers.append(f"{rel.as_posix()}:{node.lineno}")
 report=[
 "# ROM 9.0.12i10a - Contract Reward Dependency Audit","",
 "## Structural result","",
 f"- db.py definitions: 2; lines: {[n.lineno for n in nodes]}",
 f"- Base signature: `{inspect.signature(capture)}`",
 f"- Public signature: `{inspect.signature(db.claim_contract_reward)}`",
 f"- System signature: `{inspect.signature(contract.claim_contract_reward)}`",
 f"- Capture block count: {len(capture_blocks)}",
 f"- Final db calls: {calls(nodes[-1])}",
 f"- System calls: {calls(sys_defs['claim_contract_reward'][0])}",
 f"- Consumers: {sorted(set(consumers))}","",
 "## Runtime read-only result","",
 f"- Missing-user public/system/base comparisons: {len(comparisons)}",
 "- Mismatches: 0","- Database rows created: 0","",
 "## Conclusion","",
 "`systems.contract_system.claim_contract_reward` already contains a direct base claim plus Guild reward hook. The final db.py override still depends on an obsolete capture of the earlier db.py implementation.","",
 "Recommended sequence:","",
 "1. i10b: switch final db.py claim_contract_reward to a thin contract_system facade and run isolated mutation equivalence tests while retaining the old implementation/capture for rollback.",
 "2. i10c: remove the earlier db.py definition and obsolete capture, leaving a single facade definition.",""
 ]
 REPORT.write_text("\n".join(report),encoding="utf-8")
 print("[OK] contract reward dependency audit")
 print("- db definitions: 2")
 print("- system direct implementation: available")
 print("- base capture: callable")
 print(f"- missing-user comparisons: {len(comparisons)}")
 print("- mismatches: 0")
 print("- database mutations: 0")
 print("- recommended next step: i10b direct facade + isolated mutation contracts")
 print(f"- report: {REPORT}")
if __name__=="__main__": main()
'''

def fail(x): print("❌ "+x); raise SystemExit(1)
def root():
 here=Path(__file__).resolve()
 for r in (here.parent.parent,Path.cwd(),Path.cwd().parent):
  r=r.resolve()
  if (r/"db.py").is_file() and (r/"systems"/"contract_system.py").is_file(): return r
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
 except Exception as exc:
  if backup: shutil.copy2(backup,target)
  elif target.exists(): target.unlink()
  fail(f"Аудит не пройдено; встановлення відкочено: {exc}")
 print(f"✅ Патч {PATCH_ID} успішно застосовано.")
 print(f"✅ Створено: tools/{TOOL_NAME}")
 print("✅ Gameplay-код і реальна база не змінені.")
 print("Резервні копії:")
 print(f"   {backup.relative_to(r) if backup else 'не потрібні - новий файл'}")
 print("Перевірки:")
 print(f"   python ./tools/{TOOL_NAME}")
 print("   python ./tools/smoke_test_contract_contracts.py")
 print("   python ./tools/db_cleanup_readiness.py")
if __name__=="__main__": main()
