#!/usr/bin/env python3
"""ROM Stage 21.9.4c: implement the pure V2 reward settlement application service."""
from __future__ import annotations
import ast, json, os, shutil, subprocess, sys
from datetime import datetime, timezone
from pathlib import Path

STAGE="21.9.4c";BRANCH="rewrite/rom-v2";PARENT="6be014dbee4b18fed450389b8a47c4407ef3dd34"
PREREQ=Path("reports/stage_21_9_4b_resolved_reward_settlement_parity.json")
APP=Path("rom_v2/domain/central_loot.py");TEST=Path("tests_v2/test_central_loot.py")
TOOL=Path("tools/check_stage_21_9_4c_reward_settlement.py")
REPORT=Path("reports/stage_21_9_4c_reward_settlement_implementation.json")
DOC=Path("MD/STAGE_21_9_4C_CENTRAL_LOOT_IMPLEMENTATION.md")
FAILURE=Path("reports/stage_21_9_4c_failure_rollback.json");SELF=Path("patch/patch_21_9_4c_implement_central_loot_pipeline.py")
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
 if (d.get("stage"),d.get("status"),d.get("conclusion")) != ("21.9.4b","PASS","GO_TO_IMPLEMENTATION"):raise PatchError("invalid_prerequisite")
 if d.get("implementation_authorized") is not True or d.get("runtime_integration_authorized") is not False or d.get("production_persistence_authorized") is not False:raise PatchError("invalid_authorization_boundary")
 if d.get("summary",{}).get("remaining_unresolved_contracts") != 0:raise PatchError("unresolved_contracts_remain")
 c=d.get("v2_loot_contract",{})
 if c.get("planner")!="CentralLootPlanner" or c.get("rng_injected") is not True or c.get("inventory_mutation") is not False or c.get("premium_input") is not False:raise PatchError("invalid_loot_contract")
 if git(r,"diff","--cached","--name-only").stdout.strip():raise PatchError("pre_staged_changes")
 dirty=set()
 for line in git(r,"status","--porcelain","--untracked-files=all").stdout.splitlines():
  x=line[3:].strip().replace("\\","/").split(" -> ",1)[-1]
  if x!=SELF.as_posix() and x not in ALLOWED_DIRTY:dirty.add(x)
 if dirty:raise PatchError(f"unexpected_dirty:{sorted(dirty)}")
 return d

def backup(r):
 b=r/"backup"/f"stage_21_9_4c_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}";b.mkdir(parents=True);state={}
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

def app_text():return '''\"\"\"Pure deterministic V2 central loot planner.

The planner owns no persistence, inventory mutation, presentation, generated
item identity, event loot, story quest items, Premium rules, or runtime wiring.
\"\"\"
from __future__ import annotations
from dataclasses import dataclass
from typing import Literal, Protocol, Sequence

EnemyClass = Literal["normal", "elite", "boss"]
LootKind = Literal["item", "equipment_request"]

class CentralLootConfigurationError(ValueError):
    \"\"\"Raised before rolling when a rule set violates the planner contract.\"\"\"

class LootRandomSource(Protocol):
    \"\"\"Explicit RNG boundary; implementations must preserve call ordering.\"\"\"
    def random(self) -> float: ...

@dataclass(frozen=True, slots=True)
class LootCandidate:
    key: str
    weight: float = 1.0
    quantity: int = 1
    kind: LootKind = "item"

@dataclass(frozen=True, slots=True)
class LootRule:
    rule_key: str
    source_group: str
    chances: tuple[tuple[EnemyClass, float], ...]
    candidates: tuple[LootCandidate, ...]
    enabled: bool = True

    def chance_for(self, enemy_class: EnemyClass) -> float:
        return dict(self.chances).get(enemy_class, 0.0)

@dataclass(frozen=True, slots=True)
class LootGroup:
    group_key: str
    rules: tuple[LootRule, ...]
    max_per_kill: int | None = None

@dataclass(frozen=True, slots=True)
class CentralLootCommand:
    source_group: str
    key: str
    quantity: int
    kind: LootKind

@dataclass(frozen=True, slots=True)
class CentralLootEquipmentRequest:
    source_group: str
    request_key: str
    player_class: str
    enemy_class: EnemyClass
    enemy_level: int

@dataclass(frozen=True, slots=True)
class LootRollTrace:
    group_key: str
    rule_key: str
    chance: float
    roll: float | None
    outcome: Literal["disabled", "miss", "selected", "group_limit"]
    selected_key: str | None = None
    selection_roll: float | None = None

@dataclass(frozen=True, slots=True)
class CentralLootResult:
    immutable_loot_commands: tuple[CentralLootCommand, ...]
    equipment_generation_requests: tuple[CentralLootEquipmentRequest, ...]
    roll_trace: tuple[LootRollTrace, ...]

class CentralLootPlanner:
    \"\"\"Roll source-ordered groups and rules without side effects or rerolls.\"\"\"
    def plan(self, *, enemy_class: EnemyClass, enemy_level: int,
             player_class: str, location_key: str,
             rules: Sequence[LootGroup], rng: LootRandomSource) -> CentralLootResult:
        self._validate(enemy_class, enemy_level, player_class, location_key, rules)
        commands=[]; equipment=[]; trace=[]
        for group in rules:
            selected_count=0
            for rule in group.rules:
                if group.max_per_kill is not None and selected_count >= group.max_per_kill:
                    trace.append(LootRollTrace(group.group_key,rule.rule_key,rule.chance_for(enemy_class),None,"group_limit"));continue
                if not rule.enabled:
                    trace.append(LootRollTrace(group.group_key,rule.rule_key,rule.chance_for(enemy_class),None,"disabled"));continue
                chance=rule.chance_for(enemy_class); roll=float(rng.random())
                if not 0.0 <= roll < 1.0:raise CentralLootConfigurationError("rng_random_out_of_range")
                if roll >= chance:
                    trace.append(LootRollTrace(group.group_key,rule.rule_key,chance,roll,"miss"));continue
                candidate,selection_roll=self._weighted(rule.candidates,rng)
                selected_count+=1
                if candidate.kind=="equipment_request":
                    equipment.append(CentralLootEquipmentRequest(rule.source_group,candidate.key,player_class,enemy_class,enemy_level))
                else:
                    commands.append(CentralLootCommand(rule.source_group,candidate.key,candidate.quantity,candidate.kind))
                trace.append(LootRollTrace(group.group_key,rule.rule_key,chance,roll,"selected",candidate.key,selection_roll))
        return CentralLootResult(tuple(commands),tuple(equipment),tuple(trace))

    @staticmethod
    def _weighted(candidates: Sequence[LootCandidate], rng: LootRandomSource) -> tuple[LootCandidate, float | None]:
        if len(candidates)==1:return candidates[0],None
        total=sum(float(x.weight) for x in candidates); draw=float(rng.random())
        if not 0.0 <= draw < 1.0:raise CentralLootConfigurationError("rng_random_out_of_range")
        point=draw*total; upto=0.0
        for candidate in candidates:
            upto+=float(candidate.weight)
            if point < upto:return candidate,draw
        return candidates[-1],draw

    @staticmethod
    def _validate(enemy_class, enemy_level, player_class, location_key, groups):
        if enemy_class not in ("normal","elite","boss"):raise CentralLootConfigurationError("invalid_enemy_class")
        if int(enemy_level)<=0:raise CentralLootConfigurationError("positive_enemy_level_required")
        if not player_class.strip() or not location_key.strip():raise CentralLootConfigurationError("player_class_and_location_required")
        group_keys=set();rule_keys=set()
        for group in groups:
            if not group.group_key or group.group_key in group_keys:raise CentralLootConfigurationError("invalid_or_duplicate_group_key")
            group_keys.add(group.group_key)
            if group.max_per_kill is not None and group.max_per_kill<0:raise CentralLootConfigurationError("negative_group_limit")
            for rule in group.rules:
                if not rule.rule_key or rule.rule_key in rule_keys:raise CentralLootConfigurationError("invalid_or_duplicate_rule_key")
                rule_keys.add(rule.rule_key)
                chances=dict(rule.chances)
                if len(chances)!=len(rule.chances) or any(k not in ("normal","elite","boss") or not 0.0<=float(v)<=1.0 for k,v in rule.chances):raise CentralLootConfigurationError("invalid_chance_matrix")
                if not rule.candidates:raise CentralLootConfigurationError("empty_candidates")
                if any(not c.key or c.quantity<=0 or c.weight<=0 or c.kind not in ("item","equipment_request") for c in rule.candidates):raise CentralLootConfigurationError("invalid_candidate")
'''

def test_text():return '''import unittest
from rom_v2.domain.central_loot import *

class SeqRng:
 def __init__(self,*values):self.values=list(values);self.calls=0
 def random(self):self.calls+=1;return self.values.pop(0)

def rule(key,chance=1.0,candidates=None,enabled=True):
 return LootRule(key,"mob",(("normal",chance),("elite",chance),("boss",chance)),tuple(candidates or (LootCandidate(key),)),enabled)

class CentralLootPlannerTests(unittest.TestCase):
 def test_source_order_and_independent_rolls(self):
  rng=SeqRng(.1,.9);groups=(LootGroup("g",(rule("a",.5),rule("b",.5))),)
  out=CentralLootPlanner().plan(enemy_class="normal",enemy_level=3,player_class="scout",location_key="x",rules=groups,rng=rng)
  self.assertEqual([x.key for x in out.immutable_loot_commands],["a"]);self.assertEqual([x.outcome for x in out.roll_trace],["selected","miss"]);self.assertEqual(rng.calls,2)
 def test_weighted_selection_preserves_draw_order(self):
  rng=SeqRng(.1,.8);r=rule("r",1,(LootCandidate("a",1),LootCandidate("b",3)))
  out=CentralLootPlanner().plan(enemy_class="elite",enemy_level=2,player_class="mage",location_key="x",rules=(LootGroup("g",(r,)),),rng=rng)
  self.assertEqual(out.immutable_loot_commands[0].key,"b");self.assertEqual(rng.calls,2)
 def test_single_candidate_consumes_no_selection_draw(self):
  rng=SeqRng(.2);out=CentralLootPlanner().plan(enemy_class="boss",enemy_level=5,player_class="knight",location_key="x",rules=(LootGroup("g",(rule("a"),)),),rng=rng)
  self.assertEqual(rng.calls,1);self.assertIsNone(out.roll_trace[0].selection_roll)
 def test_group_limit_stops_additional_rng_draws(self):
  rng=SeqRng(.1);out=CentralLootPlanner().plan(enemy_class="normal",enemy_level=1,player_class="warrior",location_key="x",rules=(LootGroup("g",(rule("a"),rule("b")),1),),rng=rng)
  self.assertEqual(rng.calls,1);self.assertEqual([x.outcome for x in out.roll_trace],["selected","group_limit"])
 def test_disabled_rule_consumes_no_rng(self):
  rng=SeqRng();out=CentralLootPlanner().plan(enemy_class="normal",enemy_level=1,player_class="priest",location_key="x",rules=(LootGroup("g",(rule("a",enabled=False),)),),rng=rng)
  self.assertEqual(rng.calls,0);self.assertEqual(out.roll_trace[0].outcome,"disabled")
 def test_equipment_is_deferred_request_not_item(self):
  rng=SeqRng(.0);r=rule("eq",1,(LootCandidate("armor",1,1,"equipment_request"),))
  out=CentralLootPlanner().plan(enemy_class="boss",enemy_level=7,player_class="rogue",location_key="x",rules=(LootGroup("g",(r,)),),rng=rng)
  self.assertFalse(out.immutable_loot_commands);self.assertEqual(out.equipment_generation_requests[0].request_key,"armor")
 def test_invalid_configuration_fails_before_rng(self):
  rng=SeqRng(.1);bad=LootRule("r","g",(("normal",1.1),),(LootCandidate("a"),))
  with self.assertRaises(CentralLootConfigurationError):CentralLootPlanner().plan(enemy_class="normal",enemy_level=1,player_class="x",location_key="x",rules=(LootGroup("g",(bad,)),),rng=rng)
  self.assertEqual(rng.calls,0)
 def test_contract_has_no_premium_or_inventory_input(self):
  names=CentralLootPlanner.plan.__annotations__
  self.assertNotIn("premium",names);self.assertNotIn("inventory",names)

if __name__=="__main__":unittest.main()
'''

def tool_text():return '''#!/usr/bin/env python3
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from rom_v2.domain.central_loot import CentralLootPlanner, LootRandomSource
assert CentralLootPlanner and LootRandomSource
print("STAGE_21_9_4C_CENTRAL_LOOT_SMOKE: PASS")
'''

def run_canonical_ci(r, env):
 tmp=r/"reports/.stage_21_9_4c_ci.tmp.json";tmp.unlink(missing_ok=True)
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
  contract=preflight(r);print("[1/10] [PASS] Stage 21.9.4b zero-unresolved implementation prerequisite verified.");print("[2/10] [PASS] Branch, exact parent, dirty allowlist and clean index verified.")
  b,state=backup(r);print("[3/10] [PASS] Fail-safe backup created before production mutation.")
  write(r,APP,app_text());write(r,TEST,test_text());write(r,TOOL,tool_text());print("[4/10] [PASS] Central loot planner, immutable DTOs and RNG port implemented.")
  for rel in (SELF,APP,TEST,TOOL):ast.parse((r/rel).read_text(encoding="utf-8"),filename=rel.as_posix())
  p=run([sys.executable,"-m","py_compile",APP.as_posix(),TEST.as_posix(),TOOL.as_posix()],r,False)
  if p.returncode:raise PatchError(f"py_compile_failed:{p.stderr}")
  print("[5/10] [PASS] Python compile gate passed.")
  p=run([sys.executable,"-m","unittest",TEST.as_posix(),"-v"],r,False)
  if p.returncode:raise PatchError(f"integration_tests_failed:{p.stdout}:{p.stderr}")
  print("[6/10] [PASS] Deterministic ordering, weights, limits, deferred equipment and validation tests passed.")
  p=run([sys.executable,TOOL.as_posix()],r,False)
  if p.returncode or "SMOKE: PASS" not in p.stdout:raise PatchError(f"smoke_failed:{p.stdout}:{p.stderr}")
  print("[7/10] [PASS] Central loot planner smoke check passed.")
  clean(r);env=os.environ.copy();env["PYTHONDONTWRITEBYTECODE"]="1";env["PYTHONHASHSEED"]="0";ci_data=run_canonical_ci(r,env)
  if protected(r)!=before:raise PatchError("protected_runtime_changed")
  prod={line[3:].strip().replace("\\","/") for line in git(r,"status","--porcelain","--untracked-files=all").stdout.splitlines() if line[3:].strip().replace("\\","/").startswith("rom_v2/")}
  if prod!={APP.as_posix()}:raise PatchError(f"unauthorized_production_scope:{sorted(prod)}")
  print("[8/10] [PASS] Canonical V2 CI passed; only authorized domain module changed.")
  out={"schema_version":1,"stage":STAGE,"status":"PASS","conclusion":"API_READY","generated_at_utc":datetime.now(timezone.utc).isoformat(),"source_contract":PREREQ.as_posix(),"domain_service":"CentralLootPlanner","implementation":APP.as_posix(),"tests":TEST.as_posix(),"implemented":["pure_planner","immutable_dtos","injected_rng","source_ordered_groups","independent_rule_rolls","weighted_selection","group_limit","deferred_equipment_generation","roll_trace","premium_excluded","no_inventory_mutation"],"not_connected":["sqlite","production_inventory","generated_equipment_persistence","runtime","telegram","event_story_merger","pvp"],"runtime_integration":"NOT_CONNECTED","production_persistence":"NOT_CONNECTED","manual_game_check":"NOT_REQUIRED","database_opened":False,"v1_wal_shm_manipulated":False,"verification":{"canonical_v2_ci":ci_data}}
  write(r,REPORT,json.dumps(out,ensure_ascii=False,indent=2));write(r,DOC,"""# Stage 21.9.4c - Central loot pipeline implementation

- Status: **PASS**
- Conclusion: **API_READY**
- Runtime integration: **NOT_CONNECTED**
- Production persistence: **NOT_CONNECTED**
- Manual game check: **NOT_REQUIRED**

Implemented a pure V2 central loot planner with immutable rules and results, an explicit RNG protocol, source-order rule traversal, weighted selection, group limits, deferred equipment-generation requests, deterministic roll trace, no Premium input, and no inventory mutation.

SQLite, production inventory, generated-equipment persistence, event/story merger, Telegram/runtime wiring, and PvP loot remain excluded.
""");print("[9/10] [PASS] Machine report and Markdown documentation written.")
  expected={x.as_posix() for x in TARGETS};git(r,"add","--",APP.as_posix(),TEST.as_posix(),TOOL.as_posix());git(r,"add","-f","--",SELF.as_posix(),REPORT.as_posix(),DOC.as_posix());staged={x.strip().replace("\\","/") for x in git(r,"diff","--cached","--name-only").stdout.splitlines() if x.strip()}
  if staged!=expected:raise PatchError(f"staging_mismatch:{sorted(staged)}")
  p=git(r,"commit","-m","Stage 21.9.4c: implement central loot pipeline",check=False)
  if p.returncode:raise PatchError(f"commit_failed:{p.stdout}:{p.stderr}")
  commit=git(r,"rev-parse","HEAD").stdout.strip();changed={x.strip().replace("\\","/") for x in git(r,"diff-tree","--no-commit-id","--name-only","-r",commit).stdout.splitlines() if x.strip()}
  if changed!=expected:raise PatchError(f"commit_scope:{sorted(changed)}")
  (r/FAILURE).unlink(missing_ok=True);print(f"[10/10] [PASS] Central loot pipeline implementation committed: {commit}");print("CONCLUSION: API_READY");print("PATCH STATUS: PASS");print(f"GIT COMMIT STATUS: PASS ({commit})");print("RUNTIME INTEGRATION: NOT_CONNECTED");print("PRODUCTION PERSISTENCE: NOT_CONNECTED");print("MANUAL GAME CHECK: NOT_REQUIRED");print("FAIL-SAFE ROLLBACK: ARMED");return 0
 except Exception as e:
  restored=restore(r,b,state);recovery=run([sys.executable,"-m","compileall","-q","rom_v2"],r,False);f={"schema_version":1,"stage":STAGE,"status":"FAIL_ROLLED_BACK","failed_at_utc":datetime.now(timezone.utc).isoformat(),"reason":str(e),"restored_files":restored,"recovery_compile_returncode":recovery.returncode,"main_py_allowed_after_recovery":recovery.returncode==0,"database_opened":False,"v1_wal_shm_manipulated":False};p=r/FAILURE;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(f,ensure_ascii=False,indent=2)+"\n",encoding="utf-8");print(f"[10/10] [FAIL] {e}; rollback: FAIL_ROLLED_BACK");return 1
if __name__=="__main__":raise SystemExit(main())
