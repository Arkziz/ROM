#!/usr/bin/env python3
"""Stage 21.13.6a: refine the V1 Story navigation contract without production mutation."""
from __future__ import annotations
import ast,hashlib,json,re,shutil,subprocess,sys
from datetime import datetime,timezone
from pathlib import Path
STAGE="21.13.6a";PARENT="de4973b1b4f673683fcfd25b238b6d216dfb4c9a"
SELF="patch/patch_21_13_6a_refine_story_navigation_contract.py"
PREREQ=Path("reports/stage_21_13_6_existing_story_navigation_audit.json")
REPORT=Path("reports/stage_21_13_6a_refined_story_navigation_contract.json")
DOC=Path("MD/STAGE_21_13_6A_REFINED_STORY_NAVIGATION_CONTRACT.md")
FAILURE=Path("reports/stage_21_13_6a_failure_rollback.json")
TARGETS=(Path(SELF),REPORT,DOC);ALLOWED={SELF,"ROM_FULL_DUMP.txt",FAILURE.as_posix()}
PROTECTED=(Path("main.py"),Path("game.db-wal"),Path("game.db-shm"))
OWNERS=(
 Path("data/story_quest_hierarchy.py"),
 Path("handlers/story_quest_hierarchy_ui.py"),
 Path("handlers/profile.py"),
 Path("systems/story_quest_location_presentation.py"),
 Path("data/story_quest_title_presentation.py"),
 Path("db_modules/story_quests.py"),
)
CONTRACTS=(
 "STORY_TO_SECTION_TO_QUEST_HIERARCHY","LOCALIZED_LOCATION_AND_SECTION_NAMES",
 "ACTIVE_QUEST_TARGET_PRESENTATION","QUEST_STATUS_AND_PROGRESS_PRESENTATION",
 "NAVIGATION_CALLBACK_AND_RETURN_PATHS","LOCKED_AVAILABLE_COMPLETED_VISIBILITY",
 "NO_FORBIDDEN_CHAPTER_TERM_IN_UI","STABLE_ID_TO_HUMAN_LABEL_RESOLUTION",
)
DECISIONS={
 "STORY_TO_SECTION_TO_QUEST_HIERARCHY":{
  "rule":"The user flow is Story list -> Section list -> Quest list -> Quest detail; section boundaries and ordering come only from canonical hierarchy metadata.",
  "owners":["data/story_quest_hierarchy.py","handlers/story_quest_hierarchy_ui.py"],
  "must_preserve":["stories","sections","quests","quest_detail"],
  "must_not":"Flatten the hierarchy or derive sections from display text."},
 "LOCALIZED_LOCATION_AND_SECTION_NAMES":{
  "rule":"Every user-facing location and section label is resolved from canonical metadata; technical IDs are internal only.",
  "owners":["data/story_quest_hierarchy.py","systems/story_quest_location_presentation.py"],
  "required_labels":{"start_path":"Початок Шляху","dark_forest":"Темний Бір"},
  "must_not":"Format start_path or dark_forest directly for UI."},
 "ACTIVE_QUEST_TARGET_PRESENTATION":{
  "rule":"The active quest detail presents its current canonical objective/progress text and does not invent a target from quest type or ID.",
  "owners":["db_modules/story_quests.py","handlers/story_quest_hierarchy_ui.py"],
  "source_priority":["persisted active quest state","canonical objective/progress metadata"],
  "must_not":"Guess active target from title, location ID, or quest number."},
 "QUEST_STATUS_AND_PROGRESS_PRESENTATION":{
  "rule":"Quest entries distinguish active, available, locked, and completed states; progress belongs to the active quest state and completion is persistent.",
  "owners":["db_modules/story_quests.py","handlers/story_quest_hierarchy_ui.py"],
  "statuses":["active","available","locked","completed"],
  "must_not":"Treat unavailable as completed or expose stale progress after completion."},
 "NAVIGATION_CALLBACK_AND_RETURN_PATHS":{
  "rule":"Callbacks form a bounded hierarchy and every detail/list surface returns to its immediate parent, while the root returns to the canonical profile/account surface.",
  "owners":["handlers/story_quest_hierarchy_ui.py","handlers/profile.py"],
  "return_chain":["quest_detail->quest_list","quest_list->section_list","section_list->story_list","story_list->profile"],
  "must_not":"Create dead-end callbacks or return directly to an unrelated menu."},
 "LOCKED_AVAILABLE_COMPLETED_VISIBILITY":{
  "rule":"Visibility and labels follow V1 hierarchy policy: completed remains visible, active is identifiable, available can be opened, and locked remains non-actionable without leaking spoiler titles.",
  "owners":["handlers/story_quest_hierarchy_ui.py","data/story_quest_title_presentation.py","db_modules/story_quests.py"],
  "spoiler_policy":"Locked quest labels use the canonical spoiler-safe title presentation path.",
  "must_not":"Expose locked quest spoiler titles or make locked entries actionable."},
 "NO_FORBIDDEN_CHAPTER_TERM_IN_UI":{
  "rule":"All Ukrainian user-facing Story navigation uses 'розділ'; forms of 'глава' are forbidden in UI text and metadata.",
  "owners":["data/story_quest_hierarchy.py","handlers/story_quest_hierarchy_ui.py","handlers/profile.py"],
  "allowed_term":"розділ","forbidden_terms":["глава","глави","главу","главою","главі"],
  "scope":"User-visible runtime strings and Story navigation metadata; historical tests/reports/comments are evidence only and not runtime defects."},
 "STABLE_ID_TO_HUMAN_LABEL_RESOLUTION":{
  "rule":"Stable story/location/section/quest IDs remain internal keys and all human labels are obtained through canonical resolvers or authoritative metadata.",
  "owners":["data/story_quest_hierarchy.py","systems/story_quest_location_presentation.py","data/story_quest_title_presentation.py"],
  "must_not":"Humanize IDs with replace/strip/title or duplicate label maps in handlers."},
}
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
def status(r):
 return [(x[:2],x[3:].split(" -> ")[-1].replace("\\","/")) for x in git(r,"status","--porcelain=v1","--untracked-files=all").stdout.splitlines() if x]
def backup(r):
 folder=r/"backup"/("stage_21_13_6a_"+datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ"));folder.mkdir(parents=True);state={}
 for rel in TARGETS:
  p=r/rel;state[rel.as_posix()]=p.exists()
  if p.exists():(folder/rel).parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,folder/rel)
 return folder,state
def restore(r,folder,state):
 restored=[]
 if folder:
  for name,existed in state.items():
   dst=r/name;src=folder/name
   if existed and src.exists():dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dst);restored.append(name)
   elif not existed and dst.exists():dst.unlink();restored.append(name+":deleted")
 git(r,"reset","--quiet",check=False);return restored
def owner_evidence(r):
 out={}
 patterns=re.compile(r"(?i)(story|quest|section|розділ|істор|квест|location|active|completed|locked|callback|progress|objective)")
 for rel in OWNERS:
  p=r/rel
  if not p.exists():raise PatchError("missing_authoritative_owner:"+rel.as_posix())
  text=p.read_text(encoding="utf-8-sig");ast.parse(text)
  lines=[{"line":i,"text":line.strip()[:500]} for i,line in enumerate(text.splitlines(),1) if patterns.search(line)]
  out[rel.as_posix()]={"sha256":sha(p),"line_count":len(text.splitlines()),"semantic_hits":lines[:200]}
 return out
def runtime_forbidden_hits(r):
 terms=re.compile(r"(?i)\b(глава|глави|главу|главою|главі)\b");hits=[]
 for rel in OWNERS:
  for i,line in enumerate((r/rel).read_text(encoding="utf-8-sig").splitlines(),1):
   if terms.search(line):hits.append({"file":rel.as_posix(),"line":i,"text":line.strip()[:500]})
 return hits
def main():
 r=root();folder=None;state={};before={p.as_posix():sha(r/p) for p in PROTECTED}
 try:
  audit=json.loads((r/PREREQ).read_text(encoding="utf-8-sig"));summary=audit.get("summary",{})
  if git(r,"rev-parse","HEAD").stdout.strip()!=PARENT:raise PatchError("wrong_exact_parent")
  if audit.get("stage")!="21.13.6" or audit.get("conclusion")!="GO_TO_SEMANTIC_REFINEMENT" or summary.get("contract_count")!=8 or summary.get("review_required_contracts")!=8:raise PatchError("invalid_stage_21_13_6_prerequisite")
  print("[1/10] [PASS] Stage 21.13.6 read-only audit prerequisite and 8/8 review matrix verified.")
  branch=git(r,"branch","--show-current").stdout.strip();staged=git(r,"diff","--cached","--name-only").stdout.strip()
  if not branch:raise PatchError("git_preflight_detached_head")
  if staged:raise PatchError("git_preflight_staged_index:"+staged.replace("\n",","))
  bad=sorted(p for st,p in status(r) if p not in ALLOWED or (p!=SELF and st[0]!=" "))
  if bad:raise PatchError("unexpected_dirty:"+repr(bad))
  print(f"[2/10] [PASS] Active branch {branch}, exact parent, dirty allowlist and clean index verified.")
  folder,state=backup(r);print("[3/10] [PASS] Refinement artifacts backed up before publication.")
  evidence=owner_evidence(r);print("[4/10] [PASS] Six authoritative V1 Story navigation owners parsed successfully.")
  if tuple(DECISIONS)!=CONTRACTS or len(DECISIONS)!=8:raise PatchError("refined_contract_matrix_mismatch")
  for name,decision in DECISIONS.items():
   if not decision.get("rule") or not decision.get("owners"):raise PatchError("incomplete_decision:"+name)
   for owner in decision["owners"]:
    if owner not in evidence:raise PatchError("unknown_owner:"+name+":"+owner)
  print("[5/10] [PASS] All 8 navigation contracts refined with explicit authoritative owners and fail-closed rules.")
  forbidden=runtime_forbidden_hits(r);print(f"[6/10] [PASS] Runtime-owner terminology scope isolated: {len(forbidden)} current forbidden-term evidence hit(s) retained for parity resolution.")
  compile_v1=run([sys.executable,"-m","py_compile",*[str(r/x) for x in OWNERS]],r,False);compile_v2=run([sys.executable,"-m","compileall","-q","rom_v2"],r,False)
  if compile_v1.returncode or compile_v2.returncode:raise PatchError("compile_gate_failed:"+compile_v1.stdout+compile_v1.stderr+compile_v2.stdout+compile_v2.stderr)
  print("[7/10] [PASS] Authoritative V1 owners and existing V2 compile gates passed.")
  if before!={p.as_posix():sha(r/p) for p in PROTECTED}:raise PatchError("protected_runtime_changed")
  print("[8/10] [PASS] Production entry point and DB sidecars remained byte-identical; database was not opened.")
  rows=[{"contract":name,"classification":"REFINED","decision":DECISIONS[name],"implementation_status":"WAIT_FOR_PARITY_RESOLUTION"} for name in CONTRACTS]
  payload={"schema_version":1,"stage":STAGE,"status":"PASS","conclusion":"GO_TO_PARITY_RESOLUTION","parent":PARENT,"source_audit":PREREQ.as_posix(),"source_audit_sha256":sha(r/PREREQ),"summary":{"contract_count":8,"refined_contracts":8,"confirmed_contracts":0,"review_required_contracts":0,"implementation_authorized":False,"database_opened":False,"production_code_changed":False,"v1_wal_shm_manipulated":False},"authoritative_owners":evidence,"runtime_forbidden_term_hits":forbidden,"contract_matrix":rows,"parity_resolution_requirements":["Classify every runtime-owner forbidden-term hit as user-visible, metadata, comment, or test-only.","Verify exact callback grammar and immediate-parent return paths.","Verify active/available/locked/completed state derivation from persisted V1 state.","Verify spoiler-safe locked quest labels and canonical location/section resolvers.","Produce a resolved 8/8 contract matrix before any implementation."],"manual_game_check":"NOT_REQUIRED_CONTRACT_ONLY","suggested_next_patch":"patch_21_13_6b_resolve_story_navigation_parity.py","backup_path":folder.relative_to(r).as_posix()}
  write(r/REPORT,json.dumps(payload,ensure_ascii=False,indent=2)+"\n")
  lines=["# Stage 21.13.6a - Refined Story navigation contract","","- Status: **PASS**","- Conclusion: **GO_TO_PARITY_RESOLUTION**","- Contracts: **8/8 REFINED**","- Implementation authorized: **NO**","- Database opened: **NO**","- Production mutation: **NO**","- Manual game check: **NOT_REQUIRED_CONTRACT_ONLY**","","## Refined contracts",*[f"### {name}\n\n{DECISIONS[name]['rule']}\n\nOwners: "+", ".join(f"`{x}`" for x in DECISIONS[name]["owners"])+"\n" for name in CONTRACTS],"## Current runtime-owner terminology evidence","",f"Forbidden-term evidence hits requiring parity classification: **{len(forbidden)}**","","## Next patch","","`patch_21_13_6b_resolve_story_navigation_parity.py`",""]
  write(r/DOC,"\n".join(lines));print("[9/10] [PASS] JSON and Markdown refined Story navigation contract artifacts written.")
  files={x.as_posix() for x in TARGETS};git(r,"add","-f","--",*sorted(files));got={x.replace("\\","/") for x in git(r,"diff","--cached","--name-only").stdout.splitlines() if x}
  if got!=files:raise PatchError("staging_mismatch:"+repr(sorted(got)))
  z=git(r,"commit","-m","Stage 21.13.6a: refine Story navigation contract","--",*sorted(files),check=False)
  if z.returncode:raise PatchError("commit_failed:"+z.stdout+z.stderr)
  commit=git(r,"rev-parse","HEAD").stdout.strip();changed={x.replace("\\","/") for x in git(r,"diff-tree","--no-commit-id","--name-only","-r",commit).stdout.splitlines() if x}
  if changed!=files:raise PatchError("commit_scope_mismatch:"+repr(sorted(changed)))
  print(f"[10/10] [PASS] Refined Story navigation contract committed: {commit}")
  print("CONCLUSION: GO_TO_PARITY_RESOLUTION\nPATCH STATUS: PASS\nCONTRACT MATRIX: 8 REFINED / 0 REVIEW_REQUIRED / 8 TOTAL\nIMPLEMENTATION AUTHORIZED: False\nDATABASE OPENED: False\nPRODUCTION CODE CHANGED: False\nMANUAL GAME CHECK: NOT_REQUIRED_CONTRACT_ONLY\nFAIL-SAFE ROLLBACK: ARMED\nSUGGESTED NEXT PATCH: patch_21_13_6b_resolve_story_navigation_parity.py")
  return 0
 except Exception as error:
  restored=restore(r,folder,state);recovery=run([sys.executable,"-m","compileall","-q","rom_v2"],r,False)
  write(r/FAILURE,json.dumps({"stage":STAGE,"status":"FAIL_ROLLED_BACK","reason":str(error),"restored_files":restored,"recovery_compile_returncode":recovery.returncode,"main_py_must_not_run":recovery.returncode!=0,"database_opened":False,"v1_wal_shm_manipulated":False},ensure_ascii=False,indent=2)+"\n")
  print(f"[10/10] [FAIL] {error}; rollback: FAIL_ROLLED_BACK");return 1
if __name__=="__main__":raise SystemExit(main())
