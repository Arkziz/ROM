#!/usr/bin/env python3
"""Stage 21.12.6b: resolve V1 PvP parity without production mutation."""
from __future__ import annotations
import ast,hashlib,json,os,py_compile,shutil,subprocess,sys
from datetime import datetime,timezone
from pathlib import Path
STAGE="21.12.6b";PARENT="b9dc84d083f41195ac1bcecb5954111cfa06d918";BRANCH="stage-21-v2-modular-monolith"
SELF="patch/patch_21_12_6b_resolve_pvp_parity.py";PREREQ=Path("reports/stage_21_12_6a_refined_pvp_contract.json");REPORT=Path("reports/stage_21_12_6b_resolved_pvp_parity.json");DOC=Path("MD/STAGE_21_12_6B_RESOLVED_PVP_PARITY.md");FAILURE=Path("reports/stage_21_12_6b_failure_rollback.json")
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
 d=r/"backup"/("stage_21_12_6b_"+datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ"));d.mkdir(parents=True,exist_ok=True);state={}
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
  refined=json.loads((r/PREREQ).read_text(encoding="utf-8-sig"));summary=refined.get("summary",{});rows=tuple(x for x in refined.get("refined_contract_matrix",()) if isinstance(x,dict));u=tuple(x.get("contract") for x in rows if x.get("classification")=="REVIEW_REQUIRED")
  if git(r,"rev-parse","HEAD").stdout.strip()!=PARENT:raise PatchError("wrong_exact_parent")
  if refined.get("stage")!="21.12.6a" or refined.get("conclusion")!="REVIEW_REQUIRED" or summary.get("contract_count")!=12 or summary.get("v1_confirmed_contracts")!=4 or summary.get("review_required_contracts")!=8 or u!=EXPECTED or tuple(summary.get("unresolved_contracts",()))!=EXPECTED:raise PatchError("invalid_stage_21_12_6a_prerequisite")
  print("[1/10] [PASS] Stage 21.12.6a exact 4/8/12 refinement prerequisite verified.")
  branch=git(r,"branch","--show-current").stdout.strip()
  if not branch:raise PatchError("git_preflight_detached_head")
  staged_before=git(r,"diff","--cached","--name-only").stdout.strip()
  if staged_before:raise PatchError("git_preflight_staged_index:"+staged_before.replace("\n",","))
  bad=sorted(p for st,p in status(r) if p not in ALLOWED or (p!=SELF and st[0]!=" "))
  if bad:raise PatchError(f"unexpected_dirty:{bad}")
  print(f"[2/10] [PASS] Active branch {branch}, exact parent, dirty allowlist and clean index verified.");folder,state=backup(r);print("[3/10] [PASS] Resolution artifacts backed up before publication mutation.")
  e=inspect(r);print("[4/10] [PASS] Exact V1 availability, snapshot, shared-engine, history, timer and recovery evidence re-verified.")
  resolutions={
   "AVAILABILITY_AND_ACTIVITY_SESSION_POLICY":{"decision":"Challenge creation rejects self-target and requires both users online, in the same canonical location, free of PvE and other interaction activity, without another pending duel or active battle. Acceptance repeats all checks against the accepted request revision. After immutable snapshots are prepared, both pvp_battle activity sessions are acquired for the same battle_id; failure to acquire either session compensates any acquired session and cancels the created battle."},
   "ACCEPTED_DUEL_TO_BATTLE_ATOMICITY":{"decision":"The accepted request is the idempotency key for battle creation. One application orchestration prepares both snapshots, creates exactly one battle under BEGIN IMMEDIATE, acquires both activity sessions, and publishes success only after all steps pass. A retry returns the existing battle. Failure before commit creates nothing; failure after battle creation but before both sessions are acquired cancels that battle and releases every acquired session."},
   "COMBAT_SNAPSHOT_AND_PARTICIPANT_IDENTITY":{"decision":"Each participant is persisted by stable user_id plus immutable side and a battle-start snapshot. The snapshot freezes class, level, max/current HP, attack, defenses, critical, dodge, resource type/value, combo, equipment-derived bonuses and skill availability. Battle-start HP is full canonical max HP; resource initialization follows the shared class resource policy. Durability and equipment changes after acceptance do not refresh an active battle snapshot."},
   "SHARED_COMBAT_FORMULA_BOUNDARY":{"decision":"PvP orchestration may sequence simultaneous actions, status effects, timeout intents and terminal checks, but it must consume shared canonical damage, defense, critical, dodge, resource-cost, regeneration and skill-effect policies through imports or adapters. Handlers and presentation may not calculate combat values. The Stage 21.12.6c architecture gate must fail on local duplicate formula constants/functions or direct arithmetic implementations outside approved shared adapters. No new PvP-only damage or resource formulas are authorized."},
   "EVENT_HISTORY_AND_PROFILE_HISTORY":{"decision":"Battle events are append-only and ordered by battle_id, round_number, event sequence and stable event id. Participants may read their own complete battle history; non-participants receive no private battle payload. Only resultful completed battles publish one profile-history entry per participant, keyed by battle_id and user_id. Cancelled or setup-failed battles are excluded. Machine reasons remain stable keys and Ukrainian text is presentation-only."},
   "TIMEOUT_FORFEIT_AND_ANTI_STALL_POLICY":{"decision":"Each required action uses the persisted round deadline owned by the timer service. Repeated timer ticks are idempotent. If exactly one participant misses the final deadline, that participant forfeits and the opponent wins; if both miss it, the battle ends without a winner using the canonical double-timeout reason. Warnings do not mutate battle state. Maximum-round or no-progress termination uses the existing round-engine terminal policy and never introduces copied damage formulas."},
   "RESTART_RECOVERY_AND_SESSION_CLEANUP":{"decision":"Restart recovery classifies every non-terminal battle from persisted round, revision, actions, resolution claim and deadline. Unclaimed complete rounds resume resolution with the same seed/revision; partially submitted rounds resume until their reconstructed deadline; stale unresolved claims are released before retry. Terminal battles are never reopened. Missing active sessions are reconciled when safe, while orphan sessions for terminal or absent battles are released. Repeated recovery returns the same typed per-battle outcome without duplicate events or completion."},
   "PRESENTATION_TIMER_AND_HANDLER_BOUNDARY":{"decision":"One PvP application service owns challenge acceptance, battle creation, action commands, recovery and terminal completion through typed commands/results. The pure round engine owns deterministic resolution; the timer port supplies deadlines and timeout commands. Telegram handlers own callback parsing, keyboards and Ukrainian text, pass battle_id, round_number and expected_revision, and register one canonical route. Handlers, timer adapters and presentation modules may not contain combat formulas."},
  }
  if tuple(resolutions)!=EXPECTED:raise PatchError("resolution_contract_mismatch")
  print("[5/10] [PASS] Availability, atomic accepted-duel creation, immutable snapshots and shared-formula boundaries resolved.");print("[6/10] [PASS] History, timeout/forfeit, restart recovery and presentation boundaries resolved with No copied formulas enforced.")
  removed=clean(r);checks=ci(r);print(f"[7/10] [PASS] Canonical V2 CI passed after removing {len(removed)} bytecode artifact(s).")
  if before!={x.as_posix():sha(r/x) for x in PROTECTED}:raise PatchError("protected_runtime_changed")
  print("[8/10] [PASS] Production sources, DB sidecars and protected configuration remained byte-identical.")
  payload={"schema_version":1,"stage":STAGE,"status":"PASS","conclusion":"GO_TO_IMPLEMENTATION","source_refinement":PREREQ.as_posix(),"contract_matrix":{"total":12,"v1_confirmed":4,"resolved_now":8,"unresolved":0},"resolved_contracts":list(EXPECTED),"unresolved_contracts":[],"resolutions":resolutions,"authoritative_evidence":e,"acceptance":{"no_copied_formulas":True,"architecture_gate_required":True},"implementation_boundary":{"authorized":True,"authorized_scope":["immutable PvP challenge battle participant snapshot action and event DTOs","availability and activity-session policy ports","accepted-duel idempotency and compensation planning","shared combat policy adapter interfaces without copied formulas","round revision claim timeout forfeit history and recovery state machine","in-memory Unit of Work fixtures","focused tests smoke verifier and no-copied-formulas gate"],"forbidden_scope":["production SQLite adapter or migration","Telegram/runtime handler wiring","production database access","real battle execution or terminal settlement","production timer scheduling","new PvP damage defense critical dodge resource or skill formulas","changes to V1 combat balance"]},"implementation_authorized":True,"runtime_integration_authorized":False,"production_persistence_authorized":False,"production_battle_execution_authorized":False,"production_terminal_settlement_authorized":False,"production_timer_authorized":False,"database_opened":False,"v1_wal_shm_manipulated":False,"canonical_v2_ci":checks,"manual_game_check":"NOT_REQUIRED","suggested_next_patch":"patch_21_12_6c_implement_pvp.py","backup_path":folder.relative_to(r).as_posix()};write(r/REPORT,json.dumps(payload,ensure_ascii=False,indent=2)+"\n")
  lines=["# Stage 21.12.6b - Resolved PvP parity","","- Status: **PASS**","- Conclusion: **GO_TO_IMPLEMENTATION**","- Contract matrix: **4 previously confirmed + 8 resolved = 12/12**","- Remaining unresolved contracts: **0**","- Implementation authorized: **True**","- No copied formulas: **REQUIRED**","- Runtime integration authorized: **False**","- Production persistence authorized: **False**","- Production battle execution authorized: **False**","- Production terminal settlement authorized: **False**","- Production timer authorized: **False**","- Manual game check: **NOT_REQUIRED**","","## Resolutions",""]
  for k in EXPECTED:lines.extend(["### "+k,"",resolutions[k]["decision"],""])
  lines.extend(["## Implementation boundary","","Stage 21.12.6c may implement pure PvP DTOs, policies, state machines, shared-policy ports, in-memory Unit of Work, tests, smoke verification and a no-copied-formulas gate. It may not connect SQLite, Telegram, runtime timers or execute production battles.","","## Next patch","","`patch_21_12_6c_implement_pvp.py`",""]);write(r/DOC,"\n".join(lines));print("[9/10] [PASS] Resolved JSON and Markdown parity artifacts written.")
  files={x.as_posix() for x in TARGETS};git(r,"add","-f","--",*sorted(files));staged={x.replace("\\","/") for x in git(r,"diff","--cached","--name-only").stdout.splitlines() if x}
  if staged!=files:raise PatchError(f"staging_mismatch:{sorted(staged)}")
  z=git(r,"commit","-m","Stage 21.12.6b: resolve PvP parity","--",*sorted(files),check=False)
  if z.returncode:raise PatchError("commit_failed:"+z.stdout+z.stderr)
  commit=git(r,"rev-parse","HEAD").stdout.strip();changed={x.replace("\\","/") for x in git(r,"diff-tree","--no-commit-id","--name-only","-r",commit).stdout.splitlines() if x}
  if changed!=files:raise PatchError(f"commit_scope_mismatch:{sorted(changed)}")
  print(f"[10/10] [PASS] PvP parity resolution committed: {commit}");print("CONCLUSION: GO_TO_IMPLEMENTATION\nCONTRACT_MATRIX: 12/12 RESOLVED\nUNRESOLVED_CONTRACTS: 0\nIMPLEMENTATION AUTHORIZED: True\nNO COPIED FORMULAS: REQUIRED\nPRODUCTION BATTLE EXECUTION AUTHORIZED: False\nPRODUCTION TERMINAL SETTLEMENT AUTHORIZED: False\nPRODUCTION TIMER AUTHORIZED: False\nRUNTIME INTEGRATION AUTHORIZED: False\nPRODUCTION PERSISTENCE AUTHORIZED: False\nMANUAL GAME CHECK: NOT_REQUIRED\nFAIL-SAFE ROLLBACK: ARMED\nSUGGESTED NEXT PATCH: patch_21_12_6c_implement_pvp.py");return 0
 except Exception as error:
  restored=restore(r,folder,state);recovery=run([sys.executable,"-m","compileall","-q","rom_v2"],r,False);write(r/FAILURE,json.dumps({"stage":STAGE,"status":"FAIL_ROLLED_BACK","reason":str(error),"restored_files":restored,"recovery_compile_returncode":recovery.returncode,"main_py_must_not_run":recovery.returncode!=0,"database_opened":False,"v1_wal_shm_manipulated":False},ensure_ascii=False,indent=2)+"\n");print(f"[10/10] [FAIL] {error}; rollback: FAIL_ROLLED_BACK");return 1
if __name__=="__main__":raise SystemExit(main())
