#!/usr/bin/env python3
"""ROM Stage 21.9.2c: implement pure V2 level-up-gold parity."""
from __future__ import annotations
import ast,hashlib,json,os,shutil,subprocess,sys
from datetime import datetime,timezone
from pathlib import Path

STAGE="21.9.2c";BRANCH="rewrite/rom-v2";PARENT="975908737b336ecc9f828fef24006a4035bc83e8"
PREREQ=Path("reports/stage_21_9_2b_resolved_level_up_gold_parity.json")
DOMAIN=Path("rom_v2/domain/level_up_gold.py");TEST=Path("tests_v2/test_level_up_gold.py")
TOOL=Path("tools/check_stage_21_9_2c_level_up_gold.py")
REPORT=Path("reports/stage_21_9_2c_level_up_gold_implementation.json")
DOC=Path("MD/STAGE_21_9_2C_LEVEL_UP_GOLD_IMPLEMENTATION.md")
FAILURE=Path("reports/stage_21_9_2c_failure_rollback.json");SELF=Path("patch/patch_21_9_2c_implement_level_up_gold.py")
TARGETS=(SELF,DOMAIN,TEST,TOOL,REPORT,DOC)
ALLOWED_DIRTY={"ROM_FULL_DUMP.txt",FAILURE.as_posix(),"reports/v2_ci_failure.json","reports/v2_ci_result.json"}
PROTECTED=("game.db","game.db-wal","game.db-shm",".env","rom_v2/.env",".runtime/v2/db/rom_v2.db")

class PatchError(RuntimeError):pass
def run(c,r,check=True,env=None):
 p=subprocess.run(c,cwd=r,text=True,capture_output=True,encoding="utf-8",errors="replace",env=env)
 if check and p.returncode:raise PatchError(f"command_failed:{c}:{p.stdout[-1800:]}:{p.stderr[-1800:]}")
 return p
def git(r,*a,check=True):return run(["git",*a],r,check)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest() if p.is_file() else None
def protected(r):return {x:sha(r/x) for x in PROTECTED}
def write(r,p,s):q=r/p;q.parent.mkdir(parents=True,exist_ok=True);q.write_text(s.rstrip()+"\n",encoding="utf-8")
def preflight(r):
 if git(r,"branch","--show-current").stdout.strip()!=BRANCH:raise PatchError("wrong_branch")
 head=git(r,"rev-parse","HEAD").stdout.strip()
 if head!=PARENT:raise PatchError(f"wrong_parent:{head}")
 d=json.loads((r/PREREQ).read_text(encoding="utf-8"))
 if (d.get("stage"),d.get("status"),d.get("conclusion"))!=("21.9.2b","PASS","GO_TO_IMPLEMENTATION"):raise PatchError("invalid_prerequisite")
 if d.get("implementation_authorized") is not True or d.get("runtime_integration_authorized") is not False or d.get("summary",{}).get("remaining_unresolved_contracts")!=0:raise PatchError("invalid_boundary")
 matrix=d.get("exact_gold_matrix",{})
 if matrix.get("count")!=10 or matrix.get("minimum_level")!=2 or matrix.get("maximum_level")!=11 or matrix.get("gaps")!=[]:raise PatchError("invalid_exact_matrix_contract")
 if git(r,"diff","--cached","--name-only").stdout.strip():raise PatchError("pre_staged_changes")
 dirty=set()
 for line in git(r,"status","--porcelain","--untracked-files=all").stdout.splitlines():
  x=line[3:].strip().replace("\\","/").split(" -> ",1)[-1]
  if x!=SELF.as_posix() and x not in ALLOWED_DIRTY:dirty.add(x)
 if dirty:raise PatchError(f"unexpected_dirty:{sorted(dirty)}")
 return d
def backup(r):
 b=r/"backup"/f"stage_21_9_2c_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}";b.mkdir(parents=True);state={}
 for rel in TARGETS:
  p=r/rel;state[rel.as_posix()]=p.exists()
  if p.exists():q=b/rel;q.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,q)
 return b,state
def restore(r,b,state):
 git(r,"reset","--mixed",check=False);done=[]
 if b:
  for rel in TARGETS:
   p=r/rel;q=b/rel
   if state.get(rel.as_posix()) and q.exists():p.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(q,p);done.append(rel.as_posix())
   elif p.exists() and rel!=SELF:p.unlink();done.append("removed:"+rel.as_posix())
 return done
def clean(r):
 for base in (r/"rom_v2",r/"tests_v2",r/"tests",r/"tools"):
  if not base.exists():continue
  for p in base.rglob("*.pyc"):p.unlink(missing_ok=True)
  for d in sorted(base.rglob("__pycache__"),key=lambda x:len(x.parts),reverse=True):
   try:d.rmdir()
   except OSError:pass

def domain_text(values,source_hash):
 matrix=repr({int(k):float(v) for k,v in values.items()})
 return f'''"""Pure exact level-up reward calculation for ROM V2.

Source contract hash: {source_hash}. No persistence, settlement, presentation,
runtime, Telegram, fallback formula, or extrapolation is implemented here.
"""
from __future__ import annotations
from types import MappingProxyType
from typing import Any, Mapping

_LEVEL_UP_GOLD_BY_REACHED_LEVEL = {matrix}
LEVEL_UP_GOLD_BY_REACHED_LEVEL: Mapping[int,float] = MappingProxyType(_LEVEL_UP_GOLD_BY_REACHED_LEVEL)
CONFIGURED_MIN_REACHED_LEVEL=min(LEVEL_UP_GOLD_BY_REACHED_LEVEL)
CONFIGURED_MAX_REACHED_LEVEL=max(LEVEL_UP_GOLD_BY_REACHED_LEVEL)

def calculate_v2_level_up_reward(reached_level: int) -> dict[str,Any]:
    """Return the exact V1 reward row and fail closed if gold is unconfigured."""
    level=int(reached_level)
    if level not in LEVEL_UP_GOLD_BY_REACHED_LEVEL:
        raise ValueError(f"Level-up gold is not configured for reached level {{level}}. Add an audited combat-income matrix before enabling this level.")
    milestone=level%5==0
    return {{"reached_level":level,"gold":LEVEL_UP_GOLD_BY_REACHED_LEVEL[level],"small_health_potions":3,"small_mana_potions":1,"refine_stones":4 if milestone else 2,"medium_health_potions":2 if milestone else 0,"medium_mana_potions":1 if milestone else 0,"crystals":0,"milestone":milestone}}

def calculate_v2_level_up_rewards(old_level: int,new_level: int) -> dict[str,Any]:
    """Aggregate every reached level in ascending V1 order."""
    old_level=int(old_level);new_level=int(new_level)
    levels=list(range(old_level+1,new_level+1)) if new_level>old_level else []
    rows=[calculate_v2_level_up_reward(level) for level in levels]
    return {{"old_level":old_level,"new_level":new_level,"reached_levels":levels,"milestone_levels":[row["reached_level"] for row in rows if row["milestone"]],"gold":sum(row["gold"] for row in rows),"small_health_potions":sum(row["small_health_potions"] for row in rows),"small_mana_potions":sum(row["small_mana_potions"] for row in rows),"refine_stones":sum(row["refine_stones"] for row in rows),"medium_health_potions":sum(row["medium_health_potions"] for row in rows),"medium_mana_potions":sum(row["medium_mana_potions"] for row in rows),"crystals":sum(row["crystals"] for row in rows),"rows":rows}}
'''
def tests():return '''import unittest
from rom_v2.domain.level_up_gold import *

class LevelUpGoldTests(unittest.TestCase):
 def test_exact_matrix(self):
  self.assertEqual(dict(LEVEL_UP_GOLD_BY_REACHED_LEVEL),{2:0.45,3:1.43,4:4.30,5:11.98,6:34.40,7:69.58,8:130.73,9:255.74,10:479.19,11:881.25})
 def test_range_contiguous(self):self.assertEqual((CONFIGURED_MIN_REACHED_LEVEL,CONFIGURED_MAX_REACHED_LEVEL,len(LEVEL_UP_GOLD_BY_REACHED_LEVEL)),(2,11,10))
 def test_single_non_milestone_shape(self):
  row=calculate_v2_level_up_reward(2);self.assertEqual(row,{"reached_level":2,"gold":0.45,"small_health_potions":3,"small_mana_potions":1,"refine_stones":2,"medium_health_potions":0,"medium_mana_potions":0,"crystals":0,"milestone":False})
 def test_single_milestone_shape(self):
  row=calculate_v2_level_up_reward(5);self.assertTrue(row["milestone"]);self.assertEqual((row["refine_stones"],row["medium_health_potions"],row["medium_mana_potions"]),(4,2,1))
 def test_unconfigured_fails_closed(self):
  for level in (1,12,50):
   with self.assertRaises(ValueError):calculate_v2_level_up_reward(level)
 def test_multi_level_ascending_and_exact_gold(self):
  result=calculate_v2_level_up_rewards(1,5);self.assertEqual(result["reached_levels"],[2,3,4,5]);self.assertEqual(result["milestone_levels"],[5]);self.assertAlmostEqual(result["gold"],18.16,places=9)
 def test_reverse_and_equal_are_empty(self):
  for old,new in ((5,5),(5,4)):
   result=calculate_v2_level_up_rewards(old,new);self.assertEqual(result["rows"],[]);self.assertEqual(result["gold"],0)
 def test_matrix_immutable(self):
  with self.assertRaises(TypeError):LEVEL_UP_GOLD_BY_REACHED_LEVEL[2]=999
if __name__=="__main__":unittest.main()
'''
def tool():return '''#!/usr/bin/env python3
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from rom_v2.domain.level_up_gold import calculate_v2_level_up_rewards
result=calculate_v2_level_up_rewards(1,3)
assert result["reached_levels"]==[2,3] and abs(result["gold"]-1.88)<1e-9
print("STAGE_21_9_2C_LEVEL_UP_GOLD_SMOKE: PASS")
'''
def main():
 r=Path.cwd().resolve();b=None;state={};before=protected(r)
 try:
  contract=preflight(r);print("[1/10] [PASS] Stage 21.9.2b zero-unresolved implementation prerequisite verified.");print("[2/10] [PASS] Branch, exact parent, dirty allowlist and clean index verified.")
  b,state=backup(r);print("[3/10] [PASS] Fail-safe backup created before production mutation.")
  values=contract["exact_gold_matrix"]["values"];write(r,DOMAIN,domain_text(values,contract["exact_gold_matrix"]["source_sha256"]));write(r,TEST,tests());write(r,TOOL,tool());print("[4/10] [PASS] Pure exact V2 level-up-gold API implemented.")
  for rel in (SELF,DOMAIN,TEST,TOOL):ast.parse((r/rel).read_text(encoding="utf-8"),filename=rel.as_posix())
  p=run([sys.executable,"-m","py_compile",DOMAIN.as_posix(),TEST.as_posix(),TOOL.as_posix()],r,False)
  if p.returncode:raise PatchError(f"py_compile_failed:{p.stderr}")
  print("[5/10] [PASS] Python compile gate passed.")
  p=run([sys.executable,"-m","unittest",TEST.as_posix(),"-v"],r,False)
  if p.returncode:raise PatchError(f"targeted_tests_failed:{p.stdout}:{p.stderr}")
  print("[6/10] [PASS] Exact values, fail-closed, aggregation and result-shape tests passed.")
  p=run([sys.executable,TOOL.as_posix()],r,False)
  if p.returncode or "SMOKE: PASS" not in p.stdout:raise PatchError(f"smoke_failed:{p.stdout}:{p.stderr}")
  print("[7/10] [PASS] Level-up-gold smoke check passed.")
  clean(r);env=os.environ.copy();env["PYTHONDONTWRITEBYTECODE"]="1";env["PYTHONHASHSEED"]="0";p=run([sys.executable,"-B","tools/run_v2_ci.py"],r,False,env)
  if p.returncode:raise PatchError(f"canonical_v2_ci_failed:{p.stdout}:{p.stderr}")
  if protected(r)!=before:raise PatchError("protected_runtime_changed")
  prod={line[3:].strip().replace("\\","/") for line in git(r,"status","--porcelain","--untracked-files=all").stdout.splitlines() if line[3:].strip().replace("\\","/").startswith("rom_v2/")}
  if prod!={DOMAIN.as_posix()}:raise PatchError(f"unauthorized_production_scope:{sorted(prod)}")
  print("[8/10] [PASS] Canonical V2 CI passed; only authorized production module changed.")
  out={"schema_version":1,"stage":STAGE,"status":"PASS","conclusion":"API_READY","generated_at_utc":datetime.now(timezone.utc).isoformat(),"source_contract":PREREQ.as_posix(),"implementation":DOMAIN.as_posix(),"tests":TEST.as_posix(),"exact_gold_matrix":values,"implemented":["exact_single_level_reward","fail_closed_unconfigured_level","ascending_multi_level_aggregation","source_faithful_result_shape"],"not_connected":["sqlite","settlement","repository_uow","runtime","telegram","presentation"],"manual_game_check":"NOT_REQUIRED","database_opened":False,"v1_wal_shm_manipulated":False}
  write(r,REPORT,json.dumps(out,ensure_ascii=False,indent=2));write(r,DOC,"""# Stage 21.9.2c - Level-up gold implementation

- Status: **PASS**
- Conclusion: **API_READY**
- Runtime integration: **NOT_CONNECTED**
- Production persistence: **NOT_CONNECTED**
- Manual game check: **NOT_REQUIRED**

Pure V2 API now owns the exact reached-level gold matrix for levels 2-11, fail-closed unconfigured-level behavior, ascending multi-level aggregation, and the source-faithful reward result shape. SQLite settlement, runtime, Telegram, and presentation remain disconnected.
""");print("[9/10] [PASS] Machine report and Markdown documentation written.")
  expected={x.as_posix() for x in TARGETS};git(r,"add","--",DOMAIN.as_posix(),TEST.as_posix(),TOOL.as_posix());git(r,"add","-f","--",SELF.as_posix(),REPORT.as_posix(),DOC.as_posix());staged={x.strip().replace("\\","/") for x in git(r,"diff","--cached","--name-only").stdout.splitlines() if x.strip()}
  if staged!=expected:raise PatchError(f"staging_mismatch:{sorted(staged)}")
  p=git(r,"commit","-m","Stage 21.9.2c: implement exact level-up gold",check=False)
  if p.returncode:raise PatchError(f"commit_failed:{p.stdout}:{p.stderr}")
  commit=git(r,"rev-parse","HEAD").stdout.strip();changed={x.strip().replace("\\","/") for x in git(r,"diff-tree","--no-commit-id","--name-only","-r",commit).stdout.splitlines() if x.strip()}
  if changed!=expected:raise PatchError(f"commit_scope:{sorted(changed)}")
  (r/FAILURE).unlink(missing_ok=True);print(f"[10/10] [PASS] Exact level-up-gold implementation committed: {commit}");print("CONCLUSION: API_READY");print("PATCH STATUS: PASS");print(f"GIT COMMIT STATUS: PASS ({commit})");print("RUNTIME INTEGRATION: NOT_CONNECTED");print("PRODUCTION PERSISTENCE: NOT_CONNECTED");print("MANUAL GAME CHECK: NOT_REQUIRED");print("FAIL-SAFE ROLLBACK: ARMED");return 0
 except Exception as e:
  restored=restore(r,b,state);recovery=run([sys.executable,"-m","compileall","-q","rom_v2"],r,False);f={"schema_version":1,"stage":STAGE,"status":"FAIL_ROLLED_BACK","failed_at_utc":datetime.now(timezone.utc).isoformat(),"reason":str(e),"restored_files":restored,"recovery_compile_returncode":recovery.returncode,"main_py_allowed_after_recovery":recovery.returncode==0,"database_opened":False,"v1_wal_shm_manipulated":False};p=r/FAILURE;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(f,ensure_ascii=False,indent=2)+"\n",encoding="utf-8");print(f"[10/10] [FAIL] {e}; rollback: FAIL_ROLLED_BACK");return 1
if __name__=="__main__":raise SystemExit(main())
