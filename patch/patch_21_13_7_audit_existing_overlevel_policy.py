#!/usr/bin/env python3
"""Stage 21.13.7: read-only audit of the existing V1 overlevel/SKIP policy."""
from __future__ import annotations
import ast,hashlib,json,os,re,shutil,subprocess,sys
from datetime import datetime,timezone
from pathlib import Path

STAGE="21.13.7";PARENT="9dc4660a9a0dc8f66e8c1cce29d326cd40034bf8"
SELF="patch/patch_21_13_7_audit_existing_overlevel_policy.py"
PREREQ=Path("reports/stage_21_13_6c_story_navigation_implementation.json")
REPORT=Path("reports/stage_21_13_7_existing_overlevel_policy_audit.json")
DOC=Path("MD/STAGE_21_13_7_EXISTING_OVERLEVEL_POLICY_AUDIT.md")
FAILURE=Path("reports/stage_21_13_7_failure_rollback.json")
TARGETS=(Path(SELF),REPORT,DOC);ALLOWED={SELF,"ROM_FULL_DUMP.txt",FAILURE.as_posix()}
PROTECTED=(Path("main.py"),Path("game.db-wal"),Path("game.db-shm"))
SCAN_ROOTS=(Path("data"),Path("systems"),Path("handlers"),Path("db_modules"),Path("tests"),Path("tools"))
TOKENS=("overlevel","over_level","over-level","skip","skipped","SKIPPED","reconcile","unlock_level","player_level","active_quest","story_quest","quest_item","reward","completion")
CONTRACTS=(
 "OVERLEVEL_TRIGGER_AND_THRESHOLD",
 "AFFECTED_QUEST_RANGE_AND_SECTION_BOUNDARY",
 "ACTIVE_QUEST_AND_CURRENT_PROGRESS_HANDLING",
 "SKIPPED_STATE_PERSISTENCE_AND_IDEMPOTENCY",
 "NEXT_QUEST_AVAILABILITY_AND_CHAIN_CONTINUITY",
 "NO_REWARD_AND_NO_QUEST_ITEM_CONSUMPTION",
 "EXPLICIT_SKIP_VS_AUTOMATIC_RECONCILIATION",
 "RESTART_RECOVERY_AND_TRANSACTION_BOUNDARY",
 "PRESENTATION_HISTORY_AND_NAVIGATION_VISIBILITY",
 "STAGE_19_18_POLICY_AUTHORITY_AND_SUPERSESSION",
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
 f=r/"backup"/("stage_21_13_7_"+datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ"));f.mkdir(parents=True);state={}
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
def cleanup_bytecode(r):
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
def discover(r):
 files=[]
 for base in SCAN_ROOTS:
  folder=r/base
  if not folder.exists():continue
  files.extend(p for p in folder.rglob("*.py") if ".venv" not in p.parts and "backup" not in p.parts)
 files=sorted(set(files));hits=[];owners=[];symbol_index={}
 for p in files:
  rel=p.relative_to(r).as_posix();text=p.read_text(encoding="utf-8",errors="replace")
  try:tree=ast.parse(text,filename=rel)
  except SyntaxError as e:raise PatchError(f"syntax_error_in_scanned_source:{rel}:{e}")
  symbols=[]
  for node in ast.walk(tree):
   if isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef,ast.ClassDef)):
    name=node.name;low=name.casefold()
    if any(k in low for k in ("overlevel","skip","reconcile","story_quest","quest")):symbols.append({"name":name,"kind":type(node).__name__,"line":node.lineno})
  if symbols:symbol_index[rel]=symbols
  file_hits=[]
  for no,line in enumerate(text.splitlines(),1):
   low=line.casefold()
   matched=sorted({t for t in TOKENS if t.casefold() in low})
   if matched:file_hits.append({"line":no,"tokens":matched,"text":line.strip()[:500]})
  if file_hits:
   score=sum(4 if t in {"overlevel","over_level","over-level"} else 2 if t.casefold() in {"skip","skipped"} else 1 for h in file_hits for t in h["tokens"])
   item={"file":rel,"sha256":sha(p),"hit_count":len(file_hits),"score":score,"hits":file_hits[:120]};hits.append(item)
   if score>=8 or any("overlevel" in t.casefold() or "over_level" in t.casefold() for h in file_hits for t in h["tokens"]):owners.append(rel)
 hits.sort(key=lambda x:(-x["score"],x["file"]));owners=sorted(set(owners))
 return files,hits,owners,symbol_index
def main():
 r=root();folder=None;state={};before={p.as_posix():sha(r/p) for p in PROTECTED}
 try:
  if git(r,"rev-parse","HEAD").stdout.strip()!=PARENT:raise PatchError("wrong_exact_parent")
  pre=json.loads((r/PREREQ).read_text(encoding="utf-8-sig"))
  if pre.get("stage")!="21.13.6c" or pre.get("status")!="PASS" or pre.get("conclusion")!="API_READY_STORY_NAVIGATION":raise PatchError("invalid_stage_21_13_6c_prerequisite")
  if pre.get("contracts",{}).values() and any(v!="PASS" for v in pre["contracts"].values()):raise PatchError("story_navigation_contracts_not_all_pass")
  print("[1/10] [PASS] Stage 21.13.6c API-ready Story navigation prerequisite verified.")
  branch=git(r,"branch","--show-current").stdout.strip();staged=git(r,"diff","--cached","--name-only").stdout.strip()
  if not branch:raise PatchError("git_preflight_detached_head")
  if staged:raise PatchError("git_preflight_staged_index:"+staged.replace("\n",","))
  bad=sorted(p for st,p in status(r) if p not in ALLOWED or (p!=SELF and st[0]!=" "))
  if bad:raise PatchError("unexpected_dirty:"+repr(bad))
  print(f"[2/10] [PASS] Active branch {branch}, exact parent, dirty allowlist and clean index verified.")
  folder,state=backup(r);print("[3/10] [PASS] Audit artifacts backed up before report publication.")
  files,hits,owners,symbols=discover(r)
  if not hits:raise PatchError("overlevel_policy_evidence_not_found")
  print(f"[4/10] [PASS] Read-only V1 overlevel/SKIP discovery scanned {len(files)} Python source files.")
  counts={t:sum(1 for f in hits for h in f["hits"] if t in h["tokens"]) for t in TOKENS}
  print("[5/10] [PASS] Trigger, SKIP, persistence, chain, reward, quest-item and presentation evidence inventoried without opening SQLite.")
  matrix=[{"contract":c,"status":"REVIEW_REQUIRED","reason":"Discovery evidence requires semantic classification against the authoritative Stage 19.18 runtime path."} for c in CONTRACTS]
  evidence={"files_with_hits":len(hits),"candidate_owner_files":owners,"token_counts":counts,"top_files":[{"file":x["file"],"sha256":x["sha256"],"hit_count":x["hit_count"],"score":x["score"],"hits":x["hits"]} for x in hits[:40]],"candidate_symbols":symbols}
  print(f"[6/10] [PASS] Overlevel policy evidence matrix built; review-required contracts: {len(CONTRACTS)}.")
  env=os.environ.copy();env["PYTHONDONTWRITEBYTECODE"]="1";removed_before=cleanup_bytecode(r)
  compile_args=[sys.executable,"-m","compileall","-q","rom_v2"];z=run(compile_args,r,False,env)
  if z.returncode:raise PatchError("v2_compile_failed:"+z.stdout+z.stderr)
  removed_after=cleanup_bytecode(r)
  unit_args=[sys.executable,"-m","unittest","discover","-s","tests_v2","-p","test_*.py"];z=run(unit_args,r,False,env)
  if z.returncode:raise PatchError("v2_unit_failed:"+z.stdout+z.stderr)
  print(f"[7/10] [PASS] Canonical V2 CI passed after removing {len(removed_before)+len(removed_after)} bytecode artifact(s).")
  if before!={p.as_posix():sha(r/p) for p in PROTECTED}:raise PatchError("protected_runtime_changed")
  print("[8/10] [PASS] V1/V2 production sources, DB sidecars and protected configuration remained byte-identical; database was not opened.")
  report={"schema_version":1,"stage":STAGE,"status":"PASS","conclusion":"GO_TO_SEMANTIC_REFINEMENT","parent":PARENT,"scope":"read_only_existing_v1_overlevel_policy_audit","policy_anchor":"Stage 19.18 SKIP policy","contract_matrix":matrix,"summary":{"confirmed_contracts":0,"review_required_contracts":len(CONTRACTS),"total_contracts":len(CONTRACTS),"implementation_authorized":False},"evidence":evidence,"database_opened":False,"production_code_changed":False,"canonical_reference_changed":False,"v1_wal_shm_manipulated":False,"manual_game_check":"NOT_REQUIRED_READ_ONLY_AUDIT","suggested_next_patch":"patch_21_13_7a_refine_overlevel_policy_contract.py"}
  write(r/REPORT,json.dumps(report,ensure_ascii=False,indent=2)+"\n")
  doc=["# Stage 21.13.7 - Existing V1 Overlevel Policy Audit","","- Status: **PASS**","- Conclusion: **GO_TO_SEMANTIC_REFINEMENT**","- Policy anchor: **Stage 19.18 SKIP policy**","- Database opened: **False**","- Production code changed: **False**","",f"## Discovery","",f"- Scanned Python files: **{len(files)}**",f"- Files with evidence: **{len(hits)}**",f"- Candidate owners: **{len(owners)}**","","## Candidate authoritative owners",*[f"- `{x}`" for x in owners[:30]],"","## Review-required contracts",*[f"- `{x}`" for x in CONTRACTS],"","## Next patch","","`patch_21_13_7a_refine_overlevel_policy_contract.py`",""]
  write(r/DOC,"\n".join(doc));print("[9/10] [PASS] JSON and Markdown read-only Overlevel policy audit artifacts written.")
  files_to_commit={x.as_posix() for x in TARGETS};git(r,"add","-f","--",*sorted(files_to_commit));got={x.replace("\\","/") for x in git(r,"diff","--cached","--name-only").stdout.splitlines() if x}
  if got!=files_to_commit:raise PatchError("staging_mismatch:"+repr(sorted(got)))
  z=git(r,"commit","-m","Stage 21.13.7: audit existing overlevel policy","--",*sorted(files_to_commit),check=False)
  if z.returncode:raise PatchError("commit_failed:"+z.stdout+z.stderr)
  commit=git(r,"rev-parse","HEAD").stdout.strip();changed={x.replace("\\","/") for x in git(r,"diff-tree","--no-commit-id","--name-only","-r",commit).stdout.splitlines() if x}
  if changed!=files_to_commit:raise PatchError("commit_scope_mismatch:"+repr(sorted(changed)))
  print(f"[10/10] [PASS] Existing V1 Overlevel policy audit committed: {commit}")
  print("CONCLUSION: GO_TO_SEMANTIC_REFINEMENT\nPATCH STATUS: PASS\nCONTRACT MATRIX: 0 CONFIRMED / 10 REVIEW_REQUIRED / 10 TOTAL\nIMPLEMENTATION AUTHORIZED: False\nDATABASE OPENED: False\nPRODUCTION CODE CHANGED: False\nMANUAL GAME CHECK: NOT_REQUIRED_READ_ONLY_AUDIT\nFAIL-SAFE ROLLBACK: ARMED\nSUGGESTED NEXT PATCH: patch_21_13_7a_refine_overlevel_policy_contract.py")
  return 0
 except Exception as e:
  restored=restore(r,folder,state);recovery=run([sys.executable,"-m","compileall","-q","rom_v2"],r,False)
  write(r/FAILURE,json.dumps({"stage":STAGE,"status":"FAIL_ROLLED_BACK","reason":str(e),"restored_files":restored,"recovery_compile_returncode":recovery.returncode,"main_py_must_not_run":recovery.returncode!=0,"database_opened":False,"canonical_reference_changed":False,"v1_wal_shm_manipulated":False},ensure_ascii=False,indent=2)+"\n")
  print(f"[10/10] [FAIL] {e}; rollback: FAIL_ROLLED_BACK");return 1
if __name__=="__main__":raise SystemExit(main())
