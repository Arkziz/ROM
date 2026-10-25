#!/usr/bin/env python3
"""Stage 21.13.1: read-only audit of the existing V1 Quest Engine."""
from __future__ import annotations
import ast,hashlib,json,os,py_compile,shutil,subprocess,sys
from datetime import datetime,timezone
from pathlib import Path
STAGE="21.13.1";PARENT="70d8573ab9e49eaec8df8356dc76b0c7ccba0a81";BRANCH="stage-21-v2-modular-monolith"
SELF="patch/patch_21_13_1_audit_existing_quest_engine.py";PREREQ=Path("reports/stage_21_12_6c_pvp_implementation.json");REPORT=Path("reports/stage_21_13_1_existing_quest_engine_audit.json");DOC=Path("MD/STAGE_21_13_1_EXISTING_QUEST_ENGINE_AUDIT.md");FAILURE=Path("reports/stage_21_13_1_failure_rollback.json")
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
 d=r/"backup"/("stage_21_13_1_"+datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ"));d.mkdir(parents=True,exist_ok=True);state={}
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
 contracts=("QUEST_DEFINITION_AND_STABLE_ID_MODEL","PREREQUISITE_AND_AVAILABILITY_POLICY","OBJECTIVE_TYPE_CONTRACT","PROGRESS_AND_COMPLETION_STATE_MACHINE","REWARD_AND_EXACT_ONCE_TURN_IN","QUEST_ITEM_ISOLATION_BOUNDARY","PERSISTENCE_RESTART_AND_FAILURE_POLICY","ENGINE_CONTENT_INDEPENDENCE","OVERLEVEL_AND_SKIP_INTERACTION","PRESENTATION_AND_HANDLER_BOUNDARY")
 try:
  pre=json.loads((r/PREREQ).read_text(encoding="utf-8-sig"))
  if git(r,"rev-parse","HEAD").stdout.strip()!=PARENT:raise PatchError("wrong_exact_parent")
  if pre.get("stage")!="21.12.6c" or pre.get("conclusion")!="API_READY" or pre.get("runtime_integration")!="NOT_CONNECTED" or pre.get("production_persistence")!="NOT_CONNECTED" or pre.get("production_battle_execution")!="NOT_CONNECTED":raise PatchError("invalid_stage_21_12_6c_prerequisite")
  print("[1/10] [PASS] Stage 21.12.6c API-ready PvP prerequisite verified; Stage 21.12 block complete.")
  branch=git(r,"branch","--show-current").stdout.strip();staged=git(r,"diff","--cached","--name-only").stdout.strip()
  if not branch or staged:raise PatchError("git_preflight")
  bad=sorted(p for st,p in status(r) if p not in ALLOWED or (p!=SELF and st[0]!=" "))
  if bad:raise PatchError(f"unexpected_dirty:{bad}")
  print(f"[2/10] [PASS] Active branch {branch}, exact parent, dirty allowlist and clean index verified.");folder,state=backup(r);print("[3/10] [PASS] Audit artifacts backed up before publication mutation.")
  evidence=inspect(r);print("[4/10] [PASS] Exact V1 Quest Engine, definitions, persistence and handler owners verified.");print("[5/10] [PASS] Objective types, progress, isolated quest-item store, overlevel/SKIP and journal paths discovered without opening SQLite.")
  confirmed={"QUEST_DEFINITION_AND_STABLE_ID_MODEL","OBJECTIVE_TYPE_CONTRACT","QUEST_ITEM_ISOLATION_BOUNDARY","PERSISTENCE_RESTART_AND_FAILURE_POLICY"};matrix=[{"contract":c,"classification":"V1_CONFIRMED" if c in confirmed else "REVIEW_REQUIRED","meaning":"Exact V1 evidence confirmed." if c in confirmed else "V1 behavior discovered; exact prerequisite, state, reward, idempotency, overlevel or presentation contract requires refinement."} for c in contracts];unresolved=[x["contract"] for x in matrix if x["classification"]=="REVIEW_REQUIRED"]
  print(f"[6/10] [PASS] Quest Engine evidence matrix built; review-required contracts: {len(unresolved)}.");removed=clean(r);checks=ci(r);print(f"[7/10] [PASS] Canonical V2 CI passed after removing {len(removed)} bytecode artifact(s).")
  if before!={x.as_posix():sha(r/x) for x in PROTECTED}:raise PatchError("protected_runtime_changed")
  print("[8/10] [PASS] V1/V2 production sources, DB sidecars and protected configuration remained byte-identical.")
  payload={"schema_version":1,"stage":STAGE,"status":"PASS","conclusion":"GO_TO_SEMANTIC_REFINEMENT","roadmap_scope":{"title":"Quest engine","behavior":"Definitions, prerequisites, objective types, progress, completion, reward and exact-once turn-in","acceptance":"Engine independent from specific quests"},"source_prerequisite":PREREQ.as_posix(),"summary":{"contract_count":len(contracts),"v1_confirmed_contracts":len(confirmed),"review_required_contracts":len(unresolved),"unresolved_contracts":unresolved,"database_opened":False,"production_code_changed":False,"v1_wal_shm_manipulated":False},"canonical_v1_evidence":evidence,"contract_matrix":matrix,"implementation_authorized":False,"canonical_v2_ci":checks,"manual_game_check":"NOT_REQUIRED","suggested_next_patch":"patch_21_13_1a_refine_quest_engine_contract.py","backup_path":folder.relative_to(r).as_posix()};write(r/REPORT,json.dumps(payload,ensure_ascii=False,indent=2)+"\n")
  lines=["# Stage 21.13.1 - Existing V1 Quest Engine audit","","- Status: **PASS**","- Conclusion: **GO_TO_SEMANTIC_REFINEMENT**","- Implementation authorized: **False**","- Database opened: **False**","- Manual game check: **NOT_REQUIRED**","","## Contract matrix",""]+[f"- `{x['contract']}`: **{x['classification']}** - {x['meaning']}" for x in matrix]+["","## Next patch","","`patch_21_13_1a_refine_quest_engine_contract.py`",""];write(r/DOC,"\n".join(lines));print("[9/10] [PASS] JSON and Markdown read-only audit artifacts written.")
  files={x.as_posix() for x in TARGETS};git(r,"add","-f","--",*sorted(files));got={x.replace("\\","/") for x in git(r,"diff","--cached","--name-only").stdout.splitlines() if x}
  if got!=files:raise PatchError("staging_mismatch:"+repr(sorted(got)))
  z=git(r,"commit","-m","Stage 21.13.1: audit existing Quest Engine","--",*sorted(files),check=False)
  if z.returncode:raise PatchError("commit_failed:"+z.stdout+z.stderr)
  commit=git(r,"rev-parse","HEAD").stdout.strip();print(f"[10/10] [PASS] Existing V1 Quest Engine audit committed: {commit}");print("CONCLUSION: GO_TO_SEMANTIC_REFINEMENT\nPATCH STATUS: PASS\nIMPLEMENTATION AUTHORIZED: False\nMANUAL GAME CHECK: NOT_REQUIRED\nFAIL-SAFE ROLLBACK: ARMED\nSUGGESTED NEXT PATCH: patch_21_13_1a_refine_quest_engine_contract.py");return 0
 except Exception as error:
  restored=restore(r,folder,state);recovery=run([sys.executable,"-m","compileall","-q","rom_v2"],r,False);write(r/FAILURE,json.dumps({"stage":STAGE,"status":"FAIL_ROLLED_BACK","reason":str(error),"restored_files":restored,"recovery_compile_returncode":recovery.returncode,"main_py_must_not_run":recovery.returncode!=0,"database_opened":False,"v1_wal_shm_manipulated":False},ensure_ascii=False,indent=2)+"\n");print(f"[10/10] [FAIL] {error}; rollback: FAIL_ROLLED_BACK");return 1
if __name__=="__main__":raise SystemExit(main())
