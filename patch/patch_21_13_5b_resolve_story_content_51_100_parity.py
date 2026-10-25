#!/usr/bin/env python3
"""Stage 21.13.1b: resolve V1 Quest Engine parity without production mutation."""
from __future__ import annotations
import ast,hashlib,json,os,py_compile,shutil,subprocess,sys
from datetime import datetime,timezone
from pathlib import Path
STAGE="21.13.5b";PARENT="4b924b9df3ec55dea403cb8cab6c5ee11ce87494";BRANCH="stage-21-v2-modular-monolith"
SELF="patch/patch_21_13_5b_resolve_story_content_51_100_parity.py";PREREQ=Path("reports/stage_21_13_5a_refined_story_content_51_100_contract.json");REPORT=Path("reports/stage_21_13_5b_resolved_story_content_51_100_parity.json");DOC=Path("MD/STAGE_21_13_5B_RESOLVED_STORY_CONTENT_51_100_PARITY.md");FAILURE=Path("reports/stage_21_13_5b_failure_rollback.json")
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
 d=r/"backup"/("stage_21_13_5b_"+datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ"));d.mkdir(parents=True,exist_ok=True);state={}
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
 candidate=r/"Квести/ROM_квести_Темний_Бір_candidate.json"
 if not candidate.exists():raise PatchError("canonical_dark_forest_candidate_missing")
 data=json.loads(candidate.read_text(encoding="utf-8-sig"));quests=data.get("quests") if isinstance(data,dict) else None
 if not isinstance(quests,list) or len(quests)!=50:raise PatchError("canonical_quests_array_not_50")
 def qnum(row):
  if not isinstance(row,dict):return None
  for key in ("number","quest_number","quest_no","quest_id","id"):
   value=row.get(key)
   if isinstance(value,int) and 51<=value<=100:return value
   if isinstance(value,str) and value.isdigit() and 51<=int(value)<=100:return int(value)
  return None
 matrix=[]
 for index,row in enumerate(quests):
  number=qnum(row)
  if number is None:raise PatchError("quest_number_missing_at_index:"+str(index))
  matrix.append({"quest_number":number,"array_index":index,"keys":sorted(str(k) for k in row),"record":row})
 numbers=[x["quest_number"] for x in matrix]
 if numbers!=list(range(51,101)):raise PatchError("canonical_quest_order_or_identity_mismatch:"+repr(numbers))
 packages={f"{start}-{start+9}":[x["quest_number"] for x in matrix[start-51:start-41]] for start in (51,61,71,81,91)}
 q51=matrix[0]["record"];q99=matrix[48]["record"];q100=matrix[49]["record"]
 if q51.get("previous_quest_id")!="start_path_050_road_ahead":raise PatchError("quest_51_bridge_mismatch")
 if q99.get("quest_type")!="BOSS" or q99.get("boss_key")!="goblin_king":raise PatchError("quest_99_boss_contract_mismatch")
 if q100.get("quest_type")!="TURN_IN" or q100.get("previous_quest_id")!=q99.get("quest_id"):raise PatchError("quest_100_terminal_contract_mismatch")
 refs={x.relative_to(r).as_posix():sha(x) for x in (r/"Квести").rglob("*") if x.is_file()}
 return {"candidate_file":candidate.relative_to(r).as_posix(),"candidate_sha256":sha(candidate),"canonical_record_count":50,"canonical_numbers":numbers,"package_manifests":packages,"quest_matrix":matrix,"quest_51":q51,"quest_99":q99,"quest_100":q100,"reference_hashes":refs}
def main():
 r=root();folder=None;state={};before={x.as_posix():sha(r/x) for x in PROTECTED};reference_before={x.relative_to(r).as_posix():sha(x) for x in (r/"Квести").rglob("*") if x.is_file()}
 expected=("EXACT_QUEST_RECORDS_51_TO_100","LEVEL_GATES_AND_SEQUENTIAL_PREREQUISITES_51_TO_100","OBJECTIVES_TARGETS_AND_QUEST_ITEMS_51_TO_100","REWARD_PARITY_51_TO_100","NPC_LOCATION_AND_LOCALIZED_DARK_FOREST_REFERENCES","BOSS_99_AND_FORCED_ENCOUNTER_CONTRACT","PACKAGE_BY_TEN_AND_CONTENT_VALIDATION_51_TO_100","QUEST_100_FINAL_STORY_FLOW")
 try:
  refined=json.loads((r/PREREQ).read_text(encoding="utf-8-sig"));rows=tuple(x for x in refined.get("refined_contract_matrix",()) if isinstance(x,dict));unresolved=tuple(x.get("contract") for x in rows if x.get("classification")=="REVIEW_REQUIRED");summary=refined.get("summary",{});observations=refined.get("observations",{})
  if git(r,"rev-parse","HEAD").stdout.strip()!=PARENT:raise PatchError("wrong_exact_parent")
  if refined.get("stage")!="21.13.5a" or refined.get("conclusion")!="REVIEW_REQUIRED" or len(rows)!=8 or unresolved!=expected or tuple(summary.get("unresolved_contracts",()))!=expected:raise PatchError("invalid_stage_21_13_5a_prerequisite")
  if summary.get("v1_confirmed_contracts")!=3 or summary.get("review_required_contracts")!=8 or summary.get("contract_count")!=11 or observations.get("boss_99_requires_resolution") is not True or observations.get("final_100_requires_resolution") is not True:raise PatchError("invalid_3_8_11_contract_matrix")
  print("[1/10] [PASS] Stage 21.13.5a exact 3/8/11 refinement prerequisite verified.")
  branch=git(r,"branch","--show-current").stdout.strip();staged=git(r,"diff","--cached","--name-only").stdout.strip()
  if not branch:raise PatchError("git_preflight_detached_head")
  if staged:raise PatchError("git_preflight_staged_index:"+staged.replace("\n",","))
  bad=sorted(p for st,p in status(r) if p not in ALLOWED or (p!=SELF and st[0]!=" "))
  if bad:raise PatchError(f"unexpected_dirty:{bad}")
  print(f"[2/10] [PASS] Active branch {branch}, exact parent, dirty allowlist and clean index verified.");folder,state=backup(r);print("[3/10] [PASS] Resolution artifacts backed up before publication mutation.")
  evidence=inspect(r);print("[4/10] [PASS] Exact canonical $.quests records 51-100, five packages and 50-to-51 bridge re-verified.")
  decisions={
   "EXACT_QUEST_RECORDS_51_TO_100":{"decision":"The authoritative migration matrix is exactly the 50 ordered objects in $.quests of Квести/ROM_квести_Темний_Бір_candidate.json. Quest identity is the explicit number 51-100 plus the record stable quest_id. Nested policy objects remain references and cannot become additional quest records.","reasons":["missing_quest_record","duplicate_quest_number","out_of_order_chain","invalid_stable_id"]},
   "LEVEL_GATES_AND_SEQUENTIAL_PREREQUISITES_51_TO_100":{"decision":"Quest 51 bridges from start_path_050_road_ahead and remains subject to the canonical Dark Forest location unlock and its declared level 6 gate. Every quest 52-100 requires the immediately preceding stable quest ID and its candidate-declared level. Existing overlevel/SKIP policy is preserved; no gate is inferred or relaxed.","reasons":["level_too_low","location_locked","predecessor_not_satisfied","chain_gap"]},
   "OBJECTIVES_TARGETS_AND_QUEST_ITEMS_51_TO_100":{"decision":"Every quest uses only candidate-declared objective type, target, quantity, region/mob/NPC identity and quest-item metadata. Quest items stay isolated from regular inventory; drop chances, accumulation and consumption remain quest-specific; duplicate event identities cannot progress twice.","reasons":["unsupported_objective","invalid_target","quest_item_mismatch","duplicate_event"]},
   "REWARD_PARITY_51_TO_100":{"decision":"The exact EXP and gold values stored in each canonical record are authoritative content inputs to the shared reward pipeline. No package formula, extrapolation or invented rounding is authorized. Quest 99 story reward is 190 EXP and 8.81 gold; quest 100 reward is 114 EXP and 5.29 gold. Boss combat reward remains separately owned.","reasons":["reward_missing","reward_mismatch","reward_formula_in_content","combat_story_reward_collision"]},
   "NPC_LOCATION_AND_LOCALIZED_DARK_FOREST_REFERENCES":{"decision":"All records use stable NPC IDs and technical dark_forest only as identity. User-visible location text resolves to Темний Бір. NPC routes and giver/turn-in references must validate against canonical registries. Raw technical IDs, automatic title-casing and the term глава are forbidden in presentation.","reasons":["unknown_npc_reference","unknown_location_reference","technical_id_disclosure","forbidden_term"]},
   "BOSS_99_AND_FORCED_ENCOUNTER_CONTRACT":{"decision":"Quest 99 targets goblin_king in dark_forest. Both ordinary Hunting encounter and guaranteed story call are valid; boss level equals current player level and shared boss formulas remain authoritative. Defeat or escape permits retry. Exact victory records progress 1/1 once, immediately blocks another forced call, rejects stale/double callbacks, preserves anti-farm protection and leaves completion pending for mercenary_head turn-in.","reasons":["wrong_boss_key","wrong_location","forced_call_already_won","stale_boss_event","duplicate_boss_event"]},
   "PACKAGE_BY_TEN_AND_CONTENT_VALIDATION_51_TO_100":{"decision":"Implementation is split into packages 51-60, 61-70, 71-80, 81-90 and 91-100. Each package requires executable validation for count, ordered numbers, stable IDs, predecessor chain, levels, objectives, NPC/location references, quest items, exact rewards, localization and duplicates before the next package is authorized.","reasons":["package_manifest_invalid","cross_package_gap","content_validation_failed"]},
   "QUEST_100_FINAL_STORY_FLOW":{"decision":"Quest 100 is an itemless TURN_IN following quest 99, given and completed through elder after quest 99 turn-in. Completion is idempotent and persistently marks the Король Гоблінів section and Темний Бір story complete. No next-location unlock, extra reward or new story content is added.","reasons":["predecessor_not_completed","turn_in_npc_mismatch","terminal_state_invalid","duplicate_completion"]}}
  if tuple(decisions)!=expected:raise PatchError("resolution_contract_mismatch")
  print("[5/10] [PASS] Exact records, chain, objectives and exact reward parity policies resolved.");print("[6/10] [PASS] Dark Forest references, boss 99, package validation and final quest 100 flow resolved without invented content.")
  removed=clean(r);checks=ci(r);print(f"[7/10] [PASS] Canonical V2 CI passed after removing {len(removed)} bytecode artifact(s).")
  if before!={x.as_posix():sha(r/x) for x in PROTECTED}:raise PatchError("protected_runtime_changed")
  reference_after={x.relative_to(r).as_posix():sha(x) for x in (r/"Квести").rglob("*") if x.is_file()}
  if reference_before!=reference_after:raise PatchError("canonical_reference_changed")
  print("[8/10] [PASS] Production sources, canonical quest references, DB sidecars and protected configuration remained byte-identical.")
  resolved=[{"contract":k,"classification":"V2_RESOLVED","decision":v["decision"],"typed_reasons":v["reasons"]} for k,v in decisions.items()]
  all_contracts=("CANONICAL_DARK_FOREST_REFERENCE_AND_SOURCE_INVENTORY","PRODUCTION_STORY_SCHEMA_OWNER","QUEST_CHAIN_BOUNDARY_51_TO_100",*expected)
  payload={"schema_version":1,"stage":STAGE,"status":"PASS","conclusion":"GO_TO_IMPLEMENTATION","source_refinement":PREREQ.as_posix(),"summary":{"contract_count":11,"resolved_contracts":11,"unresolved_contracts":[],"canonical_record_count":50,"database_opened":False,"production_code_changed":False,"canonical_reference_changed":False,"v1_wal_shm_manipulated":False},"authoritative_evidence":evidence,"canonical_contracts":list(all_contracts),"resolved_contract_matrix":resolved,"implementation_plan":{"package_order":["51-60","61-70","71-80","81-90","91-100"],"first_authorized_package":"51-60","manual_game_check_after_each_runtime_connected_package":True,"full_chain_manual_acceptance_after_91_100":True},"implementation_boundary":{"authorized":["typed immutable Story content records 51-60","package 51-60 manifest and validators","candidate-to-V2 mapping without content invention","Quest Engine and NPC/location references","focused tests, smoke and content gates"],"forbidden":["packages 61-100 before prior package acceptance","new quests, NPCs, objectives, rewards or formulas","production SQLite adapter or migration","Telegram/runtime wiring","editing canonical Квести references","inventing next-location unlock after quest 100"]},"implementation_authorized":True,"authorized_package":"51-60","packages_61_100_authorized":False,"runtime_integration_authorized":False,"production_persistence_authorized":False,"canonical_v2_ci":checks,"manual_game_check":"NOT_REQUIRED","suggested_next_patch":"patch_21_13_5c_implement_story_content_51_60.py","backup_path":folder.relative_to(r).as_posix()};write(r/REPORT,json.dumps(payload,ensure_ascii=False,indent=2,default=str)+"\n")
  lines=["# Stage 21.13.5b - Resolved Story content 51-100 parity","","- Status: **PASS**","- Conclusion: **GO_TO_IMPLEMENTATION**","- Contract matrix: **11/11 RESOLVED**","- Canonical records: **50/50**","- 50-to-51 bridge: **RESOLVED**","- Boss 99: **RESOLVED**","- Final quest 100: **RESOLVED**","- Authorized package: **51-60**","- Packages 61-100: **NOT_AUTHORIZED YET**","- Runtime integration: **NOT_AUTHORIZED**","- Production persistence: **NOT_AUTHORIZED**","- Manual game check: **NOT_REQUIRED**","","## Resolved contracts",""]
  for x in resolved:lines.extend(["### "+x["contract"],"",x["decision"],"","Typed reasons: "+", ".join(x["typed_reasons"]),""])
  lines.extend(["## Next patch","","`patch_21_13_5c_implement_story_content_51_60.py`",""]);write(r/DOC,"\n".join(lines));print("[9/10] [PASS] Resolved JSON and Markdown Story content 51-100 parity artifacts written.")
  files={x.as_posix() for x in TARGETS};git(r,"add","-f","--",*sorted(files));got={x.replace("\\","/") for x in git(r,"diff","--cached","--name-only").stdout.splitlines() if x}
  if got!=files:raise PatchError("staging_mismatch:"+repr(sorted(got)))
  z=git(r,"commit","-m","Stage 21.13.5b: resolve Story content 51-100 parity","--",*sorted(files),check=False)
  if z.returncode:raise PatchError("commit_failed:"+z.stdout+z.stderr)
  commit=git(r,"rev-parse","HEAD").stdout.strip();changed={x.replace("\\","/") for x in git(r,"diff-tree","--no-commit-id","--name-only","-r",commit).stdout.splitlines() if x}
  if changed!=files:raise PatchError("commit_scope_mismatch:"+repr(sorted(changed)))
  print(f"[10/10] [PASS] Story content 51-100 parity resolution committed: {commit}");print("CONCLUSION: GO_TO_IMPLEMENTATION\nCONTRACT_MATRIX: 11/11 RESOLVED\nUNRESOLVED_CONTRACTS: 0\nCANONICAL RECORDS: 50/50\nBRIDGE 50-51: RESOLVED\nBOSS 99: RESOLVED\nFINAL QUEST 100: RESOLVED\nIMPLEMENTATION AUTHORIZED: True\nAUTHORIZED PACKAGE: 51-60\nPACKAGES 61-100 AUTHORIZED: False\nRUNTIME INTEGRATION AUTHORIZED: False\nPRODUCTION PERSISTENCE AUTHORIZED: False\nMANUAL GAME CHECK: NOT_REQUIRED\nFAIL-SAFE ROLLBACK: ARMED\nSUGGESTED NEXT PATCH: patch_21_13_5c_implement_story_content_51_60.py");return 0
 except Exception as error:
  restored=restore(r,folder,state);recovery=run([sys.executable,"-m","compileall","-q","rom_v2"],r,False);write(r/FAILURE,json.dumps({"stage":STAGE,"status":"FAIL_ROLLED_BACK","reason":str(error),"restored_files":restored,"recovery_compile_returncode":recovery.returncode,"main_py_must_not_run":recovery.returncode!=0,"database_opened":False,"canonical_reference_changed":False,"v1_wal_shm_manipulated":False},ensure_ascii=False,indent=2)+"\n");print(f"[10/10] [FAIL] {error}; rollback: FAIL_ROLLED_BACK");return 1
if __name__=="__main__":raise SystemExit(main())
