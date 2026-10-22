#!/usr/bin/env python3
"""ROM Stage 21.9.6c: implement pure V2 post-combat hooks API."""
from __future__ import annotations
import ast, json, os, shutil, subprocess, sys
from datetime import datetime, timezone
from pathlib import Path

STAGE="21.9.6c";BRANCH="rewrite/rom-v2";PARENT="0123f5b8ccd2559f19450ef9f7b079ed0ee00280"
PREREQ=Path("reports/stage_21_9_6b_resolved_reward_settlement_parity.json")
APP=Path("rom_v2/application/post_combat_hooks.py");TEST=Path("tests_v2/test_post_combat_hooks.py")
TOOL=Path("tools/check_stage_21_9_6c_post_combat_hooks.py")
REPORT=Path("reports/stage_21_9_6c_post_combat_hooks_implementation.json")
DOC=Path("MD/STAGE_21_9_6C_POST_COMBAT_HOOKS_IMPLEMENTATION.md")
FAILURE=Path("reports/stage_21_9_6c_failure_rollback.json");SELF=Path("patch/patch_21_9_6c_implement_post_combat_hooks.py")
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
 if (d.get("stage"),d.get("status"),d.get("conclusion")) != ("21.9.6b","PASS","GO_TO_IMPLEMENTATION"):raise PatchError("invalid_prerequisite")
 if d.get("implementation_authorized") is not True or d.get("runtime_integration_authorized") is not False or d.get("production_persistence_authorized") is not False:raise PatchError("invalid_authorization_boundary")
 if d.get("summary",{}).get("remaining_unresolved_contracts") != 0:raise PatchError("unresolved_contracts_remain")
 c=d.get("v2_post_combat_contract",{})
 expected=["story_region_kill","story_boss_completion","story_item_drop","daily_quest","guild_contract","event_statistics","durability"]
 if c.get("coordinator")!="PostCombatHookCoordinator" or c.get("event")!="SettledVictoryEvent" or c.get("scope")!="settled_victory_only" or c.get("stable_key_source")!="reward_settlement_operation_key" or c.get("durable_consumer_order")!=expected or c.get("reward_mutation") is not False or c.get("consumer_idempotency") is not True or c.get("single_hook_commit") is not True:raise PatchError("invalid_post_combat_contract")
 if git(r,"diff","--cached","--name-only").stdout.strip():raise PatchError("pre_staged_changes")
 dirty=set()
 for line in git(r,"status","--porcelain","--untracked-files=all").stdout.splitlines():
  x=line[3:].strip().replace("\\","/").split(" -> ",1)[-1]
  if x!=SELF.as_posix() and x not in ALLOWED_DIRTY:dirty.add(x)
 if dirty:raise PatchError(f"unexpected_dirty:{sorted(dirty)}")
 return d

def backup(r):
 b=r/"backup"/f"stage_21_9_6c_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}";b.mkdir(parents=True);state={}
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

def app_text():return '''"""Pure application API for deterministic post-combat hook dispatch.

Reward settlement must already be committed. This module owns no SQLite,
runtime, Telegram, notifications, or reward mutation.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Protocol, Sequence

CANONICAL_CONSUMER_ORDER = (
    "story_region_kill", "story_boss_completion", "story_item_drop",
    "daily_quest", "guild_contract", "event_statistics", "durability",
)

class PostCombatHookContractError(ValueError):
    """Raised before mutation when an event or consumer plan is invalid."""

@dataclass(frozen=True, slots=True)
class SettledVictoryEvent:
    operation_key: str
    battle_id: str
    actor_id: int
    enemy_key: str
    enemy_class: str
    enemy_level: int
    location_key: str
    settlement_status: str
    exp_awarded: int
    combat_gold_awarded: str
    loot_summary_keys: tuple[str, ...] = ()

@dataclass(frozen=True, slots=True)
class PostCombatConsumerResult:
    consumer_key: str
    status: str

@dataclass(frozen=True, slots=True)
class PostCombatDispatchResult:
    operation_key: str
    consumer_results: tuple[PostCombatConsumerResult, ...]
    commit_count: int

class PostCombatConsumerPort(Protocol):
    consumer_key: str
    def consume(self, event: SettledVictoryEvent) -> None: ...

class PostCombatHooksUnitOfWorkPort(Protocol):
    def is_consumer_complete(self, operation_key: str, consumer_key: str) -> bool: ...
    def mark_consumer_complete(self, operation_key: str, consumer_key: str) -> None: ...
    def commit(self) -> None: ...
    def rollback(self) -> None: ...

class PostCombatHookCoordinator:
    """Run canonical durable consumers exactly once with one hook commit."""
    def dispatch(self, *, event: SettledVictoryEvent,
                 consumers: Sequence[PostCombatConsumerPort],
                 unit_of_work: PostCombatHooksUnitOfWorkPort) -> PostCombatDispatchResult:
        self._validate_event(event)
        by_key={consumer.consumer_key:consumer for consumer in consumers}
        if len(by_key)!=len(consumers):raise PostCombatHookContractError("duplicate_consumer_key")
        unknown=set(by_key)-set(CANONICAL_CONSUMER_ORDER)
        if unknown:raise PostCombatHookContractError(f"unknown_consumer_keys:{sorted(unknown)}")
        results=[]
        try:
            for key in CANONICAL_CONSUMER_ORDER:
                consumer=by_key.get(key)
                if consumer is None:continue
                if unit_of_work.is_consumer_complete(event.operation_key,key):
                    results.append(PostCombatConsumerResult(key,"already_complete"));continue
                consumer.consume(event)
                unit_of_work.mark_consumer_complete(event.operation_key,key)
                results.append(PostCombatConsumerResult(key,"applied"))
            unit_of_work.commit()
        except Exception:
            unit_of_work.rollback()
            raise
        return PostCombatDispatchResult(event.operation_key,tuple(results),1)

    @staticmethod
    def _validate_event(event: SettledVictoryEvent) -> None:
        if not event.operation_key.strip() or not event.battle_id.strip():raise PostCombatHookContractError("stable_keys_required")
        if event.actor_id<=0 or event.enemy_level<=0:raise PostCombatHookContractError("positive_actor_and_enemy_level_required")
        if event.enemy_class not in ("normal","elite","boss"):raise PostCombatHookContractError("invalid_enemy_class")
        if event.settlement_status!="committed":raise PostCombatHookContractError("settlement_must_be_committed")
        if event.exp_awarded<0:raise PostCombatHookContractError("negative_exp_summary")
        if not event.enemy_key.strip() or not event.location_key.strip():raise PostCombatHookContractError("enemy_and_location_required")
'''

def test_text():return '''import unittest
from rom_v2.application.post_combat_hooks import *

class Consumer:
 def __init__(self,key,log,fail=False):self.consumer_key=key;self.log=log;self.fail=fail
 def consume(self,event):
  self.log.append(self.consumer_key)
  if self.fail:raise RuntimeError("consumer_failure")
class Uow:
 def __init__(self,complete=()):self.complete=set(complete);self.marked=[];self.commits=0;self.rollbacks=0
 def is_consumer_complete(self,o,k):return (o,k) in self.complete
 def mark_consumer_complete(self,o,k):self.marked.append((o,k));self.complete.add((o,k))
 def commit(self):self.commits+=1
 def rollback(self):self.rollbacks+=1

def event(status="committed",enemy_class="normal"):
 return SettledVictoryEvent("op-1","battle-1",7,"mob",enemy_class,3,"start_path",status,10,"2.50",("item",))

class PostCombatHookCoordinatorTests(unittest.TestCase):
 def test_canonical_order_and_single_commit(self):
  log=[];u=Uow();cs=[Consumer("durability",log),Consumer("story_region_kill",log),Consumer("guild_contract",log)]
  out=PostCombatHookCoordinator().dispatch(event=event(),consumers=cs,unit_of_work=u)
  self.assertEqual(log,["story_region_kill","guild_contract","durability"]);self.assertEqual(u.commits,1);self.assertEqual(out.commit_count,1)
 def test_completed_consumer_is_skipped(self):
  log=[];u=Uow({("op-1","story_region_kill")});out=PostCombatHookCoordinator().dispatch(event=event(),consumers=[Consumer("story_region_kill",log),Consumer("daily_quest",log)],unit_of_work=u)
  self.assertEqual(log,["daily_quest"]);self.assertEqual([x.status for x in out.consumer_results],["already_complete","applied"])
 def test_failure_rolls_back_hook_uow_without_commit(self):
  log=[];u=Uow()
  with self.assertRaises(RuntimeError):PostCombatHookCoordinator().dispatch(event=event(),consumers=[Consumer("story_region_kill",log),Consumer("daily_quest",log,True)],unit_of_work=u)
  self.assertEqual(u.commits,0);self.assertEqual(u.rollbacks,1)
 def test_uncommitted_settlement_fails_before_consumer(self):
  log=[];u=Uow()
  with self.assertRaises(PostCombatHookContractError):PostCombatHookCoordinator().dispatch(event=event("processing"),consumers=[Consumer("story_region_kill",log)],unit_of_work=u)
  self.assertFalse(log);self.assertEqual(u.commits,0)
 def test_normal_elite_boss_share_event_contract(self):
  for kind in ("normal","elite","boss"):
   u=Uow();PostCombatHookCoordinator().dispatch(event=event(enemy_class=kind),consumers=[],unit_of_work=u);self.assertEqual(u.commits,1)
 def test_duplicate_and_unknown_consumers_rejected(self):
  for consumers in ([Consumer("daily_quest",[]),Consumer("daily_quest",[])],[Consumer("shadow",[])]):
   with self.assertRaises(PostCombatHookContractError):PostCombatHookCoordinator().dispatch(event=event(),consumers=consumers,unit_of_work=Uow())
 def test_event_has_summary_not_reward_commands(self):
  fields=SettledVictoryEvent.__dataclass_fields__
  for forbidden in ("exp_command","gold_command","loot_command","quest_reward_command"):self.assertNotIn(forbidden,fields)

if __name__=="__main__":unittest.main()
'''

def tool_text():return '''#!/usr/bin/env python3
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from rom_v2.application.post_combat_hooks import PostCombatHookCoordinator, SettledVictoryEvent, CANONICAL_CONSUMER_ORDER
assert PostCombatHookCoordinator and SettledVictoryEvent and len(CANONICAL_CONSUMER_ORDER)==7
print("STAGE_21_9_6C_POST_COMBAT_HOOKS_SMOKE: PASS")
'''

def run_canonical_ci(r, env):
 tmp=r/"reports/.stage_21_9_6c_ci.tmp.json";tmp.unlink(missing_ok=True)
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
  contract=preflight(r);print("[1/10] [PASS] Stage 21.9.6b zero-unresolved implementation prerequisite verified.");print("[2/10] [PASS] Branch, exact parent, dirty allowlist and clean index verified.")
  b,state=backup(r);print("[3/10] [PASS] Fail-safe backup created before production mutation.")
  write(r,APP,app_text());write(r,TEST,test_text());write(r,TOOL,tool_text());print("[4/10] [PASS] Post-combat coordinator, immutable event/result DTOs and ports implemented.")
  for rel in (SELF,APP,TEST,TOOL):ast.parse((r/rel).read_text(encoding="utf-8"),filename=rel.as_posix())
  p=run([sys.executable,"-m","py_compile",APP.as_posix(),TEST.as_posix(),TOOL.as_posix()],r,False)
  if p.returncode:raise PatchError(f"py_compile_failed:{p.stderr}")
  print("[5/10] [PASS] Python compile gate passed.")
  p=run([sys.executable,"-m","unittest",TEST.as_posix(),"-v"],r,False)
  if p.returncode:raise PatchError(f"integration_tests_failed:{p.stdout}:{p.stderr}")
  print("[6/10] [PASS] Canonical order, exact-once skip, rollback, scope and no-reward-command tests passed.")
  p=run([sys.executable,TOOL.as_posix()],r,False)
  if p.returncode or "SMOKE: PASS" not in p.stdout:raise PatchError(f"smoke_failed:{p.stdout}:{p.stderr}")
  print("[7/10] [PASS] Post-combat hooks smoke check passed.")
  clean(r);env=os.environ.copy();env["PYTHONDONTWRITEBYTECODE"]="1";env["PYTHONHASHSEED"]="0";ci_data=run_canonical_ci(r,env)
  if protected(r)!=before:raise PatchError("protected_runtime_changed")
  prod={line[3:].strip().replace("\\","/") for line in git(r,"status","--porcelain","--untracked-files=all").stdout.splitlines() if line[3:].strip().replace("\\","/").startswith("rom_v2/")}
  if prod!={APP.as_posix()}:raise PatchError(f"unauthorized_production_scope:{sorted(prod)}")
  print("[8/10] [PASS] Canonical V2 CI passed; only authorized post-combat application module changed.")
  out={"schema_version":1,"stage":STAGE,"status":"PASS","conclusion":"API_READY","generated_at_utc":datetime.now(timezone.utc).isoformat(),"source_contract":PREREQ.as_posix(),"application_service":"PostCombatHookCoordinator","implementation":APP.as_posix(),"tests":TEST.as_posix(),"implemented":["immutable_settled_victory_event","canonical_consumer_order","consumer_ports","unit_of_work_port","exact_once_consumer_skip","single_hook_commit","durable_failure_rollback","settled_victory_only","reward_mutation_excluded","presentation_excluded"],"not_connected":["sqlite","production_consumer_adapters","reward_settlement_wiring","runtime","telegram","notifications"],"runtime_integration":"NOT_CONNECTED","production_persistence":"NOT_CONNECTED","manual_game_check":"NOT_REQUIRED","database_opened":False,"v1_wal_shm_manipulated":False,"verification":{"canonical_v2_ci":ci_data}}
  write(r,REPORT,json.dumps(out,ensure_ascii=False,indent=2));write(r,DOC,"""# Stage 21.9.6c - Premium combat modifiers implementation

- Status: **PASS**
- Conclusion: **API_READY**
- Runtime integration: **NOT_CONNECTED**
- Production persistence: **NOT_CONNECTED**
- Manual game check: **NOT_REQUIRED**

Implemented a V2 post-combat application API with an immutable settled-victory event, canonical durable consumer order, explicit consumer and Unit-of-Work ports, exact-once consumer skipping, one hook commit, rollback on durable failure, and no reward mutation commands.

SQLite, production consumer adapters, reward-settlement wiring, runtime, Telegram, and notifications remain excluded.
""");print("[9/10] [PASS] Machine report and Markdown documentation written.")
  expected={x.as_posix() for x in TARGETS};git(r,"add","--",APP.as_posix(),TEST.as_posix(),TOOL.as_posix());git(r,"add","-f","--",SELF.as_posix(),REPORT.as_posix(),DOC.as_posix());staged={x.strip().replace("\\","/") for x in git(r,"diff","--cached","--name-only").stdout.splitlines() if x.strip()}
  if staged!=expected:raise PatchError(f"staging_mismatch:{sorted(staged)}")
  p=git(r,"commit","-m","Stage 21.9.6c: implement Premium combat modifiers",check=False)
  if p.returncode:raise PatchError(f"commit_failed:{p.stdout}:{p.stderr}")
  commit=git(r,"rev-parse","HEAD").stdout.strip();changed={x.strip().replace("\\","/") for x in git(r,"diff-tree","--no-commit-id","--name-only","-r",commit).stdout.splitlines() if x.strip()}
  if changed!=expected:raise PatchError(f"commit_scope:{sorted(changed)}")
  (r/FAILURE).unlink(missing_ok=True);print(f"[10/10] [PASS] Post-combat hooks implementation committed: {commit}");print("CONCLUSION: API_READY");print("PATCH STATUS: PASS");print(f"GIT COMMIT STATUS: PASS ({commit})");print("RUNTIME INTEGRATION: NOT_CONNECTED");print("PRODUCTION PERSISTENCE: NOT_CONNECTED");print("MANUAL GAME CHECK: NOT_REQUIRED");print("FAIL-SAFE ROLLBACK: ARMED");return 0
 except Exception as e:
  restored=restore(r,b,state);recovery=run([sys.executable,"-m","compileall","-q","rom_v2"],r,False);f={"schema_version":1,"stage":STAGE,"status":"FAIL_ROLLED_BACK","failed_at_utc":datetime.now(timezone.utc).isoformat(),"reason":str(e),"restored_files":restored,"recovery_compile_returncode":recovery.returncode,"main_py_allowed_after_recovery":recovery.returncode==0,"database_opened":False,"v1_wal_shm_manipulated":False};p=r/FAILURE;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(f,ensure_ascii=False,indent=2)+"\n",encoding="utf-8");print(f"[10/10] [FAIL] {e}; rollback: FAIL_ROLLED_BACK");return 1
if __name__=="__main__":raise SystemExit(main())
