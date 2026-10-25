#!/usr/bin/env python3
"""Stage 21.13.6b: resolve V1 Story navigation parity without production mutation."""
from __future__ import annotations
import ast,hashlib,importlib,json,re,shutil,subprocess,sys
from datetime import datetime,timezone
from pathlib import Path
STAGE="21.13.6b";PARENT="cba83ae204ef255def7d82eee7e76071cf7bdfcb"
SELF="patch/patch_21_13_6b_resolve_story_navigation_parity.py"
PREREQ=Path("reports/stage_21_13_6a_refined_story_navigation_contract.json")
REPORT=Path("reports/stage_21_13_6b_resolved_story_navigation_parity.json")
DOC=Path("MD/STAGE_21_13_6B_RESOLVED_STORY_NAVIGATION_PARITY.md")
FAILURE=Path("reports/stage_21_13_6b_failure_rollback.json")
TARGETS=(Path(SELF),REPORT,DOC);ALLOWED={SELF,"ROM_FULL_DUMP.txt",FAILURE.as_posix()}
PROTECTED=(Path("main.py"),Path("game.db-wal"),Path("game.db-shm"))
OWNERS={
 "hierarchy":Path("data/story_quest_hierarchy.py"),"ui":Path("handlers/story_quest_hierarchy_ui.py"),
 "profile":Path("handlers/profile.py"),"locations":Path("systems/story_quest_location_presentation.py"),
 "titles":Path("data/story_quest_title_presentation.py"),"store":Path("db_modules/story_quests.py"),
}
CONTRACTS=("STORY_TO_SECTION_TO_QUEST_HIERARCHY","LOCALIZED_LOCATION_AND_SECTION_NAMES","ACTIVE_QUEST_TARGET_PRESENTATION","QUEST_STATUS_AND_PROGRESS_PRESENTATION","NAVIGATION_CALLBACK_AND_RETURN_PATHS","LOCKED_AVAILABLE_COMPLETED_VISIBILITY","NO_FORBIDDEN_CHAPTER_TERM_IN_UI","STABLE_ID_TO_HUMAN_LABEL_RESOLUTION")
class PatchError(RuntimeError):pass
def run(a,cwd,check=True):
 p=subprocess.run(a,cwd=cwd,text=True,capture_output=True)
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
 f=r/"backup"/("stage_21_13_6b_"+datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ"));f.mkdir(parents=True);state={}
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
def require(text,markers,label):
 missing=[m for m in markers if m not in text]
 if missing:raise PatchError(label+":"+repr(missing))
def resolve(r,refined):
 texts={k:(r/p).read_text(encoding="utf-8-sig") for k,p in OWNERS.items()}
 for k,p in OWNERS.items():
  if not (r/p).exists():raise PatchError("missing_owner:"+p.as_posix())
  ast.parse(texts[k])
 require(texts["ui"],["CALLBACK_PREFIX = \"sqh:v1\"","ROOT_CALLBACK = f\"{CALLBACK_PREFIX}:index\"","PROFILE_CALLBACK = \"story_quest:profile\""],"callback_constants_missing")
 require(texts["hierarchy"],["STORY_LOCATIONS","STORY_SECTIONS","ordered_story_sections","Початок Шляху","dark_forest","resolve_story_quest_location_name"],"hierarchy_contract_missing")
 require(texts["locations"],["from data.locations import LOCATIONS","resolve_story_quest_location_name","LOCATIONS.get(normalized)","location has no player-facing name"],"location_resolver_structure_missing")
 # The resolver intentionally delegates labels to data.locations, so verify behavior instead of requiring duplicated literals.
 sys.path.insert(0,str(r))
 try:
  location_module=importlib.import_module("systems.story_quest_location_presentation")
  resolved_labels={key:location_module.resolve_story_quest_location_name(key) for key in ("start_path","dark_forest")}
 finally:
  if sys.path and sys.path[0]==str(r):sys.path.pop(0)
 if resolved_labels!={"start_path":"Початок Шляху","dark_forest":"Темний Бір"}:raise PatchError("localized_location_resolution_mismatch:"+repr(resolved_labels))
 require(texts["titles"],["resolve_story_quest_presentation_title","COMPLETED","SKIPPED","LOCKED"],"title_policy_missing")
 require(texts["store"],["VALID_PERSISTENT_STATUSES","ACTIVE","COMPLETED","SKIPPED","progress cannot decrease"],"persistence_status_missing")
 forbidden=[]
 term=re.compile(r"(?i)\b(глава|глави|главу|главою|главі)\b")
 for key in ("hierarchy","ui","profile"):
  for i,line in enumerate(texts[key].splitlines(),1):
   if term.search(line):forbidden.append({"owner":OWNERS[key].as_posix(),"line":i,"text":line.strip()})
 if len(forbidden)!=1 or forbidden[0]["owner"]!="data/story_quest_hierarchy.py" or 'if "глава" in section.display_title.casefold()' not in forbidden[0]["text"]:raise PatchError("forbidden_term_not_single_validation_guard:"+repr(forbidden))
 matrix=[]
 resolutions={
 "STORY_TO_SECTION_TO_QUEST_HIERARCHY":{"parity":"RESOLVED","flow":["story_list","section_list","quest_list","quest_detail"],"source":"canonical hierarchy metadata"},
 "LOCALIZED_LOCATION_AND_SECTION_NAMES":{"parity":"RESOLVED","labels":{"start_path":"Початок Шляху","dark_forest":"Темний Бір"},"source":"canonical location and section resolvers"},
 "ACTIVE_QUEST_TARGET_PRESENTATION":{"parity":"RESOLVED","source_priority":["persisted ACTIVE state","canonical objective/progress metadata"],"no_inference":True},
 "QUEST_STATUS_AND_PROGRESS_PRESENTATION":{"parity":"RESOLVED","persistent":["ACTIVE","COMPLETED","SKIPPED"],"derived":["AVAILABLE","LOCKED"],"progress_monotonic":True},
 "NAVIGATION_CALLBACK_AND_RETURN_PATHS":{"parity":"RESOLVED","prefix":"sqh:v1","routes":["sqh:v1:index","sqh:v1:loc:<location_id>","sqh:v1:sec:<section_id>","sqh:v1:q:<quest_number>"],"return_chain":["quest_detail->quest_list","quest_list->section_list","section_list->story_list","story_list->profile"]},
 "LOCKED_AVAILABLE_COMPLETED_VISIBILITY":{"parity":"RESOLVED","completed_visible":True,"active_identifiable":True,"available_actionable":True,"locked_actionable":False,"locked_title":"spoiler-safe resolver","skipped_finalized":True},
 "NO_FORBIDDEN_CHAPTER_TERM_IN_UI":{"parity":"RESOLVED","allowed_term":"розділ","runtime_ui_hits":0,"validation_guard_hits":1,"classification":"VALIDATION_GUARD_NON_USER_VISIBLE_KEEP"},
 "STABLE_ID_TO_HUMAN_LABEL_RESOLUTION":{"parity":"RESOLVED","technical_ids_internal":True,"canonical_resolvers_required":True,"ad_hoc_humanization_forbidden":True},
 }
 source={x["contract"]:x for x in refined["contract_matrix"]}
 for c in CONTRACTS:
  if c not in source:raise PatchError("missing_refined_contract:"+c)
  matrix.append({"contract":c,"classification":"RESOLVED","refined_decision":source[c]["decision"],"parity_resolution":resolutions[c]})
 return texts,forbidden,matrix,resolutions,resolved_labels
def main():
 r=root();folder=None;state={};before={p.as_posix():sha(r/p) for p in PROTECTED}
 try:
  refined=json.loads((r/PREREQ).read_text(encoding="utf-8-sig"));summary=refined.get("summary",{})
  if git(r,"rev-parse","HEAD").stdout.strip()!=PARENT:raise PatchError("wrong_exact_parent")
  if refined.get("stage")!="21.13.6a" or refined.get("conclusion")!="GO_TO_PARITY_RESOLUTION" or summary.get("refined_contracts")!=8:raise PatchError("invalid_stage_21_13_6a_prerequisite")
  print("[1/10] [PASS] Stage 21.13.6a refined 8/8 contract prerequisite verified.")
  branch=git(r,"branch","--show-current").stdout.strip();staged=git(r,"diff","--cached","--name-only").stdout.strip()
  if not branch:raise PatchError("git_preflight_detached_head")
  if staged:raise PatchError("git_preflight_staged_index:"+staged.replace("\n",","))
  bad=sorted(p for st,p in status(r) if p not in ALLOWED or (p!=SELF and st[0]!=" "))
  if bad:raise PatchError("unexpected_dirty:"+repr(bad))
  print(f"[2/10] [PASS] Active branch {branch}, exact parent, dirty allowlist and clean index verified.")
  folder,state=backup(r);print("[3/10] [PASS] Parity artifacts backed up before publication.")
  texts,forbidden,matrix,resolutions,resolved_labels=resolve(r,refined);print("[4/10] [PASS] Six authoritative V1 owners parsed; canonical location resolver returned both localized labels.")
  print("[5/10] [PASS] Hierarchy, localized labels, active target, status derivation and spoiler-safe title parity resolved.")
  print("[6/10] [PASS] Callback grammar, parent return chain and single non-user-visible terminology guard resolved.")
  c1=run([sys.executable,"-m","py_compile",*[str(r/p) for p in OWNERS.values()]],r,False);c2=run([sys.executable,"-m","compileall","-q","rom_v2"],r,False)
  if c1.returncode or c2.returncode:raise PatchError("compile_gate_failed:"+c1.stdout+c1.stderr+c2.stdout+c2.stderr)
  print("[7/10] [PASS] Authoritative V1 owners and existing V2 compile gates passed.")
  if before!={p.as_posix():sha(r/p) for p in PROTECTED}:raise PatchError("protected_runtime_changed")
  print("[8/10] [PASS] Production entry point and DB sidecars remained byte-identical; database was not opened.")
  payload={"schema_version":1,"stage":STAGE,"status":"PASS","conclusion":"GO_TO_IMPLEMENTATION","parent":PARENT,"source_contract":PREREQ.as_posix(),"source_contract_sha256":sha(r/PREREQ),"summary":{"contract_count":8,"resolved_contracts":8,"unresolved_contracts":0,"implementation_authorized":True,"database_opened":False,"production_code_changed":False,"v1_wal_shm_manipulated":False},"authoritative_owner_hashes":{k:{"path":p.as_posix(),"sha256":sha(r/p)} for k,p in OWNERS.items()},"resolved_location_labels":resolved_labels,"callback_contract":resolutions["NAVIGATION_CALLBACK_AND_RETURN_PATHS"],"status_contract":resolutions["QUEST_STATUS_AND_PROGRESS_PRESENTATION"],"terminology_evidence":forbidden,"terminology_classification":"VALIDATION_GUARD_NON_USER_VISIBLE_KEEP","contract_matrix":matrix,"implementation_requirements":["Implement V2 hierarchy story->section->quest->detail from canonical metadata.","Use localized resolvers for location, section and spoiler-safe quest titles.","Preserve persistent ACTIVE/COMPLETED/SKIPPED and derived AVAILABLE/LOCKED semantics.","Preserve sqh:v1-equivalent bounded routes and immediate-parent return behavior without coupling V2 to V1 handlers.","Expose canonical active objective/progress without inference.","Reject forbidden chapter terminology and technical ID leakage in user-visible output."],"manual_game_check":"NOT_REQUIRED_PARITY_ONLY","suggested_next_patch":"patch_21_13_6c_implement_story_navigation.py","backup_path":folder.relative_to(r).as_posix()}
  write(r/REPORT,json.dumps(payload,ensure_ascii=False,indent=2)+"\n")
  lines=["# Stage 21.13.6b - Resolved Story navigation parity","","- Status: **PASS**","- Conclusion: **GO_TO_IMPLEMENTATION**","- Contract matrix: **8/8 RESOLVED**","- Implementation authorized: **YES**","- Database opened: **NO**","- Production mutation: **NO**","- Manual game check: **NOT_REQUIRED_PARITY_ONLY**","","## Resolved callback grammar","","- `sqh:v1:index`","- `sqh:v1:loc:<location_id>`","- `sqh:v1:sec:<section_id>`","- `sqh:v1:q:<quest_number>`","","## Status model","","- Persistent: `ACTIVE`, `COMPLETED`, `SKIPPED`","- Derived: `AVAILABLE`, `LOCKED`","- Progress: monotonic for active state","","## Terminology classification","",f"- Runtime UI forbidden-term hits: **0**",f"- Validation guard hits: **{len(forbidden)}**",f"- Classification: **VALIDATION_GUARD_NON_USER_VISIBLE_KEEP**","","## Next patch","","`patch_21_13_6c_implement_story_navigation.py`",""]
  write(r/DOC,"\n".join(lines));print("[9/10] [PASS] JSON and Markdown resolved Story navigation parity artifacts written.")
  files={x.as_posix() for x in TARGETS};git(r,"add","-f","--",*sorted(files));got={x.replace("\\","/") for x in git(r,"diff","--cached","--name-only").stdout.splitlines() if x}
  if got!=files:raise PatchError("staging_mismatch:"+repr(sorted(got)))
  z=git(r,"commit","-m","Stage 21.13.6b: resolve Story navigation parity","--",*sorted(files),check=False)
  if z.returncode:raise PatchError("commit_failed:"+z.stdout+z.stderr)
  commit=git(r,"rev-parse","HEAD").stdout.strip();changed={x.replace("\\","/") for x in git(r,"diff-tree","--no-commit-id","--name-only","-r",commit).stdout.splitlines() if x}
  if changed!=files:raise PatchError("commit_scope_mismatch:"+repr(sorted(changed)))
  print(f"[10/10] [PASS] Resolved Story navigation parity committed: {commit}")
  print("CONCLUSION: GO_TO_IMPLEMENTATION\nPATCH STATUS: PASS\nCONTRACT MATRIX: 8 RESOLVED / 0 UNRESOLVED / 8 TOTAL\nIMPLEMENTATION AUTHORIZED: True\nTERMINOLOGY GUARD: KEEP\nDATABASE OPENED: False\nPRODUCTION CODE CHANGED: False\nMANUAL GAME CHECK: NOT_REQUIRED_PARITY_ONLY\nFAIL-SAFE ROLLBACK: ARMED\nSUGGESTED NEXT PATCH: patch_21_13_6c_implement_story_navigation.py")
  return 0
 except Exception as error:
  restored=restore(r,folder,state);recovery=run([sys.executable,"-m","compileall","-q","rom_v2"],r,False)
  write(r/FAILURE,json.dumps({"stage":STAGE,"status":"FAIL_ROLLED_BACK","reason":str(error),"restored_files":restored,"recovery_compile_returncode":recovery.returncode,"main_py_must_not_run":recovery.returncode!=0,"database_opened":False,"v1_wal_shm_manipulated":False},ensure_ascii=False,indent=2)+"\n")
  print(f"[10/10] [FAIL] {error}; rollback: FAIL_ROLLED_BACK");return 1
if __name__=="__main__":raise SystemExit(main())
