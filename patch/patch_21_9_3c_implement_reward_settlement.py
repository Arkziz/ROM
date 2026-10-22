#!/usr/bin/env python3
"""ROM Stage 21.9.3c: implement the pure V2 reward settlement application service."""
from __future__ import annotations
import ast, json, os, shutil, subprocess, sys
from datetime import datetime, timezone
from pathlib import Path

STAGE="21.9.3c";BRANCH="rewrite/rom-v2";PARENT="bc1fdf3cee970612f4374380a59565b675e17ca8"
PREREQ=Path("reports/stage_21_9_3b_resolved_reward_settlement_parity.json")
APP=Path("rom_v2/application/reward_settlement.py");TEST=Path("tests_v2/test_reward_settlement.py")
TOOL=Path("tools/check_stage_21_9_3c_reward_settlement.py")
REPORT=Path("reports/stage_21_9_3c_reward_settlement_implementation.json")
DOC=Path("MD/STAGE_21_9_3C_REWARD_SETTLEMENT_IMPLEMENTATION.md")
FAILURE=Path("reports/stage_21_9_3c_failure_rollback.json");SELF=Path("patch/patch_21_9_3c_implement_reward_settlement.py")
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
 if (d.get("stage"),d.get("status"),d.get("conclusion"))!=("21.9.3b","PASS","GO_TO_IMPLEMENTATION"):raise PatchError("invalid_prerequisite")
 if d.get("implementation_authorized") is not True or d.get("runtime_integration_authorized") is not False or d.get("production_persistence_authorized") is not False:raise PatchError("invalid_authorization_boundary")
 if d.get("summary",{}).get("remaining_unresolved_contracts")!=0:raise PatchError("unresolved_contracts_remain")
 app=d.get("v2_application_contract",{})
 if app.get("service")!="RewardSettlementService" or app.get("commit_count")!=1 or app.get("rollback_on_any_failure") is not True or app.get("presentation_inside_transaction") is not False:raise PatchError("invalid_application_contract")
 if git(r,"diff","--cached","--name-only").stdout.strip():raise PatchError("pre_staged_changes")
 dirty=set()
 for line in git(r,"status","--porcelain","--untracked-files=all").stdout.splitlines():
  x=line[3:].strip().replace("\\","/").split(" -> ",1)[-1]
  if x!=SELF.as_posix() and x not in ALLOWED_DIRTY:dirty.add(x)
 if dirty:raise PatchError(f"unexpected_dirty:{sorted(dirty)}")
 return d
def backup(r):
 b=r/"backup"/f"stage_21_9_3c_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}";b.mkdir(parents=True);state={}
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

def app_text():return '''"""Atomic exact-once reward settlement application service.

This module defines application DTOs and ports only. It does not provide a
SQLite adapter, runtime wiring, Telegram presentation, or gameplay formulas.
"""
from __future__ import annotations
from dataclasses import dataclass, replace
from typing import Any, Literal, Mapping, Protocol, Sequence

from rom_v2.domain.level_up_gold import calculate_v2_level_up_rewards
from rom_v2.domain.player_progression import PlayerProgressionResult, apply_player_exp_award

RewardSettlementSource = Literal["pve", "pve_boss"]
RewardLootStatus = Literal["applied", "pending", "rejected"]

class RewardSettlementError(RuntimeError):
    """Base application-service failure."""

class RewardSettlementInProgressError(RewardSettlementError):
    """Raised when the stable operation key is already being processed."""

class RewardSettlementValidationError(RewardSettlementError):
    """Raised before any mutation when command data is invalid."""

@dataclass(frozen=True, slots=True)
class RewardLootCommand:
    item_key: str
    quantity: int

@dataclass(frozen=True, slots=True)
class RewardObjectiveProgressCommand:
    progress_key: str
    amount: int

@dataclass(frozen=True, slots=True)
class RewardSettlementCommand:
    operation_key: str
    source_type: RewardSettlementSource
    actor_id: int
    encounter_id: str
    exp_award: int
    base_combat_gold: float
    premium_combat_gold: float = 0.0
    loot_commands: tuple[RewardLootCommand, ...] = ()
    objective_progress_commands: tuple[RewardObjectiveProgressCommand, ...] = ()

@dataclass(frozen=True, slots=True)
class RewardPlayerProgressState:
    level: int
    exp: int
    level_cap: int | None

@dataclass(frozen=True, slots=True)
class RewardLootOutcome:
    status: RewardLootStatus
    applied: tuple[RewardLootCommand, ...] = ()
    pending: tuple[RewardLootCommand, ...] = ()
    rejected: tuple[RewardLootCommand, ...] = ()

@dataclass(frozen=True, slots=True)
class RewardSettlementResult:
    operation_key: str
    status: Literal["completed"]
    duplicate: bool
    progression: PlayerProgressionResult
    level_up_rewards: Mapping[str, Any]
    combat_gold: float
    loot_outcome: RewardLootOutcome
    objective_progress: tuple[RewardObjectiveProgressCommand, ...]
    history_record_id: str

class RewardSettlementClaimRepository(Protocol):
    def claim(self, operation_key: str) -> Literal["claimed", "completed", "processing"]: ...
    def completed_result(self, operation_key: str) -> RewardSettlementResult: ...
    def complete(self, operation_key: str, result: RewardSettlementResult) -> None: ...

class RewardPlayerProgressionRepository(Protocol):
    def get_state(self, actor_id: int) -> RewardPlayerProgressState: ...
    def apply(self, actor_id: int, result: PlayerProgressionResult) -> None: ...

class RewardWalletRepository(Protocol):
    def credit(self, actor_id: int, amount: float, source: str) -> None: ...

class RewardLootRepository(Protocol):
    def apply(self, actor_id: int, commands: Sequence[RewardLootCommand]) -> RewardLootOutcome: ...

class RewardObjectiveProgressRepository(Protocol):
    def apply(self, actor_id: int, commands: Sequence[RewardObjectiveProgressCommand]) -> tuple[RewardObjectiveProgressCommand, ...]: ...

class RewardHistoryRepository(Protocol):
    def append(self, operation_key: str, actor_id: int, summary: Mapping[str, Any]) -> str: ...

class RewardSettlementUnitOfWork(Protocol):
    claims: RewardSettlementClaimRepository
    progression: RewardPlayerProgressionRepository
    wallet: RewardWalletRepository
    loot: RewardLootRepository
    objective_progress: RewardObjectiveProgressRepository
    history: RewardHistoryRepository
    def commit(self) -> None: ...
    def rollback(self) -> None: ...

class RewardSettlementService:
    """Orchestrate one exact-once PvE settlement through one Unit of Work."""
    def settle(self, command: RewardSettlementCommand, uow: RewardSettlementUnitOfWork) -> RewardSettlementResult:
        self._validate(command)
        try:
            claim = uow.claims.claim(command.operation_key)
            if claim == "completed":
                previous = uow.claims.completed_result(command.operation_key)
                return replace(previous, duplicate=True)
            if claim == "processing":
                raise RewardSettlementInProgressError(command.operation_key)
            if claim != "claimed":
                raise RewardSettlementError(f"unsupported_claim_outcome:{claim}")

            initial = uow.progression.get_state(command.actor_id)
            progression = apply_player_exp_award(
                initial.level, initial.exp, command.exp_award, initial.level_cap
            )
            level_rewards = calculate_v2_level_up_rewards(initial.level, progression.level)
            uow.progression.apply(command.actor_id, progression)

            level_gold = float(level_rewards["gold"])
            if level_gold:
                uow.wallet.credit(command.actor_id, level_gold, "level_up_gold")
            combat_gold = float(command.base_combat_gold) + float(command.premium_combat_gold)
            if combat_gold:
                uow.wallet.credit(command.actor_id, combat_gold, "combat_gold")

            loot_outcome = uow.loot.apply(command.actor_id, command.loot_commands)
            if loot_outcome.status not in ("applied", "pending", "rejected"):
                raise RewardSettlementError(f"unsupported_loot_outcome:{loot_outcome.status}")
            objective_progress = uow.objective_progress.apply(
                command.actor_id, command.objective_progress_commands
            )
            summary = {
                "source_type": command.source_type,
                "encounter_id": command.encounter_id,
                "exp_award": command.exp_award,
                "level_ups": progression.level_ups,
                "level_up_gold": level_gold,
                "combat_gold": combat_gold,
                "loot_status": loot_outcome.status,
                "objective_progress_count": len(objective_progress),
            }
            history_record_id = uow.history.append(
                command.operation_key, command.actor_id, summary
            )
            result = RewardSettlementResult(
                operation_key=command.operation_key,
                status="completed",
                duplicate=False,
                progression=progression,
                level_up_rewards=level_rewards,
                combat_gold=combat_gold,
                loot_outcome=loot_outcome,
                objective_progress=objective_progress,
                history_record_id=history_record_id,
            )
            uow.claims.complete(command.operation_key, result)
            uow.commit()
            return result
        except Exception:
            uow.rollback()
            raise

    @staticmethod
    def _validate(command: RewardSettlementCommand) -> None:
        if not command.operation_key.strip():
            raise RewardSettlementValidationError("operation_key_required")
        if command.source_type not in ("pve", "pve_boss"):
            raise RewardSettlementValidationError("unsupported_source_type")
        if int(command.actor_id) <= 0:
            raise RewardSettlementValidationError("positive_actor_id_required")
        if not command.encounter_id.strip():
            raise RewardSettlementValidationError("encounter_id_required")
        if int(command.exp_award) < 0:
            raise RewardSettlementValidationError("negative_exp_award_forbidden")
        if float(command.base_combat_gold) < 0 or float(command.premium_combat_gold) < 0:
            raise RewardSettlementValidationError("negative_combat_gold_forbidden")
        if any(not item.item_key.strip() or int(item.quantity) <= 0 for item in command.loot_commands):
            raise RewardSettlementValidationError("invalid_loot_command")
        if any(not item.progress_key.strip() or int(item.amount) <= 0 for item in command.objective_progress_commands):
            raise RewardSettlementValidationError("invalid_objective_progress_command")
'''

def test_text():return '''import copy
import unittest
from dataclasses import replace
from rom_v2.application.reward_settlement import (
 RewardLootCommand, RewardLootOutcome, RewardPlayerProgressState,
 RewardObjectiveProgressCommand, RewardSettlementCommand,
 RewardSettlementInProgressError, RewardSettlementService,
 RewardSettlementUnitOfWork, RewardSettlementValidationError,
)

class FakeUow:
 def __init__(self, fail_at=None):
  self.fail_at=fail_at;self.commit_count=0;self.rollback_count=0;self.events=[]
  self.claims=self.Claims(self);self.progression=self.Progress(self);self.wallet=self.Wallet(self);self.loot=self.Loot(self);self.objective_progress=self.Quests(self);self.history=self.History(self)
  self._stable=self.snapshot()
 def snapshot(self):
  return copy.deepcopy({"claim_rows":getattr(self,"claim_rows",{}),"state":getattr(self,"state",RewardPlayerProgressState(1,0,11)),"credits":getattr(self,"credits",[]),"loot_rows":getattr(self,"loot_rows",[]),"quest_rows":getattr(self,"quest_rows",[]),"history_rows":getattr(self,"history_rows",[])})
 def restore(self,s):
  self.claim_rows=s["claim_rows"];self.state=s["state"];self.credits=s["credits"];self.loot_rows=s["loot_rows"];self.quest_rows=s["quest_rows"];self.history_rows=s["history_rows"]
 def trip(self,name):
  self.events.append(name)
  if self.fail_at==name:raise RuntimeError(name)
 def commit(self):self.trip("commit");self.commit_count+=1;self._stable=self.snapshot()
 def rollback(self):self.rollback_count+=1;self.events.append("rollback");self.restore(self._stable)
 class Claims:
  def __init__(self,u):self.u=u;u.claim_rows={}
  def claim(self,key):
   self.u.trip("claim");row=self.u.claim_rows.get(key)
   if row and row[0]=="completed":return "completed"
   if row:return "processing"
   self.u.claim_rows[key]=("processing",None);return "claimed"
  def completed_result(self,key):return self.u.claim_rows[key][1]
  def complete(self,key,result):self.u.trip("complete");self.u.claim_rows[key]=("completed",result)
 class Progress:
  def __init__(self,u):self.u=u;u.state=RewardPlayerProgressState(1,0,11)
  def get_state(self,actor):self.u.trip("get_state");return self.u.state
  def apply(self,actor,result):self.u.trip("progression");self.u.state=RewardPlayerProgressState(result.level,result.exp,11)
 class Wallet:
  def __init__(self,u):self.u=u;u.credits=[]
  def credit(self,actor,amount,source):self.u.trip("wallet_"+source);self.u.credits.append((amount,source))
 class Loot:
  def __init__(self,u):self.u=u;u.loot_rows=[]
  def apply(self,actor,commands):self.u.trip("loot");self.u.loot_rows.extend(commands);return RewardLootOutcome("applied",tuple(commands))
 class Quests:
  def __init__(self,u):self.u=u;u.quest_rows=[]
  def apply(self,actor,commands):self.u.trip("quest");self.u.quest_rows.extend(commands);return tuple(commands)
 class History:
  def __init__(self,u):self.u=u;u.history_rows=[]
  def append(self,key,actor,summary):self.u.trip("history");self.u.history_rows.append((key,summary));return "history-1"

def command(key="op-1",source="pve"):
 return RewardSettlementCommand(key,source,7,"enc-9",500,10.0,2.5,(RewardLootCommand("item-a",1),),(RewardObjectiveProgressCommand("kill-a",1),))

class RewardSettlementIntegrationTests(unittest.TestCase):
 def test_exact_once_duplicate_returns_prior_result(self):
  u=FakeUow();service=RewardSettlementService();first=service.settle(command(),u);second=service.settle(command(),u)
  self.assertFalse(first.duplicate);self.assertTrue(second.duplicate);self.assertEqual(u.commit_count,1);self.assertEqual(len(u.credits),2);self.assertEqual(len(u.history_rows),1)
 def test_one_commit_and_order(self):
  u=FakeUow();result=RewardSettlementService().settle(command(),u)
  self.assertEqual(u.commit_count,1);self.assertEqual(u.rollback_count,0);self.assertEqual(result.progression.level,2)
  self.assertEqual(u.events,["claim","get_state","progression","wallet_level_up_gold","wallet_combat_gold","loot","quest","history","complete","commit"])
 def test_premium_applies_only_to_combat_gold(self):
  u=FakeUow();result=RewardSettlementService().settle(command(),u)
  self.assertEqual(result.combat_gold,12.5);self.assertEqual(u.credits,[(0.45,"level_up_gold"),(12.5,"combat_gold")])
 def test_processing_duplicate_fails_closed(self):
  u=FakeUow();u.claim_rows["op-1"]=("processing",None)
  with self.assertRaises(RewardSettlementInProgressError):RewardSettlementService().settle(command(),u)
  self.assertEqual(u.commit_count,0);self.assertEqual(u.rollback_count,1)
 def test_rollback_at_every_mutation_boundary(self):
  for boundary in ("progression","wallet_level_up_gold","wallet_combat_gold","loot","quest","history","complete","commit"):
   with self.subTest(boundary=boundary):
    u=FakeUow(boundary);initial=u.snapshot()
    with self.assertRaises(RuntimeError):RewardSettlementService().settle(command(),u)
    self.assertEqual(u.snapshot(),initial);self.assertEqual(u.commit_count,0);self.assertEqual(u.rollback_count,1)
 def test_pending_loot_is_explicit_success_outcome(self):
  u=FakeUow()
  def pending(actor,commands):u.trip("loot");return RewardLootOutcome("pending",pending=tuple(commands))
  u.loot.apply=pending;result=RewardSettlementService().settle(command(),u);self.assertEqual(result.loot_outcome.status,"pending");self.assertEqual(u.commit_count,1)
 def test_pvp_and_invalid_input_rejected_before_mutation(self):
  for bad in (command(source="pvp"),replace(command(),operation_key=""),replace(command(),exp_award=-1)):
   u=FakeUow()
   with self.assertRaises(RewardSettlementValidationError):RewardSettlementService().settle(bad,u)
   self.assertEqual(u.events,[]);self.assertEqual(u.rollback_count,0)
 def test_service_has_no_presentation_port(self):
  self.assertFalse(any("message" in name or "send" in name for name in RewardSettlementUnitOfWork.__annotations__))

if __name__=="__main__":unittest.main()
'''

def tool_text():return '''#!/usr/bin/env python3
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from rom_v2.application.reward_settlement import RewardSettlementCommand, RewardSettlementService
assert RewardSettlementService and RewardSettlementCommand.__dataclass_fields__["operation_key"]
print("STAGE_21_9_3C_REWARD_SETTLEMENT_SMOKE: PASS")
'''

def run_canonical_ci(r,env):
 tmp=r/"reports/.stage_21_9_3c_ci.tmp.json";tmp.unlink(missing_ok=True)
 command=[sys.executable,"-B","tools/run_v2_ci.py","--project-root",str(r),"--json-out",str(tmp)]
 p=run(command,r,False,env)
 data=None
 if tmp.is_file():
  try:data=json.loads(tmp.read_text(encoding="utf-8"))
  except Exception:data=None
  tmp.unlink(missing_ok=True)
 if p.returncode==0 and isinstance(data,dict) and data.get("status")=="PASS":return data
 # A single clean retry is allowed because static CI can observe transient bytecode
 # emitted by prior targeted test subprocesses on some Windows/Python versions.
 clean(r);retry=run(command,r,False,env);retry_data=None
 if tmp.is_file():
  try:retry_data=json.loads(tmp.read_text(encoding="utf-8"))
  except Exception:retry_data=None
  tmp.unlink(missing_ok=True)
 if retry.returncode or not isinstance(retry_data,dict) or retry_data.get("status")!="PASS":
  detail=json.dumps(retry_data if retry_data is not None else data,ensure_ascii=False)
  raise PatchError(f"canonical_v2_ci_failed_after_clean_retry:{detail}:{retry.stdout[-1200:]}:{retry.stderr[-4000:]}")
 return retry_data

def main():
 r=Path.cwd().resolve();b=None;state={};before=protected(r)
 try:
  contract=preflight(r);print("[1/10] [PASS] Stage 21.9.3b zero-unresolved implementation prerequisite verified.");print("[2/10] [PASS] Branch, exact parent, dirty allowlist and clean index verified.")
  b,state=backup(r);print("[3/10] [PASS] Fail-safe backup created before production mutation.")
  write(r,APP,app_text());write(r,TEST,test_text());write(r,TOOL,tool_text());print("[4/10] [PASS] Reward settlement application service, DTOs and ports implemented.")
  for rel in (SELF,APP,TEST,TOOL):ast.parse((r/rel).read_text(encoding="utf-8"),filename=rel.as_posix())
  p=run([sys.executable,"-m","py_compile",APP.as_posix(),TEST.as_posix(),TOOL.as_posix()],r,False)
  if p.returncode:raise PatchError(f"py_compile_failed:{p.stderr}")
  print("[5/10] [PASS] Python compile gate passed.")
  p=run([sys.executable,"-m","unittest",TEST.as_posix(),"-v"],r,False)
  if p.returncode:raise PatchError(f"integration_tests_failed:{p.stdout}:{p.stderr}")
  print("[6/10] [PASS] Exact-once, duplicate, one-commit, rollback and boundary integration tests passed.")
  p=run([sys.executable,TOOL.as_posix()],r,False)
  if p.returncode or "SMOKE: PASS" not in p.stdout:raise PatchError(f"smoke_failed:{p.stdout}:{p.stderr}")
  print("[7/10] [PASS] Reward settlement smoke check passed.")
  clean(r);env=os.environ.copy();env["PYTHONDONTWRITEBYTECODE"]="1";env["PYTHONHASHSEED"]="0";ci_data=run_canonical_ci(r,env)
  if protected(r)!=before:raise PatchError("protected_runtime_changed")
  prod={line[3:].strip().replace("\\","/") for line in git(r,"status","--porcelain","--untracked-files=all").stdout.splitlines() if line[3:].strip().replace("\\","/").startswith("rom_v2/")}
  if prod!={APP.as_posix()}:raise PatchError(f"unauthorized_production_scope:{sorted(prod)}")
  print("[8/10] [PASS] Canonical V2 CI passed; only authorized application module changed.")
  out={"schema_version":1,"stage":STAGE,"status":"PASS","conclusion":"API_READY","generated_at_utc":datetime.now(timezone.utc).isoformat(),"source_contract":PREREQ.as_posix(),"application_service":"RewardSettlementService","implementation":APP.as_posix(),"tests":TEST.as_posix(),"implemented":["stable_operation_key","one_unit_of_work","exact_once_duplicate_result","processing_conflict","single_commit","rollback_all_mutations","premium_combat_gold_only","explicit_loot_outcome","objective_progress_order","append_only_history_port","presentation_after_commit_boundary","pve_and_pve_boss_scope"],"not_connected":["sqlite","production_repositories","runtime","telegram","pvp"],"runtime_integration":"NOT_CONNECTED","production_persistence":"NOT_CONNECTED","manual_game_check":"NOT_REQUIRED","database_opened":False,"v1_wal_shm_manipulated":False,"verification":{"canonical_v2_ci":ci_data}}
  write(r,REPORT,json.dumps(out,ensure_ascii=False,indent=2));write(r,DOC,"""# Stage 21.9.3c - Reward settlement implementation

- Status: **PASS**
- Conclusion: **API_READY**
- Runtime integration: **NOT_CONNECTED**
- Production persistence: **NOT_CONNECTED**
- Manual game check: **NOT_REQUIRED**

Implemented a V2 application service with immutable commands/results, explicit repository and Unit-of-Work ports, one commit, exact-once duplicate behavior, processing conflict, full rollback, Premium limited to combat gold, explicit loot outcomes, objective progress ordering, append-only history, PvE/PvE-boss scope, and no presentation inside the transaction.

SQLite adapters, production repositories, Telegram/runtime wiring, and PvP integration remain excluded.
""");print("[9/10] [PASS] Machine report and Markdown documentation written.")
  expected={x.as_posix() for x in TARGETS};git(r,"add","--",APP.as_posix(),TEST.as_posix(),TOOL.as_posix());git(r,"add","-f","--",SELF.as_posix(),REPORT.as_posix(),DOC.as_posix());staged={x.strip().replace("\\","/") for x in git(r,"diff","--cached","--name-only").stdout.splitlines() if x.strip()}
  if staged!=expected:raise PatchError(f"staging_mismatch:{sorted(staged)}")
  p=git(r,"commit","-m","Stage 21.9.3c: implement reward settlement service",check=False)
  if p.returncode:raise PatchError(f"commit_failed:{p.stdout}:{p.stderr}")
  commit=git(r,"rev-parse","HEAD").stdout.strip();changed={x.strip().replace("\\","/") for x in git(r,"diff-tree","--no-commit-id","--name-only","-r",commit).stdout.splitlines() if x.strip()}
  if changed!=expected:raise PatchError(f"commit_scope:{sorted(changed)}")
  (r/FAILURE).unlink(missing_ok=True);print(f"[10/10] [PASS] Reward settlement implementation committed: {commit}");print("CONCLUSION: API_READY");print("PATCH STATUS: PASS");print(f"GIT COMMIT STATUS: PASS ({commit})");print("RUNTIME INTEGRATION: NOT_CONNECTED");print("PRODUCTION PERSISTENCE: NOT_CONNECTED");print("MANUAL GAME CHECK: NOT_REQUIRED");print("FAIL-SAFE ROLLBACK: ARMED");return 0
 except Exception as e:
  restored=restore(r,b,state);recovery=run([sys.executable,"-m","compileall","-q","rom_v2"],r,False);f={"schema_version":1,"stage":STAGE,"status":"FAIL_ROLLED_BACK","failed_at_utc":datetime.now(timezone.utc).isoformat(),"reason":str(e),"restored_files":restored,"recovery_compile_returncode":recovery.returncode,"main_py_allowed_after_recovery":recovery.returncode==0,"database_opened":False,"v1_wal_shm_manipulated":False};p=r/FAILURE;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(f,ensure_ascii=False,indent=2)+"\n",encoding="utf-8");print(f"[10/10] [FAIL] {e}; rollback: FAIL_ROLLED_BACK");return 1
if __name__=="__main__":raise SystemExit(main())
