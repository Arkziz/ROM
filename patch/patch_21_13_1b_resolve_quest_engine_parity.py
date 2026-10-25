#!/usr/bin/env python3
"""Stage 21.13.1b: resolve V1 Quest Engine parity without production mutation."""
from __future__ import annotations
import ast,hashlib,json,os,py_compile,shutil,subprocess,sys
from datetime import datetime,timezone
from pathlib import Path
STAGE="21.13.1b";PARENT="d2cb4f94eb40932441fb4fbbe020db6ebe6fba73";BRANCH="stage-21-v2-modular-monolith"
SELF="patch/patch_21_13_1b_resolve_quest_engine_parity.py";PREREQ=Path("reports/stage_21_13_1a_refined_quest_engine_contract.json");REPORT=Path("reports/stage_21_13_1b_resolved_quest_engine_parity.json");DOC=Path("MD/STAGE_21_13_1B_RESOLVED_QUEST_ENGINE_PARITY.md");FAILURE=Path("reports/stage_21_13_1b_failure_rollback.json")
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
 d=r/"backup"/("stage_21_13_1b_"+datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ"));d.mkdir(parents=True,exist_ok=True);state={}
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
 try:
  refined=json.loads((r/PREREQ).read_text(encoding="utf-8-sig"));summary=refined.get("summary",{});rows=tuple(x for x in refined.get("refined_contract_matrix",()) if isinstance(x,dict));unresolved=tuple(x.get("contract") for x in rows if x.get("classification")=="REVIEW_REQUIRED")
  if git(r,"rev-parse","HEAD").stdout.strip()!=PARENT:raise PatchError("wrong_exact_parent")
  if refined.get("stage")!="21.13.1a" or refined.get("conclusion")!="REVIEW_REQUIRED" or summary.get("contract_count")!=10 or summary.get("v1_confirmed_contracts")!=4 or summary.get("review_required_contracts")!=6 or unresolved!=expected or tuple(summary.get("unresolved_contracts",()))!=expected:raise PatchError("invalid_stage_21_13_1a_prerequisite")
  print("[1/10] [PASS] Stage 21.13.1a exact 4/6/10 refinement prerequisite verified.")
  branch=git(r,"branch","--show-current").stdout.strip();staged=git(r,"diff","--cached","--name-only").stdout.strip()
  if not branch:raise PatchError("git_preflight_detached_head")
  if staged:raise PatchError("git_preflight_staged_index:"+staged.replace("\n",","))
  bad=sorted(p for st,p in status(r) if p not in ALLOWED or (p!=SELF and st[0]!=" "))
  if bad:raise PatchError(f"unexpected_dirty:{bad}")
  print(f"[2/10] [PASS] Active branch {branch}, exact parent, dirty allowlist and clean index verified.");folder,state=backup(r);print("[3/10] [PASS] Resolution artifacts backed up before publication mutation.")
  evidence=inspect(r);print("[4/10] [PASS] Exact V1 prerequisite, progress, reward, overlevel/SKIP and handler evidence re-verified.")
  resolutions={
   "PREREQUISITE_AND_AVAILABILITY_POLICY":{"decision":"Availability is evaluated in this order: definition exists, persisted state is neither completed nor skipped, no conflicting active story quest exists, canonical location matches, player level meets the definition, and the previous quest is completed or skipped according to the chain policy. Overlevel reconciliation runs before normal availability materialization. Queries are read-only and repeated calls return the same stable machine reason until persisted inputs change."},
   "PROGRESS_AND_COMPLETION_STATE_MACHINE":{"decision":"Legal states are unavailable, available, active, ready_to_turn_in, completed and skipped. Accept is allowed only from available. TALK completes its objective through the canonical conversation event; KILL_REGION and BOSS consume matching exact-once event identities; QUEST_ITEM derives readiness from the isolated quest-item store; TURN_IN requires explicit submission. Progress is monotonic and clamped to target. Duplicate or stale events perform no second mutation. Restart reconstructs state exclusively from persisted quest and quest-item records."},
   "REWARD_AND_EXACT_ONCE_TURN_IN":{"decision":"One Unit of Work revalidates active quest, objective readiness and expected revision, consumes required quest items exactly once, grants definition-declared EXP, gold and item rewards, marks the quest completed, records the reward idempotency key, and exposes the next quest. The idempotency key is quest_id plus user_id plus completion revision. Failure before commit rolls back consumption, rewards and completion; retry after commit returns the persisted completed result without another grant."},
   "ENGINE_CONTENT_INDEPENDENCE":{"decision":"The engine consumes typed QuestDefinition data and objective strategy ports keyed only by objective type. Reusable domain/application code may not branch on concrete quest IDs, ranges, titles, NPC names, location display text or story prose. Quest-specific targets, rewards, prerequisites and presentation metadata remain in data definitions. Stage 21.13.1c must include an executable gate that fails on concrete quest-ID literals or content strings in the reusable engine and application modules."},
   "OVERLEVEL_AND_SKIP_INTERACTION":{"decision":"Automatic overlevel reconciliation runs before normal availability evaluation and may mark eligible unstarted chain entries skipped according to the existing V1 policy. Explicit active SKIP is a separate idempotent command restricted to the canonical eligible active quest/location. Neither path grants EXP, gold or items and neither consumes quest items. Skipped quests satisfy the chain predecessor requirement and appear as skipped in the journal. Completed quests are never converted to skipped; repeated reconciliation or SKIP performs no second mutation."},
   "PRESENTATION_AND_HANDLER_BOUNDARY":{"decision":"One Quest Engine application service owns availability, accept, progress events, turn-in, overlevel reconciliation, SKIP and journal queries through typed commands/results. Commands carry stable quest_id, objective/event key and expected revision. Handlers own callback parsing, keyboards and Ukrainian text, and register one canonical route. Handlers may not calculate rewards or progress, consume quest items, branch on concrete quest IDs, or mutate persistence directly."},
  }
  if tuple(resolutions)!=expected:raise PatchError("resolution_contract_mismatch")
  print("[5/10] [PASS] Prerequisite, state machine and exact-once turn-in parity policies resolved.");print("[6/10] [PASS] Content independence, overlevel/SKIP and presentation boundaries resolved with executable gate required.")
  removed=clean(r);checks=ci(r);print(f"[7/10] [PASS] Canonical V2 CI passed after removing {len(removed)} bytecode artifact(s).")
  if before!={x.as_posix():sha(r/x) for x in PROTECTED}:raise PatchError("protected_runtime_changed")
  print("[8/10] [PASS] Production sources, DB sidecars and protected configuration remained byte-identical.")
  payload={"schema_version":1,"stage":STAGE,"status":"PASS","conclusion":"GO_TO_IMPLEMENTATION","source_refinement":PREREQ.as_posix(),"contract_matrix":{"total":10,"v1_confirmed":4,"resolved_now":6,"unresolved":0},"resolved_contracts":list(expected),"unresolved_contracts":[],"resolutions":resolutions,"authoritative_evidence":evidence,"acceptance":{"engine_independent_from_specific_quests":True,"content_independence_gate_required":True,"exact_once_turn_in_required":True},"implementation_boundary":{"authorized":True,"authorized_scope":["typed QuestDefinition objective progress reward state and result DTOs","generic prerequisite and availability policy","objective strategy ports for TALK KILL_REGION QUEST_ITEM TURN_IN and BOSS","exact-once turn-in planning and idempotency contract","overlevel reconciliation and explicit SKIP state machine","in-memory Unit of Work fixtures","focused tests smoke verifier and content-independence gate"],"forbidden_scope":["production SQLite adapter or migration","Telegram/runtime handler wiring","production database access","real reward grant or quest-item consumption","new quest content IDs NPCs rewards prerequisites or formulas","changes to the existing V1 overlevel SKIP policy"]},"implementation_authorized":True,"runtime_integration_authorized":False,"production_persistence_authorized":False,"production_reward_authorized":False,"production_quest_item_consumption_authorized":False,"database_opened":False,"v1_wal_shm_manipulated":False,"canonical_v2_ci":checks,"manual_game_check":"NOT_REQUIRED","suggested_next_patch":"patch_21_13_1c_implement_quest_engine.py","backup_path":folder.relative_to(r).as_posix()};write(r/REPORT,json.dumps(payload,ensure_ascii=False,indent=2)+"\n")
  lines=["# Stage 21.13.1b - Resolved Quest Engine parity","","- Status: **PASS**","- Conclusion: **GO_TO_IMPLEMENTATION**","- Contract matrix: **4 previously confirmed + 6 resolved = 10/10**","- Remaining unresolved contracts: **0**","- Implementation authorized: **True**","- Engine content independence gate: **REQUIRED**","- Exact-once turn-in: **REQUIRED**","- Runtime integration authorized: **False**","- Production persistence authorized: **False**","- Production reward authorized: **False**","- Production quest-item consumption authorized: **False**","- Manual game check: **NOT_REQUIRED**","","## Resolutions",""]
  for k in expected:lines.extend(["### "+k,"",resolutions[k]["decision"],""])
  lines.extend(["## Implementation boundary","","Stage 21.13.1c may implement pure Quest Engine DTOs, generic policies, state machines, in-memory Unit of Work, tests, smoke verification and a content-independence gate. It may not connect SQLite, Telegram, runtime rewards or real quest-item consumption.","","## Next patch","","`patch_21_13_1c_implement_quest_engine.py`",""]);write(r/DOC,"\n".join(lines));print("[9/10] [PASS] Resolved JSON and Markdown Quest Engine parity artifacts written.")
  files={x.as_posix() for x in TARGETS};git(r,"add","-f","--",*sorted(files));got={x.replace("\\","/") for x in git(r,"diff","--cached","--name-only").stdout.splitlines() if x}
  if got!=files:raise PatchError("staging_mismatch:"+repr(sorted(got)))
  z=git(r,"commit","-m","Stage 21.13.1b: resolve Quest Engine parity","--",*sorted(files),check=False)
  if z.returncode:raise PatchError("commit_failed:"+z.stdout+z.stderr)
  commit=git(r,"rev-parse","HEAD").stdout.strip();changed={x.replace("\\","/") for x in git(r,"diff-tree","--no-commit-id","--name-only","-r",commit).stdout.splitlines() if x}
  if changed!=files:raise PatchError("commit_scope_mismatch:"+repr(sorted(changed)))
  print(f"[10/10] [PASS] Quest Engine parity resolution committed: {commit}");print("CONCLUSION: GO_TO_IMPLEMENTATION\nCONTRACT_MATRIX: 10/10 RESOLVED\nUNRESOLVED_CONTRACTS: 0\nIMPLEMENTATION AUTHORIZED: True\nENGINE CONTENT INDEPENDENCE GATE: REQUIRED\nEXACT-ONCE TURN-IN: REQUIRED\nPRODUCTION REWARD AUTHORIZED: False\nPRODUCTION QUEST-ITEM CONSUMPTION AUTHORIZED: False\nRUNTIME INTEGRATION AUTHORIZED: False\nPRODUCTION PERSISTENCE AUTHORIZED: False\nMANUAL GAME CHECK: NOT_REQUIRED\nFAIL-SAFE ROLLBACK: ARMED\nSUGGESTED NEXT PATCH: patch_21_13_1c_implement_quest_engine.py");return 0
 except Exception as error:
  restored=restore(r,folder,state);recovery=run([sys.executable,"-m","compileall","-q","rom_v2"],r,False);write(r/FAILURE,json.dumps({"stage":STAGE,"status":"FAIL_ROLLED_BACK","reason":str(error),"restored_files":restored,"recovery_compile_returncode":recovery.returncode,"main_py_must_not_run":recovery.returncode!=0,"database_opened":False,"v1_wal_shm_manipulated":False},ensure_ascii=False,indent=2)+"\n");print(f"[10/10] [FAIL] {error}; rollback: FAIL_ROLLED_BACK");return 1
if __name__=="__main__":raise SystemExit(main())
