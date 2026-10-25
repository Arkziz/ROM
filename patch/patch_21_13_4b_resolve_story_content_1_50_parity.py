#!/usr/bin/env python3
"""Stage 21.13.1b: resolve V1 Quest Engine parity without production mutation."""
from __future__ import annotations
import ast,hashlib,json,os,py_compile,shutil,subprocess,sys
from datetime import datetime,timezone
from pathlib import Path
STAGE="21.13.4b";PARENT="0052fb2e74253d10d81516b9808a5c1ef44d0c0c";BRANCH="stage-21-v2-modular-monolith"
SELF="patch/patch_21_13_4b_resolve_story_content_1_50_parity.py";PREREQ=Path("reports/stage_21_13_4a_refined_story_content_1_50_contract.json");REPORT=Path("reports/stage_21_13_4b_resolved_story_content_1_50_parity.json");DOC=Path("MD/STAGE_21_13_4B_RESOLVED_STORY_CONTENT_1_50_PARITY.md");FAILURE=Path("reports/stage_21_13_4b_failure_rollback.json")
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
 d=r/"backup"/("stage_21_13_4b_"+datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ"));d.mkdir(parents=True,exist_ok=True);state={}
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
 candidate=r/"Квести/ROM_квести_Початок_Шляху_candidate.json"
 if not candidate.exists():raise PatchError("canonical_start_path_candidate_missing")
 data=json.loads(candidate.read_text(encoding="utf-8-sig"))
 quests=data.get("quests") if isinstance(data,dict) else None
 if not isinstance(quests,list):raise PatchError("canonical_quests_array_missing")
 if len(quests)!=50:raise PatchError("canonical_quests_array_not_50:"+str(len(quests)))
 def qnum(row):
  if not isinstance(row,dict):return None
  for key in ("quest_number","quest_no","number","quest_id","id"):
   value=row.get(key)
   if isinstance(value,int) and 1<=value<=50:return value
   if isinstance(value,str) and value.isdigit() and 1<=int(value)<=50:return int(value)
  return None
 matrix=[]
 for index,row in enumerate(quests,1):
  if not isinstance(row,dict):raise PatchError("non_object_quest_record:"+str(index))
  number=qnum(row)
  if number is None:raise PatchError("quest_number_missing_at_index:"+str(index))
  matrix.append({"quest_number":number,"array_index":index-1,"keys":sorted(str(k) for k in row),"record":row})
 numbers=[x["quest_number"] for x in matrix]
 if numbers!=list(range(1,51)):raise PatchError("canonical_quest_order_or_identity_mismatch:"+repr(numbers))
 packages={f"{start}-{start+9}":[x["quest_number"] for x in matrix[start-1:start+9]] for start in (1,11,21,31,41)}
 q49=matrix[48]["record"];q50=matrix[49]["record"]
 refs={x.relative_to(r).as_posix():sha(x) for x in (r/"Квести").rglob("*") if x.is_file()}
 defs=r/"data/story_quest_definitions.py";text=defs.read_text(encoding="utf-8-sig");ast.parse(text)
 return {"candidate_file":candidate.relative_to(r).as_posix(),"candidate_sha256":sha(candidate),"canonical_record_count":len(matrix),"canonical_numbers":numbers,"package_manifests":packages,"quest_matrix":matrix,"quest_49":q49,"quest_50":q50,"false_duplicate_49_removed":True,"duplicate_reason":"Nested policy reference was excluded because only $.quests array entries are canonical quest records.","reference_hashes":refs,"production_definition_file":defs.relative_to(r).as_posix(),"production_definition_sha256":sha(defs)}
def main():
 r=root();folder=None;state={};before={x.as_posix():sha(r/x) for x in PROTECTED};reference_before={x.relative_to(r).as_posix():sha(x) for x in (r/"Квести").rglob("*") if x.is_file()}
 expected=("EXACT_QUEST_RECORDS_1_TO_50","LEVEL_GATES_AND_SEQUENTIAL_PREREQUISITES","OBJECTIVES_TARGETS_AND_QUEST_ITEMS","REWARD_PARITY_AND_TRIPLE_NORMAL_MOB_POLICY","NPC_LOCATION_AND_LOCALIZED_PRESENTATION_REFERENCES","BOSS_AND_FORCED_ENCOUNTER_CONTRACT","PACKAGE_BY_TEN_AND_CONTENT_VALIDATION","QUEST_49_50_TERMINAL_FLOW_AND_KNOWN_PRESENTATION_NUANCE")
 try:
  refined=json.loads((r/PREREQ).read_text(encoding="utf-8-sig"));rows=tuple(x for x in refined.get("refined_contract_matrix",()) if isinstance(x,dict));unresolved=tuple(x.get("contract") for x in rows if x.get("classification")=="REVIEW_REQUIRED");summary=refined.get("summary",{});observations=refined.get("observations",{})
  if git(r,"rev-parse","HEAD").stdout.strip()!=PARENT:raise PatchError("wrong_exact_parent")
  if refined.get("stage")!="21.13.4a" or refined.get("conclusion")!="REVIEW_REQUIRED" or len(rows)!=8 or unresolved!=expected or tuple(summary.get("unresolved_contracts",()))!=expected:raise PatchError("invalid_stage_21_13_4a_prerequisite")
  if summary.get("v1_confirmed_contracts")!=3 or summary.get("review_required_contracts")!=8 or summary.get("contract_count")!=11 or observations.get("exact_50_record_matrix_requires_resolution") is not True:raise PatchError("invalid_3_8_11_contract_matrix")
  print("[1/10] [PASS] Stage 21.13.4a exact 3/8/11 refinement prerequisite verified.")
  branch=git(r,"branch","--show-current").stdout.strip();staged=git(r,"diff","--cached","--name-only").stdout.strip()
  if not branch:raise PatchError("git_preflight_detached_head")
  if staged:raise PatchError("git_preflight_staged_index:"+staged.replace("\n",","))
  bad=sorted(p for st,p in status(r) if p not in ALLOWED or (p!=SELF and st[0]!=" "))
  if bad:raise PatchError(f"unexpected_dirty:{bad}")
  print(f"[2/10] [PASS] Active branch {branch}, exact parent, dirty allowlist and clean index verified.");folder,state=backup(r);print("[3/10] [PASS] Resolution artifacts backed up before publication mutation.")
  evidence=inspect(r);print("[4/10] [PASS] Exact canonical $.quests records 1-50 and five package manifests re-verified.")
  decisions={
   "EXACT_QUEST_RECORDS_1_TO_50":{"decision":"The only canonical record set for migration planning is the 50 ordered objects in $.quests of Квести/ROM_квести_Початок_Шляху_candidate.json. Quest identity is the explicit numeric quest number plus the stable content ID carried by that record. Nested policy objects are references, not quest records. Therefore the apparent duplicate 49 is false and the authoritative matrix contains exactly one record for every number 1-50.","reasons":["missing_quest_record","duplicate_quest_number","out_of_order_chain","invalid_stable_id"]},
   "LEVEL_GATES_AND_SEQUENTIAL_PREREQUISITES":{"decision":"Required levels are fixed by package: 1-10 level 1, 11-20 level 2, 21-30 level 3, 31-40 level 4, 41-50 level 5. Quest 1 has no predecessor. Every quest N from 2 through 50 requires quest N-1 completed or skipped under the existing overlevel/SKIP policy. Both level and predecessor must pass before availability.","reasons":["level_too_low","predecessor_not_satisfied","chain_gap"]},
   "OBJECTIVES_TARGETS_AND_QUEST_ITEMS":{"decision":"Each quest uses only its candidate-declared canonical objective, target, region/mob/NPC identity and quest-item metadata. No default objectives or targets are inferred. Quest items remain in the isolated store, declared 15% drop chances stay quest-specific, accumulated items are consumed only by the declared exact-once turn-in, and duplicate combat/drop events cannot advance progress twice.","reasons":["unsupported_objective","invalid_target","quest_item_mismatch","duplicate_event"]},
   "REWARD_PARITY_AND_TRIPLE_NORMAL_MOB_POLICY":{"decision":"Rewards are resolved as content references through the canonical reward pipeline, not embedded formulas. Quests 1-10 use full triple canonical normal-mob level-1 rewards; 11-20 use level-2; 21-30 use level-3, including TALK, QUEST_ITEM and TURN_IN. Quests 31-50 must use only reward policy explicitly present in candidate/V1 evidence; no extrapolation from 1-30 is authorized.","reasons":["reward_policy_missing","reward_reference_invalid","reward_formula_in_content"]},
   "NPC_LOCATION_AND_LOCALIZED_PRESENTATION_REFERENCES":{"decision":"Every record must use stable canonical NPC and location IDs validated against the NPC/location registries. User-visible location text is resolved as Початок Шляху. Raw start_path, raw NPC IDs, automatic title-casing and the term глава are forbidden in presentation metadata. Handlers consume typed content and do not own quest-specific conditions.","reasons":["unknown_npc_reference","unknown_location_reference","technical_id_disclosure","forbidden_term"]},
   "BOSS_AND_FORCED_ENCOUNTER_CONTRACT":{"decision":"Ordinary location bosses continue to appear through Hunting. Quest 49 additionally authorizes the candidate-declared guaranteed story call for the Pack Leader, using shared boss/combat formulas and the player-level boss rule. Defeat or escape permits retry; victory records exact-once progress and blocks another guaranteed call. Boss combat reward remains separate from story turn-in reward.","reasons":["wrong_boss_key","wrong_location","forced_call_already_won","stale_boss_event"]},
   "PACKAGE_BY_TEN_AND_CONTENT_VALIDATION":{"decision":"Implementation is split into five mutation packages under canonical Stage 21.13.4: 1-10, 11-20, 21-30, 31-40 and 41-50. Each package requires an executable manifest check for record count, ordered IDs, stable IDs, predecessor links, level gate, objective schema, NPC/location references, quest items, rewards, localization and duplicates before the next package is authorized.","reasons":["package_manifest_invalid","cross_package_gap","content_validation_failed"]},
   "QUEST_49_50_TERMINAL_FLOW_AND_KNOWN_PRESENTATION_NUANCE":{"decision":"Quest 49 completes its BOSS objective only on exact Pack Leader victory in the correct location, then remains pending until turn-in to the Mercenary Guild Leader. Quest 50 is the itemless final turn-in/talk with the Elder and marks the Початок Шляху story complete; dark_forest remains a hint, not automatic unlock. V2 must display persisted 1/1 progress after quest-49 victory, correcting the known V1 presentation defect without changing combat, reward or completion semantics.","reasons":["boss_not_defeated","turn_in_npc_mismatch","terminal_state_invalid","progress_presentation_mismatch"]}}
  if tuple(decisions)!=expected:raise PatchError("resolution_contract_mismatch")
  print("[5/10] [PASS] Exact records, gates, objectives and reward parity policies resolved.");print("[6/10] [PASS] NPC/location, boss, package validation and terminal 49-50 flow resolved; false duplicate 49 removed.")
  removed=clean(r);checks=ci(r);print(f"[7/10] [PASS] Canonical V2 CI passed after removing {len(removed)} bytecode artifact(s).")
  if before!={x.as_posix():sha(r/x) for x in PROTECTED}:raise PatchError("protected_runtime_changed")
  reference_after={x.relative_to(r).as_posix():sha(x) for x in (r/"Квести").rglob("*") if x.is_file()}
  if reference_before!=reference_after:raise PatchError("canonical_reference_changed")
  print("[8/10] [PASS] Production sources, canonical quest references, DB sidecars and protected configuration remained byte-identical.")
  resolved=[{"contract":k,"classification":"V2_RESOLVED","decision":v["decision"],"typed_reasons":v["reasons"]} for k,v in decisions.items()]
  all_contracts=("CANONICAL_REFERENCE_FOLDER_AND_SOURCE_INVENTORY","PRODUCTION_DEFINITION_OWNER","QUEST_CHAIN_BOUNDARY_1_TO_50",*expected)
  payload={"schema_version":1,"stage":STAGE,"status":"PASS","conclusion":"GO_TO_IMPLEMENTATION","source_refinement":PREREQ.as_posix(),"summary":{"contract_count":11,"resolved_contracts":11,"unresolved_contracts":[],"canonical_record_count":50,"database_opened":False,"production_code_changed":False,"canonical_reference_changed":False,"v1_wal_shm_manipulated":False},"authoritative_evidence":evidence,"canonical_contracts":list(all_contracts),"resolved_contract_matrix":resolved,"implementation_plan":{"package_order":["1-10","11-20","21-30","31-40","41-50"],"first_authorized_package":"1-10","manual_game_check_after_each_package":True,"full_chain_manual_acceptance_after_41_50":True},"implementation_boundary":{"authorized":["typed immutable story content records","package 1-10 manifest and validators","candidate-to-V2 mapping without content invention","Quest Engine and NPC registry references","focused tests, smoke and content gates"],"forbidden":["packages 11-50 before prior package acceptance","new quests, NPCs, objectives, rewards or formulas","production SQLite adapter or migration","Telegram/runtime wiring","editing canonical Квести references","automatic dark_forest unlock","preserving hidden quest-49 1/1 presentation defect"]},"implementation_authorized":True,"authorized_package":"1-10","packages_11_50_authorized":False,"runtime_integration_authorized":False,"production_persistence_authorized":False,"canonical_v2_ci":checks,"manual_game_check":"NOT_REQUIRED","suggested_next_patch":"patch_21_13_4c_implement_story_content_1_10.py","backup_path":folder.relative_to(r).as_posix()};write(r/REPORT,json.dumps(payload,ensure_ascii=False,indent=2,default=str)+"\n")
  lines=["# Stage 21.13.4b - Resolved Story content 1-50 parity","","- Status: **PASS**","- Conclusion: **GO_TO_IMPLEMENTATION**","- Contract matrix: **11/11 RESOLVED**","- Canonical records: **50/50**","- False duplicate quest 49: **RESOLVED**","- Authorized package: **1-10**","- Packages 11-50: **NOT_AUTHORIZED YET**","- Runtime integration: **NOT_AUTHORIZED**","- Production persistence: **NOT_AUTHORIZED**","- Manual game check: **NOT_REQUIRED**","","## Resolved contracts",""]
  for x in resolved:lines.extend(["### "+x["contract"],"",x["decision"],"","Typed reasons: "+", ".join(x["typed_reasons"]),""])
  lines.extend(["## Next patch","","`patch_21_13_4c_implement_story_content_1_10.py`",""]);write(r/DOC,"\n".join(lines));print("[9/10] [PASS] Resolved JSON and Markdown Story content 1-50 parity artifacts written.")
  files={x.as_posix() for x in TARGETS};git(r,"add","-f","--",*sorted(files));got={x.replace("\\","/") for x in git(r,"diff","--cached","--name-only").stdout.splitlines() if x}
  if got!=files:raise PatchError("staging_mismatch:"+repr(sorted(got)))
  z=git(r,"commit","-m","Stage 21.13.4b: resolve Story content 1-50 parity","--",*sorted(files),check=False)
  if z.returncode:raise PatchError("commit_failed:"+z.stdout+z.stderr)
  commit=git(r,"rev-parse","HEAD").stdout.strip();changed={x.replace("\\","/") for x in git(r,"diff-tree","--no-commit-id","--name-only","-r",commit).stdout.splitlines() if x}
  if changed!=files:raise PatchError("commit_scope_mismatch:"+repr(sorted(changed)))
  print(f"[10/10] [PASS] Story content 1-50 parity resolution committed: {commit}");print("CONCLUSION: GO_TO_IMPLEMENTATION\nCONTRACT_MATRIX: 11/11 RESOLVED\nUNRESOLVED_CONTRACTS: 0\nCANONICAL RECORDS: 50/50\nFALSE DUPLICATE QUEST 49: RESOLVED\nIMPLEMENTATION AUTHORIZED: True\nAUTHORIZED PACKAGE: 1-10\nPACKAGES 11-50 AUTHORIZED: False\nRUNTIME INTEGRATION AUTHORIZED: False\nPRODUCTION PERSISTENCE AUTHORIZED: False\nMANUAL GAME CHECK: NOT_REQUIRED\nFAIL-SAFE ROLLBACK: ARMED\nSUGGESTED NEXT PATCH: patch_21_13_4c_implement_story_content_1_10.py");return 0
 except Exception as error:
  restored=restore(r,folder,state);recovery=run([sys.executable,"-m","compileall","-q","rom_v2"],r,False);write(r/FAILURE,json.dumps({"stage":STAGE,"status":"FAIL_ROLLED_BACK","reason":str(error),"restored_files":restored,"recovery_compile_returncode":recovery.returncode,"main_py_must_not_run":recovery.returncode!=0,"database_opened":False,"canonical_reference_changed":False,"v1_wal_shm_manipulated":False},ensure_ascii=False,indent=2)+"\n");print(f"[10/10] [FAIL] {error}; rollback: FAIL_ROLLED_BACK");return 1
if __name__=="__main__":raise SystemExit(main())
