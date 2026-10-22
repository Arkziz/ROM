#!/usr/bin/env python3
"""ROM Stage 21.9.5c: implement pure V2 Premium combat modifiers."""
from __future__ import annotations
import ast, json, os, shutil, subprocess, sys
from datetime import datetime, timezone
from pathlib import Path

STAGE="21.9.5c";BRANCH="rewrite/rom-v2";PARENT="e3b01a53ca92d03fca491edd3b89afdc74b1c556"
PREREQ=Path("reports/stage_21_9_5b_resolved_reward_settlement_parity.json")
APP=Path("rom_v2/domain/premium_combat.py");TEST=Path("tests_v2/test_premium_combat.py")
TOOL=Path("tools/check_stage_21_9_5c_premium_combat.py")
REPORT=Path("reports/stage_21_9_5c_premium_combat_modifiers_implementation.json")
DOC=Path("MD/STAGE_21_9_5C_PREMIUM_COMBAT_MODIFIERS_IMPLEMENTATION.md")
FAILURE=Path("reports/stage_21_9_5c_failure_rollback.json");SELF=Path("patch/patch_21_9_5c_implement_premium_combat_modifiers.py")
TARGETS=(SELF,APP,TEST,TOOL,REPORT,DOC)
ALLOWED_DIRTY={"ROM_FULL_DUMP.txt",FAILURE.as_posix(),"reports/v2_ci_failure.json","reports/v2_ci_result.json"}
PROTECTED=("game.db","game.db-wal","game.db-shm",".env","rom_v2/.env",".runtime/v2/db/rom_v2.db")

class PatchError(RuntimeError):pass
def run(c,r,check=True,env=None):
 p=subprocess.run(c,cwd=r,text=True,capture_output=True,encoding="utf-8",errors="replace",env=env)
 if check and p.returncode:raise PatchError(f"command_failed:{c}:{p.stdout[-2000:]}:{p.stderr[-2000:]}")
 return p
def git(r,*a,check=True):return run(["git",*a],r,check)
def sha(p):
 import hashlib
 return hashlib.sha256(p.read_bytes()).hexdigest() if p.is_file() else None
def protected(r):return {x:sha(r/x) for x in PROTECTED}
def write(r,p,s):q=r/p;q.parent.mkdir(parents=True,exist_ok=True);q.write_text(s.rstrip()+"\n",encoding="utf-8")
def preflight(r):
 if git(r,"branch","--show-current").stdout.strip()!=BRANCH:raise PatchError("wrong_branch")
 head=git(r,"rev-parse","HEAD").stdout.strip()
 if head!=PARENT:raise PatchError(f"wrong_exact_parent:{head}")
 d=json.loads((r/PREREQ).read_text(encoding="utf-8"))
 if (d.get("stage"),d.get("status"),d.get("conclusion")) != ("21.9.5b","PASS","GO_TO_IMPLEMENTATION"):raise PatchError("invalid_prerequisite")
 if d.get("implementation_authorized") is not True or d.get("runtime_integration_authorized") is not False or d.get("production_persistence_authorized") is not False:raise PatchError("invalid_authorization_boundary")
 if d.get("summary",{}).get("remaining_unresolved_contracts") != 0:raise PatchError("unresolved_contracts_remain")
 c=d.get("v2_premium_combat_contract",{})
 if c.get("service")!="PremiumCombatModifier" or c.get("active_multiplier")!="1.25" or c.get("inactive_multiplier")!="1.0" or c.get("loot_effect") is not False or c.get("non_combat_effect") is not False or c.get("clock_inside_modifier") is not False:raise PatchError("invalid_premium_combat_contract")
 if git(r,"diff","--cached","--name-only").stdout.strip():raise PatchError("pre_staged_changes")
 dirty=set()
 for line in git(r,"status","--porcelain","--untracked-files=all").stdout.splitlines():
  x=line[3:].strip().replace("\\","/").split(" -> ",1)[-1]
  if x!=SELF.as_posix() and x not in ALLOWED_DIRTY:dirty.add(x)
 if dirty:raise PatchError(f"unexpected_dirty:{sorted(dirty)}")
 return d

def backup(r):
 b=r/"backup"/f"stage_21_9_5c_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}";b.mkdir(parents=True);state={}
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

def app_text():return '''"""Pure Premium combat reward modifier.

This module applies the source-faithful Premium modifier only to finalized
combat EXP and combat gold. It owns no clock, persistence, loot, presentation,
runtime wiring, or non-combat reward policy.
"""
from __future__ import annotations
from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_EVEN

ACTIVE_MULTIPLIER = Decimal("1.25")
INACTIVE_MULTIPLIER = Decimal("1.0")
CENT = Decimal("0.01")

@dataclass(frozen=True, slots=True)
class PremiumCombatSnapshot:
    active: bool

@dataclass(frozen=True, slots=True)
class PremiumCombatBreakdown:
    premium_active: bool
    exp_base: int
    exp_bonus: int
    exp_final: int
    gold_base: Decimal
    gold_bonus: Decimal
    gold_final: Decimal
    multiplier: Decimal

class PremiumCombatModifier:
    """Apply Premium exactly once to combat-only rewards."""

    def apply(self, *, base_combat_exp: int, base_combat_gold: Decimal,
              premium_active_snapshot: PremiumCombatSnapshot) -> PremiumCombatBreakdown:
        exp_base = max(0, int(base_combat_exp))
        gold_base = self._money(max(Decimal("0"), Decimal(base_combat_gold)))
        multiplier = ACTIVE_MULTIPLIER if premium_active_snapshot.active else INACTIVE_MULTIPLIER
        exp_bonus = (exp_base * 25) // 100 if premium_active_snapshot.active else 0
        exp_final = exp_base + exp_bonus
        gold_final = self._money(gold_base * multiplier)
        gold_bonus = self._money(gold_final - gold_base)
        return PremiumCombatBreakdown(
            premium_active=premium_active_snapshot.active,
            exp_base=exp_base, exp_bonus=exp_bonus, exp_final=exp_final,
            gold_base=gold_base, gold_bonus=gold_bonus, gold_final=gold_final,
            multiplier=multiplier,
        )

    @staticmethod
    def _money(value: Decimal) -> Decimal:
        return value.quantize(CENT, rounding=ROUND_HALF_EVEN)
'''

def test_text():return '''import unittest
from decimal import Decimal
from rom_v2.domain.premium_combat import *

class PremiumCombatModifierTests(unittest.TestCase):
 def test_active_exact_25_percent(self):
  out=PremiumCombatModifier().apply(base_combat_exp=101,base_combat_gold=Decimal("10.01"),premium_active_snapshot=PremiumCombatSnapshot(True))
  self.assertEqual((out.exp_base,out.exp_bonus,out.exp_final),(101,25,126))
  self.assertEqual((out.gold_base,out.gold_bonus,out.gold_final),(Decimal("10.01"),Decimal("2.50"),Decimal("12.51")))
  self.assertEqual(out.multiplier,Decimal("1.25"))
 def test_inactive_is_identity(self):
  out=PremiumCombatModifier().apply(base_combat_exp=101,base_combat_gold=Decimal("10.01"),premium_active_snapshot=PremiumCombatSnapshot(False))
  self.assertEqual((out.exp_bonus,out.exp_final),(0,101));self.assertEqual((out.gold_bonus,out.gold_final),(Decimal("0.00"),Decimal("10.01")))
 def test_exp_rounds_down(self):
  out=PremiumCombatModifier().apply(base_combat_exp=3,base_combat_gold=Decimal("0"),premium_active_snapshot=PremiumCombatSnapshot(True))
  self.assertEqual((out.exp_bonus,out.exp_final),(0,3))
 def test_gold_rounding_boundary(self):
  out=PremiumCombatModifier().apply(base_combat_exp=0,base_combat_gold=Decimal("0.02"),premium_active_snapshot=PremiumCombatSnapshot(True))
  self.assertEqual(out.gold_final,Decimal("0.02"));self.assertEqual(out.gold_bonus,Decimal("0.00"))
 def test_negative_inputs_clamp_to_zero(self):
  out=PremiumCombatModifier().apply(base_combat_exp=-9,base_combat_gold=Decimal("-2"),premium_active_snapshot=PremiumCombatSnapshot(True))
  self.assertEqual(out.exp_final,0);self.assertEqual(out.gold_final,Decimal("0.00"))
 def test_api_has_no_clock_loot_or_non_combat_inputs(self):
  names=PremiumCombatModifier.apply.__annotations__
  for forbidden in ("now","expires_at","loot","quest","level_up_gold"):self.assertNotIn(forbidden,names)
 def test_snapshot_is_explicit(self):
  with self.assertRaises(TypeError):PremiumCombatModifier().apply(base_combat_exp=1,base_combat_gold=Decimal("1"))

if __name__=="__main__":unittest.main()
'''

def tool_text():return '''#!/usr/bin/env python3
from decimal import Decimal
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from rom_v2.domain.premium_combat import PremiumCombatModifier, PremiumCombatSnapshot
out=PremiumCombatModifier().apply(base_combat_exp=100,base_combat_gold=Decimal("10.00"),premium_active_snapshot=PremiumCombatSnapshot(True))
assert out.exp_final==125 and out.gold_final==Decimal("12.50")
print("STAGE_21_9_5C_PREMIUM_COMBAT_SMOKE: PASS")
'''

def run_canonical_ci(r, env):
 tmp=r/"reports/.stage_21_9_5c_ci.tmp.json";tmp.unlink(missing_ok=True)
 command=[sys.executable,"-B","tools/run_v2_ci.py","--project-root",str(r),"--json-out",str(tmp)]
 process=run(command,r,False,env)
 data=None
 if tmp.is_file():
  try:data=json.loads(tmp.read_text(encoding="utf-8"))
  except Exception:data=None
  tmp.unlink(missing_ok=True)
 if process.returncode or not isinstance(data,dict) or data.get("status")!="PASS":
  detail=json.dumps(data,ensure_ascii=False) if data is not None else "missing_ci_json"
  raise PatchError(f"canonical_v2_ci_failed:{detail}:{process.stdout[-1200:]}:{process.stderr[-4000:]}")
 return data

def main():
 r=Path.cwd().resolve();b=None;state={};before=protected(r)
 try:
  contract=preflight(r);print("[1/10] [PASS] Stage 21.9.5b zero-unresolved implementation prerequisite verified.");print("[2/10] [PASS] Branch, exact parent, dirty allowlist and clean index verified.")
  b,state=backup(r);print("[3/10] [PASS] Fail-safe backup created before production mutation.")
  write(r,APP,app_text());write(r,TEST,test_text());write(r,TOOL,tool_text());print("[4/10] [PASS] Premium combat modifier, immutable snapshot and breakdown DTOs implemented.")
  for rel in (SELF,APP,TEST,TOOL):ast.parse((r/rel).read_text(encoding="utf-8"),filename=rel.as_posix())
  p=run([sys.executable,"-m","py_compile",APP.as_posix(),TEST.as_posix(),TOOL.as_posix()],r,False)
  if p.returncode:raise PatchError(f"py_compile_failed:{p.stderr}")
  print("[5/10] [PASS] Python compile gate passed.")
  p=run([sys.executable,"-m","unittest",TEST.as_posix(),"-v"],r,False)
  if p.returncode:raise PatchError(f"integration_tests_failed:{p.stdout}:{p.stderr}")
  print("[6/10] [PASS] Active, inactive, arithmetic, rounding, clamp and scope tests passed.")
  p=run([sys.executable,TOOL.as_posix()],r,False)
  if p.returncode or "SMOKE: PASS" not in p.stdout:raise PatchError(f"smoke_failed:{p.stdout}:{p.stderr}")
  print("[7/10] [PASS] Premium combat modifier smoke check passed.")
  clean(r);env=os.environ.copy();env["PYTHONDONTWRITEBYTECODE"]="1";env["PYTHONHASHSEED"]="0";ci_data=run_canonical_ci(r,env)
  if protected(r)!=before:raise PatchError("protected_runtime_changed")
  prod={line[3:].strip().replace("\\","/") for line in git(r,"status","--porcelain","--untracked-files=all").stdout.splitlines() if line[3:].strip().replace("\\","/").startswith("rom_v2/")}
  if prod!={APP.as_posix()}:raise PatchError(f"unauthorized_production_scope:{sorted(prod)}")
  print("[8/10] [PASS] Canonical V2 CI passed; only authorized Premium domain module changed.")
  out={"schema_version":1,"stage":STAGE,"status":"PASS","conclusion":"API_READY","generated_at_utc":datetime.now(timezone.utc).isoformat(),"source_contract":PREREQ.as_posix(),"domain_service":"PremiumCombatModifier","implementation":APP.as_posix(),"tests":TEST.as_posix(),"implemented":["pure_modifier","explicit_active_snapshot","immutable_breakdown","exact_1_25_multiplier","integer_exp_floor","cent_gold_rounding","inactive_identity","negative_clamp","loot_excluded","non_combat_excluded","clock_external"],"not_connected":["sqlite","premium_persistence","reward_settlement_wiring","runtime","telegram","non_combat_rewards","loot"],"runtime_integration":"NOT_CONNECTED","production_persistence":"NOT_CONNECTED","manual_game_check":"NOT_REQUIRED","database_opened":False,"v1_wal_shm_manipulated":False,"verification":{"canonical_v2_ci":ci_data}}
  write(r,REPORT,json.dumps(out,ensure_ascii=False,indent=2));write(r,DOC,"""# Stage 21.9.5c - Premium combat modifiers implementation

- Status: **PASS**
- Conclusion: **API_READY**
- Runtime integration: **NOT_CONNECTED**
- Production persistence: **NOT_CONNECTED**
- Manual game check: **NOT_REQUIRED**

Implemented a pure V2 Premium combat modifier with explicit active snapshot, immutable breakdown, exact 1.25 multiplier, integer EXP floor semantics, cent gold rounding, inactive identity behavior, negative-input clamping, and no internal clock.

SQLite, Premium persistence, reward-settlement wiring, runtime, Telegram, non-combat rewards, and loot remain excluded.
""");print("[9/10] [PASS] Machine report and Markdown documentation written.")
  expected={x.as_posix() for x in TARGETS};git(r,"add","--",APP.as_posix(),TEST.as_posix(),TOOL.as_posix());git(r,"add","-f","--",SELF.as_posix(),REPORT.as_posix(),DOC.as_posix());staged={x.strip().replace("\\","/") for x in git(r,"diff","--cached","--name-only").stdout.splitlines() if x.strip()}
  if staged!=expected:raise PatchError(f"staging_mismatch:{sorted(staged)}")
  p=git(r,"commit","-m","Stage 21.9.5c: implement Premium combat modifiers",check=False)
  if p.returncode:raise PatchError(f"commit_failed:{p.stdout}:{p.stderr}")
  commit=git(r,"rev-parse","HEAD").stdout.strip();changed={x.strip().replace("\\","/") for x in git(r,"diff-tree","--no-commit-id","--name-only","-r",commit).stdout.splitlines() if x.strip()}
  if changed!=expected:raise PatchError(f"commit_scope:{sorted(changed)}")
  (r/FAILURE).unlink(missing_ok=True);print(f"[10/10] [PASS] Premium combat modifiers implementation committed: {commit}");print("CONCLUSION: API_READY");print("PATCH STATUS: PASS");print(f"GIT COMMIT STATUS: PASS ({commit})");print("RUNTIME INTEGRATION: NOT_CONNECTED");print("PRODUCTION PERSISTENCE: NOT_CONNECTED");print("MANUAL GAME CHECK: NOT_REQUIRED");print("FAIL-SAFE ROLLBACK: ARMED");return 0
 except Exception as e:
  restored=restore(r,b,state);recovery=run([sys.executable,"-m","compileall","-q","rom_v2"],r,False);f={"schema_version":1,"stage":STAGE,"status":"FAIL_ROLLED_BACK","failed_at_utc":datetime.now(timezone.utc).isoformat(),"reason":str(e),"restored_files":restored,"recovery_compile_returncode":recovery.returncode,"main_py_allowed_after_recovery":recovery.returncode==0,"database_opened":False,"v1_wal_shm_manipulated":False};p=r/FAILURE;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(f,ensure_ascii=False,indent=2)+"\n",encoding="utf-8");print(f"[10/10] [FAIL] {e}; rollback: FAIL_ROLLED_BACK");return 1
if __name__=="__main__":raise SystemExit(main())
