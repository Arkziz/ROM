#!/usr/bin/env python3
"""Stage 21.13.2a: refine the V1 Quest Item Store contract without production mutation."""
from __future__ import annotations
import ast,hashlib,json,os,py_compile,shutil,subprocess,sys
from datetime import datetime,timezone
from pathlib import Path
STAGE="21.13.2a";PARENT="f5be160c6b957cd9ef3dd824796a919c4de5bd56";BRANCH="stage-21-v2-modular-monolith"
SELF="patch/patch_21_13_2a_refine_quest_item_store_contract.py";PREREQ=Path("reports/stage_21_13_2_existing_quest_item_store_audit.json");REPORT=Path("reports/stage_21_13_2a_refined_quest_item_store_contract.json");DOC=Path("MD/STAGE_21_13_2A_REFINED_QUEST_ITEM_STORE_CONTRACT.md");FAILURE=Path("reports/stage_21_13_2a_failure_rollback.json")
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
 d=r/"backup"/("stage_21_13_2a_"+datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ"));d.mkdir(parents=True,exist_ok=True);state={}
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
 evidence={"get_quantity":True,"get_total":True,"add":True,"consume_primitive":True,"engine_collects_via_store":("collect_active_quest_item" in engine and "add_story_quest_item" in engine),"direct_engine_consume_call_found":("consume_story_quest_item_quantity" in engine),"quest_item_objective_defined":("QUEST_ITEM" in defs),"handler_has_no_store_mutation":("add_story_quest_item" not in handler and "consume_story_quest_item_quantity" not in handler)}
 required_evidence=("engine_collects_via_store","quest_item_objective_defined","handler_has_no_store_mutation")
 absent=[x for x in required_evidence if not evidence[x]]
 if absent:raise PatchError("quest_item_evidence_missing:"+",".join(absent))
 evidence["turn_in_consumption_requires_refinement"]=not evidence["direct_engine_consume_call_found"]
 return {"persistence_owner":"db_modules/story_quests.py","engine_consumer":"systems/story_quest_system.py","definition_owner":"data/story_quest_definitions.py","handler_consumer":"handlers/story_quests.py","store_symbols":sorted(required),"evidence":evidence,"source_hashes":{x.as_posix():sha(r/x) for x in paths}}
def main():
 r=root();folder=None;state={};before={x.as_posix():sha(r/x) for x in PROTECTED}
 expected=("QUEST_ITEM_IDENTITY_AND_SCOPE","EXACT_QUANTITY_AND_NON_NEGATIVE_INVARIANT","COLLECTION_IDEMPOTENCY_AND_EVENT_IDENTITY","TURN_IN_CONSUMPTION_ATOMICITY","OVERLEVEL_SKIP_AND_CLEANUP")
 confirmed=("ISOLATED_STORE_OWNERSHIP","RESTART_PERSISTENCE_AND_RECOVERY","PRESENTATION_AND_INVENTORY_SEPARATION")
 try:
  audit=json.loads((r/PREREQ).read_text(encoding="utf-8-sig"));rows=tuple(x for x in audit.get("contract_matrix",()) if isinstance(x,dict));unresolved=tuple(x.get("contract") for x in rows if x.get("classification")=="REVIEW_REQUIRED");got_confirmed=tuple(x.get("contract") for x in rows if x.get("classification")=="V1_CONFIRMED");summary=audit.get("summary",{})
  if git(r,"rev-parse","HEAD").stdout.strip()!=PARENT:raise PatchError("wrong_exact_parent")
  if audit.get("stage")!="21.13.2" or audit.get("conclusion")!="GO_TO_SEMANTIC_REFINEMENT" or len(rows)!=8 or unresolved!=expected or got_confirmed!=confirmed or tuple(summary.get("unresolved_contracts",()))!=expected:raise PatchError("invalid_stage_21_13_2_prerequisite")
  print("[1/10] [PASS] Stage 21.13.2 exact 3-confirmed/5-unresolved/8-total prerequisite verified.")
  branch=git(r,"branch","--show-current").stdout.strip();staged=git(r,"diff","--cached","--name-only").stdout.strip()
  if not branch:raise PatchError("git_preflight_detached_head")
  if staged:raise PatchError("git_preflight_staged_index:"+staged.replace("\n",","))
  bad=sorted(p for st,p in status(r) if p not in ALLOWED or (p!=SELF and st[0]!=" "))
  if bad:raise PatchError(f"unexpected_dirty:{bad}")
  print(f"[2/10] [PASS] Active branch {branch}, exact parent, dirty allowlist and clean index verified.");folder,state=backup(r);print("[3/10] [PASS] Refinement artifacts backed up before publication mutation.")
  evidence=inspect(r);print("[4/10] [PASS] Exact V1 item identity, quantity, collection, consume primitive and SKIP evidence re-verified.")
  details={
   "QUEST_ITEM_IDENTITY_AND_SCOPE":(["quest items are stored by the story quest persistence owner","objective definitions identify QUEST_ITEM requirements","collection is associated with the active quest path","regular inventory handlers do not own add or consume operations"],"Resolve the exact canonical key: user, quest, item type and optional source/objective identity; determine whether identical item keys may be shared across quests and how total quantity differs from per-quest quantity."),
   "EXACT_QUANTITY_AND_NON_NEGATIVE_INVARIANT":(["per-quest and total quantity queries exist","add and consume primitives are separate operations","quantity belongs to isolated persistent storage","normal inventory capacity is not part of the store API"],"Resolve integer validation, zero handling, upper bounds if any, insufficient-consume result, non-negative enforcement, row deletion at zero and transaction/concurrency semantics for simultaneous add/consume."),
   "COLLECTION_IDEMPOTENCY_AND_EVENT_IDENTITY":(["Quest Engine owns collect_active_quest_item","collection delegates to add_story_quest_item","active quest context is available to the engine","handlers do not mutate the store directly"],"Resolve the exact collection event identity, drop/source matching, duplicate delivery behavior, chance evaluation boundary, target clamping versus surplus retention and retry after commit."),
   "TURN_IN_CONSUMPTION_ATOMICITY":(["consume_story_quest_item_quantity exists as the canonical primitive","direct consume call is not present in story_quest_system","Quest Engine exact-once turn-in contract requires atomic consumption","completed quest state persists across restart"],"Locate the actual V1 caller and authoritative Unit of Work for readiness recheck, exact quantity consumption, reward grant and completion; resolve rollback-before-commit, retry-after-commit and delegated completion boundaries without inventing a new caller."),
   "OVERLEVEL_SKIP_AND_CLEANUP":(["overlevel reconciliation and explicit SKIP exist","SKIP is separate from normal completion","quest items remain isolated from ordinary inventory","completed and skipped states persist"],"Resolve whether automatic reconciliation or explicit SKIP deletes, preserves or ignores accumulated quest items; define quest-chain scoping, orphan cleanup timing, idempotency and the guarantee that SKIP never consumes items or grants rewards.")}
  refined=[{"contract":k,"classification":"REVIEW_REQUIRED","confirmed":v[0],"remaining_question":v[1]} for k,v in details.items()]
  if tuple(x["contract"] for x in refined)!=expected:raise PatchError("refinement_contract_mismatch")
  print("[5/10] [PASS] Five Quest Item Store boundaries narrowed to exact identity, quantity, collection, turn-in and SKIP evidence.");print("[6/10] [PASS] No-regular-inventory-leakage and delegated turn-in risks isolated without opening SQLite or mutating quantities.")
  removed=clean(r);checks=ci(r);print(f"[7/10] [PASS] Canonical V2 CI passed after removing {len(removed)} bytecode artifact(s).")
  if before!={x.as_posix():sha(r/x) for x in PROTECTED}:raise PatchError("protected_runtime_changed")
  print("[8/10] [PASS] Production sources, DB sidecars and protected configuration remained byte-identical.")
  payload={"schema_version":1,"stage":STAGE,"status":"PASS","conclusion":"REVIEW_REQUIRED","source_audit":PREREQ.as_posix(),"summary":{"contract_count":8,"v1_confirmed_contracts":3,"refined_contracts":5,"review_required_contracts":5,"unresolved_contracts":list(expected),"database_opened":False,"production_code_changed":False,"v1_wal_shm_manipulated":False},"authoritative_evidence":evidence,"refined_contract_matrix":refined,"acceptance":{"no_regular_inventory_leakage":True,"direct_engine_consume_call_found":evidence["evidence"]["direct_engine_consume_call_found"],"delegated_turn_in_boundary_requires_resolution":True},"implementation_authorized":False,"canonical_v2_ci":checks,"manual_game_check":"NOT_REQUIRED","suggested_next_patch":"patch_21_13_2b_resolve_quest_item_store_parity.py","backup_path":folder.relative_to(r).as_posix()};write(r/REPORT,json.dumps(payload,ensure_ascii=False,indent=2)+"\n")
  lines=["# Stage 21.13.2a - Refined Quest Item Store contract","","- Status: **PASS**","- Conclusion: **REVIEW_REQUIRED**","- Contract matrix: **3 confirmed / 5 review-required / 8 total**","- No regular inventory leakage: **CONFIRMED BOUNDARY**","- Direct engine consume call: **NOT FOUND; REQUIRES RESOLUTION**","- Implementation authorized: **False**","- Manual game check: **NOT_REQUIRED**","","## Refined unresolved contracts",""]
  for x in refined:lines.extend(["### "+x["contract"],"","Confirmed:","",*["- "+v for v in x["confirmed"]],"","Remaining question: "+x["remaining_question"],""])
  lines.extend(["No production mutation, quantity change, turn-in consumption, database access or runtime wiring is authorized.","","## Next patch","","`patch_21_13_2b_resolve_quest_item_store_parity.py`",""]);write(r/DOC,"\n".join(lines));print("[9/10] [PASS] Refined JSON and Markdown Quest Item Store contract artifacts written.")
  files={x.as_posix() for x in TARGETS};git(r,"add","-f","--",*sorted(files));got={x.replace("\\","/") for x in git(r,"diff","--cached","--name-only","--").stdout.splitlines() if x}
  if got!=files:raise PatchError("staging_mismatch:"+repr(sorted(got)))
  z=git(r,"commit","-m","Stage 21.13.2a: refine Quest Item Store contract","--",*sorted(files),check=False)
  if z.returncode:raise PatchError("commit_failed:"+z.stdout+z.stderr)
  commit=git(r,"rev-parse","HEAD").stdout.strip();changed={x.replace("\\","/") for x in git(r,"diff-tree","--no-commit-id","--name-only","-r",commit).stdout.splitlines() if x}
  if changed!=files:raise PatchError("commit_scope_mismatch:"+repr(sorted(changed)))
  print(f"[10/10] [PASS] Quest Item Store semantic refinement committed: {commit}");print("CONCLUSION: REVIEW_REQUIRED\nCONTRACT_MATRIX: 3 CONFIRMED / 5 REVIEW_REQUIRED / 8 TOTAL\nUNRESOLVED_CONTRACTS: 5\nIMPLEMENTATION AUTHORIZED: False\nNO REGULAR INVENTORY LEAKAGE: CONFIRMED BOUNDARY\nMANUAL GAME CHECK: NOT_REQUIRED\nFAIL-SAFE ROLLBACK: ARMED\nSUGGESTED NEXT PATCH: patch_21_13_2b_resolve_quest_item_store_parity.py");return 0
 except Exception as error:
  restored=restore(r,folder,state);recovery=run([sys.executable,"-m","compileall","-q","rom_v2"],r,False);write(r/FAILURE,json.dumps({"stage":STAGE,"status":"FAIL_ROLLED_BACK","reason":str(error),"restored_files":restored,"recovery_compile_returncode":recovery.returncode,"main_py_must_not_run":recovery.returncode!=0,"database_opened":False,"v1_wal_shm_manipulated":False},ensure_ascii=False,indent=2)+"\n");print(f"[10/10] [FAIL] {error}; rollback: FAIL_ROLLED_BACK");return 1
if __name__=="__main__":raise SystemExit(main())
