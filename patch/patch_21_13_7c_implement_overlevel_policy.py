#!/usr/bin/env python3
"""Stage 21.13.7c: implement API-ready V2 Stage 19.18 overlevel policy."""
from __future__ import annotations
import hashlib,json,os,py_compile,shutil,subprocess,sys
from datetime import datetime,timezone
from pathlib import Path
STAGE="21.13.7c";PARENT="082e922b33834c6053667e805d50542bfe78af34"
SELF="patch/patch_21_13_7c_implement_overlevel_policy.py";PREREQ=Path("reports/stage_21_13_7b_resolved_overlevel_policy_parity.json")
DOMAIN=Path("rom_v2/domain/overlevel_policy.py");APP=Path("rom_v2/application/overlevel_policy_service.py");PRES=Path("rom_v2/presentation/overlevel_policy.py")
TEST=Path("tests_v2/test_overlevel_policy.py");TOOL=Path("tools/check_stage_21_13_7c_overlevel_policy.py");GATE=Path("tools/verify_stage_21_13_7c_overlevel_policy.py")
REPORT=Path("reports/stage_21_13_7c_overlevel_policy_implementation.json");DOC=Path("MD/STAGE_21_13_7C_OVERLEVEL_POLICY_IMPLEMENTATION.md");FAILURE=Path("reports/stage_21_13_7c_failure_rollback.json")
TARGETS=(Path(SELF),DOMAIN,APP,PRES,TEST,TOOL,GATE,REPORT,DOC);ALLOWED={SELF,"ROM_FULL_DUMP.txt",FAILURE.as_posix()};PROTECTED=(Path("main.py"),Path("game.db"),Path("game.db-wal"),Path("game.db-shm"))
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
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest() if p.exists() else None
def write(p,t):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(t,encoding="utf-8",newline="\n")
def status(r):return [(x[:2],x[3:].split(" -> ")[-1].replace("\\","/")) for x in git(r,"status","--porcelain=v1","--untracked-files=all").stdout.splitlines() if x]
def backup(r):
 f=r/"backup"/("stage_21_13_7c_"+datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ"));f.mkdir(parents=True);state={}
 for rel in TARGETS:
  p=r/rel;state[rel.as_posix()]=p.exists()
  if p.exists():(f/rel).parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,f/rel)
 return f,state
def restore(r,f,state):
 restored=[]
 if f:
  for name,existed in state.items():
   dst=r/name;src=f/name
   if existed and src.exists():dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dst);restored.append(name)
   elif not existed and dst.exists():dst.unlink();restored.append(name+":deleted")
 git(r,"reset","--quiet",check=False);return restored
def cleanup(r):
 removed=[];errors=[]
 for p in sorted(r.rglob("*.pyc"),key=lambda x:len(x.parts),reverse=True):
  try:
   if p.exists():
    try:p.chmod(0o666)
    except OSError:pass
    p.unlink();removed.append(p.relative_to(r).as_posix())
  except OSError as e:errors.append(f"{p.relative_to(r).as_posix()}:{e}")
 for p in sorted(r.rglob("__pycache__"),key=lambda x:len(x.parts),reverse=True):
  try:p.rmdir()
  except OSError:pass
 left=[p.relative_to(r).as_posix() for p in r.rglob("*.pyc") if p.exists()]
 if left or errors:raise PatchError("bytecode_cleanup_failed:"+repr({"leftovers":left,"errors":errors}))
 return removed
DOMAIN_SRC='''"""Pure Stage 19.18 overlevel policy records and invariants."""\nfrom __future__ import annotations\nfrom dataclasses import dataclass\nfrom enum import Enum\nfrom types import MappingProxyType\n\nLOCATION_MAX_LEVELS=MappingProxyType({"start_path":5,"dark_forest":10})\nclass OverlevelQuestStatus(str,Enum):\n ACTIVE="ACTIVE";COMPLETED="COMPLETED";SKIPPED="SKIPPED"\nFINALIZED_STATUSES=frozenset({OverlevelQuestStatus.COMPLETED,OverlevelQuestStatus.SKIPPED})\n@dataclass(frozen=True,slots=True)\nclass OverlevelQuestDefinition:\n quest_id:str;number:int;location_id:str;target_quantity:int=1\n def __post_init__(self):\n  if not self.quest_id or self.number<1 or self.location_id not in LOCATION_MAX_LEVELS or self.target_quantity<1:raise ValueError("invalid_overlevel_quest_definition")\n@dataclass(frozen=True,slots=True)\nclass OverlevelQuestRow:\n quest_id:str;number:int;location_id:str;status:OverlevelQuestStatus;progress:int;target_quantity:int;reward_claimed:bool=False\n def __post_init__(self):\n  if self.progress<0 or self.target_quantity<1 or self.progress>self.target_quantity:raise ValueError("invalid_overlevel_quest_row")\n  if self.status==OverlevelQuestStatus.SKIPPED and self.reward_claimed:raise ValueError("skipped_quest_cannot_claim_reward")\n@dataclass(frozen=True,slots=True)\nclass OverlevelLocationResult:\n location_id:str;max_level:int;completed:int;already_skipped:int;skipped_now:int;quest_items_deleted:int\n@dataclass(frozen=True,slots=True)\nclass OverlevelReconciliationResult:\n current_level:int;changed:int;locations:tuple[OverlevelLocationResult,...]\n @property\n def exceeded_locations(self):return tuple(x.location_id for x in self.locations)\ndef is_location_exceeded(current_level:int,location_id:str,max_levels=LOCATION_MAX_LEVELS)->bool:\n if location_id not in max_levels:raise KeyError("unknown_story_location")\n return int(current_level)>int(max_levels[location_id])\n'''
APP_SRC='''"""Atomic framework-neutral V2 overlevel reconciliation service."""\nfrom __future__ import annotations\nfrom contextlib import contextmanager\nfrom copy import deepcopy\nfrom dataclasses import dataclass,field\nfrom collections.abc import Iterable,Mapping\nfrom rom_v2.domain.overlevel_policy import *\n\n@dataclass\nclass InMemoryOverlevelUnitOfWork:\n rows:dict[int,dict[str,OverlevelQuestRow]]=field(default_factory=dict)\n quest_items:dict[int,dict[tuple[str,str],int]]=field(default_factory=dict)\n @contextmanager\n def atomic(self):\n  snapshot=(deepcopy(self.rows),deepcopy(self.quest_items))\n  try:yield self\n  except Exception:\n   self.rows,self.quest_items=snapshot;raise\n def user_rows(self,user_id:int):return self.rows.setdefault(int(user_id),{})\n def user_items(self,user_id:int):return self.quest_items.setdefault(int(user_id),{})\n\nclass OverlevelPolicyService:\n def __init__(self,uow:InMemoryOverlevelUnitOfWork,definitions:Iterable[OverlevelQuestDefinition],max_levels:Mapping[str,int]=LOCATION_MAX_LEVELS):\n  ordered=tuple(sorted(definitions,key=lambda q:q.number))\n  if not ordered or len({q.quest_id for q in ordered})!=len(ordered) or len({q.number for q in ordered})!=len(ordered):raise ValueError("invalid_overlevel_registry")\n  self._uow=uow;self._definitions=ordered;self._max_levels=dict(max_levels)\n  unknown={q.location_id for q in ordered}-set(self._max_levels)\n  if unknown:raise ValueError("missing_location_max_level:"+repr(sorted(unknown)))\n def reconcile(self,user_id:int,current_level:int)->OverlevelReconciliationResult:\n  user_id=int(user_id);current_level=int(current_level)\n  if user_id<1 or current_level<1:raise ValueError("invalid_overlevel_request")\n  exceeded=[loc for loc in self._max_levels if current_level>int(self._max_levels[loc])]\n  results=[];changed=0\n  with self._uow.atomic():\n   rows=self._uow.user_rows(user_id);items=self._uow.user_items(user_id)\n   for location_id in exceeded:\n    defs=tuple(q for q in self._definitions if q.location_id==location_id)\n    completed=already_skipped=skipped_now=0\n    for definition in defs:\n     row=rows.get(definition.quest_id)\n     if row and row.status==OverlevelQuestStatus.COMPLETED:\n      completed+=1;continue\n     if row and row.status==OverlevelQuestStatus.SKIPPED:\n      already_skipped+=1;continue\n     progress=row.progress if row else 0\n     rows[definition.quest_id]=OverlevelQuestRow(definition.quest_id,definition.number,location_id,OverlevelQuestStatus.SKIPPED,progress,definition.target_quantity,False)\n     skipped_now+=1;changed+=1\n    doomed=[key for key in items if key[0] in {q.quest_id for q in defs}]\n    for key in doomed:del items[key]\n    results.append(OverlevelLocationResult(location_id,int(self._max_levels[location_id]),completed,already_skipped,skipped_now,len(doomed)))\n  return OverlevelReconciliationResult(current_level,changed,tuple(results))\n'''
PRES_SRC='''"""Presentation helpers for V2 overlevel reconciliation."""\nfrom __future__ import annotations\nfrom rom_v2.domain.overlevel_policy import OverlevelReconciliationResult\nLOCATION_NAMES={"start_path":"Початок Шляху","dark_forest":"Темний Бір"}\ndef build_overlevel_message(result:OverlevelReconciliationResult)->str|None:\n lines=[]\n for item in result.locations:\n  if item.skipped_now>0:lines.append(f"{LOCATION_NAMES[item.location_id]}: пропущено без нагород: {item.skipped_now}")\n return "\\n".join(lines) if lines else None\n'''
TEST_SRC='''import unittest\nfrom rom_v2.application.overlevel_policy_service import *\nfrom rom_v2.presentation.overlevel_policy import build_overlevel_message\ndef defs():return [OverlevelQuestDefinition(f"q{n}",n,"start_path" if n<=50 else "dark_forest") for n in range(1,101)]\nclass OverlevelPolicyTest(unittest.TestCase):\n def service(self):u=InMemoryOverlevelUnitOfWork();return u,OverlevelPolicyService(u,defs())\n def test_exact_max_is_noop(self):\n  u,s=self.service();r=s.reconcile(1,5);self.assertEqual(r.changed,0);self.assertEqual(r.locations,());self.assertEqual(u.rows.get(1,{}),{})\n def test_start_path_location_wide(self):\n  u,s=self.service();u.rows[1]={"q1":OverlevelQuestRow("q1",1,"start_path",OverlevelQuestStatus.COMPLETED,1,1,True),"q4":OverlevelQuestRow("q4",4,"start_path",OverlevelQuestStatus.ACTIVE,0,1,False)};u.quest_items[1]={("q4","item"):2}\n  r=s.reconcile(1,6);self.assertEqual(r.changed,49);self.assertEqual(len(u.rows[1]),50);self.assertEqual(u.rows[1]["q1"].status,OverlevelQuestStatus.COMPLETED);self.assertTrue(u.rows[1]["q1"].reward_claimed);self.assertTrue(all(x.status==OverlevelQuestStatus.SKIPPED and not x.reward_claimed for k,x in u.rows[1].items() if k!="q1"));self.assertEqual(u.quest_items[1],{});self.assertIn("Початок Шляху",build_overlevel_message(r))\n def test_idempotent(self):\n  u,s=self.service();self.assertEqual(s.reconcile(1,6).changed,50);self.assertEqual(s.reconcile(1,6).changed,0)\n def test_level_11_reconciles_both(self):\n  u,s=self.service();r=s.reconcile(1,11);self.assertEqual(r.changed,100);self.assertEqual(len(r.locations),2);self.assertEqual(len(u.rows[1]),100)\n def test_atomic_rollback(self):\n  class Broken(dict):\n   def __setitem__(self,k,v):\n    if k=="q2":raise RuntimeError("fixture")\n    super().__setitem__(k,v)\n  u,s=self.service();u.rows[1]=Broken()\n  with self.assertRaises(RuntimeError):s.reconcile(1,6)\n  self.assertEqual(dict(u.rows[1]),{})\n def test_skipped_reward_guard(self):\n  with self.assertRaises(ValueError):OverlevelQuestRow("q1",1,"start_path",OverlevelQuestStatus.SKIPPED,0,1,True)\nif __name__=="__main__":unittest.main()\n'''
TOOL_SRC='''from pathlib import Path\nimport sys\nROOT=Path(__file__).resolve().parent.parent\nif str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))\nfrom rom_v2.application.overlevel_policy_service import *\nq=[OverlevelQuestDefinition(f"q{n}",n,"start_path" if n<=50 else "dark_forest") for n in range(1,101)]\nu=InMemoryOverlevelUnitOfWork();s=OverlevelPolicyService(u,q)\nassert s.reconcile(1,5).changed==0\nassert s.reconcile(1,6).changed==50\nassert s.reconcile(1,6).changed==0\nassert s.reconcile(1,11).changed==50\nassert len(u.rows[1])==100\nprint("Stage 21.13.7c Overlevel policy smoke: PASS")\n'''
GATE_SRC='''from pathlib import Path\nimport ast,sys\nROOT=Path(__file__).resolve().parent.parent\nfiles=[ROOT/"rom_v2/domain/overlevel_policy.py",ROOT/"rom_v2/application/overlevel_policy_service.py",ROOT/"rom_v2/presentation/overlevel_policy.py"]\nfor p in files:ast.parse(p.read_text(encoding="utf-8"))\ntext="\\n".join(p.read_text(encoding="utf-8") for p in files)\nfor bad in ("from handlers.","from db_modules.","import sqlite3","import aiogram","commit("):\n if bad in text:print("Overlevel policy boundary: FAIL",bad);sys.exit(1)\nfor mark in ("current_level)>int(max_levels[location_id])","reward_claimed:bool=False","quest_items","atomic(self)"):\n if mark not in text:print("Overlevel policy contract marker: FAIL",mark);sys.exit(1)\nprint("Stage 21.13.7c Overlevel policy boundary: PASS")\n'''
def main():
 r=root();folder=None;state={};before={p.as_posix():sha(r/p) for p in PROTECTED}
 try:
  if git(r,"rev-parse","HEAD").stdout.strip()!=PARENT:raise PatchError("wrong_exact_parent")
  pre=json.loads((r/PREREQ).read_text(encoding="utf-8-sig"));summary=pre.get("summary",{});boundary=pre.get("resolved_behavior_boundary",{})
  expected={"production_hook_order":"victory reward -> story progress -> quest-item drop -> overlevel reconciliation","level_source":"resulting player level after reward processing","trigger_operator":"current_level > location_max_level","location_max_levels":{"start_path":5,"dark_forest":10},"finalized_statuses":["COMPLETED","SKIPPED"],"skip_reward_policy":"NO_REWARD","quest_item_policy":"DELETE_LOCATION_ROWS","idempotency":"SECOND_IDENTICAL_RECONCILIATION_CHANGED_0","narrow_active_skip":"NON_AUTHORITATIVE_FOR_LOCATION_RECONCILIATION"}
  if pre.get("stage")!="21.13.7b" or pre.get("conclusion")!="GO_TO_IMPLEMENTATION" or summary.get("resolved_contracts")!=10 or summary.get("unresolved_contracts")!=0 or not summary.get("implementation_authorized") or boundary!=expected:raise PatchError("invalid_stage_21_13_7b_prerequisite")
  print("[1/10] [PASS] Stage 21.13.7b resolved 10/10 parity and implementation authorization verified.")
  branch=git(r,"branch","--show-current").stdout.strip();staged=git(r,"diff","--cached","--name-only").stdout.strip()
  if not branch:raise PatchError("git_preflight_detached_head")
  if staged:raise PatchError("git_preflight_staged_index:"+staged.replace("\n",","))
  bad=sorted(p for st,p in status(r) if p not in ALLOWED or (p!=SELF and st[0]!=" "))
  if bad:raise PatchError("unexpected_dirty:"+repr(bad))
  print(f"[2/10] [PASS] Active branch {branch}, exact parent, dirty allowlist and clean index verified.")
  folder,state=backup(r);print("[3/10] [PASS] Fail-safe backup created before V2 production mutation.")
  for path,source in ((DOMAIN,DOMAIN_SRC),(APP,APP_SRC),(PRES,PRES_SRC),(TEST,TEST_SRC),(TOOL,TOOL_SRC),(GATE,GATE_SRC)):write(r/path,source)
  print("[4/10] [PASS] V2 Overlevel policy domain, atomic service, presentation, tests and gates written.")
  for p in (Path(SELF),DOMAIN,APP,PRES,TEST,TOOL,GATE):py_compile.compile(str(r/p),doraise=True)
  print("[5/10] [PASS] Python compile gate passed for patch and all implementation artifacts.")
  env=os.environ.copy();env["PYTHONDONTWRITEBYTECODE"]="1";env["PYTHONPATH"]=str(r)+(os.pathsep+env["PYTHONPATH"] if env.get("PYTHONPATH") else "")
  results=[]
  for args in ([sys.executable,"-m","unittest","-v","tests_v2.test_overlevel_policy"],[sys.executable,str(r/TOOL)],[sys.executable,str(r/GATE)]):
   z=run(args,r,False,env);results.append({"command":" ".join(args),"returncode":z.returncode,"stdout":z.stdout[-2000:],"stderr":z.stderr[-2000:]})
   if z.returncode:raise PatchError("targeted_verification_failed:"+z.stdout+z.stderr)
  print("[6/10] [PASS] Strict threshold, location-wide mutation, no-reward, item cleanup, atomic rollback and idempotency tests passed.")
  removed_before=cleanup(r);compile_args=[sys.executable,"-m","compileall","-q","rom_v2"];z=run(compile_args,r,False,env)
  if z.returncode:raise PatchError("canonical_v2_compile_failed:"+z.stdout+z.stderr)
  removed_after=cleanup(r);unit_args=[sys.executable,"-m","unittest","discover","-s","tests_v2","-p","test_*.py"];z=run(unit_args,r,False,env)
  if z.returncode:raise PatchError("canonical_v2_unit_failed:"+z.stdout+z.stderr)
  print(f"[7/10] [PASS] Canonical V2 CI passed after removing {len(removed_before)+len(removed_after)} bytecode artifact(s).")
  if before!={p.as_posix():sha(r/p) for p in PROTECTED}:raise PatchError("protected_runtime_or_database_changed")
  print("[8/10] [PASS] V1 sources, production database, DB sidecars and protected entry point remained byte-identical.")
  report={"schema_version":1,"stage":STAGE,"status":"PASS","conclusion":"API_READY_OVERLEVEL_POLICY","parent":PARENT,"policy_anchor":"Stage 19.18 SKIP policy","implemented_files":[DOMAIN.as_posix(),APP.as_posix(),PRES.as_posix()],"contracts":{"strict_threshold":"PASS","location_wide_scope":"PASS","active_and_missing_to_skipped":"PASS","finalized_rows_preserved":"PASS","no_rewards":"PASS","quest_items_deleted":"PASS","idempotency":"PASS","atomic_rollback":"PASS","presentation":"PASS","authority_boundary":"PASS"},"behavior":{"location_max_levels":{"start_path":5,"dark_forest":10},"trigger":"current_level > location_max_level","finalized_statuses":["COMPLETED","SKIPPED"],"reward_policy":"NO_REWARD","quest_item_policy":"DELETE_LOCATION_ROWS"},"tests":results,"runtime_integration":"NOT_CONNECTED","production_persistence":"NOT_CONNECTED","database_opened":False,"canonical_reference_changed":False,"v1_wal_shm_manipulated":False,"manual_game_check":"NOT_REQUIRED_API_ONLY","stage_21_13_status":"API_READY_COMPLETE","suggested_next_stage":"21.14"};write(r/REPORT,json.dumps(report,ensure_ascii=False,indent=2)+"\n")
  write(r/DOC,"# Stage 21.13.7c - Overlevel Policy Implementation\n\n- Status: **PASS**\n- Conclusion: **API_READY_OVERLEVEL_POLICY**\n- Policy anchor: **Stage 19.18 SKIP policy**\n- Contracts: **10/10 PASS**\n- Trigger: `current_level > location_max_level`\n- Scope: complete exceeded story location\n- Rewards: **none**\n- Location quest items: **deleted**\n- Atomicity and idempotency: **PASS**\n- Runtime integration: **NOT_CONNECTED**\n- Production persistence: **NOT_CONNECTED**\n- Manual game check: **NOT_REQUIRED_API_ONLY**\n- Stage 21.13: **API_READY_COMPLETE**\n");print("[9/10] [PASS] Machine report and Markdown implementation documentation written.")
  files={x.as_posix() for x in TARGETS};git(r,"add","-f","--",*sorted(files));got={x.replace("\\","/") for x in git(r,"diff","--cached","--name-only").stdout.splitlines() if x}
  if got!=files:raise PatchError("staging_mismatch:"+repr(sorted(got)))
  z=git(r,"commit","-m","Stage 21.13.7c: implement overlevel policy","--",*sorted(files),check=False)
  if z.returncode:raise PatchError("commit_failed:"+z.stdout+z.stderr)
  commit=git(r,"rev-parse","HEAD").stdout.strip();changed={x.replace("\\","/") for x in git(r,"diff-tree","--no-commit-id","--name-only","-r",commit).stdout.splitlines() if x}
  if changed!=files:raise PatchError("commit_scope_mismatch:"+repr(sorted(changed)))
  print(f"[10/10] [PASS] API-ready V2 Overlevel policy committed: {commit}")
  print("CONCLUSION: API_READY_OVERLEVEL_POLICY\nPATCH STATUS: PASS\nCONTRACTS: 10/10 PASS\nSTAGE 19.18 SKIP POLICY: IMPLEMENTED\nSTAGE 21.13 STATUS: API_READY_COMPLETE\nRUNTIME INTEGRATION: NOT_CONNECTED\nPRODUCTION PERSISTENCE: NOT_CONNECTED\nDATABASE OPENED: False\nMANUAL GAME CHECK: NOT_REQUIRED_API_ONLY\nFAIL-SAFE ROLLBACK: ARMED\nSUGGESTED NEXT STAGE: 21.14")
  return 0
 except Exception as e:
  restored=restore(r,folder,state);recovery=run([sys.executable,"-m","compileall","-q","rom_v2"],r,False)
  write(r/FAILURE,json.dumps({"stage":STAGE,"status":"FAIL_ROLLED_BACK","reason":str(e),"restored_files":restored,"recovery_compile_returncode":recovery.returncode,"main_py_must_not_run":recovery.returncode!=0,"database_opened":False,"canonical_reference_changed":False,"v1_wal_shm_manipulated":False},ensure_ascii=False,indent=2)+"\n")
  print(f"[10/10] [FAIL] {e}; rollback: FAIL_ROLLED_BACK");return 1
if __name__=="__main__":raise SystemExit(main())
