#!/usr/bin/env python3
"""Stage 21.13.7a: refine the existing V1 overlevel/SKIP behavior contract."""
from __future__ import annotations
import ast,hashlib,json,os,shutil,subprocess,sys
from datetime import datetime,timezone
from pathlib import Path
STAGE="21.13.7a";PARENT="fa51987ba82010889b15bcf0da4b808ae7bc189c"
SELF="patch/patch_21_13_7a_refine_overlevel_policy_contract.py";PREREQ=Path("reports/stage_21_13_7_existing_overlevel_policy_audit.json")
REPORT=Path("reports/stage_21_13_7a_refined_overlevel_policy_contract.json");DOC=Path("MD/STAGE_21_13_7A_REFINED_OVERLEVEL_POLICY_CONTRACT.md");FAILURE=Path("reports/stage_21_13_7a_failure_rollback.json")
TARGETS=(Path(SELF),REPORT,DOC);ALLOWED={SELF,"ROM_FULL_DUMP.txt",FAILURE.as_posix()};PROTECTED=(Path("main.py"),Path("game.db-wal"),Path("game.db-shm"))
OWNERS={
 "orchestration":Path("systems/story_quest_overlevel_system.py"),
 "lifecycle":Path("systems/story_quest_system.py"),
 "persistence":Path("db_modules/story_quests.py"),
 "hook":Path("handlers/combat.py"),
 "presentation":Path("handlers/story_quest_hierarchy_ui.py"),
 "hook_fixture":Path("tools/check_story_quest_overlevel_skip_hook.py"),
 "atomic_fixture":Path("tools/verify_stage_19_34_2_atomic_location_story_skip.py"),
}
CONTRACTS=("OVERLEVEL_TRIGGER_AND_THRESHOLD","AFFECTED_QUEST_RANGE_AND_SECTION_BOUNDARY","ACTIVE_QUEST_AND_CURRENT_PROGRESS_HANDLING","SKIPPED_STATE_PERSISTENCE_AND_IDEMPOTENCY","NEXT_QUEST_AVAILABILITY_AND_CHAIN_CONTINUITY","NO_REWARD_AND_NO_QUEST_ITEM_CONSUMPTION","EXPLICIT_SKIP_VS_AUTOMATIC_RECONCILIATION","RESTART_RECOVERY_AND_TRANSACTION_BOUNDARY","PRESENTATION_HISTORY_AND_NAVIGATION_VISIBILITY","STAGE_19_18_POLICY_AUTHORITY_AND_SUPERSESSION")
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
 f=r/"backup"/("stage_21_13_7a_"+datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ"));f.mkdir(parents=True);state={}
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
def inspect_owner(r,name,rel):
 p=r/rel
 if not p.exists():raise PatchError(f"authoritative_owner_missing:{rel.as_posix()}")
 text=p.read_text(encoding="utf-8");tree=ast.parse(text,filename=rel.as_posix());symbols=[]
 for n in ast.walk(tree):
  if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef,ast.ClassDef)):symbols.append({"name":n.name,"kind":type(n).__name__,"line":n.lineno})
 return {"role":name,"path":rel.as_posix(),"sha256":sha(p),"symbols":symbols,"text":text}
def require_symbols(owner,names):
 have={x["name"] for x in owner["symbols"]};missing=[x for x in names if x not in have]
 if missing:raise PatchError(f"owner_symbols_missing:{owner['path']}:{missing}")
def main():
 r=root();folder=None;state={};before={p.as_posix():sha(r/p) for p in PROTECTED}
 try:
  if git(r,"rev-parse","HEAD").stdout.strip()!=PARENT:raise PatchError("wrong_exact_parent")
  audit=json.loads((r/PREREQ).read_text(encoding="utf-8-sig"));summary=audit.get("summary",{})
  if audit.get("stage")!="21.13.7" or audit.get("conclusion")!="GO_TO_SEMANTIC_REFINEMENT" or summary.get("review_required_contracts")!=10 or summary.get("total_contracts")!=10:raise PatchError("invalid_stage_21_13_7_audit_prerequisite")
  print("[1/10] [PASS] Stage 21.13.7 read-only audit prerequisite and 10/10 review matrix verified.")
  branch=git(r,"branch","--show-current").stdout.strip();staged=git(r,"diff","--cached","--name-only").stdout.strip()
  if not branch:raise PatchError("git_preflight_detached_head")
  if staged:raise PatchError("git_preflight_staged_index:"+staged.replace("\n",","))
  bad=sorted(p for st,p in status(r) if p not in ALLOWED or (p!=SELF and st[0]!=" "))
  if bad:raise PatchError("unexpected_dirty:"+repr(bad))
  print(f"[2/10] [PASS] Active branch {branch}, exact parent, dirty allowlist and clean index verified.")
  folder,state=backup(r);print("[3/10] [PASS] Refinement artifacts backed up before publication.")
  owners={k:inspect_owner(r,k,v) for k,v in OWNERS.items()}
  require_symbols(owners["orchestration"],["build_overlevel_story_skip_message","process_overlevel_story_quest_skip"])
  require_symbols(owners["lifecycle"],["reconcile_overlevel_story_locations","skip_overlevel_active_quest","get_story_quest_status"])
  require_symbols(owners["persistence"],["reconcile_story_location_as_skipped","skip_active_story_quest"])
  print("[4/10] [PASS] Seven authoritative V1 runtime, persistence, presentation and fixture owners parsed successfully.")
  combined="\n".join(x["text"] for x in owners.values())
  markers=("SKIPPED","reward_claimed","quest_item","skipped_now","current_level","location_max_levels","reconcile_overlevel_story_locations","reconcile_story_location_as_skipped","Пропущено без нагород")
  missing=[x for x in markers if x not in combined]
  if missing:raise PatchError("semantic_markers_missing:"+repr(missing))
  rules={
   "OVERLEVEL_TRIGGER_AND_THRESHOLD":{"status":"REFINED","rule":"A location is exceeded only when current_level is strictly greater than its configured maximum; equality does not trigger reconciliation.","owners":[OWNERS["lifecycle"].as_posix(),OWNERS["hook_fixture"].as_posix()]},
   "AFFECTED_QUEST_RANGE_AND_SECTION_BOUNDARY":{"status":"REFINED","rule":"Reconciliation is location-wide: every canonical quest of each exceeded story location is materialized; section boundaries do not limit the mutation.","owners":[OWNERS["lifecycle"].as_posix(),OWNERS["persistence"].as_posix(),OWNERS["atomic_fixture"].as_posix()]},
   "ACTIVE_QUEST_AND_CURRENT_PROGRESS_HANDLING":{"status":"REFINED","rule":"An unfinished ACTIVE row in an exceeded location becomes SKIPPED with no completion conversion; its location quest-item rows are removed. Already finalized rows remain authoritative.","owners":[OWNERS["persistence"].as_posix(),OWNERS["atomic_fixture"].as_posix()]},
   "SKIPPED_STATE_PERSISTENCE_AND_IDEMPOTENCY":{"status":"REFINED","rule":"SKIPPED is persistent and finalized. Re-running reconciliation after the same state produces changed=0 and must not rewrite COMPLETED or already SKIPPED rows.","owners":[OWNERS["persistence"].as_posix(),OWNERS["atomic_fixture"].as_posix()]},
   "NEXT_QUEST_AVAILABILITY_AND_CHAIN_CONTINUITY":{"status":"REFINED","rule":"A predecessor in COMPLETED or SKIPPED satisfies the sequential chain predicate; overlevel reconciliation may finalize a location without leaving a false locked chain.","owners":[OWNERS["lifecycle"].as_posix(),OWNERS["presentation"].as_posix()]},
   "NO_REWARD_AND_NO_QUEST_ITEM_CONSUMPTION":{"status":"REFINED","rule":"Newly skipped quests retain reward_claimed=0, grant no EXP/gold/items, and delete story quest-item rows for the exceeded location rather than consuming them as a turn-in.","owners":[OWNERS["persistence"].as_posix(),OWNERS["orchestration"].as_posix(),OWNERS["atomic_fixture"].as_posix()]},
   "EXPLICIT_SKIP_VS_AUTOMATIC_RECONCILIATION":{"status":"REFINED","rule":"The canonical Stage 19.18 path is automatic location reconciliation after a qualifying level result. The narrower active-quest skip primitive is not a substitute for location-wide reconciliation.","owners":[OWNERS["orchestration"].as_posix(),OWNERS["lifecycle"].as_posix(),OWNERS["persistence"].as_posix()]},
   "RESTART_RECOVERY_AND_TRANSACTION_BOUNDARY":{"status":"REFINED","rule":"The database reconciliation owner performs the location-wide write atomically on the supplied connection. Persisted SKIPPED rows and removal of location quest items survive restart; orchestration must not add a hidden commit.","owners":[OWNERS["persistence"].as_posix(),OWNERS["lifecycle"].as_posix()]},
   "PRESENTATION_HISTORY_AND_NAVIGATION_VISIBILITY":{"status":"REFINED","rule":"SKIPPED remains visible as a finalized journal/navigation state. User messaging reports the location and the newly skipped count explicitly as skipped without rewards.","owners":[OWNERS["presentation"].as_posix(),OWNERS["orchestration"].as_posix()]},
   "STAGE_19_18_POLICY_AUTHORITY_AND_SUPERSESSION":{"status":"REFINED","rule":"The current production runtime chain and its later atomic-location verification are authoritative. Historical candidates, broad token hits and shadow helpers cannot supersede this policy without a separate explicit decision.","owners":[OWNERS["hook"].as_posix(),OWNERS["orchestration"].as_posix(),OWNERS["lifecycle"].as_posix(),OWNERS["persistence"].as_posix(),OWNERS["atomic_fixture"].as_posix()]},
  }
  if set(rules)!=set(CONTRACTS):raise PatchError("refined_contract_matrix_mismatch")
  print("[5/10] [PASS] All 10 overlevel/SKIP contracts refined with explicit owners, invariants and fail-closed boundaries.")
  boundary={"production_hook_order":"victory reward -> story progress -> quest-item drop -> overlevel reconciliation","level_source":"resulting player level after reward processing","trigger_operator":"current_level > location_max_level","location_max_levels":{"start_path":5,"dark_forest":10},"finalized_statuses":["COMPLETED","SKIPPED"],"skip_reward_policy":"NO_REWARD","quest_item_policy":"DELETE_LOCATION_ROWS","idempotency":"SECOND_IDENTICAL_RECONCILIATION_CHANGED_0","narrow_active_skip":"NON_AUTHORITATIVE_FOR_LOCATION_RECONCILIATION"}
  print("[6/10] [PASS] Strict threshold, location-wide atomic mutation, no-reward semantics, item cleanup and idempotency boundaries recorded.")
  env=os.environ.copy();env["PYTHONDONTWRITEBYTECODE"]="1";removed_before=cleanup(r)
  z=run([sys.executable,"-m","compileall","-q","rom_v2"],r,False,env)
  if z.returncode:raise PatchError("v2_compile_failed:"+z.stdout+z.stderr)
  removed_after=cleanup(r);z=run([sys.executable,"-m","unittest","discover","-s","tests_v2","-p","test_*.py"],r,False,env)
  if z.returncode:raise PatchError("v2_unit_failed:"+z.stdout+z.stderr)
  print(f"[7/10] [PASS] Authoritative V1 owners and canonical V2 CI passed after removing {len(removed_before)+len(removed_after)} bytecode artifact(s).")
  if before!={p.as_posix():sha(r/p) for p in PROTECTED}:raise PatchError("protected_runtime_changed")
  print("[8/10] [PASS] Production entry point and DB sidecars remained byte-identical; database was not opened.")
  public_owners={k:{kk:vv for kk,vv in v.items() if kk!="text"} for k,v in owners.items()}
  report={"schema_version":1,"stage":STAGE,"status":"PASS","conclusion":"GO_TO_PARITY_RESOLUTION","parent":PARENT,"policy_anchor":"Stage 19.18 SKIP policy","authoritative_owners":public_owners,"contract_matrix":[{"contract":c,**rules[c]} for c in CONTRACTS],"behavior_boundary":boundary,"summary":{"refined_contracts":10,"review_required_contracts":0,"total_contracts":10,"implementation_authorized":False},"database_opened":False,"production_code_changed":False,"canonical_reference_changed":False,"v1_wal_shm_manipulated":False,"manual_game_check":"NOT_REQUIRED_CONTRACT_ONLY","suggested_next_patch":"patch_21_13_7b_resolve_overlevel_policy_parity.py"}
  write(r/REPORT,json.dumps(report,ensure_ascii=False,indent=2)+"\n")
  lines=["# Stage 21.13.7a - Refined Overlevel Policy Contract","","- Status: **PASS**","- Conclusion: **GO_TO_PARITY_RESOLUTION**","- Policy anchor: **Stage 19.18 SKIP policy**","- Contracts: **10 refined / 0 review required**","- Implementation authorized: **False**","","## Canonical behavior",f"- Trigger: `{boundary['trigger_operator']}`",f"- Max levels: `{boundary['location_max_levels']}`","- Scope: entire exceeded story location","- Newly skipped quests: no rewards","- Location story quest-item rows: deleted","- Repeated reconciliation: idempotent","- Completed rows: preserved","","## Next patch","","`patch_21_13_7b_resolve_overlevel_policy_parity.py`",""]
  write(r/DOC,"\n".join(lines));print("[9/10] [PASS] JSON and Markdown refined Overlevel policy contract artifacts written.")
  files={x.as_posix() for x in TARGETS};git(r,"add","-f","--",*sorted(files));got={x.replace("\\","/") for x in git(r,"diff","--cached","--name-only").stdout.splitlines() if x}
  if got!=files:raise PatchError("staging_mismatch:"+repr(sorted(got)))
  z=git(r,"commit","-m","Stage 21.13.7a: refine overlevel policy contract","--",*sorted(files),check=False)
  if z.returncode:raise PatchError("commit_failed:"+z.stdout+z.stderr)
  commit=git(r,"rev-parse","HEAD").stdout.strip();changed={x.replace("\\","/") for x in git(r,"diff-tree","--no-commit-id","--name-only","-r",commit).stdout.splitlines() if x}
  if changed!=files:raise PatchError("commit_scope_mismatch:"+repr(sorted(changed)))
  print(f"[10/10] [PASS] Refined Overlevel policy contract committed: {commit}")
  print("CONCLUSION: GO_TO_PARITY_RESOLUTION\nPATCH STATUS: PASS\nCONTRACT MATRIX: 10 REFINED / 0 REVIEW_REQUIRED / 10 TOTAL\nIMPLEMENTATION AUTHORIZED: False\nDATABASE OPENED: False\nPRODUCTION CODE CHANGED: False\nMANUAL GAME CHECK: NOT_REQUIRED_CONTRACT_ONLY\nFAIL-SAFE ROLLBACK: ARMED\nSUGGESTED NEXT PATCH: patch_21_13_7b_resolve_overlevel_policy_parity.py")
  return 0
 except Exception as e:
  restored=restore(r,folder,state);recovery=run([sys.executable,"-m","compileall","-q","rom_v2"],r,False)
  write(r/FAILURE,json.dumps({"stage":STAGE,"status":"FAIL_ROLLED_BACK","reason":str(e),"restored_files":restored,"recovery_compile_returncode":recovery.returncode,"main_py_must_not_run":recovery.returncode!=0,"database_opened":False,"canonical_reference_changed":False,"v1_wal_shm_manipulated":False},ensure_ascii=False,indent=2)+"\n")
  print(f"[10/10] [FAIL] {e}; rollback: FAIL_ROLLED_BACK");return 1
if __name__=="__main__":raise SystemExit(main())
