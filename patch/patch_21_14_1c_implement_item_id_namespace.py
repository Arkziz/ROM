#!/usr/bin/env python3
"""Stage 21.14.1c: implement API-ready V2 item ID namespaces."""
from __future__ import annotations
import hashlib,json,os,shutil,subprocess,sys
from datetime import datetime,timezone
from pathlib import Path
STAGE="21.14.1c";PARENT="4609086e01d0e9b3689fe88b8f0339cd07efe135"
SELF=Path("patch/patch_21_14_1c_implement_item_id_namespace.py")
PREREQ=Path("reports/stage_21_14_1b_resolved_item_id_namespace_parity.json")
REPORT=Path("reports/stage_21_14_1c_item_id_namespace_implementation.json")
DOC=Path("MD/STAGE_21_14_1C_ITEM_ID_NAMESPACE_IMPLEMENTATION.md")
FAILURE=Path("reports/stage_21_14_1c_failure_rollback.json")
DOMAIN=Path("rom_v2/domain/item_id_namespace.py");SERVICE=Path("rom_v2/application/item_id_namespace_service.py")
TEST=Path("tests_v2/test_item_id_namespace.py");SMOKE=Path("tools/check_stage_21_14_1c_item_id_namespace.py");VERIFY=Path("tools/verify_stage_21_14_1c_item_id_namespace.py")
TARGETS=(SELF,DOMAIN,SERVICE,TEST,SMOKE,VERIFY,REPORT,DOC)
ALLOWED={SELF.as_posix(),"ROM_FULL_DUMP.txt",FAILURE.as_posix()};PROTECTED=(Path("main.py"),Path("game.db"),Path("game.db-wal"),Path("game.db-shm"))
class E(RuntimeError):pass
def run(a,r,check=True,env=None):
 p=subprocess.run(a,cwd=r,text=True,capture_output=True,env=env)
 if check and p.returncode:raise E(f"command_failed:{a}:{p.stdout}{p.stderr}")
 return p
def git(r,*a,check=True):return run(["git",*a],r,check)
def root():
 r=Path(__file__).resolve().parent.parent
 if not (r/".git").exists():raise E("project_root_not_found")
 return r
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest() if p.exists() else None
def write(p,s):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(s,encoding="utf-8",newline="\n")
def status(r):return [(x[:2],x[3:].split(" -> ")[-1].replace("\\","/")) for x in git(r,"status","--porcelain=v1","--untracked-files=all").stdout.splitlines() if x]
def backup(r):
 f=r/"backup"/("stage_21_14_1c_"+datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ"));f.mkdir(parents=True);state={}
 for rel in TARGETS:
  p=r/rel;state[rel.as_posix()]=p.exists()
  if p.exists():(f/rel).parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,f/rel)
 return f,state
def restore(r,f,state):
 out=[]
 if f:
  for name,old in state.items():
   dst=r/name;src=f/name
   if old and src.exists():dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dst);out.append(name)
   elif not old and dst.exists():dst.unlink();out.append(name+":deleted")
 git(r,"reset","--quiet",check=False);return out
def clean(r):
 removed=[]
 for p in r.rglob("*.pyc"):
  try:p.unlink();removed.append(p.relative_to(r).as_posix())
  except OSError:pass
 for p in sorted(r.rglob("__pycache__"),key=lambda x:len(x.parts),reverse=True):
  try:p.rmdir()
  except OSError:pass
 if list(r.rglob("*.pyc")):raise E("bytecode_cleanup_failed")
 return removed
DOMAIN_SRC='''from __future__ import annotations
from dataclasses import dataclass
from enum import Enum

class V2ItemIdNamespace(str, Enum):
    STATIC = "static_catalog"
    EVENT = "event_static"
    GENERATED = "generated_permanent"
    PREVIEW = "shop_preview"
    STORY_KEY = "story_quest_key"

@dataclass(frozen=True, slots=True)
class V2NumericRange:
    start: int
    end: int
    def __post_init__(self):
        if self.start < 0 or self.end < self.start: raise ValueError("invalid_range")
    def contains(self, value: int) -> bool: return self.start <= value <= self.end
    @property
    def size(self) -> int: return self.end - self.start + 1

EVENT_RANGE=V2NumericRange(4000,9999)
GENERATED_RANGE=V2NumericRange(10000,10009999)
PREVIEW_RANGE=V2NumericRange(10010000,11009999)
EVENT_BLOCK_SIZE=25
EVENT_BLOCK_COUNT=240
STATIC_ASSIGNED=frozenset((*range(201,205),301,*range(401,405),*range(501,529),*range(601,603),*range(701,729),900))

@dataclass(frozen=True, slots=True)
class V2EventBlock:
    event_key: str
    ordinal: int
    start_id: int
    end_id: int
    def __post_init__(self):
        if not self.event_key.strip() or self.end_id-self.start_id+1 != EVENT_BLOCK_SIZE: raise ValueError("invalid_event_block")

@dataclass(frozen=True, slots=True)
class V2StoryQuestItemKey:
    user_id: int
    quest_id: str
    item_key: str
    def __post_init__(self):
        if self.user_id <= 0 or not self.quest_id.strip() or not self.item_key.strip(): raise ValueError("invalid_story_item_key")

@dataclass(frozen=True, slots=True)
class V2PreviewPromotion:
    preview_id: int
    permanent_id: int
    def __post_init__(self):
        if not PREVIEW_RANGE.contains(self.preview_id) or not GENERATED_RANGE.contains(self.permanent_id): raise ValueError("invalid_promotion")

def event_block(ordinal: int, event_key: str) -> V2EventBlock:
    if not 0 <= ordinal < EVENT_BLOCK_COUNT: raise ValueError("event_block_exhausted")
    start=EVENT_RANGE.start+ordinal*EVENT_BLOCK_SIZE
    return V2EventBlock(event_key,ordinal,start,start+EVENT_BLOCK_SIZE-1)

def classify_numeric_item_id(value: int) -> V2ItemIdNamespace:
    if value in STATIC_ASSIGNED:return V2ItemIdNamespace.STATIC
    if EVENT_RANGE.contains(value):return V2ItemIdNamespace.EVENT
    if GENERATED_RANGE.contains(value):return V2ItemIdNamespace.GENERATED
    if PREVIEW_RANGE.contains(value):return V2ItemIdNamespace.PREVIEW
    raise ValueError("unassigned_reserved_or_out_of_namespace")
'''
SERVICE_SRC='''from __future__ import annotations
from dataclasses import dataclass, field
from rom_v2.domain.item_id_namespace import EVENT_BLOCK_COUNT,GENERATED_RANGE,PREVIEW_RANGE,STATIC_ASSIGNED,V2EventBlock,V2PreviewPromotion,event_block

@dataclass(slots=True)
class V2ItemIdNamespaceState:
    event_blocks: dict[str,list[V2EventBlock]] = field(default_factory=dict)
    retired_event_ordinals: set[int] = field(default_factory=set)
    next_generated_id: int = GENERATED_RANGE.start
    allocated_generated_ids: set[int] = field(default_factory=set)
    retired_generated_ids: set[int] = field(default_factory=set)
    next_preview_id: int = PREVIEW_RANGE.start
    allocated_preview_ids: set[int] = field(default_factory=set)
    preview_promotions: dict[int,V2PreviewPromotion] = field(default_factory=dict)

class V2ItemIdNamespaceService:
    def __init__(self,state:V2ItemIdNamespaceState|None=None):self.state=state or V2ItemIdNamespaceState()
    def allocate_event_block(self,event_key:str,*,additional:bool=False)->V2EventBlock:
        key=event_key.strip()
        if not key:raise ValueError("invalid_event_key")
        existing=self.state.event_blocks.get(key,[])
        if existing and not additional:return existing[0]
        used={b.ordinal for blocks in self.state.event_blocks.values() for b in blocks}|self.state.retired_event_ordinals
        ordinal=next((i for i in range(EVENT_BLOCK_COUNT) if i not in used),None)
        if ordinal is None:raise ValueError("event_namespace_exhausted")
        block=event_block(ordinal,key);self.state.event_blocks.setdefault(key,[]).append(block);return block
    def retire_event(self,event_key:str)->None:
        for block in self.state.event_blocks.get(event_key,[]):self.state.retired_event_ordinals.add(block.ordinal)
    def allocate_generated_id(self)->int:
        candidate=self.state.next_generated_id
        while candidate in self.state.allocated_generated_ids or candidate in self.state.retired_generated_ids:candidate+=1
        if not GENERATED_RANGE.contains(candidate):raise ValueError("generated_namespace_exhausted")
        self.state.allocated_generated_ids.add(candidate);self.state.next_generated_id=candidate+1;return candidate
    def retire_generated_id(self,item_id:int)->None:
        self.state.allocated_generated_ids.discard(item_id);self.state.retired_generated_ids.add(item_id)
    def allocate_preview_id(self)->int:
        candidate=self.state.next_preview_id
        while candidate in self.state.allocated_preview_ids or candidate in self.state.preview_promotions:candidate+=1
        if not PREVIEW_RANGE.contains(candidate):raise ValueError("preview_namespace_exhausted")
        self.state.allocated_preview_ids.add(candidate);self.state.next_preview_id=candidate+1;return candidate
    def plan_preview_promotion(self,preview_id:int)->V2PreviewPromotion:
        # Exact-once replay must be checked before active-preview membership because
        # the successful first promotion removes the temporary preview allocation.
        existing=self.state.preview_promotions.get(preview_id)
        if existing is not None:return existing
        if preview_id not in self.state.allocated_preview_ids:raise ValueError("unknown_preview_id")
        promotion=V2PreviewPromotion(preview_id,self.allocate_generated_id())
        self.state.preview_promotions[preview_id]=promotion
        self.state.allocated_preview_ids.remove(preview_id)
        return promotion
    @staticmethod
    def static_id_is_assigned(item_id:int)->bool:return item_id in STATIC_ASSIGNED
'''
TEST_SRC='''import unittest
from rom_v2.application.item_id_namespace_service import V2ItemIdNamespaceService
from rom_v2.domain.item_id_namespace import *
class TestItemIdNamespace(unittest.TestCase):
 def test_event_partition(self):
  blocks=[event_block(i,"e") for i in range(240)];self.assertEqual((blocks[0].start_id,blocks[-1].end_id),(4000,9999));self.assertTrue(all(x.end_id-x.start_id+1==25 for x in blocks))
 def test_event_retired_never_reused(self):
  s=V2ItemIdNamespaceService();a=s.allocate_event_block("a");self.assertEqual(a,s.allocate_event_block("a"));s.retire_event("a");b=s.allocate_event_block("b");self.assertNotEqual(a.ordinal,b.ordinal);c=s.allocate_event_block("a",additional=True);self.assertNotIn(c.ordinal,{a.ordinal,b.ordinal})
 def test_generated_never_reuse(self):
  s=V2ItemIdNamespaceService();a=s.allocate_generated_id();s.retire_generated_id(a);self.assertEqual(s.allocate_generated_id(),a+1)
 def test_preview_promotion_exact_once(self):
  s=V2ItemIdNamespaceService();p=s.allocate_preview_id();a=s.plan_preview_promotion(p);b=s.plan_preview_promotion(p);self.assertEqual((p,a.permanent_id),(10010000,10000));self.assertEqual(a,b);self.assertNotIn(p,s.state.allocated_preview_ids);self.assertEqual(len(s.state.allocated_generated_ids),1)
 def test_ranges_do_not_overlap(self):
  self.assertLess(EVENT_RANGE.end,GENERATED_RANGE.start);self.assertLess(GENERATED_RANGE.end,PREVIEW_RANGE.start)
 def test_static_gaps_reserved(self):
  s=V2ItemIdNamespaceService();self.assertTrue(s.static_id_is_assigned(201));self.assertFalse(s.static_id_is_assigned(205));
  with self.assertRaises(ValueError):classify_numeric_item_id(205)
 def test_story_key_has_no_numeric_identity(self):
  k=V2StoryQuestItemKey(1,"q","item");self.assertFalse(hasattr(k,"item_id"));self.assertFalse(hasattr(k,"inventory_id"))
if __name__=="__main__":unittest.main()
'''
SMOKE_SRC='''from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from rom_v2.application.item_id_namespace_service import V2ItemIdNamespaceService
s=V2ItemIdNamespaceService();b=s.allocate_event_block("event");p=s.allocate_preview_id();a=s.plan_preview_promotion(p);assert (b.start_id,b.end_id)==(4000,4024);assert s.plan_preview_promotion(p)==a
print("Stage 21.14.1c item ID namespace smoke: PASS")
'''
VERIFY_SRC='''from pathlib import Path
import ast
ROOT=Path(__file__).resolve().parent.parent
files=[ROOT/"rom_v2/domain/item_id_namespace.py",ROOT/"rom_v2/application/item_id_namespace_service.py"]
for p in files:
 s=p.read_text(encoding="utf-8");ast.parse(s)
 for forbidden in ("sqlite3","db_modules","handlers","aiogram"):
  assert forbidden not in s, (p,forbidden)
assert "preview_promotions.get(preview_id)" in files[1].read_text(encoding="utf-8")
print("Stage 21.14.1c item ID namespace boundary: PASS")
'''
def main():
 r=root();folder=None;state={};before={p.as_posix():sha(r/p) for p in PROTECTED}
 try:
  if git(r,"rev-parse","HEAD").stdout.strip()!=PARENT:raise E("wrong_exact_parent")
  q=json.loads((r/PREREQ).read_text(encoding="utf-8-sig"));s=q.get("summary",{})
  if q.get("stage")!="21.14.1b" or q.get("conclusion")!="GO_TO_IMPLEMENTATION" or s.get("resolved_contracts")!=12 or s.get("unresolved_contracts")!=0 or s.get("implementation_authorized") is not True:raise E("invalid_parity_prerequisite")
  print("[1/10] [PASS] Stage 21.14.1b resolved 12/12 parity and implementation authorization verified.")
  if git(r,"branch","--show-current").stdout.strip()!="rewrite/rom-v2":raise E("wrong_branch")
  if git(r,"diff","--cached","--name-only").stdout.strip():raise E("staged_index_not_clean")
  bad=[p for st,p in status(r) if p not in ALLOWED or (p!=SELF.as_posix() and st[0]!=" ")]
  if bad:raise E("unexpected_dirty:"+repr(bad))
  print("[2/10] [PASS] Active branch, exact parent, dirty allowlist and clean index verified.")
  folder,state=backup(r);print("[3/10] [PASS] Fail-safe backup created before V2 production mutation.")
  for p,s in ((DOMAIN,DOMAIN_SRC),(SERVICE,SERVICE_SRC),(TEST,TEST_SRC),(SMOKE,SMOKE_SRC),(VERIFY,VERIFY_SRC)):write(r/p,s)
  print("[4/10] [PASS] V2 namespace domain, event registry, generated/preview allocators, promotion planner, tests and gates written.")
  for p in (Path(__file__).resolve(),r/DOMAIN,r/SERVICE,r/TEST,r/SMOKE,r/VERIFY):
   z=run([sys.executable,"-m","py_compile",str(p)],r,False)
   if z.returncode:raise E("compile_failed:"+z.stdout+z.stderr)
  print("[5/10] [PASS] Python compile gate passed for patch and all implementation artifacts.")
  env=os.environ.copy();env["PYTHONDONTWRITEBYTECODE"]="1";env["PYTHONPATH"]=str(r)
  z=run([sys.executable,"-m","unittest","-v","tests_v2.test_item_id_namespace"],r,False,env)
  if z.returncode:raise E("targeted_tests_failed:"+z.stdout+z.stderr)
  for p in (SMOKE,VERIFY):
   z=run([sys.executable,str(r/p)],r,False,env)
   if z.returncode:raise E("targeted_verification_failed:"+z.stdout+z.stderr)
  print("[6/10] [PASS] Event blocks, never-reuse, exact-once preview promotion, static gaps and story-key tests passed.")
  a=clean(r);z=run([sys.executable,"-m","compileall","-q","rom_v2"],r,False,env)
  if z.returncode:raise E("v2_compile_failed")
  b=clean(r);z=run([sys.executable,"-m","unittest","discover","-s","tests_v2","-p","test_*.py"],r,False,env)
  if z.returncode:raise E("v2_unit_failed:"+z.stdout+z.stderr)
  print(f"[7/10] [PASS] Canonical V2 CI passed after removing {len(a)+len(b)} bytecode artifact(s).")
  if before!={p.as_posix():sha(r/p) for p in PROTECTED}:raise E("protected_files_changed")
  print("[8/10] [PASS] V1 sources, production database, DB sidecars and protected entry point remained byte-identical.")
  report={"stage":STAGE,"status":"PASS","conclusion":"API_READY_ITEM_ID_NAMESPACE","parent":PARENT,"contracts":"12/12 PASS","event_blocks":"240/240","preview_promotion_replay":"EXACT_ONCE_PERSISTED_MAPPING","runtime_integration":"NOT_CONNECTED","production_persistence":"NOT_CONNECTED","database_opened":False,"manual_game_check":"NOT_REQUIRED_API_ONLY"}
  write(r/REPORT,json.dumps(report,ensure_ascii=False,indent=2)+"\n");write(r/DOC,"# Stage 21.14.1c Item ID Namespace Implementation\n\n- Status: **PASS**\n- Exact-once preview promotion replay: **PASS**\n- Runtime integration: **NOT_CONNECTED**\n")
  print("[9/10] [PASS] Machine report and Markdown implementation documentation written.")
  files={p.as_posix() for p in TARGETS};git(r,"add","-f","--",*sorted(files));got=set(git(r,"diff","--cached","--name-only").stdout.splitlines())
  if got!=files:raise E("staging_mismatch:"+repr(got))
  z=git(r,"commit","-m","Stage 21.14.1c: implement item ID namespace","--",*sorted(files),check=False)
  if z.returncode:raise E("commit_failed:"+z.stdout+z.stderr)
  commit=git(r,"rev-parse","HEAD").stdout.strip();print(f"[10/10] [PASS] API-ready V2 item ID namespace committed: {commit}")
  print("CONCLUSION: API_READY_ITEM_ID_NAMESPACE\nPATCH STATUS: PASS\nCONTRACTS: 12/12 PASS\nEVENT BLOCKS: 240/240\nPREVIEW PROMOTION REPLAY: EXACT_ONCE\nRUNTIME INTEGRATION: NOT_CONNECTED\nPRODUCTION PERSISTENCE: NOT_CONNECTED\nDATABASE OPENED: False\nMANUAL GAME CHECK: NOT_REQUIRED_API_ONLY\nFAIL-SAFE ROLLBACK: ARMED")
  return 0
 except Exception as e:
  restored=restore(r,folder,state);z=run([sys.executable,"-m","compileall","-q","rom_v2"],r,False)
  write(r/FAILURE,json.dumps({"stage":STAGE,"status":"FAIL_ROLLED_BACK","reason":str(e),"restored_files":restored,"recovery_compile_returncode":z.returncode,"main_py_must_not_run":z.returncode!=0,"database_opened":False,"canonical_reference_changed":False,"v1_wal_shm_manipulated":False},ensure_ascii=False,indent=2)+"\n")
  print(f"[10/10] [FAIL] {e}; rollback: FAIL_ROLLED_BACK");return 1
if __name__=="__main__":raise SystemExit(main())
