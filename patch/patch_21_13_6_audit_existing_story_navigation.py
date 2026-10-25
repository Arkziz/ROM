#!/usr/bin/env python3
"""Stage 21.13.6: read-only audit of existing V1 Story navigation."""
from __future__ import annotations
import hashlib,json,os,re,shutil,subprocess,sys
from datetime import datetime,timezone
from pathlib import Path

STAGE="21.13.6";PARENT="a3022ce08878691be58e175b117bc2ceadd36041"
SELF="patch/patch_21_13_6_audit_existing_story_navigation.py"
PREREQ=Path("reports/stage_21_13_5g_story_content_91_100_implementation.json")
REPORT=Path("reports/stage_21_13_6_existing_story_navigation_audit.json")
DOC=Path("MD/STAGE_21_13_6_EXISTING_STORY_NAVIGATION_AUDIT.md")
FAILURE=Path("reports/stage_21_13_6_failure_rollback.json")
TARGETS=(Path(SELF),REPORT,DOC)
ALLOWED={SELF,"ROM_FULL_DUMP.txt",FAILURE.as_posix()}
PROTECTED=(Path("main.py"),Path("game.db-wal"),Path("game.db-shm"))
CONTRACTS=(
 "STORY_TO_SECTION_TO_QUEST_HIERARCHY",
 "LOCALIZED_LOCATION_AND_SECTION_NAMES",
 "ACTIVE_QUEST_TARGET_PRESENTATION",
 "QUEST_STATUS_AND_PROGRESS_PRESENTATION",
 "NAVIGATION_CALLBACK_AND_RETURN_PATHS",
 "LOCKED_AVAILABLE_COMPLETED_VISIBILITY",
 "NO_FORBIDDEN_CHAPTER_TERM_IN_UI",
 "STABLE_ID_TO_HUMAN_LABEL_RESOLUTION",
)
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
def sha(p):
 if not p.exists():return None
 return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,t):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(t,encoding="utf-8",newline="\n")
def status(r):
 out=[]
 for line in git(r,"status","--porcelain=v1","--untracked-files=all").stdout.splitlines():
  if not line:continue
  out.append((line[:2],line[3:].split(" -> ")[-1].replace("\\","/")))
 return out
def backup(r):
 stamp=datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ");folder=r/"backup"/f"stage_21_13_6_{stamp}";folder.mkdir(parents=True,exist_ok=False);state={}
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
def source_files(r):
 skip={".git",".venv","venv","backup","patch","rom_v2","tests_v2","reports","MD","__pycache__"}
 return sorted(p for p in r.rglob("*.py") if not any(part in skip for part in p.relative_to(r).parts))
def inspect(r):
 patterns={
  "hierarchy":re.compile(r"(?i)(істор|story).{0,100}(розділ|section|quest|квест)|(розділ|section).{0,100}(quest|квест)"),
  "active_target":re.compile(r"(?i)(активн.{0,20}(ціл|квест)|active.{0,20}(target|quest)|progress_text|objective_text)"),
  "callbacks":re.compile(r"(?i)(callback|inline).{0,100}(quest|story|істор|квест)|(quest|story).{0,100}(callback|inline)"),
  "statuses":re.compile(r"(?i)(locked|available|completed|active|заблок|доступ|заверш|активн)"),
  "resolver":re.compile(r"(?i)(location.{0,30}(name|label|title)|resolve.{0,30}(location|quest|section)|localized|локаліз)"),
  "forbidden_chapter":re.compile(r"(?i)\b(глава|глави|главу|главою|главі)\b"),
  "technical_ids":re.compile(r"\b(start_path|dark_forest)\b"),
 }
 hits={k:[] for k in patterns};hashes={};files=source_files(r)
 for p in files:
  rel=p.relative_to(r).as_posix();hashes[rel]=sha(p)
  try:text=p.read_text(encoding="utf-8-sig")
  except UnicodeDecodeError:continue
  for ln,line in enumerate(text.splitlines(),1):
   for key,pat in patterns.items():
    if pat.search(line):
     hits[key].append({"file":rel,"line":ln,"text":line.strip()[:500]})
 return {"files_scanned":len(files),"source_hashes":hashes,"hits":hits,"counts":{k:len(v) for k,v in hits.items()}}
def classify(ev):
 h=ev["hits"]
 rows=[]
 mapping={
  "STORY_TO_SECTION_TO_QUEST_HIERARCHY":("hierarchy",),
  "LOCALIZED_LOCATION_AND_SECTION_NAMES":("resolver","technical_ids"),
  "ACTIVE_QUEST_TARGET_PRESENTATION":("active_target",),
  "QUEST_STATUS_AND_PROGRESS_PRESENTATION":("active_target","statuses"),
  "NAVIGATION_CALLBACK_AND_RETURN_PATHS":("callbacks",),
  "LOCKED_AVAILABLE_COMPLETED_VISIBILITY":("statuses",),
  "NO_FORBIDDEN_CHAPTER_TERM_IN_UI":("forbidden_chapter",),
  "STABLE_ID_TO_HUMAN_LABEL_RESOLUTION":("resolver","technical_ids"),
 }
 for contract in CONTRACTS:
  keys=mapping[contract];evidence=sum((h[k][:25] for k in keys),[])
  # Read-only discovery is evidence, not authorization. All UI semantics require refinement.
  rows.append({"contract":contract,"classification":"REVIEW_REQUIRED","evidence_keys":list(keys),"evidence_count":sum(len(h[k]) for k in keys),"sample_evidence":evidence})
 return rows
def main():
 r=root();folder=None;state={};before={x.as_posix():sha(r/x) for x in PROTECTED}
 try:
  pre=json.loads((r/PREREQ).read_text(encoding="utf-8-sig"))
  if git(r,"rev-parse","HEAD").stdout.strip()!=PARENT:raise PatchError("wrong_exact_parent")
  if pre.get("stage")!="21.13.5g" or pre.get("conclusion")!="API_READY_STORY_CONTENT_51_100_COMPLETE" or pre.get("story_51_100",{}).get("canonical_records")!=50:raise PatchError("invalid_stage_21_13_5g_prerequisite")
  print("[1/10] [PASS] Stage 21.13.5g complete 51-100 API-ready prerequisite verified.")
  branch=git(r,"branch","--show-current").stdout.strip();staged=git(r,"diff","--cached","--name-only").stdout.strip()
  if not branch:raise PatchError("git_preflight_detached_head")
  if staged:raise PatchError("git_preflight_staged_index:"+staged.replace("\n",","))
  bad=sorted(p for st,p in status(r) if p not in ALLOWED or (p!=SELF and st[0]!=" "))
  if bad:raise PatchError("unexpected_dirty:"+repr(bad))
  print(f"[2/10] [PASS] Active branch {branch}, exact parent, dirty allowlist and clean index verified.")
  folder,state=backup(r);print("[3/10] [PASS] Audit artifacts backed up before report publication.")
  evidence=inspect(r);print(f"[4/10] [PASS] Read-only V1 Story navigation discovery scanned {evidence['files_scanned']} Python source files.")
  matrix=classify(evidence)
  if len(matrix)!=8 or tuple(x["contract"] for x in matrix)!=CONTRACTS:raise PatchError("contract_matrix_mismatch")
  print("[5/10] [PASS] Story hierarchy, active target, status, callback and label evidence collected.")
  print("[6/10] [PASS] Forbidden 'глава' term and technical location ID exposure evidence collected without mutation.")
  compile_check=run([sys.executable,"-m","compileall","-q","rom_v2"],r,False)
  if compile_check.returncode:raise PatchError("rom_v2_compile_failed:"+compile_check.stdout+compile_check.stderr)
  print("[7/10] [PASS] Existing V2 compile gate passed after read-only V1 inspection.")
  if before!={x.as_posix():sha(r/x) for x in PROTECTED}:raise PatchError("protected_runtime_changed")
  print("[8/10] [PASS] Production entry point and DB sidecars remained byte-identical; database was not opened.")
  unresolved=[x["contract"] for x in matrix]
  payload={"schema_version":1,"stage":STAGE,"status":"PASS","conclusion":"GO_TO_SEMANTIC_REFINEMENT","parent":PARENT,"scope":"Story navigation: Історія -> розділи -> квести; localized names; active target","summary":{"contract_count":8,"confirmed_contracts":0,"review_required_contracts":8,"unresolved_contracts":unresolved,"implementation_authorized":False,"database_opened":False,"production_code_changed":False,"v1_wal_shm_manipulated":False},"observations":{"forbidden_chapter_hits":evidence["counts"]["forbidden_chapter"],"technical_location_id_hits":evidence["counts"]["technical_ids"],"navigation_callback_hits":evidence["counts"]["callbacks"],"active_target_hits":evidence["counts"]["active_target"]},"evidence":evidence,"contract_matrix":matrix,"manual_game_check":"NOT_REQUIRED_READ_ONLY_AUDIT","suggested_next_patch":"patch_21_13_6a_refine_story_navigation_contract.py","backup_path":folder.relative_to(r).as_posix()}
  write(r/REPORT,json.dumps(payload,ensure_ascii=False,indent=2)+"\n")
  lines=["# Stage 21.13.6 - Existing V1 Story navigation audit","","- Status: **PASS**","- Conclusion: **GO_TO_SEMANTIC_REFINEMENT**","- Scope: **Історія -> розділи -> квести; локалізовані назви; активна ціль**","- Contracts: **0 CONFIRMED / 8 REVIEW_REQUIRED / 8 TOTAL**","- Implementation authorized: **NO**","- Database opened: **NO**","- Production mutation: **NO**","- Manual game check: **NOT_REQUIRED_READ_ONLY_AUDIT**","","## Evidence counters","",f"- Source files scanned: **{evidence['files_scanned']}**",f"- Navigation callback hits: **{evidence['counts']['callbacks']}**",f"- Active target hits: **{evidence['counts']['active_target']}**",f"- Forbidden `глава` hits: **{evidence['counts']['forbidden_chapter']}**",f"- Technical location ID hits: **{evidence['counts']['technical_ids']}**","","## Review-required contracts",*[f"- `{x}`" for x in unresolved],"","## Next patch","","`patch_21_13_6a_refine_story_navigation_contract.py`",""]
  write(r/DOC,"\n".join(lines));print("[9/10] [PASS] JSON and Markdown read-only Story navigation audit artifacts written.")
  files={x.as_posix() for x in TARGETS};git(r,"add","-f","--",*sorted(files));got={x.replace("\\","/") for x in git(r,"diff","--cached","--name-only").stdout.splitlines() if x}
  if got!=files:raise PatchError("staging_mismatch:"+repr(sorted(got)))
  z=git(r,"commit","-m","Stage 21.13.6: audit existing Story navigation","--",*sorted(files),check=False)
  if z.returncode:raise PatchError("commit_failed:"+z.stdout+z.stderr)
  commit=git(r,"rev-parse","HEAD").stdout.strip();changed={x.replace("\\","/") for x in git(r,"diff-tree","--no-commit-id","--name-only","-r",commit).stdout.splitlines() if x}
  if changed!=files:raise PatchError("commit_scope_mismatch:"+repr(sorted(changed)))
  print(f"[10/10] [PASS] Existing V1 Story navigation audit committed: {commit}")
  print("CONCLUSION: GO_TO_SEMANTIC_REFINEMENT\nPATCH STATUS: PASS\nCONTRACT MATRIX: 0 CONFIRMED / 8 REVIEW_REQUIRED / 8 TOTAL\nIMPLEMENTATION AUTHORIZED: False\nDATABASE OPENED: False\nPRODUCTION CODE CHANGED: False\nMANUAL GAME CHECK: NOT_REQUIRED_READ_ONLY_AUDIT\nFAIL-SAFE ROLLBACK: ARMED\nSUGGESTED NEXT PATCH: patch_21_13_6a_refine_story_navigation_contract.py")
  return 0
 except Exception as error:
  restored=restore(r,folder,state);recovery=run([sys.executable,"-m","compileall","-q","rom_v2"],r,False)
  write(r/FAILURE,json.dumps({"stage":STAGE,"status":"FAIL_ROLLED_BACK","reason":str(error),"restored_files":restored,"recovery_compile_returncode":recovery.returncode,"main_py_must_not_run":recovery.returncode!=0,"database_opened":False,"v1_wal_shm_manipulated":False},ensure_ascii=False,indent=2)+"\n")
  print(f"[10/10] [FAIL] {error}; rollback: FAIL_ROLLED_BACK");return 1
if __name__=="__main__":raise SystemExit(main())
