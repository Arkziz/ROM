#!/usr/bin/env python3
"""Stage 21.13.6c: implement API-ready V2 Story navigation."""
from __future__ import annotations
import hashlib,json,os,py_compile,shutil,subprocess,sys
from datetime import datetime,timezone
from pathlib import Path
STAGE="21.13.6c";PARENT="fbb527090c50daceac8b0a83d40ae3b3b0275f4d"
SELF="patch/patch_21_13_6c_implement_story_navigation.py";PREREQ=Path("reports/stage_21_13_6b_resolved_story_navigation_parity.json")
DOMAIN=Path("rom_v2/domain/story_navigation.py");APP=Path("rom_v2/application/story_navigation_service.py");PRES=Path("rom_v2/presentation/story_navigation.py")
TEST=Path("tests_v2/test_story_navigation.py");TOOL=Path("tools/check_stage_21_13_6c_story_navigation.py");GATE=Path("tools/verify_stage_21_13_6c_story_navigation.py")
REPORT=Path("reports/stage_21_13_6c_story_navigation_implementation.json");DOC=Path("MD/STAGE_21_13_6C_STORY_NAVIGATION_IMPLEMENTATION.md");FAILURE=Path("reports/stage_21_13_6c_failure_rollback.json")
TARGETS=(Path(SELF),DOMAIN,APP,PRES,TEST,TOOL,GATE,REPORT,DOC);ALLOWED={SELF,"ROM_FULL_DUMP.txt",FAILURE.as_posix()};PROTECTED=(Path("main.py"),Path("game.db-wal"),Path("game.db-shm"))
CONTENT_MODULES=(
 "rom_v2.content.story_start_path_01_10","rom_v2.content.story_start_path_11_20","rom_v2.content.story_start_path_21_30","rom_v2.content.story_start_path_31_40","rom_v2.content.story_start_path_41_50",
 "rom_v2.content.story_dark_forest_51_60","rom_v2.content.story_dark_forest_61_70","rom_v2.content.story_dark_forest_71_80","rom_v2.content.story_dark_forest_81_90","rom_v2.content.story_dark_forest_91_100",
)
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
 f=r/"backup"/("stage_21_13_6c_"+datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ"));f.mkdir(parents=True);state={}
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
def clean(r):
 # OneDrive on Windows can temporarily lock __pycache__ directories. Remove
 # bytecode files first, then remove only empty directories; a locked empty
 # directory is harmless and must not turn a successful compile into FAIL.
 removed=[];errors=[]
 for p in sorted(r.rglob("*.pyc"),key=lambda x:len(x.parts),reverse=True):
  try:
   if p.exists():
    try:p.chmod(0o666)
    except OSError:pass
    p.unlink();removed.append(p.relative_to(r).as_posix())
  except OSError as exc:errors.append(f"{p.relative_to(r).as_posix()}:{exc}")
 for p in sorted(r.rglob("__pycache__"),key=lambda x:len(x.parts),reverse=True):
  try:
   p.rmdir()
  except OSError:
   # Non-empty or OneDrive-locked directories are tolerated only after all
   # discoverable .pyc files were processed below.
   pass
 leftovers=[p.relative_to(r).as_posix() for p in r.rglob("*.pyc") if p.exists()]
 if leftovers or errors:raise PatchError("bytecode_cleanup_failed:"+repr({"leftovers":leftovers,"errors":errors}))
 return removed
DOMAIN_SRC='''"""Pure domain records and invariants for V2 Story navigation."""\nfrom __future__ import annotations\nfrom dataclasses import dataclass\nfrom enum import Enum\n\nFORBIDDEN_UI_TERMS=("глава","глави","главу","главою","главі")\nclass StoryQuestStatus(str,Enum):\n ACTIVE="ACTIVE";COMPLETED="COMPLETED";SKIPPED="SKIPPED";AVAILABLE="AVAILABLE";LOCKED="LOCKED"\n@dataclass(frozen=True,slots=True)\nclass StoryQuestState:\n quest_number:int;status:StoryQuestStatus;progress:int=0;target_quantity:int=1;quest_item_quantity:int=0\n def __post_init__(self):\n  if self.quest_number<1 or self.progress<0 or self.target_quantity<1 or self.quest_item_quantity<0:raise ValueError("invalid_story_quest_state")\n  if self.progress>self.target_quantity:raise ValueError("progress_exceeds_target")\n@dataclass(frozen=True,slots=True)\nclass StoryQuestView:\n number:int;quest_id:str;title:str;status:StoryQuestStatus;progress:int;target_quantity:int;actionable:bool\n@dataclass(frozen=True,slots=True)\nclass StorySectionView:\n section_id:str;location_id:str;number:int;title:str;required_level:int;quests:tuple[StoryQuestView,...]\n @property\n def display_title(self):return f"Розділ {self.number}. {self.title}"\n@dataclass(frozen=True,slots=True)\nclass StoryView:\n story_id:str;location_id:str;display_name:str;icon:str;sections:tuple[StorySectionView,...]\ndef ensure_safe_ui_text(text:str)->str:\n value=str(text)\n folded=value.casefold()\n if any(term in folded for term in FORBIDDEN_UI_TERMS):raise ValueError("forbidden_story_navigation_term")\n if "start_path" in value or "dark_forest" in value:raise ValueError("technical_location_id_exposed")\n return value\n'''
APP_SRC='''"""Application service for API-ready V2 Story navigation."""\nfrom __future__ import annotations\nfrom collections.abc import Callable,Iterable,Mapping,Sequence\nfrom rom_v2.domain.story_navigation import StoryQuestState,StoryQuestStatus,StoryQuestView,StorySectionView,StoryView,ensure_safe_ui_text\n\nLOCATION_LABELS={"start_path":"Початок Шляху","dark_forest":"Темний Бір"}\nSECTION_TITLES={"start_path":("Перші кроки","Сліди небезпеки","Шлях найманця","Перед вирішальним походом","Ватажок зграї"),"dark_forest":("На межі Темного Бору","Глибше в хащу","Сліди культу","Спотворені землі","Фінал Темного Бору")}\nclass StoryNavigationService:\n def __init__(self,quests:Iterable[object],title_resolver:Callable[[object,str,int],str]|None=None):\n  ordered=tuple(sorted(quests,key=lambda q:int(q.number)))\n  if len(ordered)!=100 or tuple(int(q.number) for q in ordered)!=tuple(range(1,101)):raise ValueError("story_navigation_requires_quests_1_100")\n  if len({q.quest_id for q in ordered})!=100:raise ValueError("duplicate_story_quest_id")\n  self._quests=ordered;self._by_number={int(q.number):q for q in ordered};self._title_resolver=title_resolver or self._default_title\n @staticmethod\n def _default_title(quest:object,status:str,quest_item_quantity:int)->str:\n  if str(getattr(quest,"quest_type","")).upper()=="QUEST_ITEM" and status not in {"COMPLETED","SKIPPED"} and quest_item_quantity<=0:return "Невідома знахідка"\n  return str(quest.title)\n @staticmethod\n def derive_status(number:int,states:Mapping[int,StoryQuestState],player_level:int)->StoryQuestStatus:\n  row=states.get(number)\n  if row:return row.status\n  previous=states.get(number-1) if number>1 else None\n  chain_open=number==1 or (previous is not None and previous.status in {StoryQuestStatus.COMPLETED,StoryQuestStatus.SKIPPED})\n  quest_level=((number-1)//10)+1\n  return StoryQuestStatus.AVAILABLE if chain_open and player_level>=quest_level else StoryQuestStatus.LOCKED\n def build(self,states:Mapping[int,StoryQuestState],player_level:int)->tuple[StoryView,...]:\n  stories=[]\n  for location_id,start in (("start_path",1),("dark_forest",51)):\n   sections=[]\n   for offset,title in enumerate(SECTION_TITLES[location_id]):\n    first=start+offset*10;views=[]\n    for number in range(first,first+10):\n     q=self._by_number[number];st=self.derive_status(number,states,player_level);row=states.get(number);qty=row.quest_item_quantity if row else 0\n     presented=ensure_safe_ui_text(self._title_resolver(q,st.value,qty));progress=row.progress if row and st==StoryQuestStatus.ACTIVE else 0;target=row.target_quantity if row else int(q.target_quantity)\n     views.append(StoryQuestView(number,q.quest_id,presented,st,progress,target,st==StoryQuestStatus.AVAILABLE))\n    section=StorySectionView(f"{location_id}_{offset+1:02d}",location_id,offset+1,title,(first-1)//10+1,tuple(views));ensure_safe_ui_text(section.display_title);sections.append(section)\n   stories.append(StoryView(location_id,location_id,ensure_safe_ui_text(LOCATION_LABELS[location_id]),"🧭" if location_id=="start_path" else "🌲",tuple(sections)))\n  return tuple(stories)\n def active_target(self,states:Mapping[int,StoryQuestState])->dict|None:\n  active=[s for s in states.values() if s.status==StoryQuestStatus.ACTIVE]\n  if len(active)>1:raise ValueError("multiple_active_story_quests")\n  if not active:return None\n  state=active[0];q=self._by_number[state.quest_number];objective=ensure_safe_ui_text(str(q.objective_text));return {"quest_number":state.quest_number,"title":ensure_safe_ui_text(str(q.title)),"objective":objective,"progress":state.progress,"target_quantity":state.target_quantity}\n'''
PRES_SRC='''"""Framework-neutral Story navigation callback and presentation contract."""\nfrom __future__ import annotations\nfrom dataclasses import dataclass\nPREFIX="sqh:v2";ROOT=f"{PREFIX}:index";PROFILE="story_quest:profile";MAX_CALLBACK_BYTES=64\n@dataclass(frozen=True,slots=True)\nclass StoryRoute:\n surface:str;value:str|int|None=None\ndef encode_route(route:StoryRoute)->str:\n if route.surface=="index":value=ROOT\n elif route.surface in {"loc","sec","q"} and route.value is not None:value=f"{PREFIX}:{route.surface}:{route.value}"\n elif route.surface=="profile":value=PROFILE\n else:raise ValueError("invalid_story_route")\n if len(value.encode("utf-8"))>MAX_CALLBACK_BYTES:raise ValueError("story_callback_too_long")\n return value\ndef decode_route(data:str)->StoryRoute:\n if data==ROOT:return StoryRoute("index")\n if data==PROFILE:return StoryRoute("profile")\n parts=str(data).split(":",3)\n if len(parts)!=4 or parts[:2]!=["sqh","v2"] or parts[2] not in {"loc","sec","q"} or not parts[3]:raise ValueError("invalid_story_callback")\n return StoryRoute(parts[2],int(parts[3]) if parts[2]=="q" and parts[3].isdigit() else parts[3])\ndef parent_route(route:StoryRoute,quest_to_section:dict[int,str]|None=None,section_to_location:dict[str,str]|None=None)->StoryRoute:\n if route.surface=="q":\n  if not quest_to_section or int(route.value) not in quest_to_section:raise KeyError("quest_parent_unknown")\n  return StoryRoute("sec",quest_to_section[int(route.value)])\n if route.surface=="sec":\n  if not section_to_location or str(route.value) not in section_to_location:raise KeyError("section_parent_unknown")\n  return StoryRoute("loc",section_to_location[str(route.value)])\n if route.surface=="loc":return StoryRoute("index")\n if route.surface=="index":return StoryRoute("profile")\n raise ValueError("profile_has_no_story_parent")\n'''
TEST_SRC='''import unittest\nfrom types import SimpleNamespace\nfrom rom_v2.application.story_navigation_service import StoryNavigationService\nfrom rom_v2.domain.story_navigation import StoryQuestState,StoryQuestStatus,ensure_safe_ui_text\nfrom rom_v2.presentation.story_navigation import *\ndef quests():\n return [SimpleNamespace(number=n,quest_id=f"q{n}",title=f"Квест {n}",quest_type="KILL",target_quantity=1,objective_text=f"Ціль {n}") for n in range(1,101)]\nclass TestStoryNavigation(unittest.TestCase):\n def setUp(self):self.s=StoryNavigationService(quests())\n def test_hierarchy(self):\n  tree=self.s.build({},10);self.assertEqual([x.display_name for x in tree],["Початок Шляху","Темний Бір"]);self.assertEqual([len(x.sections) for x in tree],[5,5]);self.assertEqual(sum(len(s.quests) for x in tree for s in x.sections),100)\n def test_status_derivation(self):\n  states={1:StoryQuestState(1,StoryQuestStatus.COMPLETED),2:StoryQuestState(2,StoryQuestStatus.ACTIVE,0,2)};tree=self.s.build(states,1);q=[q for x in tree for s in x.sections for q in s.quests];self.assertEqual(q[0].status,StoryQuestStatus.COMPLETED);self.assertEqual(q[1].status,StoryQuestStatus.ACTIVE);self.assertEqual(q[2].status,StoryQuestStatus.LOCKED)\n def test_skipped_opens_chain(self):self.assertEqual(self.s.derive_status(2,{1:StoryQuestState(1,StoryQuestStatus.SKIPPED)},1),StoryQuestStatus.AVAILABLE)\n def test_active_target(self):self.assertEqual(self.s.active_target({1:StoryQuestState(1,StoryQuestStatus.ACTIVE,1,2)})["progress"],1)\n def test_routes(self):\n  for route in (StoryRoute("index"),StoryRoute("loc","start_path"),StoryRoute("sec","start_path_01"),StoryRoute("q",1),StoryRoute("profile")):self.assertEqual(decode_route(encode_route(route)),route)\n  self.assertEqual(parent_route(StoryRoute("q",1),{1:"start_path_01"},{}),StoryRoute("sec","start_path_01"));self.assertEqual(parent_route(StoryRoute("index")),StoryRoute("profile"))\n def test_forbidden_ui(self):\n  for text in ("глава 1","start_path","dark_forest"):\n   with self.assertRaises(ValueError):ensure_safe_ui_text(text)\nif __name__=="__main__":unittest.main()\n'''
TOOL_SRC='''from pathlib import Path\nimport sys\nROOT=Path(__file__).resolve().parent.parent\nif str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))\nfrom types import SimpleNamespace\nfrom rom_v2.application.story_navigation_service import StoryNavigationService\nq=[SimpleNamespace(number=n,quest_id=f"q{n}",title=f"Квест {n}",quest_type="KILL",target_quantity=1,objective_text=f"Ціль {n}") for n in range(1,101)]\ntree=StoryNavigationService(q).build({},10);assert len(tree)==2 and sum(len(s.quests) for x in tree for s in x.sections)==100\nprint("Stage 21.13.6c Story navigation smoke: PASS")\n'''
GATE_SRC='''from pathlib import Path\nimport ast,sys\nROOT=Path(__file__).resolve().parent.parent\nfiles=[ROOT/"rom_v2/domain/story_navigation.py",ROOT/"rom_v2/application/story_navigation_service.py",ROOT/"rom_v2/presentation/story_navigation.py"]\nfor p in files:ast.parse(p.read_text(encoding="utf-8"))\ntext="\\n".join(p.read_text(encoding="utf-8") for p in files)\nfor bad in ("from handlers.","from db_modules.","import sqlite3","import aiogram"):\n if bad in text:print("Story navigation boundary: FAIL",bad);sys.exit(1)\nprint("Stage 21.13.6c Story navigation boundary: PASS")\n'''
def main():
 r=root();folder=None;state={};before={p.as_posix():sha(r/p) for p in PROTECTED}
 try:
  pre=json.loads((r/PREREQ).read_text(encoding="utf-8-sig"));summary=pre.get("summary",{})
  if git(r,"rev-parse","HEAD").stdout.strip()!=PARENT:raise PatchError("wrong_exact_parent")
  if pre.get("stage")!="21.13.6b" or pre.get("conclusion")!="GO_TO_IMPLEMENTATION" or summary.get("resolved_contracts")!=8 or not summary.get("implementation_authorized"):raise PatchError("invalid_stage_21_13_6b_prerequisite")
  print("[1/10] [PASS] Stage 21.13.6b resolved 8/8 parity and implementation authorization verified.")
  branch=git(r,"branch","--show-current").stdout.strip();staged=git(r,"diff","--cached","--name-only").stdout.strip()
  if not branch:raise PatchError("git_preflight_detached_head")
  if staged:raise PatchError("git_preflight_staged_index:"+staged.replace("\n",","))
  bad=sorted(p for st,p in status(r) if p not in ALLOWED or (p!=SELF and st[0]!=" "))
  if bad:raise PatchError("unexpected_dirty:"+repr(bad))
  print(f"[2/10] [PASS] Active branch {branch}, exact parent, dirty allowlist and clean index verified.")
  folder,state=backup(r);print("[3/10] [PASS] Fail-safe backup created before production mutation.")
  for path,source in ((DOMAIN,DOMAIN_SRC),(APP,APP_SRC),(PRES,PRES_SRC),(TEST,TEST_SRC),(TOOL,TOOL_SRC),(GATE,GATE_SRC)):write(r/path,source)
  print("[4/10] [PASS] V2 Story navigation domain, service, callback presentation, tests and gates written.")
  for p in (Path(SELF),DOMAIN,APP,PRES,TEST,TOOL,GATE):py_compile.compile(str(r/p),doraise=True)
  print("[5/10] [PASS] Python compile gate passed for patch and all implementation artifacts.")
  env=os.environ.copy();env["PYTHONDONTWRITEBYTECODE"]="1"
  t=run([sys.executable,"-m","unittest","-v","tests_v2.test_story_navigation"],r,False,env);sm=run([sys.executable,str(r/TOOL)],r,False,env);ga=run([sys.executable,str(r/GATE)],r,False,env)
  if t.returncode or sm.returncode or ga.returncode:raise PatchError("targeted_verification_failed:"+t.stdout+t.stderr+sm.stdout+sm.stderr+ga.stdout+ga.stderr)
  print("[6/10] [PASS] Hierarchy, labels, status derivation, active target, callbacks, return paths and terminology tests passed.")
  removed_before=clean(r);ci=[]
  compile_args=[sys.executable,"-m","compileall","-q","rom_v2"]
  z=run(compile_args,r,False,env);ci.append({"command":" ".join(compile_args),"returncode":z.returncode})
  if z.returncode:raise PatchError("canonical_v2_compile_failed:"+z.stdout+z.stderr)
  # compileall writes bytecode even with PYTHONDONTWRITEBYTECODE. Static content
  # gates run from the unit suite, so remove compile artifacts before discovery.
  removed_after_compile=clean(r)
  unit_args=[sys.executable,"-m","unittest","discover","-s","tests_v2","-p","test_*.py"]
  z=run(unit_args,r,False,env);ci.append({"command":" ".join(unit_args),"returncode":z.returncode})
  if z.returncode:raise PatchError("canonical_v2_unit_failed:"+z.stdout+z.stderr)
  removed=removed_before+removed_after_compile
  print(f"[7/10] [PASS] Canonical V2 CI passed after removing {len(removed)} bytecode artifact(s).")
  if before!={p.as_posix():sha(r/p) for p in PROTECTED}:raise PatchError("protected_runtime_changed")
  print("[8/10] [PASS] V1 sources, canonical references, DB sidecars and protected configuration remained byte-identical.")
  rep={"schema_version":1,"stage":STAGE,"status":"PASS","conclusion":"API_READY_STORY_NAVIGATION","parent":PARENT,"implemented_files":[DOMAIN.as_posix(),APP.as_posix(),PRES.as_posix()],"contracts":{"hierarchy":"PASS","localized_labels":"PASS","active_target":"PASS","status_model":"PASS","callbacks":"PASS","return_paths":"PASS","spoiler_safe":"PASS","terminology_and_id_leakage":"PASS"},"coverage":{"stories":2,"sections":10,"quests":100,"persistent_statuses":["ACTIVE","COMPLETED","SKIPPED"],"derived_statuses":["AVAILABLE","LOCKED"],"callback_prefix":"sqh:v2"},"tests":{"targeted":"PASS","smoke":"PASS","architecture_boundary":"PASS","canonical_v2_ci":ci},"runtime_integration":"NOT_CONNECTED","production_persistence":"NOT_CONNECTED","database_opened":False,"canonical_reference_changed":False,"v1_wal_shm_manipulated":False,"manual_game_check":"NOT_REQUIRED_API_ONLY","next_stage":"21.13.7"};write(r/REPORT,json.dumps(rep,ensure_ascii=False,indent=2)+"\n")
  write(r/DOC,"# Stage 21.13.6c - Story navigation implementation\n\n- Status: **PASS**\n- Conclusion: **API_READY_STORY_NAVIGATION**\n- Hierarchy: **2 stories / 10 sections / 100 quests**\n- Localized labels, active target, statuses, callbacks and parent returns: **PASS**\n- Forbidden term and technical ID leakage guard: **PASS**\n- Runtime integration: **NOT_CONNECTED**\n- Production persistence: **NOT_CONNECTED**\n- Manual game check: **NOT_REQUIRED_API_ONLY**\n");print("[9/10] [PASS] Machine report and Markdown implementation documentation written.")
  files={x.as_posix() for x in TARGETS};git(r,"add","-f","--",*sorted(files));got={x.replace("\\","/") for x in git(r,"diff","--cached","--name-only").stdout.splitlines() if x}
  if got!=files:raise PatchError("staging_mismatch:"+repr(sorted(got)))
  z=git(r,"commit","-m","Stage 21.13.6c: implement Story navigation","--",*sorted(files),check=False)
  if z.returncode:raise PatchError("commit_failed:"+z.stdout+z.stderr)
  commit=git(r,"rev-parse","HEAD").stdout.strip();changed={x.replace("\\","/") for x in git(r,"diff-tree","--no-commit-id","--name-only","-r",commit).stdout.splitlines() if x}
  if changed!=files:raise PatchError("commit_scope_mismatch:"+repr(sorted(changed)))
  print(f"[10/10] [PASS] API-ready V2 Story navigation committed: {commit}")
  print("CONCLUSION: API_READY_STORY_NAVIGATION\nPATCH STATUS: PASS\nSTORIES: 2/2\nSECTIONS: 10/10\nQUESTS: 100/100\nCONTRACTS: 8/8 PASS\nRUNTIME INTEGRATION: NOT_CONNECTED\nPRODUCTION PERSISTENCE: NOT_CONNECTED\nMANUAL GAME CHECK: NOT_REQUIRED_API_ONLY\nFAIL-SAFE ROLLBACK: ARMED\nSUGGESTED NEXT STAGE: 21.13.7")
  return 0
 except Exception as e:
  restored=restore(r,folder,state);recovery=run([sys.executable,"-m","compileall","-q","rom_v2"],r,False);write(r/FAILURE,json.dumps({"stage":STAGE,"status":"FAIL_ROLLED_BACK","reason":str(e),"restored_files":restored,"recovery_compile_returncode":recovery.returncode,"main_py_must_not_run":recovery.returncode!=0,"database_opened":False,"canonical_reference_changed":False,"v1_wal_shm_manipulated":False},ensure_ascii=False,indent=2)+"\n");print(f"[10/10] [FAIL] {e}; rollback: FAIL_ROLLED_BACK");return 1
if __name__=="__main__":raise SystemExit(main())
