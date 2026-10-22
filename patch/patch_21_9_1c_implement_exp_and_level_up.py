#!/usr/bin/env python3
"""ROM Stage 21.9.1c: implement the pure V2 EXP and level-up API.

The patch copies accepted V1 progression tables through static AST literals and
implements the source-faithful pure threshold/award transition. It does not
import V1, open SQLite, mutate players, or connect runtime/Telegram adapters.
"""
from __future__ import annotations
import ast, hashlib, json, os, shutil, subprocess, sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

STAGE="21.9.1c";BRANCH="rewrite/rom-v2";PARENT="e22ab5a6bd49d67921e72e3257f25d3a9b00741f"
PREREQ=Path("reports/stage_21_9_1b_resolved_exp_and_level_up_parity.json")
DOMAIN=Path("rom_v2/domain/player_progression.py");TEST=Path("tests_v2/test_player_progression.py")
TOOL=Path("tools/check_stage_21_9_1c_exp_and_level_up.py")
REPORT=Path("reports/stage_21_9_1c_exp_and_level_up_implementation.json")
DOC=Path("MD/STAGE_21_9_1C_EXP_AND_LEVEL_UP_IMPLEMENTATION.md")
FAILURE=Path("reports/stage_21_9_1c_failure_rollback.json");SELF=Path("patch/patch_21_9_1c_implement_exp_and_level_up.py")
TARGETS=(SELF,DOMAIN,TEST,TOOL,REPORT,DOC)
ALLOWED_DIRTY={"ROM_FULL_DUMP.txt",FAILURE.as_posix(),"reports/v2_ci_failure.json","reports/v2_ci_result.json"}
PROTECTED=("game.db","game.db-wal","game.db-shm",".env","rom_v2/.env",".runtime/v2/db/rom_v2.db")
SOURCE=Path("data/player_progression.py")

class PatchError(RuntimeError):pass

def run(cmd,r,check=True,env=None):
 p=subprocess.run(cmd,cwd=r,text=True,capture_output=True,encoding="utf-8",errors="replace",env=env)
 if check and p.returncode:raise PatchError(f"command_failed:{cmd}:{p.stdout[-2000:]}:{p.stderr[-2000:]}")
 return p
def git(r,*a,check=True):return run(["git",*a],r,check)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest() if p.is_file() else None
def protected(r):return {x:sha(r/x) for x in PROTECTED}
def write(r,p,s):q=r/p;q.parent.mkdir(parents=True,exist_ok=True);q.write_text(s.rstrip()+"\n",encoding="utf-8")

def extract_config(r):
 """Extract only literal accepted tables and function hashes from V1 source."""
 p=r/SOURCE;text=p.read_text(encoding="utf-8-sig");tree=ast.parse(text,filename=SOURCE.as_posix());values={};symbols={}
 for node in tree.body:
  names=[];value=None
  if isinstance(node,ast.Assign):names=[x.id for x in node.targets if isinstance(x,ast.Name)];value=node.value
  elif isinstance(node,ast.AnnAssign) and isinstance(node.target,ast.Name):names=[node.target.id];value=node.value
  for name in names:
   if name in {"BASE_EXP_BY_LEVEL","CONDITIONAL_MOBS_TO_NEXT_BY_LEVEL"}:values[name]=ast.literal_eval(value)
  if isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef)) and node.name in {"get_base_exp_for_level","get_exp_to_next_level","apply_exp_award"}:
   source=ast.get_source_segment(text,node) or "";symbols[node.name]=hashlib.sha256(source.encode()).hexdigest()
 if set(values)!={"BASE_EXP_BY_LEVEL","CONDITIONAL_MOBS_TO_NEXT_BY_LEVEL"} or len(values["BASE_EXP_BY_LEVEL"])!=50 or len(values["CONDITIONAL_MOBS_TO_NEXT_BY_LEVEL"])!=50:raise PatchError("invalid_v1_progression_tables")
 if len(symbols)!=3:raise PatchError("missing_v1_progression_symbols")
 return values,symbols,sha(p)

def preflight(r):
 if git(r,"branch","--show-current").stdout.strip()!=BRANCH:raise PatchError("wrong_branch")
 head=git(r,"rev-parse","HEAD").stdout.strip()
 if head!=PARENT:raise PatchError(f"wrong_exact_parent:{head}")
 d=json.loads((r/PREREQ).read_text(encoding="utf-8"))
 if (d.get("stage"),d.get("status"),d.get("conclusion"))!=("21.9.1b","PASS","GO_TO_IMPLEMENTATION"):raise PatchError("invalid_prerequisite")
 if d.get("implementation_authorized") is not True or d.get("runtime_integration_authorized") is not False or d.get("summary",{}).get("remaining_unresolved_contracts")!=0:raise PatchError("invalid_implementation_boundary")
 if git(r,"diff","--cached","--name-only").stdout.strip():raise PatchError("pre_staged_changes")
 dirty=set()
 for line in git(r,"status","--porcelain","--untracked-files=all").stdout.splitlines():
  x=line[3:].strip().replace("\\","/");x=x.split(" -> ",1)[-1]
  if x!=SELF.as_posix() and x not in ALLOWED_DIRTY:dirty.add(x)
 if dirty:raise PatchError(f"unexpected_dirty:{sorted(dirty)}")

def backup(r):
 b=r/"backup"/f"stage_21_9_1c_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}";b.mkdir(parents=True);state={}
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

def clean_bytecode(r):
 for base in (r/"rom_v2",r/"tests_v2",r/"tests",r/"tools"):
  if not base.exists():continue
  for p in base.rglob("*.pyc"):p.unlink(missing_ok=True)
  for d in sorted(base.rglob("__pycache__"),key=lambda x:len(x.parts),reverse=True):
   try:d.rmdir()
   except OSError:pass

def domain_text(values,source_hash,symbols):
 base=repr(dict(sorted(values["BASE_EXP_BY_LEVEL"].items())));mobs=repr(dict(sorted(values["CONDITIONAL_MOBS_TO_NEXT_BY_LEVEL"].items())))
 return f'''"""Pure source-faithful player progression for ROM V2.

Generated from accepted V1 configuration hash {source_hash}. No persistence,
runtime, Telegram, reward delivery, or universal idempotency behavior lives here.
"""
from __future__ import annotations
from dataclasses import dataclass
from types import MappingProxyType
from typing import Mapping

_BASE_EXP_BY_LEVEL = {base}
_CONDITIONAL_MOBS_TO_NEXT_BY_LEVEL = {mobs}
BASE_EXP_BY_LEVEL: Mapping[int,int] = MappingProxyType(_BASE_EXP_BY_LEVEL)
CONDITIONAL_MOBS_TO_NEXT_BY_LEVEL: Mapping[int,int] = MappingProxyType(_CONDITIONAL_MOBS_TO_NEXT_BY_LEVEL)
CONFIGURED_MIN_LEVEL = min(BASE_EXP_BY_LEVEL)
CONFIGURED_MAX_LEVEL = max(BASE_EXP_BY_LEVEL)
V1_SOURCE_SHA256 = "{source_hash}"
V1_SYMBOL_SHA256 = {repr(symbols)}

@dataclass(frozen=True, slots=True)
class PlayerProgressionResult:
    level: int
    exp: int
    exp_to_next: int
    level_ups: int
    unapplied_exp: int

    @property
    def reached_levels(self) -> tuple[int, ...]:
        return tuple(range(self.level-self.level_ups+1,self.level+1)) if self.level_ups else ()

    @property
    def attribute_points_awarded(self) -> int:
        """V1 transaction contract awards five points per gained level."""
        return self.level_ups*5

def get_player_base_exp_for_level(level: int) -> int:
    level=int(level)
    if level in BASE_EXP_BY_LEVEL:return BASE_EXP_BY_LEVEL[level]
    if level>CONFIGURED_MAX_LEVEL:
        return int(BASE_EXP_BY_LEVEL[CONFIGURED_MAX_LEVEL]*(1.12**(level-CONFIGURED_MAX_LEVEL)))
    return BASE_EXP_BY_LEVEL[CONFIGURED_MIN_LEVEL]

def get_player_exp_to_next_level(level: int) -> int:
    level=int(level);base=get_player_base_exp_for_level(level)
    if level in CONDITIONAL_MOBS_TO_NEXT_BY_LEVEL:
        return int(base*CONDITIONAL_MOBS_TO_NEXT_BY_LEVEL[level])
    mobs_required=int(CONDITIONAL_MOBS_TO_NEXT_BY_LEVEL[CONFIGURED_MAX_LEVEL]*(1.10**(level-CONFIGURED_MAX_LEVEL)))
    return int(base*mobs_required)

def apply_player_exp_award(level: int, exp: int, amount: int, level_cap: int|None=None) -> PlayerProgressionResult:
    """Mirror V1 residual, multi-level, cap and unapplied-EXP semantics."""
    level,exp,amount=int(level),int(exp),int(amount);level_ups=0
    while amount>0:
        if level_cap is not None and level>=int(level_cap):break
        required=get_player_exp_to_next_level(level);missing=required-exp
        if amount<missing:exp+=amount;amount=0
        else:amount-=missing;exp=0;level+=1;level_ups+=1
    return PlayerProgressionResult(level,exp,get_player_exp_to_next_level(level),level_ups,amount)
'''

def test_text():return '''import unittest
from rom_v2.domain.player_progression import *

class PlayerProgressionTests(unittest.TestCase):
 def test_tables_cover_1_to_50(self):
  self.assertEqual((min(BASE_EXP_BY_LEVEL),max(BASE_EXP_BY_LEVEL),len(BASE_EXP_BY_LEVEL)),(1,50,50))
  self.assertEqual(len(CONDITIONAL_MOBS_TO_NEXT_BY_LEVEL),50)
 def test_known_thresholds(self):
  self.assertEqual(get_player_exp_to_next_level(1),500)
  self.assertEqual(get_player_base_exp_for_level(15),120)
  self.assertEqual(get_player_base_exp_for_level(30),600)
 def test_below_threshold(self):
  result=apply_player_exp_award(1,0,499,30);self.assertEqual((result.level,result.exp,result.level_ups,result.unapplied_exp),(1,499,0,0))
 def test_exact_threshold_and_residual(self):
  result=apply_player_exp_award(1,0,505,30);self.assertEqual((result.level,result.exp,result.level_ups),(2,5,1))
 def test_multi_level(self):
  amount=get_player_exp_to_next_level(1)+get_player_exp_to_next_level(2)+7
  result=apply_player_exp_award(1,0,amount,30);self.assertEqual((result.level,result.exp,result.level_ups,result.reached_levels),(3,7,2,(2,3)))
  self.assertEqual(result.attribute_points_awarded,10)
 def test_cap_returns_unapplied(self):
  result=apply_player_exp_award(30,4,500,30);self.assertEqual((result.level,result.exp,result.unapplied_exp),(30,4,500))
 def test_zero_and_negative_match_v1(self):
  for amount in (0,-5):
   result=apply_player_exp_award(2,9,amount,30);self.assertEqual((result.level,result.exp,result.level_ups,result.unapplied_exp),(2,9,0,amount))
 def test_configuration_is_immutable(self):
  with self.assertRaises(TypeError):BASE_EXP_BY_LEVEL[1]=999

if __name__=="__main__":unittest.main()
'''
def tool_text():return '''#!/usr/bin/env python3
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from rom_v2.domain.player_progression import apply_player_exp_award,get_player_exp_to_next_level
amount=get_player_exp_to_next_level(1)+3
result=apply_player_exp_award(1,0,amount,30)
assert (result.level,result.exp,result.level_ups)==(2,3,1)
print("STAGE_21_9_1C_EXP_LEVEL_UP_SMOKE: PASS")
'''

def main():
 r=Path.cwd().resolve();b=None;state={};before=protected(r)
 try:
  preflight(r);print("[1/10] [PASS] Stage 21.9.1b zero-unresolved implementation prerequisite verified.")
  print("[2/10] [PASS] Branch, exact parent, dirty allowlist and clean index verified.")
  b,state=backup(r);print("[3/10] [PASS] Fail-safe backup created before production mutation.")
  values,symbols,source_hash=extract_config(r);write(r,DOMAIN,domain_text(values,source_hash,symbols));write(r,TEST,test_text());write(r,TOOL,tool_text())
  print("[4/10] [PASS] Pure source-faithful V2 EXP and level-up API implemented.")
  for rel in (SELF,DOMAIN,TEST,TOOL):ast.parse((r/rel).read_text(encoding="utf-8"),filename=rel.as_posix())
  cp=run([sys.executable,"-m","py_compile",DOMAIN.as_posix(),TEST.as_posix(),TOOL.as_posix()],r,False)
  if cp.returncode:raise PatchError(f"py_compile_failed:{cp.stderr}")
  print("[5/10] [PASS] Python compile gate passed.")
  tests=run([sys.executable,"-m","unittest",TEST.as_posix(),"-v"],r,False)
  if tests.returncode:raise PatchError(f"targeted_tests_failed:{tests.stdout}:{tests.stderr}")
  print("[6/10] [PASS] Curve, residual, multi-level, cap, points and boundary tests passed.")
  smoke=run([sys.executable,TOOL.as_posix()],r,False)
  if smoke.returncode or "SMOKE: PASS" not in smoke.stdout:raise PatchError(f"smoke_failed:{smoke.stdout}:{smoke.stderr}")
  print("[7/10] [PASS] EXP and level-up smoke check passed.")
  clean_bytecode(r);env=os.environ.copy();env["PYTHONDONTWRITEBYTECODE"]="1";env["PYTHONHASHSEED"]="0"
  ci=run([sys.executable,"-B","tools/run_v2_ci.py"],r,False,env)
  if ci.returncode:raise PatchError(f"canonical_v2_ci_failed:{ci.stdout}:{ci.stderr}")
  if protected(r)!=before:raise PatchError("protected_runtime_changed")
  prod={line[3:].strip().replace("\\","/") for line in git(r,"status","--porcelain","--untracked-files=all").stdout.splitlines() if line[3:].strip().replace("\\","/").startswith("rom_v2/")}
  if prod!={DOMAIN.as_posix()}:raise PatchError(f"unauthorized_production_scope:{sorted(prod)}")
  print("[8/10] [PASS] Canonical V2 CI passed; only authorized production module changed.")
  payload={"schema_version":1,"stage":STAGE,"status":"PASS","conclusion":"API_READY","generated_at_utc":datetime.now(timezone.utc).isoformat(),"source_v1":SOURCE.as_posix(),"source_v1_sha256":source_hash,"implementation":DOMAIN.as_posix(),"tests":TEST.as_posix(),"configured_levels":[1,50],"implemented":["thresholds","residual_exp","multi_level","explicit_level_cap","unapplied_exp","reached_levels","attribute_points_projection"],"not_connected":["sqlite","repository_uow","runtime","telegram","reward_delivery","profile"],"manual_game_check":"NOT_REQUIRED","database_opened":False,"v1_wal_shm_manipulated":False}
  write(r,REPORT,json.dumps(payload,ensure_ascii=False,indent=2));write(r,DOC,"""# Stage 21.9.1c - EXP and level-up implementation

- Status: **PASS**
- Conclusion: **API_READY**
- Runtime integration: **NOT_CONNECTED**
- Production persistence: **NOT_CONNECTED**
- Manual game check: **NOT_REQUIRED**

## Implemented

Pure immutable V2 progression provides the accepted 1-50 configuration, EXP thresholds, residual EXP, multi-level transitions, explicit cap handling, unapplied EXP, reached levels, and the V1 projection of five attribute points per gained level.

## Excluded

No SQLite, repository/UoW, Telegram, runtime reward delivery, profile presentation, universal idempotency ledger, or mutation of a player is connected.
""")
  print("[9/10] [PASS] Machine report and Markdown documentation written.")
  expected={x.as_posix() for x in TARGETS};git(r,"add","--",DOMAIN.as_posix(),TEST.as_posix(),TOOL.as_posix());git(r,"add","-f","--",SELF.as_posix(),REPORT.as_posix(),DOC.as_posix())
  staged={x.strip().replace("\\","/") for x in git(r,"diff","--cached","--name-only").stdout.splitlines() if x.strip()}
  if staged!=expected:raise PatchError(f"staging_mismatch:{sorted(staged)}")
  cp=git(r,"commit","-m","Stage 21.9.1c: implement EXP and level-up domain",check=False)
  if cp.returncode:raise PatchError(f"commit_failed:{cp.stdout}:{cp.stderr}")
  commit=git(r,"rev-parse","HEAD").stdout.strip();changed={x.strip().replace("\\","/") for x in git(r,"diff-tree","--no-commit-id","--name-only","-r",commit).stdout.splitlines() if x.strip()}
  if changed!=expected:raise PatchError(f"commit_scope:{sorted(changed)}")
  (r/FAILURE).unlink(missing_ok=True);print(f"[10/10] [PASS] EXP and level-up implementation committed: {commit}");print("CONCLUSION: API_READY");print("PATCH STATUS: PASS");print(f"GIT COMMIT STATUS: PASS ({commit})");print("RUNTIME INTEGRATION: NOT_CONNECTED");print("PRODUCTION PERSISTENCE: NOT_CONNECTED");print("MANUAL GAME CHECK: NOT_REQUIRED");print("FAIL-SAFE ROLLBACK: ARMED");return 0
 except Exception as exc:
  restored=restore(r,b,state);recovery=run([sys.executable,"-m","compileall","-q","rom_v2"],r,False);failure={"schema_version":1,"stage":STAGE,"status":"FAIL_ROLLED_BACK","failed_at_utc":datetime.now(timezone.utc).isoformat(),"reason":str(exc),"restored_files":restored,"recovery_compile_returncode":recovery.returncode,"main_py_allowed_after_recovery":recovery.returncode==0,"database_opened":False,"v1_wal_shm_manipulated":False};p=r/FAILURE;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(failure,ensure_ascii=False,indent=2)+"\n",encoding="utf-8");print(f"[10/10] [FAIL] {exc}; rollback: FAIL_ROLLED_BACK");return 1
if __name__=="__main__":raise SystemExit(main())
