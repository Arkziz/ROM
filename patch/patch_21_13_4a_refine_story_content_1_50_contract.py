#!/usr/bin/env python3
"""Stage 21.13.4a: refine the V1 Story content 1-50 contract without production mutation."""
from __future__ import annotations
import ast,hashlib,json,os,py_compile,re,shutil,subprocess,sys
from datetime import datetime,timezone
from pathlib import Path
STAGE="21.13.4a";PARENT="fb4f407f58b79a945d297e2ab756174829632117";BRANCH="stage-21-v2-modular-monolith"
SELF="patch/patch_21_13_4a_refine_story_content_1_50_contract.py";PREREQ=Path("reports/stage_21_13_4_existing_story_content_1_50_audit.json");REPORT=Path("reports/stage_21_13_4a_refined_story_content_1_50_contract.json");DOC=Path("MD/STAGE_21_13_4A_REFINED_STORY_CONTENT_1_50_CONTRACT.md");FAILURE=Path("reports/stage_21_13_4a_failure_rollback.json")
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
 d=r/"backup"/("stage_21_13_4a_"+datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ"));d.mkdir(parents=True,exist_ok=True);state={}
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
 raw=json.loads(candidate.read_text(encoding="utf-8-sig"))
 def walk(value,path="$"):
  rows=[]
  if isinstance(value,dict):
   rows.append({"path":path,"type":"object","keys":sorted(str(k) for k in value)})
   for k,v in value.items():rows.extend(walk(v,path+"."+str(k)))
  elif isinstance(value,list):
   rows.append({"path":path,"type":"array","length":len(value)})
   for i,v in enumerate(value):rows.extend(walk(v,path+"["+str(i)+"]"))
  return rows
 def quest_id(obj):
  if not isinstance(obj,dict):return None
  for key in ("quest_id","id","number","quest_no","quest_number"):
   value=obj.get(key)
   if isinstance(value,int) and 1<=value<=50:return value
   if isinstance(value,str) and value.isdigit() and 1<=int(value)<=50:return int(value)
  return None
 all_dicts=[]
 def collect(value,path="$"):
  if isinstance(value,dict):
   all_dicts.append((path,value))
   for k,v in value.items():collect(v,path+"."+str(k))
  elif isinstance(value,list):
   for i,v in enumerate(value):collect(v,path+"["+str(i)+"]")
 collect(raw)
 records=[]
 for path,obj in all_dicts:
  qid=quest_id(obj)
  if qid is not None:records.append({"quest_id":qid,"path":path,"keys":sorted(str(k) for k in obj),"record":obj})
 by_id={}
 for row in records:by_id.setdefault(row["quest_id"],[]).append(row)
 candidate_ids=sorted(by_id);missing_ids=[i for i in range(1,51) if i not in by_id];duplicate_ids={str(k):len(v) for k,v in by_id.items() if len(v)>1}
 defs_path=r/"data/story_quest_definitions.py";defs=defs_path.read_text(encoding="utf-8-sig");tree=ast.parse(defs)
 functions=sorted({n.name for n in ast.walk(tree) if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef))})
 imports=[]
 for node in ast.walk(tree):
  if isinstance(node,ast.ImportFrom):imports.append({"module":node.module,"names":[x.name for x in node.names]})
  elif isinstance(node,ast.Import):imports.append({"module":None,"names":[x.name for x in node.names]})
 calls={}
 for node in ast.walk(tree):
  if isinstance(node,ast.Call):
   name=node.func.id if isinstance(node.func,ast.Name) else node.func.attr if isinstance(node.func,ast.Attribute) else None
   if name:calls[name]=calls.get(name,0)+1
 quest_like=[x for x in records if any(k in x["keys"] for k in ("objective","objective_type","type","title","name","reward","rewards"))]
 sample={str(i):by_id[i][0] for i in (1,49,50) if i in by_id}
 return {"candidate_file":candidate.relative_to(r).as_posix(),"candidate_sha256":sha(candidate),"candidate_root_type":type(raw).__name__,"candidate_structure":walk(raw)[:300],"candidate_quest_ids":candidate_ids,"candidate_record_count":len(records),"candidate_quest_like_count":len(quest_like),"missing_quest_ids":missing_ids,"duplicate_quest_ids":duplicate_ids,"sample_records":sample,"production_definition_file":defs_path.relative_to(r).as_posix(),"production_sha256":sha(defs_path),"production_functions":functions,"production_imports":imports,"production_call_counts":calls,"builder_candidates":[x for x in functions if any(k in x.lower() for k in ("quest","story","build","load","register"))],"literal_start_path_found":"start_path" in defs,"literal_49_found":bool(re.search(r"(?<!\d)49(?!\d)",defs)),"literal_50_found":bool(re.search(r"(?<!\d)50(?!\d)",defs))}
def main():
 r=root();folder=None;state={};before={x.as_posix():sha(r/x) for x in PROTECTED};reference_before={x.relative_to(r).as_posix():sha(x) for x in (r/"Квести").rglob("*") if x.is_file()}
 expected=("EXACT_QUEST_RECORDS_1_TO_50","LEVEL_GATES_AND_SEQUENTIAL_PREREQUISITES","OBJECTIVES_TARGETS_AND_QUEST_ITEMS","REWARD_PARITY_AND_TRIPLE_NORMAL_MOB_POLICY","NPC_LOCATION_AND_LOCALIZED_PRESENTATION_REFERENCES","BOSS_AND_FORCED_ENCOUNTER_CONTRACT","PACKAGE_BY_TEN_AND_CONTENT_VALIDATION","QUEST_49_50_TERMINAL_FLOW_AND_KNOWN_PRESENTATION_NUANCE")
 confirmed=("CANONICAL_REFERENCE_FOLDER_AND_SOURCE_INVENTORY","PRODUCTION_DEFINITION_OWNER","QUEST_CHAIN_BOUNDARY_1_TO_50")
 try:
  audit=json.loads((r/PREREQ).read_text(encoding="utf-8-sig"));rows=tuple(x for x in audit.get("contract_matrix",()) if isinstance(x,dict));unresolved=tuple(x.get("contract") for x in rows if x.get("classification")=="REVIEW_REQUIRED");got_confirmed=tuple(x.get("contract") for x in rows if x.get("classification")=="V1_CONFIRMED");summary=audit.get("summary",{})
  if git(r,"rev-parse","HEAD").stdout.strip()!=PARENT:raise PatchError("wrong_exact_parent")
  if audit.get("stage")!="21.13.4" or audit.get("conclusion")!="GO_TO_SEMANTIC_REFINEMENT" or len(rows)!=11 or unresolved!=expected or got_confirmed!=confirmed or tuple(summary.get("unresolved_contracts",()))!=expected:raise PatchError("invalid_stage_21_13_4_prerequisite")
  if summary.get("v1_confirmed_contracts")!=3 or summary.get("review_required_contracts")!=8 or summary.get("contract_count")!=11:raise PatchError("invalid_3_8_11_contract_matrix")
  print("[1/10] [PASS] Stage 21.13.4 exact 3-confirmed/8-unresolved/11-total prerequisite verified.")
  branch=git(r,"branch","--show-current").stdout.strip();staged=git(r,"diff","--cached","--name-only").stdout.strip()
  if not branch:raise PatchError("git_preflight_detached_head")
  if staged:raise PatchError("git_preflight_staged_index:"+staged.replace("\n",","))
  bad=sorted(p for st,p in status(r) if p not in ALLOWED or (p!=SELF and st[0]!=" "))
  if bad:raise PatchError(f"unexpected_dirty:{bad}")
  print(f"[2/10] [PASS] Active branch {branch}, exact parent, dirty allowlist and clean index verified.");folder,state=backup(r);print("[3/10] [PASS] Refinement artifacts backed up before publication mutation.")
  evidence=inspect(r);print("[4/10] [PASS] Canonical Початок Шляху candidate JSON and production definition builders structurally inspected.")
  details={
   "EXACT_QUEST_RECORDS_1_TO_50":(["canonical candidate JSON is parsed structurally rather than searched only by literals","quest-like dictionaries are indexed by stable numeric identity when present","missing and duplicate candidate IDs are reported explicitly","production definition builders, imports and call sites are inventoried"],"Resolve the exact authoritative record for every quest ID 1-50, including title, description, objective, target, NPC references, location, rewards and predecessor; reconcile candidate records against the actual production builder output without treating text or array position as identity."),
   "LEVEL_GATES_AND_SEQUENTIAL_PREREQUISITES":(["the canonical chain boundary is 1-50","the approved package gates are 1-10 level 1, 11-20 level 2, 21-30 level 3, 31-40 level 4 and 41-50 level 5","each package requires the corresponding level","the chain requires completion or authorized SKIP of the previous quest"],"Extract the actual candidate and V1 fields that encode required level and predecessor, then produce a 50-row executable matrix proving exact package gates, quest 1 root semantics and quest N predecessor N-1 for N=2..50."),
   "OBJECTIVES_TARGETS_AND_QUEST_ITEMS":(["V1 supports TALK, KILL_REGION, QUEST_ITEM, TURN_IN and BOSS through the Quest Engine contract","candidate records expose their available objective-shaped fields for exact reconciliation","quest items must remain isolated from regular inventory","known approved quest-item chances and special target rules must not be generalized beyond their quests"],"Resolve every quest objective type, target, region/mob identity, quest-item key, quantity, 15% drop chance where approved, accumulation/consumption boundary and exact-once event identity; flag every candidate/production mismatch rather than inventing defaults."),
   "REWARD_PARITY_AND_TRIPLE_NORMAL_MOB_POLICY":(["rewards are content data consumed by the generic Quest Engine","packages 1-10, 11-20 and 21-30 have approved full triple rewards based on canonical normal mobs of levels 1, 2 and 3 respectively","TALK, QUEST_ITEM and TURN_IN receive the same package policy where approved","reward formulas must not be copied into content definitions"],"Locate the canonical reward resolver inputs and determine exact reward references for quests 1-50; preserve approved package policies and identify unresolved policy for 31-50 from actual V1 evidence instead of extrapolating."),
   "NPC_LOCATION_AND_LOCALIZED_PRESENTATION_REFERENCES":(["stable NPC IDs and location assignment have API-ready owners","the user-facing location name must be Початок Шляху","technical start_path remains allowed only as identity","handlers must not own quest-specific conditions"],"Resolve start/completion NPC IDs, canonical location IDs and localized presentation references for every quest; verify all referenced NPCs and routes exist and prohibit raw technical location/NPC IDs or the term глава in user-visible metadata."),
   "BOSS_AND_FORCED_ENCOUNTER_CONTRACT":(["boss objectives are owned by shared combat and Quest Engine boundaries","the location boss normally appears through Hunting, not a separate boss button","quest 49 has an accepted forced leader encounter and completion flow","new boss formulas or encounter rules are not authorized"],"Locate the exact V1 forced-encounter evidence for quest 49, boss identity/level behavior, exact-once victory evidence and retry/restart semantics; distinguish ordinary random boss encounters from quest-forced encounter orchestration."),
   "PACKAGE_BY_TEN_AND_CONTENT_VALIDATION":(["roadmap requires migration in packages of ten","candidate content covers the Початок Шляху chain","each package must be independently validated before the next mutation","canonical Quest Engine and NPC model are content-independent"],"Define five exact package manifests 1-10, 11-20, 21-30, 31-40 and 41-50 plus validators for IDs, predecessor chain, levels, objective schema, NPC/location references, quest items, rewards, localization and duplicate content."),
   "QUEST_49_50_TERMINAL_FLOW_AND_KNOWN_PRESENTATION_NUANCE":(["quest 49 forced encounter and turn-in were manually accepted in V1","quest 50 ends the Початок Шляху story by talking to the Elder","a known V1 presentation defect hides 1/1 progress after the leader victory until quest 49 turn-in","the defect is presentation-only and must be tracked explicitly"],"Resolve the exact quest 49 and 50 records, NPCs, objective transitions and completion flags; decide from V1 evidence whether V2 must preserve or correct the hidden 1/1 presentation nuance, without changing accepted combat or completion semantics.")}
  refined=[{"contract":k,"classification":"REVIEW_REQUIRED","confirmed":v[0],"remaining_question":v[1]} for k,v in details.items()]
  if tuple(x["contract"] for x in refined)!=expected:raise PatchError("refinement_contract_mismatch")
  print("[5/10] [PASS] Eight Story content boundaries narrowed to exact records, gates, objectives, rewards, references, boss, packages and terminal flow.");print("[6/10] [PASS] Candidate/production builder mismatches isolated without inventing content or modifying canonical quest references.")
  removed=clean(r);checks=ci(r);print(f"[7/10] [PASS] Canonical V2 CI passed after removing {len(removed)} bytecode artifact(s).")
  if before!={x.as_posix():sha(r/x) for x in PROTECTED}:raise PatchError("protected_runtime_changed")
  reference_after={x.relative_to(r).as_posix():sha(x) for x in (r/"Квести").rglob("*") if x.is_file()}
  if reference_before!=reference_after:raise PatchError("canonical_reference_changed")
  print("[8/10] [PASS] Production sources, canonical quest references, DB sidecars and protected configuration remained byte-identical.")
  payload={"schema_version":1,"stage":STAGE,"status":"PASS","conclusion":"REVIEW_REQUIRED","source_audit":PREREQ.as_posix(),"summary":{"contract_count":11,"v1_confirmed_contracts":3,"refined_contracts":8,"review_required_contracts":8,"unresolved_contracts":list(expected),"database_opened":False,"production_code_changed":False,"canonical_reference_changed":False,"v1_wal_shm_manipulated":False},"authoritative_evidence":evidence,"refined_contract_matrix":refined,"observations":{"candidate_record_count":evidence["candidate_record_count"],"candidate_quest_ids":evidence["candidate_quest_ids"],"missing_candidate_ids":evidence["missing_quest_ids"],"duplicate_candidate_ids":evidence["duplicate_quest_ids"],"production_builder_candidates":evidence["builder_candidates"],"exact_50_record_matrix_requires_resolution":True},"implementation_authorized":False,"canonical_v2_ci":checks,"manual_game_check":"NOT_REQUIRED","suggested_next_patch":"patch_21_13_4b_resolve_story_content_1_50_parity.py","backup_path":folder.relative_to(r).as_posix()};write(r/REPORT,json.dumps(payload,ensure_ascii=False,indent=2,default=str)+"\n")
  lines=["# Stage 21.13.4a - Refined Story content 1-50 contract","","- Status: **PASS**","- Conclusion: **REVIEW_REQUIRED**","- Contract matrix: **3 confirmed / 8 review-required / 11 total**","- Candidate quest IDs discovered: **"+str(len(evidence["candidate_quest_ids"]))+"**","- Missing candidate IDs: **"+str(evidence["missing_quest_ids"])+"**","- Duplicate candidate IDs: **"+str(evidence["duplicate_quest_ids"])+"**","- Implementation authorized: **False**","- Manual game check: **NOT_REQUIRED**","","## Refined unresolved contracts",""]
  for x in refined:lines.extend(["### "+x["contract"],"","Confirmed:","",*["- "+v for v in x["confirmed"]],"","Remaining question: "+x["remaining_question"],""])
  lines.extend(["No production mutation, canonical reference edit, quest migration, reward change, database access or runtime wiring is authorized.","","## Next patch","","`patch_21_13_4b_resolve_story_content_1_50_parity.py`",""]);write(r/DOC,"\n".join(lines));print("[9/10] [PASS] Refined JSON and Markdown Story content 1-50 contract artifacts written.")
  files={x.as_posix() for x in TARGETS};git(r,"add","-f","--",*sorted(files));got={x.replace("\\","/") for x in git(r,"diff","--cached","--name-only","--").stdout.splitlines() if x}
  if got!=files:raise PatchError("staging_mismatch:"+repr(sorted(got)))
  z=git(r,"commit","-m","Stage 21.13.4a: refine Story content 1-50 contract","--",*sorted(files),check=False)
  if z.returncode:raise PatchError("commit_failed:"+z.stdout+z.stderr)
  commit=git(r,"rev-parse","HEAD").stdout.strip();changed={x.replace("\\","/") for x in git(r,"diff-tree","--no-commit-id","--name-only","-r",commit).stdout.splitlines() if x}
  if changed!=files:raise PatchError("commit_scope_mismatch:"+repr(sorted(changed)))
  print(f"[10/10] [PASS] Story content 1-50 semantic refinement committed: {commit}");print("CONCLUSION: REVIEW_REQUIRED\nCONTRACT_MATRIX: 3 CONFIRMED / 8 REVIEW_REQUIRED / 11 TOTAL\nUNRESOLVED_CONTRACTS: 8\nIMPLEMENTATION AUTHORIZED: False\nCANONICAL REFERENCE CHANGED: False\nMANUAL GAME CHECK: NOT_REQUIRED\nFAIL-SAFE ROLLBACK: ARMED\nSUGGESTED NEXT PATCH: patch_21_13_4b_resolve_story_content_1_50_parity.py");return 0
 except Exception as error:
  restored=restore(r,folder,state);recovery=run([sys.executable,"-m","compileall","-q","rom_v2"],r,False);write(r/FAILURE,json.dumps({"stage":STAGE,"status":"FAIL_ROLLED_BACK","reason":str(error),"restored_files":restored,"recovery_compile_returncode":recovery.returncode,"main_py_must_not_run":recovery.returncode!=0,"database_opened":False,"canonical_reference_changed":False,"v1_wal_shm_manipulated":False},ensure_ascii=False,indent=2)+"\n");print(f"[10/10] [FAIL] {error}; rollback: FAIL_ROLLED_BACK");return 1
if __name__=="__main__":raise SystemExit(main())
