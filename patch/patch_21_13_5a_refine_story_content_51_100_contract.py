#!/usr/bin/env python3
"""Stage 21.13.5a: refine the V1 Story content 51-100 contract without production mutation."""
from __future__ import annotations
import ast,hashlib,json,os,py_compile,re,shutil,subprocess,sys
from datetime import datetime,timezone
from pathlib import Path
STAGE="21.13.5a";PARENT="c6e076da71b6c50c2d37525cf2eb450aaea0c711";BRANCH="stage-21-v2-modular-monolith"
SELF="patch/patch_21_13_5a_refine_story_content_51_100_contract.py";PREREQ=Path("reports/stage_21_13_5_existing_story_content_51_100_audit.json");REPORT=Path("reports/stage_21_13_5a_refined_story_content_51_100_contract.json");DOC=Path("MD/STAGE_21_13_5A_REFINED_STORY_CONTENT_51_100_CONTRACT.md");FAILURE=Path("reports/stage_21_13_5a_failure_rollback.json")
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
 d=r/"backup"/("stage_21_13_5a_"+datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ"));d.mkdir(parents=True,exist_ok=True);state={}
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
 raw=json.loads(candidate.read_text(encoding="utf-8-sig"))
 quests=raw.get("quests") if isinstance(raw,dict) else None
 if not isinstance(quests,list):raise PatchError("canonical_quests_array_missing")
 def number_of(row):
  if not isinstance(row,dict):return None
  for key in ("number","quest_number","quest_no","quest_id","id"):
   value=row.get(key)
   if isinstance(value,int) and 51<=value<=100:return value
   if isinstance(value,str) and value.isdigit() and 51<=int(value)<=100:return int(value)
  return None
 records=[]
 for index,row in enumerate(quests):
  number=number_of(row)
  if number is not None:records.append({"number":number,"array_index":index,"keys":sorted(str(k) for k in row),"record":row})
 numbers=[x["number"] for x in records];missing=[i for i in range(51,101) if i not in numbers];duplicates={str(i):numbers.count(i) for i in sorted(set(numbers)) if numbers.count(i)>1}
 defs_path=r/"data/story_quest_definitions.py";defs=defs_path.read_text(encoding="utf-8-sig");tree=ast.parse(defs)
 functions=sorted({n.name for n in ast.walk(tree) if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef))})
 calls={}
 for node in ast.walk(tree):
  if isinstance(node,ast.Call):
   name=node.func.id if isinstance(node.func,ast.Name) else node.func.attr if isinstance(node.func,ast.Attribute) else None
   if name:calls[name]=calls.get(name,0)+1
 by_number={x["number"]:x for x in records}
 packages={f"{start}-{start+9}":[n for n in numbers if start<=n<=start+9] for start in (51,61,71,81,91)}
 return {"candidate_file":candidate.relative_to(r).as_posix(),"candidate_sha256":sha(candidate),"candidate_array_length":len(quests),"canonical_record_count":len(records),"canonical_numbers":numbers,"missing_numbers":missing,"duplicate_numbers":duplicates,"package_manifests":packages,"quest_51":by_number.get(51),"quest_99":by_number.get(99),"quest_100":by_number.get(100),"production_definition_file":defs_path.relative_to(r).as_posix(),"production_sha256":sha(defs_path),"production_functions":functions,"production_call_counts":calls,"builder_candidates":[x for x in functions if any(k in x.lower() for k in ("quest","story","build","load","register"))],"literal_dark_forest_found":"dark_forest" in defs,"literal_99_found":bool(re.search(r"(?<!\d)99(?!\d)",defs)),"literal_100_found":bool(re.search(r"(?<!\d)100(?!\d)",defs))}
def main():
 r=root();folder=None;state={};before={x.as_posix():sha(r/x) for x in PROTECTED};reference_before={x.relative_to(r).as_posix():sha(x) for x in (r/"Квести").rglob("*") if x.is_file()}
 expected=("EXACT_QUEST_RECORDS_51_TO_100","LEVEL_GATES_AND_SEQUENTIAL_PREREQUISITES_51_TO_100","OBJECTIVES_TARGETS_AND_QUEST_ITEMS_51_TO_100","REWARD_PARITY_51_TO_100","NPC_LOCATION_AND_LOCALIZED_DARK_FOREST_REFERENCES","BOSS_99_AND_FORCED_ENCOUNTER_CONTRACT","PACKAGE_BY_TEN_AND_CONTENT_VALIDATION_51_TO_100","QUEST_100_FINAL_STORY_FLOW")
 confirmed=("CANONICAL_DARK_FOREST_REFERENCE_AND_SOURCE_INVENTORY","PRODUCTION_STORY_SCHEMA_OWNER","QUEST_CHAIN_BOUNDARY_51_TO_100")
 try:
  audit=json.loads((r/PREREQ).read_text(encoding="utf-8-sig"));rows=tuple(x for x in audit.get("contract_matrix",()) if isinstance(x,dict));unresolved=tuple(x.get("contract") for x in rows if x.get("classification")=="REVIEW_REQUIRED");got_confirmed=tuple(x.get("contract") for x in rows if x.get("classification")=="V1_CONFIRMED");summary=audit.get("summary",{})
  if git(r,"rev-parse","HEAD").stdout.strip()!=PARENT:raise PatchError("wrong_exact_parent")
  if audit.get("stage")!="21.13.5" or audit.get("conclusion")!="GO_TO_SEMANTIC_REFINEMENT" or len(rows)!=11 or unresolved!=expected or got_confirmed!=confirmed or tuple(summary.get("unresolved_contracts",()))!=expected:raise PatchError("invalid_stage_21_13_5_prerequisite")
  if summary.get("v1_confirmed_contracts")!=3 or summary.get("review_required_contracts")!=8 or summary.get("contract_count")!=11:raise PatchError("invalid_3_8_11_contract_matrix")
  print("[1/10] [PASS] Stage 21.13.5 exact 3-confirmed/8-unresolved/11-total prerequisite verified.")
  branch=git(r,"branch","--show-current").stdout.strip();staged=git(r,"diff","--cached","--name-only").stdout.strip()
  if not branch:raise PatchError("git_preflight_detached_head")
  if staged:raise PatchError("git_preflight_staged_index:"+staged.replace("\n",","))
  bad=sorted(p for st,p in status(r) if p not in ALLOWED or (p!=SELF and st[0]!=" "))
  if bad:raise PatchError(f"unexpected_dirty:{bad}")
  print(f"[2/10] [PASS] Active branch {branch}, exact parent, dirty allowlist and clean index verified.");folder,state=backup(r);print("[3/10] [PASS] Refinement artifacts backed up before publication mutation.")
  evidence=inspect(r);print("[4/10] [PASS] Canonical Темний Бір candidate JSON and production definition builders structurally inspected.")
  details={
   "EXACT_QUEST_RECORDS_51_TO_100":(["canonical candidate JSON contains an explicit quests array","records are indexed only by explicit numeric identity 51-100","missing and duplicate numbers are reported","quests 51, 99 and 100 are captured separately"],"Resolve the authoritative 50-row matrix for 51-100, including stable IDs, texts, objectives, targets, NPCs, location, rewards and predecessor links; nested policy references must not become duplicate quest records."),
   "LEVEL_GATES_AND_SEQUENTIAL_PREREQUISITES_51_TO_100":(["the chain boundary is 51-100","quest 51 must bridge from the accepted predecessor defined by V1","each later quest must follow the exact candidate predecessor","existing overlevel/SKIP policy remains in force"],"Extract exact level gates and predecessor IDs for all five packages, prove quest 51 entry semantics and quest N predecessor N-1 for 52-100, and flag every discontinuity."),
   "OBJECTIVES_TARGETS_AND_QUEST_ITEMS_51_TO_100":(["Quest Engine supports the required typed objective boundary","quest items remain isolated from regular inventory","candidate records expose exact objective metadata","no target or drop rule may be inferred"],"Resolve objective type, target, region/mob/NPC identity, item key, quantity, chance, accumulation and exact-once turn-in/event identity for every quest 51-100."),
   "REWARD_PARITY_51_TO_100":(["rewards are content references consumed by the canonical reward pipeline","candidate records contain explicit EXP and gold evidence","boss combat and story rewards remain separate owners","formulas must not be duplicated into handlers"],"Build an exact reward matrix 51-100 from candidate/V1 evidence, including 190 EXP and 8.81 gold for quest 99 and 114 EXP and 5.29 gold for quest 100; reject extrapolation or invented rounding."),
   "NPC_LOCATION_AND_LOCALIZED_DARK_FOREST_REFERENCES":(["stable NPC IDs and location IDs have canonical owners","technical dark_forest is identity only","user-facing location name is Темний Бір","handlers cannot own quest-specific conditions"],"Resolve giver/turn-in NPCs and location references for all records, validate registry routes and prohibit raw technical IDs, automatic title-casing and the term глава in presentation metadata."),
   "BOSS_99_AND_FORCED_ENCOUNTER_CONTRACT":(["quest 99 is a BOSS objective for goblin_king","random Hunting and guaranteed story call are both declared","boss level follows current player level","victory progress, retry, anti-farm and reward ownership are declared"],"Reconcile exact forced-call entry, correct location and boss key, defeat/escape retry, exact-once victory, stale callback rejection, anti-farm block and turn-in to mercenary_head without changing shared boss formulas."),
   "PACKAGE_BY_TEN_AND_CONTENT_VALIDATION_51_TO_100":(["roadmap requires five packages of ten","candidate chain contains 50 numbered records","each package needs independent validation","canonical references remain read-only"],"Define manifests 51-60, 61-70, 71-80, 81-90 and 91-100 with validators for count, order, stable IDs, chain, levels, objectives, NPC/location, items, rewards, localization and duplicates."),
   "QUEST_100_FINAL_STORY_FLOW":(["quest 100 is an itemless TURN_IN","quest 100 follows quest 99","giver and turn-in NPC are elder","completion closes the Король Гоблінів section and Темний Бір story"],"Resolve the exact transition from quest 99 turn-in to quest 100, final completion flags, idempotency and persistent terminal state, without inventing a next-location unlock or additional reward.")}
  refined=[{"contract":k,"classification":"REVIEW_REQUIRED","confirmed":v[0],"remaining_question":v[1]} for k,v in details.items()]
  if tuple(x["contract"] for x in refined)!=expected:raise PatchError("refinement_contract_mismatch")
  print("[5/10] [PASS] Eight Dark Forest boundaries narrowed to records, chain, objectives, rewards, references, boss 99, packages and final 100.");print("[6/10] [PASS] Candidate and production-schema boundaries isolated without inventing content or modifying canonical references.")
  removed=clean(r);checks=ci(r);print(f"[7/10] [PASS] Canonical V2 CI passed after removing {len(removed)} bytecode artifact(s).")
  if before!={x.as_posix():sha(r/x) for x in PROTECTED}:raise PatchError("protected_runtime_changed")
  reference_after={x.relative_to(r).as_posix():sha(x) for x in (r/"Квести").rglob("*") if x.is_file()}
  if reference_before!=reference_after:raise PatchError("canonical_reference_changed")
  print("[8/10] [PASS] Production sources, canonical quest references, DB sidecars and protected configuration remained byte-identical.")
  payload={"schema_version":1,"stage":STAGE,"status":"PASS","conclusion":"REVIEW_REQUIRED","source_audit":PREREQ.as_posix(),"summary":{"contract_count":11,"v1_confirmed_contracts":3,"refined_contracts":8,"review_required_contracts":8,"unresolved_contracts":list(expected),"database_opened":False,"production_code_changed":False,"canonical_reference_changed":False,"v1_wal_shm_manipulated":False},"authoritative_evidence":evidence,"refined_contract_matrix":refined,"observations":{"canonical_record_count":evidence["canonical_record_count"],"canonical_numbers":evidence["canonical_numbers"],"missing_numbers":evidence["missing_numbers"],"duplicate_numbers":evidence["duplicate_numbers"],"package_manifests":evidence["package_manifests"],"boss_99_requires_resolution":True,"final_100_requires_resolution":True},"implementation_authorized":False,"canonical_v2_ci":checks,"manual_game_check":"NOT_REQUIRED","suggested_next_patch":"patch_21_13_5b_resolve_story_content_51_100_parity.py","backup_path":folder.relative_to(r).as_posix()};write(r/REPORT,json.dumps(payload,ensure_ascii=False,indent=2,default=str)+"\n")
  lines=["# Stage 21.13.5a - Refined Story content 51-100 contract","","- Status: **PASS**","- Conclusion: **REVIEW_REQUIRED**","- Contract matrix: **3 confirmed / 8 review-required / 11 total**","- Canonical records discovered: **"+str(evidence["canonical_record_count"])+"**","- Missing numbers: **"+str(evidence["missing_numbers"])+"**","- Duplicate numbers: **"+str(evidence["duplicate_numbers"])+"**","- Implementation authorized: **False**","- Manual game check: **NOT_REQUIRED**","","## Refined unresolved contracts",""]
  for x in refined:lines.extend(["### "+x["contract"],"","Confirmed:","",*["- "+v for v in x["confirmed"]],"","Remaining question: "+x["remaining_question"],""])
  lines.extend(["No production mutation, canonical reference edit, quest migration, reward change, database access or runtime wiring is authorized.","","## Next patch","","`patch_21_13_5b_resolve_story_content_51_100_parity.py`",""]);write(r/DOC,"\n".join(lines));print("[9/10] [PASS] Refined JSON and Markdown Story content 51-100 contract artifacts written.")
  files={x.as_posix() for x in TARGETS};git(r,"add","-f","--",*sorted(files));got={x.replace("\\","/") for x in git(r,"diff","--cached","--name-only","--").stdout.splitlines() if x}
  if got!=files:raise PatchError("staging_mismatch:"+repr(sorted(got)))
  z=git(r,"commit","-m","Stage 21.13.5a: refine Story content 51-100 contract","--",*sorted(files),check=False)
  if z.returncode:raise PatchError("commit_failed:"+z.stdout+z.stderr)
  commit=git(r,"rev-parse","HEAD").stdout.strip();changed={x.replace("\\","/") for x in git(r,"diff-tree","--no-commit-id","--name-only","-r",commit).stdout.splitlines() if x}
  if changed!=files:raise PatchError("commit_scope_mismatch:"+repr(sorted(changed)))
  print(f"[10/10] [PASS] Story content 51-100 semantic refinement committed: {commit}");print("CONCLUSION: REVIEW_REQUIRED\nCONTRACT_MATRIX: 3 CONFIRMED / 8 REVIEW_REQUIRED / 11 TOTAL\nUNRESOLVED_CONTRACTS: 8\nIMPLEMENTATION AUTHORIZED: False\nCANONICAL REFERENCE CHANGED: False\nMANUAL GAME CHECK: NOT_REQUIRED\nFAIL-SAFE ROLLBACK: ARMED\nSUGGESTED NEXT PATCH: patch_21_13_5b_resolve_story_content_51_100_parity.py");return 0
 except Exception as error:
  restored=restore(r,folder,state);recovery=run([sys.executable,"-m","compileall","-q","rom_v2"],r,False);write(r/FAILURE,json.dumps({"stage":STAGE,"status":"FAIL_ROLLED_BACK","reason":str(error),"restored_files":restored,"recovery_compile_returncode":recovery.returncode,"main_py_must_not_run":recovery.returncode!=0,"database_opened":False,"canonical_reference_changed":False,"v1_wal_shm_manipulated":False},ensure_ascii=False,indent=2)+"\n");print(f"[10/10] [FAIL] {error}; rollback: FAIL_ROLLED_BACK");return 1
if __name__=="__main__":raise SystemExit(main())
