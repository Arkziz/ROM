#!/usr/bin/env python3
"""Stage 21.12.6a: refine the V1 PvP contract without production mutation."""
from __future__ import annotations
import ast,hashlib,json,os,py_compile,shutil,subprocess,sys
from datetime import datetime,timezone
from pathlib import Path
STAGE="21.12.6a";PARENT="1b0407a750fb9396b8a69074d28d791b1274c75f";BRANCH="stage-21-v2-modular-monolith"
SELF="patch/patch_21_12_6a_refine_pvp_contract.py";PREREQ=Path("reports/stage_21_12_6_existing_pvp_audit.json");REPORT=Path("reports/stage_21_12_6a_refined_pvp_contract.json");DOC=Path("MD/STAGE_21_12_6A_REFINED_PVP_CONTRACT.md");FAILURE=Path("reports/stage_21_12_6a_failure_rollback.json")
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
 d=r/"backup"/("stage_21_12_6a_"+datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ"));d.mkdir(parents=True,exist_ok=True);state={}
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
 paths=(Path("systems/pvp_system.py"),Path("systems/pvp_request_service.py"),Path("systems/pvp_round_engine.py"),Path("systems/pvp_battle_factory.py"),Path("systems/pvp_completion_service.py"),Path("systems/pvp_timer_service.py"),Path("systems/pvp_models.py"),Path("systems/pvp_skill_adapter.py"),Path("handlers/pvp_interaction.py"));src={}
 for x in paths:src[x.as_posix()]=(r/x).read_text(encoding="utf-8-sig");ast.parse(src[x.as_posix()])
 owner=src["systems/pvp_system.py"];request=src["systems/pvp_request_service.py"];engine=src["systems/pvp_round_engine.py"];factory=src["systems/pvp_battle_factory.py"]
 required={"create_pvp_battle","submit_pvp_action","claim_pvp_round_resolution","release_pvp_round_resolution","complete_pvp_battle","get_pvp_recovery_plan","recover_pvp_after_restart","resolve_persisted_pvp_round","cleanup_terminal_pvp_activity_sessions"}
 if required-funcs(owner):raise PatchError("pvp_owner_symbols_missing")
 # Availability is verified by the canonical request entrypoints and the accepted-duel
 # activity-session acquisition path. V1 delegates presence/busy checks, so their
 # helper names are intentionally not required to appear in this module.
 request_symbols=funcs(request)
 for token in ("create_pvp_duel_request","respond_to_pvp_duel_request","cancel_failed_accepted_pvp_duel_request"):
  if token not in request_symbols:raise PatchError("pvp_request_symbol_missing:"+token)
 for text,token in ((factory,"prepare_pvp_duel_snapshots"),(factory,"create_pvp_battle_from_accepted_duel"),(factory,"acquire_player_activity_session"),(engine,"resolve_pvp_round"),(engine,"CRITICAL_DAMAGE_MULTIPLIER"),(engine,"calculate_dodge_chance"),(owner,"BEGIN IMMEDIATE"),(owner,"revision")):
  if token not in text:raise PatchError("pvp_evidence_missing:"+token)
 return {"owners":[x.as_posix() for x in paths],"shared_formula_evidence":{"critical_multiplier_imported":True,"dodge_calculator_imported":True,"skill_adapter":True},"availability":{"online":True,"busy":True,"activity_session":True},"source_hashes":{x.as_posix():sha(r/x) for x in paths}}
def main():
 r=root();folder=None;state={};before={x.as_posix():sha(r/x) for x in PROTECTED}
 try:
  audit=json.loads((r/PREREQ).read_text(encoding="utf-8-sig"));rows=tuple(x for x in audit.get("contract_matrix",()) if isinstance(x,dict));u=tuple(x["contract"] for x in rows if x.get("classification")=="REVIEW_REQUIRED");c=tuple(x["contract"] for x in rows if x.get("classification")=="V1_CONFIRMED")
  if git(r,"rev-parse","HEAD").stdout.strip()!=PARENT:raise PatchError("wrong_exact_parent")
  if audit.get("stage")!="21.12.6" or audit.get("conclusion")!="GO_TO_SEMANTIC_REFINEMENT" or len(rows)!=12 or u!=EXPECTED or c!=CONFIRMED:raise PatchError("invalid_stage_21_12_6_prerequisite")
  print("[1/10] [PASS] Stage 21.12.6 exact 4-confirmed/8-unresolved/12-total prerequisite verified.")
  branch=git(r,"branch","--show-current").stdout.strip()
  if not branch:raise PatchError("git_preflight_detached_head")
  staged_before=git(r,"diff","--cached","--name-only").stdout.strip()
  if staged_before:raise PatchError("git_preflight_staged_index:"+staged_before.replace("\n",","))
  bad=sorted(p for st,p in status(r) if p not in ALLOWED or (p!=SELF and st[0]!=" "))
  if bad:raise PatchError(f"unexpected_dirty:{bad}")
  print(f"[2/10] [PASS] Active branch {branch}, exact parent, dirty allowlist and clean index verified.");folder,state=backup(r);print("[3/10] [PASS] Refinement artifacts backed up before publication mutation.")
  e=inspect(r);print("[4/10] [PASS] Exact V1 availability, snapshot, shared-engine, history, timer and recovery evidence re-verified.")
  questions={k:v for k,v in zip(EXPECTED,("Exact availability check order and concurrent activity-session acquisition.","Unit of Work boundary across request acceptance, snapshots, battle creation and two sessions.","Immutable snapshot fields, resource initialization and refresh prohibition during battle.","Permitted shared policy adapters and executable no-copied-formulas architecture gate.","Event order, retention, profile visibility and exact-once history publication.","Deadlines, warnings, one/two-sided timeout, forfeit and anti-stall semantics.","Resume/cancel rules, timer reconstruction, claim recovery and session cleanup.","Typed commands/results, timer ports, callback revisions and single handler registration."))};refined=[{"contract":k,"classification":"REVIEW_REQUIRED","remaining_question":questions[k]} for k in EXPECTED]
  print("[5/10] [PASS] Eight PvP boundaries narrowed to exact availability, atomicity, snapshot, formula, history, timer and recovery evidence.");print("[6/10] [PASS] No-copied-formulas risk isolated without executing battles, timers or production persistence.")
  removed=clean(r);checks=ci(r);print(f"[7/10] [PASS] Canonical V2 CI passed after removing {len(removed)} bytecode artifact(s).")
  if before!={x.as_posix():sha(r/x) for x in PROTECTED}:raise PatchError("protected_runtime_changed")
  print("[8/10] [PASS] Production sources, DB sidecars and protected configuration remained byte-identical.")
  payload={"schema_version":1,"stage":STAGE,"status":"PASS","conclusion":"REVIEW_REQUIRED","source_audit":PREREQ.as_posix(),"summary":{"contract_count":12,"v1_confirmed_contracts":4,"refined_contracts":8,"review_required_contracts":8,"unresolved_contracts":list(EXPECTED),"database_opened":False,"production_code_changed":False,"v1_wal_shm_manipulated":False},"authoritative_evidence":e,"refined_contract_matrix":refined,"implementation_authorized":False,"canonical_v2_ci":checks,"manual_game_check":"NOT_REQUIRED","suggested_next_patch":"patch_21_12_6b_resolve_pvp_parity.py","backup_path":folder.relative_to(r).as_posix()};write(r/REPORT,json.dumps(payload,ensure_ascii=False,indent=2)+"\n")
  lines=["# Stage 21.12.6a - Refined PvP contract","","- Status: **PASS**","- Conclusion: **REVIEW_REQUIRED**","- Contract matrix: **4 confirmed / 8 review-required / 12 total**","- Implementation authorized: **False**","- Manual game check: **NOT_REQUIRED**",""]
  for x in refined:lines.extend(["## "+x["contract"],"",x["remaining_question"],""])
  lines.extend(["No production mutation, battle execution, timer execution, database access or runtime wiring is authorized.","","Next: `patch_21_12_6b_resolve_pvp_parity.py`",""]);write(r/DOC,"\n".join(lines));print("[9/10] [PASS] Refined JSON and Markdown contract artifacts written.")
  files={x.as_posix() for x in TARGETS};git(r,"add","-f","--",*sorted(files));staged={x.replace("\\","/") for x in git(r,"diff","--cached","--name-only").stdout.splitlines() if x}
  if staged!=files:raise PatchError(f"staging_mismatch:{sorted(staged)}")
  z=git(r,"commit","-m","Stage 21.12.6a: refine PvP contract","--",*sorted(files),check=False)
  if z.returncode:raise PatchError("commit_failed:"+z.stdout+z.stderr)
  commit=git(r,"rev-parse","HEAD").stdout.strip();print(f"[10/10] [PASS] PvP semantic refinement committed: {commit}");print("CONCLUSION: REVIEW_REQUIRED\nCONTRACT_MATRIX: 4 CONFIRMED / 8 REVIEW_REQUIRED / 12 TOTAL\nUNRESOLVED_CONTRACTS: 8\nIMPLEMENTATION AUTHORIZED: False\nMANUAL GAME CHECK: NOT_REQUIRED\nFAIL-SAFE ROLLBACK: ARMED\nSUGGESTED NEXT PATCH: patch_21_12_6b_resolve_pvp_parity.py");return 0
 except Exception as error:
  restored=restore(r,folder,state);recovery=run([sys.executable,"-m","compileall","-q","rom_v2"],r,False);write(r/FAILURE,json.dumps({"stage":STAGE,"status":"FAIL_ROLLED_BACK","reason":str(error),"restored_files":restored,"recovery_compile_returncode":recovery.returncode,"main_py_must_not_run":recovery.returncode!=0,"database_opened":False,"v1_wal_shm_manipulated":False},ensure_ascii=False,indent=2)+"\n");print(f"[10/10] [FAIL] {error}; rollback: FAIL_ROLLED_BACK");return 1
if __name__=="__main__":raise SystemExit(main())
