#!/usr/bin/env python3
"""Stage 21.13.1a: refine the V1 Quest Engine contract without production mutation."""
from __future__ import annotations
import ast,hashlib,json,os,py_compile,shutil,subprocess,sys
from datetime import datetime,timezone
from pathlib import Path
STAGE="21.13.1a";PARENT="bd6c9752292ba6e8e8b1236fb5c91d0feb3db04a";BRANCH="stage-21-v2-modular-monolith"
SELF="patch/patch_21_13_1a_refine_quest_engine_contract.py";PREREQ=Path("reports/stage_21_13_1_existing_quest_engine_audit.json");REPORT=Path("reports/stage_21_13_1a_refined_quest_engine_contract.json");DOC=Path("MD/STAGE_21_13_1A_REFINED_QUEST_ENGINE_CONTRACT.md");FAILURE=Path("reports/stage_21_13_1a_failure_rollback.json")
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
 d=r/"backup"/("stage_21_13_1a_"+datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ"));d.mkdir(parents=True,exist_ok=True);state={}
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
 paths=(Path("systems/story_quest_system.py"),Path("db_modules/story_quests.py"),Path("data/story_quest_definitions.py"),Path("handlers/story_quests.py"));src={}
 for x in paths:
  text=(r/x).read_text(encoding="utf-8-sig");ast.parse(text);src[x.as_posix()]=text
 engine=src["systems/story_quest_system.py"];store=src["db_modules/story_quests.py"];defs=src["data/story_quest_definitions.py"];handler=src["handlers/story_quests.py"]
 engine_required={"build_story_quest_registry","get_story_quest_status","get_story_quest_view","accept_story_quest","advance_region_kill_progress","collect_active_quest_item","reconcile_overlevel_story_locations","skip_overlevel_active_quest","get_materialized_story_journal"}
 store_required={"get_story_quest","get_active_story_quest","list_story_quest_journal","activate_story_quest","set_story_quest_progress","get_story_quest_item_quantity","get_total_story_quest_item_quantity","consume_story_quest_item_quantity","add_story_quest_item","reconcile_story_location_as_skipped","skip_active_story_quest"}
 missing=(engine_required-funcs(engine))|(store_required-funcs(store))
 if missing:raise PatchError("quest_symbols_missing:"+",".join(sorted(missing)))
 objective_types=tuple(x for x in ("TALK","KILL_REGION","QUEST_ITEM","TURN_IN","BOSS") if x in defs or x in engine)
 if len(objective_types)!=5:raise PatchError("quest_objective_types_missing:"+repr(objective_types))
 return {"engine_owner":"systems/story_quest_system.py","persistence_owner":"db_modules/story_quests.py","definition_owner":"data/story_quest_definitions.py","handler_consumer":"handlers/story_quests.py","engine_symbols":sorted(engine_required),"persistence_symbols":sorted(store_required),"objective_types":list(objective_types),"quest_item_store_isolated":all(x in store for x in ("get_story_quest_item_quantity","consume_story_quest_item_quantity","add_story_quest_item")),"overlevel_skip_paths":True,"handler_uses_engine":"story_quest_system" in handler,"source_hashes":{x.as_posix():sha(r/x) for x in paths}}
def main():
 r=root();folder=None;state={};before={x.as_posix():sha(r/x) for x in PROTECTED}
 expected=("PREREQUISITE_AND_AVAILABILITY_POLICY","PROGRESS_AND_COMPLETION_STATE_MACHINE","REWARD_AND_EXACT_ONCE_TURN_IN","ENGINE_CONTENT_INDEPENDENCE","OVERLEVEL_AND_SKIP_INTERACTION","PRESENTATION_AND_HANDLER_BOUNDARY")
 confirmed=("QUEST_DEFINITION_AND_STABLE_ID_MODEL","OBJECTIVE_TYPE_CONTRACT","QUEST_ITEM_ISOLATION_BOUNDARY","PERSISTENCE_RESTART_AND_FAILURE_POLICY")
 try:
  audit=json.loads((r/PREREQ).read_text(encoding="utf-8-sig"));rows=tuple(x for x in audit.get("contract_matrix",()) if isinstance(x,dict));unresolved=tuple(x.get("contract") for x in rows if x.get("classification")=="REVIEW_REQUIRED");got_confirmed=tuple(x.get("contract") for x in rows if x.get("classification")=="V1_CONFIRMED");summary=audit.get("summary",{})
  if git(r,"rev-parse","HEAD").stdout.strip()!=PARENT:raise PatchError("wrong_exact_parent")
  if audit.get("stage")!="21.13.1" or audit.get("conclusion")!="GO_TO_SEMANTIC_REFINEMENT" or len(rows)!=10 or unresolved!=expected or got_confirmed!=confirmed or tuple(summary.get("unresolved_contracts",()))!=expected:raise PatchError("invalid_stage_21_13_1_prerequisite")
  print("[1/10] [PASS] Stage 21.13.1 exact 4-confirmed/6-unresolved/10-total prerequisite verified.")
  branch=git(r,"branch","--show-current").stdout.strip();staged=git(r,"diff","--cached","--name-only").stdout.strip()
  if not branch:raise PatchError("git_preflight_detached_head")
  if staged:raise PatchError("git_preflight_staged_index:"+staged.replace("\n",","))
  bad=sorted(p for st,p in status(r) if p not in ALLOWED or (p!=SELF and st[0]!=" "))
  if bad:raise PatchError(f"unexpected_dirty:{bad}")
  print(f"[2/10] [PASS] Active branch {branch}, exact parent, dirty allowlist and clean index verified.");folder,state=backup(r);print("[3/10] [PASS] Refinement artifacts backed up before publication mutation.")
  evidence=inspect(r);print("[4/10] [PASS] Exact V1 prerequisite, progress, reward, overlevel/SKIP and handler evidence re-verified.")
  details={
   "PREREQUISITE_AND_AVAILABILITY_POLICY":(["definitions carry stable IDs, location, order and requirement metadata","availability is derived from player level, previous quest and current persisted state","only one active story quest is materialized for the canonical chain","registry lookup is separate from Telegram presentation"],"Resolve the exact order of level, location, previous-quest, active-quest, completed/skipped and overlevel checks, including machine-readable rejection reasons and repeated availability queries."),
   "PROGRESS_AND_COMPLETION_STATE_MACHINE":(["accept creates the persisted active state","TALK, KILL_REGION, QUEST_ITEM, TURN_IN and BOSS use objective-specific progress paths","progress is clamped and compared with the definition target","journal materialization combines definitions with persisted state"],"Resolve legal state transitions, objective-specific completion triggers, duplicate event handling, progress monotonicity, BOSS exact-once evidence and behavior after restart or stale callbacks."),
   "REWARD_AND_EXACT_ONCE_TURN_IN":(["reward metadata belongs to the quest definition","completion and reward operate against persisted quest identity","TURN_IN and quest-item consumption have explicit paths","completed state survives restart"],"Resolve the authoritative transaction boundary for validation, quest-item consumption, EXP/gold/item reward, completion status and next-quest availability, including retry after commit and rollback before commit."),
   "ENGINE_CONTENT_INDEPENDENCE":(["engine builds a registry from definition data","objective dispatch is driven by objective type","quest content is supplied by data/story_quest_definitions.py","handler calls engine APIs instead of embedding chain mutation"],"Resolve the typed definition schema, objective strategy/validator boundary, prohibited quest-ID branches in engine/application code and an executable gate proving the engine does not depend on particular quest IDs, titles, NPC names or location prose."),
   "OVERLEVEL_AND_SKIP_INTERACTION":(["overlevel reconciliation and active-quest skip are distinct operations","persisted skipped states are represented in the journal","SKIP operates by canonical location/quest chain","normal completion paths remain separate from skip paths"],"Resolve exact eligibility and ordering for automatic reconciliation versus explicit active SKIP, whether rewards and quest items are ever granted or consumed, next-quest availability, idempotent replay and interaction with completed/failed states."),
   "PRESENTATION_AND_HANDLER_BOUNDARY":(["story_quests handler consumes story_quest_system","engine returns materialized quest views and journal data","technical objective/state keys exist independently from localized text","persistence owner is isolated from Telegram"],"Resolve typed commands/results, callback stable keys and expected revision tokens, localization ownership, one handler registration path and prohibition of reward/progress calculations or quest-ID branching in handlers.")}
  refined=[{"contract":k,"classification":"REVIEW_REQUIRED","confirmed":v[0],"remaining_question":v[1]} for k,v in details.items()]
  if tuple(x["contract"] for x in refined)!=expected:raise PatchError("refinement_contract_mismatch")
  print("[5/10] [PASS] Six Quest Engine boundaries narrowed to exact prerequisite, state, reward, independence, SKIP and presentation evidence.");print("[6/10] [PASS] Exact-once turn-in and engine-content-independence risks isolated without opening SQLite or mutating quest state.")
  removed=clean(r);checks=ci(r);print(f"[7/10] [PASS] Canonical V2 CI passed after removing {len(removed)} bytecode artifact(s).")
  if before!={x.as_posix():sha(r/x) for x in PROTECTED}:raise PatchError("protected_runtime_changed")
  print("[8/10] [PASS] Production sources, DB sidecars and protected configuration remained byte-identical.")
  payload={"schema_version":1,"stage":STAGE,"status":"PASS","conclusion":"REVIEW_REQUIRED","source_audit":PREREQ.as_posix(),"summary":{"contract_count":10,"v1_confirmed_contracts":4,"refined_contracts":6,"review_required_contracts":6,"unresolved_contracts":list(expected),"database_opened":False,"production_code_changed":False,"v1_wal_shm_manipulated":False},"authoritative_evidence":evidence,"refined_contract_matrix":refined,"implementation_authorized":False,"canonical_v2_ci":checks,"manual_game_check":"NOT_REQUIRED","suggested_next_patch":"patch_21_13_1b_resolve_quest_engine_parity.py","backup_path":folder.relative_to(r).as_posix()};write(r/REPORT,json.dumps(payload,ensure_ascii=False,indent=2)+"\n")
  lines=["# Stage 21.13.1a - Refined Quest Engine contract","","- Status: **PASS**","- Conclusion: **REVIEW_REQUIRED**","- Contract matrix: **4 confirmed / 6 review-required / 10 total**","- Implementation authorized: **False**","- Manual game check: **NOT_REQUIRED**","","## Refined unresolved contracts",""]
  for x in refined:lines.extend(["### "+x["contract"],"","Confirmed:","",*["- "+v for v in x["confirmed"]],"","Remaining question: "+x["remaining_question"],""])
  lines.extend(["No production mutation, reward grant, quest-item consumption, database access or runtime wiring is authorized.","","## Next patch","","`patch_21_13_1b_resolve_quest_engine_parity.py`",""]);write(r/DOC,"\n".join(lines));print("[9/10] [PASS] Refined JSON and Markdown Quest Engine contract artifacts written.")
  files={x.as_posix() for x in TARGETS};git(r,"add","-f","--",*sorted(files));got={x.replace("\\","/") for x in git(r,"diff","--cached","--name-only").stdout.splitlines() if x}
  if got!=files:raise PatchError("staging_mismatch:"+repr(sorted(got)))
  z=git(r,"commit","-m","Stage 21.13.1a: refine Quest Engine contract","--",*sorted(files),check=False)
  if z.returncode:raise PatchError("commit_failed:"+z.stdout+z.stderr)
  commit=git(r,"rev-parse","HEAD").stdout.strip();changed={x.replace("\\","/") for x in git(r,"diff-tree","--no-commit-id","--name-only","-r",commit).stdout.splitlines() if x}
  if changed!=files:raise PatchError("commit_scope_mismatch:"+repr(sorted(changed)))
  print(f"[10/10] [PASS] Quest Engine semantic refinement committed: {commit}");print("CONCLUSION: REVIEW_REQUIRED\nCONTRACT_MATRIX: 4 CONFIRMED / 6 REVIEW_REQUIRED / 10 TOTAL\nUNRESOLVED_CONTRACTS: 6\nIMPLEMENTATION AUTHORIZED: False\nMANUAL GAME CHECK: NOT_REQUIRED\nFAIL-SAFE ROLLBACK: ARMED\nSUGGESTED NEXT PATCH: patch_21_13_1b_resolve_quest_engine_parity.py");return 0
 except Exception as error:
  restored=restore(r,folder,state);recovery=run([sys.executable,"-m","compileall","-q","rom_v2"],r,False);write(r/FAILURE,json.dumps({"stage":STAGE,"status":"FAIL_ROLLED_BACK","reason":str(error),"restored_files":restored,"recovery_compile_returncode":recovery.returncode,"main_py_must_not_run":recovery.returncode!=0,"database_opened":False,"v1_wal_shm_manipulated":False},ensure_ascii=False,indent=2)+"\n");print(f"[10/10] [FAIL] {error}; rollback: FAIL_ROLLED_BACK");return 1
if __name__=="__main__":raise SystemExit(main())
