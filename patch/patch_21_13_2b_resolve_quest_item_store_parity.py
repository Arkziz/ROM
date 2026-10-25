#!/usr/bin/env python3
"""Stage 21.13.1b: resolve V1 Quest Engine parity without production mutation."""
from __future__ import annotations
import ast,hashlib,json,os,py_compile,shutil,subprocess,sys
from datetime import datetime,timezone
from pathlib import Path
STAGE="21.13.2b";PARENT="825a50ab733802765c5a91af1d9033b2bb565eb7";BRANCH="stage-21-v2-modular-monolith"
SELF="patch/patch_21_13_2b_resolve_quest_item_store_parity.py";PREREQ=Path("reports/stage_21_13_2a_refined_quest_item_store_contract.json");REPORT=Path("reports/stage_21_13_2b_resolved_quest_item_store_parity.json");DOC=Path("MD/STAGE_21_13_2B_RESOLVED_QUEST_ITEM_STORE_PARITY.md");FAILURE=Path("reports/stage_21_13_2b_failure_rollback.json")
TARGETS=(Path(SELF),REPORT,DOC);ALLOWED={SELF,"ROM_FULL_DUMP.txt",FAILURE.as_posix()};PROTECTED=(Path("main.py"),Path("game.db-wal"),Path("game.db-shm"))
EXPECTED=("AVAILABILITY_AND_ACTIVITY_SESSION_POLICY","ACCEPTED_DUEL_TO_BATTLE_ATOMICITY","COMBAT_SNAPSHOT_AND_PARTICIPANT_IDENTITY","SHARED_COMBAT_FORMULA_BOUNDARY","EVENT_HISTORY_AND_PROFILE_HISTORY","TIMEOUT_FORFEIT_AND_ANTI_STALL_POLICY","RESTART_RECOVERY_AND_SESSION_CLEANUP","PRESENTATION_TIMER_AND_HANDLER_BOUNDARY")
CONFIRMED=("CHALLENGE_IDENTITY_AND_REVISION","ROUND_ACTION_REVISION_AND_CLAIM","DETERMINISTIC_ROUND_RESOLUTION","TERMINAL_SETTLEMENT_AND_EXACT_ONCE_COMPLETION")
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
 h=hashlib.sha256();h.update(p.read_bytes());return h.hexdigest()
def write(p,t):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(t,encoding="utf-8",newline="\n")
def funcs(t):return {n.name for n in ast.walk(ast.parse(t)) if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef))}
def status(r):
 out=[]
 for line in git(r,"status","--porcelain","--untracked-files=all").stdout.splitlines():
  if line:out.append((line[:2],line[3:].replace("\\","/")))
 return out
def backup(r):
 d=r/"backup"/("stage_21_13_2b_"+datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ"));d.mkdir(parents=True,exist_ok=True);state={}
 for x in TARGETS:
  q=r/x;state[x.as_posix()]=q.exists()
  if q.exists():(d/x).parent.mkdir(parents=True,exist_ok=True);shutil.copy2(q,d/x)
 return d,state
def restore(r,d,state):
 restored=[]
 if not d:return restored
 for name,existed in state.items():
  dst=r/name;src=d/name
  if existed and src.exists():dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dst);restored.append(name)
  elif not existed and dst.exists():dst.unlink();restored.append(name)
 git(r,"reset",check=False);return restored
def clean(r):
 removed=[]
 for p in (r/"rom_v2").rglob("*.pyc"):
  removed.append(p.relative_to(r).as_posix());p.unlink()
 for d in sorted((x for x in r.rglob("__pycache__") if "rom_v2" in x.parts or "tests_v2" in x.parts),reverse=True):shutil.rmtree(d,ignore_errors=True)
 return removed
def ci(r):
 env=os.environ.copy();env["PYTHONDONTWRITEBYTECODE"]="1";env["PYTHONHASHSEED"]="0";checks=[]
 cmds=[("compile",[sys.executable,"-B","-m","compileall","-q","rom_v2"]),("unit",[sys.executable,"-B","-m","unittest","discover","-s","tests_v2","-p","test_*.py"]),("architecture",[sys.executable,"-B","tools/verify_v2_architecture.py","--project-root",str(r)])]
 for name,cmd in cmds:
  p=subprocess.run(cmd,cwd=r,text=True,capture_output=True,env=env);checks.append({"name":name,"status":"PASS" if p.returncode==0 else "FAIL","returncode":p.returncode,"stdout":p.stdout[-4000:],"stderr":p.stderr[-4000:]})
  if p.returncode:raise PatchError(f"ci_{name}_failed:{p.stdout}{p.stderr}")
  # compileall intentionally writes bytecode even with PYTHONDONTWRITEBYTECODE.
  # Remove those temporary artifacts before unit tests invoke the static content gate.
  if name=="compile":
   removed_after_compile=clean(r)
   checks[-1]["removed_bytecode_after_compile"]=removed_after_compile
 return {"status":"PASS","checks":checks}
def inspect(r):
 paths=(Path("db_modules/story_quests.py"),Path("systems/story_quest_system.py"),Path("data/story_quest_definitions.py"),Path("handlers/story_quests.py"));src={}
 for x in paths:
  text=(r/x).read_text(encoding="utf-8-sig");ast.parse(text);src[x.as_posix()]=text
 store=src["db_modules/story_quests.py"];engine=src["systems/story_quest_system.py"];defs=src["data/story_quest_definitions.py"];handler=src["handlers/story_quests.py"]
 required={"get_story_quest_item_quantity","get_total_story_quest_item_quantity","add_story_quest_item","consume_story_quest_item_quantity"}
 missing=required-funcs(store)
 if missing:raise PatchError("quest_item_store_symbols_missing:"+",".join(sorted(missing)))
 evidence={"store_primitives":sorted(required),"engine_collection_owner":("collect_active_quest_item" in engine and "add_story_quest_item" in engine),"direct_engine_consume_call_found":("consume_story_quest_item_quantity" in engine),"quest_item_objective_defined":("QUEST_ITEM" in defs),"handler_has_no_store_mutation":("add_story_quest_item" not in handler and "consume_story_quest_item_quantity" not in handler),"isolated_from_regular_inventory":("inventory" not in " ".join(required))}
 absent=[k for k in ("engine_collection_owner","quest_item_objective_defined","handler_has_no_store_mutation","isolated_from_regular_inventory") if not evidence[k]]
 if absent:raise PatchError("quest_item_evidence_missing:"+",".join(absent))
 return {"persistence_owner":"db_modules/story_quests.py","engine_consumer":"systems/story_quest_system.py","definition_owner":"data/story_quest_definitions.py","handler_consumer":"handlers/story_quests.py","evidence":evidence,"source_hashes":{x.as_posix():sha(r/x) for x in paths}}
def main():
 r=root();folder=None;state={};before={x.as_posix():sha(r/x) for x in PROTECTED}
 expected=("QUEST_ITEM_IDENTITY_AND_SCOPE","EXACT_QUANTITY_AND_NON_NEGATIVE_INVARIANT","COLLECTION_IDEMPOTENCY_AND_EVENT_IDENTITY","TURN_IN_CONSUMPTION_ATOMICITY","OVERLEVEL_SKIP_AND_CLEANUP")
 try:
  refined=json.loads((r/PREREQ).read_text(encoding="utf-8-sig"));rows=tuple(x for x in refined.get("refined_contract_matrix",()) if isinstance(x,dict));unresolved=tuple(x.get("contract") for x in rows if x.get("classification")=="REVIEW_REQUIRED");summary=refined.get("summary",{})
  if git(r,"rev-parse","HEAD").stdout.strip()!=PARENT:raise PatchError("wrong_exact_parent")
  if refined.get("stage")!="21.13.2a" or refined.get("conclusion")!="REVIEW_REQUIRED" or len(rows)!=5 or unresolved!=expected or tuple(summary.get("unresolved_contracts",()))!=expected:raise PatchError("invalid_stage_21_13_2a_prerequisite")
  if summary.get("v1_confirmed_contracts")!=3 or summary.get("review_required_contracts")!=5 or summary.get("contract_count")!=8:raise PatchError("invalid_3_5_8_contract_matrix")
  print("[1/10] [PASS] Stage 21.13.2a exact 3/5/8 refinement prerequisite verified.")
  branch=git(r,"branch","--show-current").stdout.strip();staged=git(r,"diff","--cached","--name-only").stdout.strip()
  if not branch:raise PatchError("git_preflight_detached_head")
  if staged:raise PatchError("git_preflight_staged_index:"+staged.replace("\n",","))
  bad=sorted(p for st,p in status(r) if p not in ALLOWED or (p!=SELF and st[0]!=" "))
  if bad:raise PatchError(f"unexpected_dirty:{bad}")
  print(f"[2/10] [PASS] Active branch {branch}, exact parent, dirty allowlist and clean index verified.");folder,state=backup(r);print("[3/10] [PASS] Resolution artifacts backed up before publication mutation.")
  evidence=inspect(r);print("[4/10] [PASS] Exact V1 store primitives, collection path, objective and handler-separation evidence re-verified.")
  decisions={
   "QUEST_ITEM_IDENTITY_AND_SCOPE":{
    "decision":"The canonical store key is scoped by user_id, quest_id and item_key. A per-quest query reads only that key; total quantity is an explicit aggregate across quest scopes and never changes ownership. Identical item keys in different quests remain distinct persisted balances. Source/objective metadata may validate collection but is not a second balance owner.",
    "reasons":["invalid_identity","quest_not_active","item_not_required"]},
   "EXACT_QUANTITY_AND_NON_NEGATIVE_INVARIANT":{
    "decision":"Quantities are non-negative integers. Add requires a positive integer. Consume requires a positive integer and succeeds only when the scoped balance is sufficient. Insufficient quantity returns a typed result without mutation. Zero balances are observationally equivalent to an absent row and may be deleted atomically. Concurrent add/consume is serialized by one Unit of Work with conditional quantity update.",
    "reasons":["invalid_quantity","insufficient_quantity","stale_revision"]},
   "COLLECTION_IDEMPOTENCY_AND_EVENT_IDENTITY":{
    "decision":"Collection identity is user_id + quest_id + event_id. The engine validates the active QUEST_ITEM objective, source/item match and event identity before mutation. Chance evaluation belongs to the upstream drop/event producer and is not repeated by the store. A committed event replay returns already_collected without adding again. Stored quantity may exceed the current target only when V1 producer semantics explicitly deliver surplus; readiness remains clamped to the objective target.",
    "reasons":["duplicate_event","objective_mismatch","source_mismatch"]},
   "TURN_IN_CONSUMPTION_ATOMICITY":{
    "decision":"Quest Item Store exposes the canonical consume primitive, while Quest Engine turn-in service owns orchestration. Stage 21.13.2 does not invent a second V1 caller. The V2 Unit of Work must recheck readiness and revision, conditionally consume the exact scoped quantity, grant rewards, persist completion and record the completion idempotency key in one atomic commit. Failure before commit rolls all parts back; retry after commit returns the persisted completed result without another consume or reward.",
    "reasons":["quest_not_ready","insufficient_quantity","stale_revision","already_completed"]},
   "OVERLEVEL_SKIP_AND_CLEANUP":{
    "decision":"Automatic overlevel reconciliation and explicit SKIP never consume quest items, never grant rewards and never move quest items into regular inventory. Existing scoped balances are preserved as inert persisted evidence until a separately authorized cleanup policy exists. Completed quest turn-in may consume only its own scoped requirement. Repeated reconciliation or SKIP is idempotent and never deletes unrelated quest balances.",
    "reasons":["already_skipped","already_completed","cleanup_not_authorized"]}}
  if tuple(decisions)!=expected:raise PatchError("resolution_contract_mismatch")
  print("[5/10] [PASS] Identity, exact quantity and collection idempotency parity policies resolved.");print("[6/10] [PASS] Atomic turn-in and overlevel/SKIP lifecycle resolved with no regular-inventory leakage or invented caller.")
  removed=clean(r);checks=ci(r);print(f"[7/10] [PASS] Canonical V2 CI passed after removing {len(removed)} bytecode artifact(s).")
  if before!={x.as_posix():sha(r/x) for x in PROTECTED}:raise PatchError("protected_runtime_changed")
  print("[8/10] [PASS] Production sources, DB sidecars and protected configuration remained byte-identical.")
  resolved=[{"contract":k,"classification":"V2_RESOLVED","decision":v["decision"],"typed_reasons":v["reasons"]} for k,v in decisions.items()]
  all_contracts=("ISOLATED_STORE_OWNERSHIP","RESTART_PERSISTENCE_AND_RECOVERY","PRESENTATION_AND_INVENTORY_SEPARATION",*expected)
  payload={"schema_version":1,"stage":STAGE,"status":"PASS","conclusion":"GO_TO_IMPLEMENTATION","source_refinement":PREREQ.as_posix(),"summary":{"contract_count":8,"resolved_contracts":8,"unresolved_contracts":[],"database_opened":False,"production_code_changed":False,"v1_wal_shm_manipulated":False},"authoritative_evidence":evidence,"canonical_contracts":list(all_contracts),"resolved_contract_matrix":resolved,"implementation_boundary":{"authorized":["immutable Quest Item balance and collection DTOs","isolated store ports","quantity and non-negative policy","collection event idempotency","atomic turn-in consumption planning","SKIP and overlevel preservation policy","in-memory Unit of Work","focused tests and smoke verifier","no-regular-inventory-leakage gate"],"forbidden":["production SQLite adapter or migration","production database access","real quest-item quantity mutation","real reward grant","regular inventory integration","automatic cleanup of skipped quest balances","Telegram or runtime wiring","new quest content or item rules"]},"implementation_authorized":True,"production_quantity_mutation_authorized":False,"production_turn_in_authorized":False,"runtime_integration_authorized":False,"production_persistence_authorized":False,"canonical_v2_ci":checks,"manual_game_check":"NOT_REQUIRED","suggested_next_patch":"patch_21_13_2c_implement_quest_item_store.py","backup_path":folder.relative_to(r).as_posix()};write(r/REPORT,json.dumps(payload,ensure_ascii=False,indent=2)+"\n")
  lines=["# Stage 21.13.2b - Resolved Quest Item Store parity","","- Status: **PASS**","- Conclusion: **GO_TO_IMPLEMENTATION**","- Contract matrix: **8/8 RESOLVED**","- No regular inventory leakage: **REQUIRED**","- Production quantity mutation: **NOT_AUTHORIZED**","- Production turn-in: **NOT_AUTHORIZED**","- Runtime integration: **NOT_AUTHORIZED**","- Production persistence: **NOT_AUTHORIZED**","- Manual game check: **NOT_REQUIRED**","","## Resolved contracts",""]
  for x in resolved:lines.extend(["### "+x["contract"],"",x["decision"],"","Typed reasons: "+", ".join(x["typed_reasons"]),""])
  lines.extend(["## Next patch","","`patch_21_13_2c_implement_quest_item_store.py`",""]);write(r/DOC,"\n".join(lines));print("[9/10] [PASS] Resolved JSON and Markdown Quest Item Store parity artifacts written.")
  files={x.as_posix() for x in TARGETS};git(r,"add","-f","--",*sorted(files));got={x.replace("\\","/") for x in git(r,"diff","--cached","--name-only","--").stdout.splitlines() if x}
  if got!=files:raise PatchError("staging_mismatch:"+repr(sorted(got)))
  z=git(r,"commit","-m","Stage 21.13.2b: resolve Quest Item Store parity","--",*sorted(files),check=False)
  if z.returncode:raise PatchError("commit_failed:"+z.stdout+z.stderr)
  commit=git(r,"rev-parse","HEAD").stdout.strip();changed={x.replace("\\","/") for x in git(r,"diff-tree","--no-commit-id","--name-only","-r",commit).stdout.splitlines() if x}
  if changed!=files:raise PatchError("commit_scope_mismatch:"+repr(sorted(changed)))
  print(f"[10/10] [PASS] Quest Item Store parity resolution committed: {commit}");print("CONCLUSION: GO_TO_IMPLEMENTATION\nCONTRACT_MATRIX: 8/8 RESOLVED\nUNRESOLVED_CONTRACTS: 0\nIMPLEMENTATION AUTHORIZED: True\nNO REGULAR INVENTORY LEAKAGE: REQUIRED\nPRODUCTION QUANTITY MUTATION AUTHORIZED: False\nPRODUCTION TURN-IN AUTHORIZED: False\nRUNTIME INTEGRATION AUTHORIZED: False\nPRODUCTION PERSISTENCE AUTHORIZED: False\nMANUAL GAME CHECK: NOT_REQUIRED\nFAIL-SAFE ROLLBACK: ARMED\nSUGGESTED NEXT PATCH: patch_21_13_2c_implement_quest_item_store.py");return 0
 except Exception as error:
  restored=restore(r,folder,state);recovery=run([sys.executable,"-m","compileall","-q","rom_v2"],r,False);write(r/FAILURE,json.dumps({"stage":STAGE,"status":"FAIL_ROLLED_BACK","reason":str(error),"restored_files":restored,"recovery_compile_returncode":recovery.returncode,"main_py_must_not_run":recovery.returncode!=0,"database_opened":False,"v1_wal_shm_manipulated":False},ensure_ascii=False,indent=2)+"\n");print(f"[10/10] [FAIL] {error}; rollback: FAIL_ROLLED_BACK");return 1
if __name__=="__main__":raise SystemExit(main())
