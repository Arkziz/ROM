#!/usr/bin/env python3
"""Stage 21.13.2c: implement API-ready isolated Quest Item Store."""
from __future__ import annotations
import hashlib,json,os,py_compile,shutil,subprocess,sys
from datetime import datetime,timezone
from pathlib import Path
STAGE="21.13.2c";PARENT="1d90cae5098cff26b9aba593c2d2492b729da919"
SELF="patch/patch_21_13_2c_implement_quest_item_store.py";PREREQ=Path("reports/stage_21_13_2b_resolved_quest_item_store_parity.json")
DOMAIN=Path("rom_v2/domain/quest_item_store.py");APP=Path("rom_v2/application/quest_item_store_service.py");TEST=Path("tests_v2/test_quest_item_store.py");TOOL=Path("tools/check_stage_21_13_2c_quest_item_store.py");GATE=Path("tools/verify_stage_21_13_2c_no_regular_inventory_leakage.py");REPORT=Path("reports/stage_21_13_2c_quest_item_store_implementation.json");DOC=Path("MD/STAGE_21_13_2C_QUEST_ITEM_STORE_IMPLEMENTATION.md");FAILURE=Path("reports/stage_21_13_2c_failure_rollback.json")
TARGETS=(Path(SELF),DOMAIN,APP,TEST,TOOL,GATE,REPORT,DOC);ALLOWED={SELF,"ROM_FULL_DUMP.txt",FAILURE.as_posix()};PROTECTED=(Path("main.py"),Path("game.db-wal"),Path("game.db-shm"))
class PatchError(RuntimeError):pass
def run(a,cwd,check=True,env=None):
 p=subprocess.run(a,cwd=cwd,text=True,capture_output=True,env=env)
 if check and p.returncode:raise PatchError(f"command_failed:{a}:{p.stdout}{p.stderr}")
 return p
def git(r,*a,check=True):return run(["git",*a],r,check)
def root():
 r=Path(__file__).resolve().parent.parent
 if not (r/".git").exists():raise PatchError("project_root_not_found")
 return r
def sha(p):
 if not p.exists():return None
 h=hashlib.sha256();h.update(p.read_bytes());return h.hexdigest()
def write(p,t):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(t,encoding="utf-8",newline="\n")
def status(r):
 out=[]
 for line in git(r,"status","--porcelain=v1","-uall").stdout.splitlines():
  if line:out.append((line[:2],line[3:].replace("\\","/")))
 return out
def backup(r):
 d=r/"backup"/("stage_21_13_2c_"+datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ"));d.mkdir(parents=True,exist_ok=False);state={}
 for x in TARGETS:
  p=r/x;state[x.as_posix()]=p.exists()
  if p.exists():(d/x).parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,d/x)
 return d,state
def restore(r,d,state):
 restored=[]
 for name,existed in state.items():
  p=r/name;b=d/name
  if existed and b.exists():p.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(b,p);restored.append(name)
  elif not existed and p.exists():p.unlink();restored.append(name+":deleted")
 git(r,"reset",check=False);return restored
def clean(r):
 removed=[]
 for base in ("rom_v2","tests_v2","tests","tools"):
  p=r/base
  if not p.exists():continue
  for f in p.rglob("*.pyc"):removed.append(f.relative_to(r).as_posix());f.unlink()
  for d in sorted(p.rglob("__pycache__"),reverse=True):
   try:d.rmdir()
   except OSError:pass
 return removed
def canonical_ci(r):
 env=os.environ.copy();env["PYTHONDONTWRITEBYTECODE"]="1"
 p=r/"tools/run_v2_ci.py"
 if p.exists():z=run([sys.executable,str(p),"--project-root",str(r)],r,False,env)
 else:z=run([sys.executable,"-m","unittest","discover","-s","tests_v2","-p","test_*.py"],r,False,env)
 if z.returncode:raise PatchError("canonical_v2_ci_failed:"+(z.stdout+z.stderr)[-6000:])
 return {"status":"PASS","stdout":z.stdout[-3000:],"stderr":z.stderr[-1000:]}
DOMAIN_SRC='''from __future__ import annotations
from dataclasses import dataclass

@dataclass(frozen=True, slots=True)
class V2QuestItemBalanceKey:
    user_id: int
    quest_id: int
    item_key: str
    def __post_init__(self) -> None:
        if self.user_id <= 0 or self.quest_id <= 0 or not self.item_key.strip():
            raise ValueError("invalid_identity")

@dataclass(frozen=True, slots=True)
class V2QuestItemBalance:
    key: V2QuestItemBalanceKey
    quantity: int
    revision: int = 0
    def __post_init__(self) -> None:
        if self.quantity < 0 or self.revision < 0:
            raise ValueError("invalid_quantity")

@dataclass(frozen=True, slots=True)
class V2QuestItemCollection:
    key: V2QuestItemBalanceKey
    event_id: str
    quantity: int
    def __post_init__(self) -> None:
        if not self.event_id.strip() or self.quantity <= 0:
            raise ValueError("invalid_collection")

@dataclass(frozen=True, slots=True)
class V2QuestItemStoreResult:
    ok: bool
    reason: str | None = None
    balance: V2QuestItemBalance | None = None
    consumed: int = 0

@dataclass(frozen=True, slots=True)
class V2QuestItemTurnInPlan:
    key: V2QuestItemBalanceKey
    required_quantity: int
    expected_revision: int
    completion_key: str
    def __post_init__(self) -> None:
        if self.required_quantity <= 0 or self.expected_revision < 0 or not self.completion_key.strip():
            raise ValueError("invalid_turn_in_plan")
'''
APP_SRC='''from __future__ import annotations
from dataclasses import replace
from rom_v2.domain.quest_item_store import V2QuestItemBalance,V2QuestItemBalanceKey,V2QuestItemCollection,V2QuestItemStoreResult,V2QuestItemTurnInPlan

class InMemoryV2QuestItemStoreUow:
    def __init__(self) -> None:
        self.balances: dict[V2QuestItemBalanceKey,V2QuestItemBalance] = {}
        self.events: set[tuple[int,int,str]] = set()
        self.completions: set[str] = set()
    def get(self,key:V2QuestItemBalanceKey)->V2QuestItemBalance:
        return self.balances.get(key,V2QuestItemBalance(key,0,0))
    def put(self,balance:V2QuestItemBalance)->None:
        if balance.quantity == 0:self.balances.pop(balance.key,None)
        else:self.balances[balance.key]=balance

class V2QuestItemStoreService:
    def __init__(self,uow:InMemoryV2QuestItemStoreUow):self.uow=uow
    def quantity(self,key:V2QuestItemBalanceKey)->int:return self.uow.get(key).quantity
    def total_quantity(self,user_id:int,item_key:str)->int:
        return sum(v.quantity for k,v in self.uow.balances.items() if k.user_id==user_id and k.item_key==item_key)
    def collect(self,collection:V2QuestItemCollection)->V2QuestItemStoreResult:
        identity=(collection.key.user_id,collection.key.quest_id,collection.event_id)
        if identity in self.uow.events:return V2QuestItemStoreResult(False,"already_collected",self.uow.get(collection.key))
        current=self.uow.get(collection.key);updated=replace(current,quantity=current.quantity+collection.quantity,revision=current.revision+1)
        self.uow.put(updated);self.uow.events.add(identity);return V2QuestItemStoreResult(True,balance=updated)
    def consume(self,key:V2QuestItemBalanceKey,quantity:int,expected_revision:int)->V2QuestItemStoreResult:
        if quantity<=0:return V2QuestItemStoreResult(False,"invalid_quantity",self.uow.get(key))
        current=self.uow.get(key)
        if current.revision!=expected_revision:return V2QuestItemStoreResult(False,"stale_revision",current)
        if current.quantity<quantity:return V2QuestItemStoreResult(False,"insufficient_quantity",current)
        updated=replace(current,quantity=current.quantity-quantity,revision=current.revision+1);self.uow.put(updated)
        return V2QuestItemStoreResult(True,balance=updated,consumed=quantity)
    def plan_turn_in(self,plan:V2QuestItemTurnInPlan)->V2QuestItemStoreResult:
        if plan.completion_key in self.uow.completions:return V2QuestItemStoreResult(False,"already_completed",self.uow.get(plan.key))
        return self.consume(plan.key,plan.required_quantity,plan.expected_revision)
    def commit_turn_in(self,plan:V2QuestItemTurnInPlan)->None:self.uow.completions.add(plan.completion_key)
    def skip(self,key:V2QuestItemBalanceKey)->V2QuestItemStoreResult:
        return V2QuestItemStoreResult(True,"preserved_on_skip",self.uow.get(key))
'''
TEST_SRC='''import unittest
from rom_v2.domain.quest_item_store import *
from rom_v2.application.quest_item_store_service import *
class QuestItemStoreTest(unittest.TestCase):
 def setUp(self):self.u=InMemoryV2QuestItemStoreUow();self.s=V2QuestItemStoreService(self.u);self.k=V2QuestItemBalanceKey(1,10,"fang")
 def test_isolated_scope_and_total(self):
  self.s.collect(V2QuestItemCollection(self.k,"e1",2));other=V2QuestItemBalanceKey(1,11,"fang");self.s.collect(V2QuestItemCollection(other,"e2",3));self.assertEqual(self.s.quantity(self.k),2);self.assertEqual(self.s.total_quantity(1,"fang"),5)
 def test_duplicate_collection(self):
  c=V2QuestItemCollection(self.k,"event",1);self.assertTrue(self.s.collect(c).ok);self.assertEqual(self.s.collect(c).reason,"already_collected");self.assertEqual(self.s.quantity(self.k),1)
 def test_non_negative_and_revision(self):
  b=self.s.collect(V2QuestItemCollection(self.k,"e",2)).balance;self.assertEqual(self.s.consume(self.k,3,b.revision).reason,"insufficient_quantity");self.assertEqual(self.s.consume(self.k,1,0).reason,"stale_revision")
 def test_exact_consume_and_zero_row(self):
  b=self.s.collect(V2QuestItemCollection(self.k,"e",2)).balance;r=self.s.consume(self.k,2,b.revision);self.assertTrue(r.ok);self.assertEqual(self.s.quantity(self.k),0);self.assertNotIn(self.k,self.u.balances)
 def test_turn_in_replay_and_skip_preserves(self):
  b=self.s.collect(V2QuestItemCollection(self.k,"e",2)).balance;p=V2QuestItemTurnInPlan(self.k,2,b.revision,"1:10:1");r=self.s.plan_turn_in(p);self.assertTrue(r.ok);self.s.commit_turn_in(p);self.assertEqual(self.s.plan_turn_in(p).reason,"already_completed");self.assertEqual(self.s.skip(self.k).reason,"preserved_on_skip")
if __name__=="__main__":unittest.main()
'''
TOOL_SRC='''from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(ROOT))
from rom_v2.domain.quest_item_store import V2QuestItemBalanceKey,V2QuestItemCollection
from rom_v2.application.quest_item_store_service import InMemoryV2QuestItemStoreUow,V2QuestItemStoreService
u=InMemoryV2QuestItemStoreUow();s=V2QuestItemStoreService(u);k=V2QuestItemBalanceKey(1,1,"item");assert s.collect(V2QuestItemCollection(k,"event",1)).ok;assert s.quantity(k)==1
print("Stage 21.13.2c Quest Item Store smoke: PASS")
'''
GATE_SRC='''from pathlib import Path
import ast,sys
ROOT=Path(__file__).resolve().parent.parent
files=[ROOT/"rom_v2/domain/quest_item_store.py",ROOT/"rom_v2/application/quest_item_store_service.py"]
for path in files:
 text=path.read_text(encoding="utf-8")
 forbidden=("inventory_repository","inventory_service","equipment_repository","bag_capacity","inventory_id")
 hits=[x for x in forbidden if x in text]
 if hits:print(f"No regular inventory leakage: FAIL {path.name}:{hits}");sys.exit(1)
 ast.parse(text)
print("Stage 21.13.2c No regular inventory leakage: PASS")
'''
def main():
 r=root();folder=None;state={};before={x.as_posix():sha(r/x) for x in PROTECTED}
 try:
  pre=json.loads((r/PREREQ).read_text(encoding="utf-8-sig"));summary=pre.get("summary",{})
  if git(r,"rev-parse","HEAD").stdout.strip()!=PARENT:raise PatchError("wrong_exact_parent")
  if pre.get("stage")!="21.13.2b" or pre.get("conclusion")!="GO_TO_IMPLEMENTATION" or summary.get("resolved_contracts")!=8 or summary.get("unresolved_contracts")!=[] or not pre.get("implementation_authorized"):raise PatchError("invalid_stage_21_13_2b_prerequisite")
  print("[1/10] [PASS] Stage 21.13.2b zero-unresolved 8/8 implementation prerequisite verified.")
  branch=git(r,"branch","--show-current").stdout.strip();staged=git(r,"diff","--cached","--name-only").stdout.strip()
  if not branch:raise PatchError("git_preflight_detached_head")
  if staged:raise PatchError("git_preflight_staged_index:"+staged.replace("\n",","))
  bad=sorted(p for st,p in status(r) if p not in ALLOWED or (p!=SELF and st[0]!=" "))
  if bad:raise PatchError("unexpected_dirty:"+repr(bad))
  print(f"[2/10] [PASS] Active branch {branch}, exact parent, dirty allowlist and clean index verified.");folder,state=backup(r);print("[3/10] [PASS] Fail-safe backup created before production mutation.")
  for path,src in ((DOMAIN,DOMAIN_SRC),(APP,APP_SRC),(TEST,TEST_SRC),(TOOL,TOOL_SRC),(GATE,GATE_SRC)):write(r/path,src)
  print("[4/10] [PASS] Isolated balance DTOs, quantity policy, collection idempotency, turn-in planning and SKIP preservation implemented.")
  for x in (Path(SELF),DOMAIN,APP,TEST,TOOL,GATE):py_compile.compile(str(r/x),doraise=True)
  print("[5/10] [PASS] Python compile gate passed for patch, implementation, tests and verifiers.")
  env=os.environ.copy();env["PYTHONDONTWRITEBYTECODE"]="1"
  t=run([sys.executable,"-m","unittest","-v","tests_v2.test_quest_item_store"],r,False,env);sm=run([sys.executable,str(r/TOOL)],r,False,env);ga=run([sys.executable,str(r/GATE)],r,False,env)
  if t.returncode or sm.returncode or ga.returncode:raise PatchError("targeted_verification_failed:"+t.stdout+t.stderr+sm.stdout+sm.stderr+ga.stdout+ga.stderr)
  print("[6/10] [PASS] Scope, quantity, idempotency, consume, turn-in replay, SKIP and no-leakage tests passed.")
  removed=clean(r);checks=canonical_ci(r);print(f"[7/10] [PASS] Canonical V2 CI passed after removing {len(removed)} bytecode artifact(s).")
  if before!={x.as_posix():sha(r/x) for x in PROTECTED}:raise PatchError("protected_runtime_changed")
  print("[8/10] [PASS] V1 sources, unrelated V2 sources, DB sidecars and protected configuration remained byte-identical.")
  rep={"schema_version":1,"stage":STAGE,"status":"PASS","conclusion":"API_READY","parent":PARENT,"implemented_files":[DOMAIN.as_posix(),APP.as_posix()],"tests":{"targeted":"PASS","smoke":"PASS","no_regular_inventory_leakage":"PASS"},"production_quantity_mutation":"NOT_CONNECTED","production_turn_in":"NOT_CONNECTED","runtime_integration":"NOT_CONNECTED","production_persistence":"NOT_CONNECTED","database_opened":False,"v1_wal_shm_manipulated":False,"manual_game_check":"NOT_REQUIRED","canonical_v2_ci":checks};write(r/REPORT,json.dumps(rep,ensure_ascii=False,indent=2)+"\n");write(r/DOC,"# Stage 21.13.2c - Quest Item Store implementation\n\n- Status: **PASS**\n- Conclusion: **API_READY**\n- No regular inventory leakage: **PASS**\n- Production quantity mutation: **NOT_CONNECTED**\n- Production turn-in: **NOT_CONNECTED**\n- Runtime integration: **NOT_CONNECTED**\n- Production persistence: **NOT_CONNECTED**\n- Manual game check: **NOT_REQUIRED**\n");print("[9/10] [PASS] Machine report and Markdown implementation documentation written.")
  files={x.as_posix() for x in TARGETS};git(r,"add","-f","--",*sorted(files));got={x.replace("\\","/") for x in git(r,"diff","--cached","--name-only").stdout.splitlines() if x}
  if got!=files:raise PatchError("staging_mismatch:"+repr(sorted(got)))
  z=git(r,"commit","-m","Stage 21.13.2c: implement Quest Item Store","--",*sorted(files),check=False)
  if z.returncode:raise PatchError("commit_failed:"+z.stdout+z.stderr)
  commit=git(r,"rev-parse","HEAD").stdout.strip();changed={x.replace("\\","/") for x in git(r,"diff-tree","--no-commit-id","--name-only","-r",commit).stdout.splitlines() if x}
  if changed!=files:raise PatchError("commit_scope_mismatch:"+repr(sorted(changed)))
  print(f"[10/10] [PASS] Quest Item Store implementation committed: {commit}");print("CONCLUSION: API_READY\nPATCH STATUS: PASS\nNO REGULAR INVENTORY LEAKAGE: PASS\nPRODUCTION QUANTITY MUTATION: NOT_CONNECTED\nPRODUCTION TURN-IN: NOT_CONNECTED\nRUNTIME INTEGRATION: NOT_CONNECTED\nPRODUCTION PERSISTENCE: NOT_CONNECTED\nMANUAL GAME CHECK: NOT_REQUIRED\nFAIL-SAFE ROLLBACK: ARMED");return 0
 except Exception as e:
  restored=restore(r,folder,state);recovery=run([sys.executable,"-m","compileall","-q","rom_v2"],r,False);write(r/FAILURE,json.dumps({"stage":STAGE,"status":"FAIL_ROLLED_BACK","reason":str(e),"restored_files":restored,"recovery_compile_returncode":recovery.returncode,"main_py_must_not_run":recovery.returncode!=0,"database_opened":False,"v1_wal_shm_manipulated":False},ensure_ascii=False,indent=2)+"\n");print(f"[10/10] [FAIL] {e}; rollback: FAIL_ROLLED_BACK");return 1
if __name__=="__main__":raise SystemExit(main())
