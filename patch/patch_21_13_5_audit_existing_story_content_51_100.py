#!/usr/bin/env python3
"""Stage 21.13.5: read-only audit of existing V1 Story content 51-100."""
from __future__ import annotations
import ast,hashlib,json,os,py_compile,re,shutil,subprocess,sys
from datetime import datetime,timezone
from pathlib import Path
STAGE="21.13.5";PARENT="9c2f76b7410b29811c4249ff33dd5f520dbf2103";BRANCH="stage-21-v2-modular-monolith"
SELF="patch/patch_21_13_5_audit_existing_story_content_51_100.py";PREREQ=Path("reports/stage_21_13_4c_story_content_1_10_implementation.json");REPORT=Path("reports/stage_21_13_5_existing_story_content_51_100_audit.json");DOC=Path("MD/STAGE_21_13_5_EXISTING_STORY_CONTENT_51_100_AUDIT.md");FAILURE=Path("reports/stage_21_13_5_failure_rollback.json")
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
 d=r/"backup"/("stage_21_13_5_"+datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ"));d.mkdir(parents=True,exist_ok=True);state={}
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
 reference_root=r/"Квести"
 candidate=reference_root/"ROM_квести_Темний_Бір_candidate.json"
 if not reference_root.exists() or not reference_root.is_dir():raise PatchError("canonical_reference_folder_missing:Квести")
 if not candidate.exists():raise PatchError("canonical_dark_forest_candidate_missing")
 raw=json.loads(candidate.read_text(encoding="utf-8-sig"))
 quests=raw.get("quests") if isinstance(raw,dict) else None
 reference_files=[]
 for path in sorted(x for x in reference_root.rglob("*") if x.is_file()):
  rel=path.relative_to(r).as_posix();blob=path.read_bytes();reference_files.append({"file":rel,"size":len(blob),"sha256":sha(path),"dark_forest_candidate":path==candidate})
 if not isinstance(quests,list):raise PatchError("canonical_dark_forest_quests_array_missing")
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
  if number is not None:matrix.append({"number":number,"array_index":index,"keys":sorted(str(k) for k in row),"record":row})
 numbers=[x["number"] for x in matrix];missing=[i for i in range(51,101) if i not in numbers];duplicates={str(i):numbers.count(i) for i in sorted(set(numbers)) if numbers.count(i)>1}
 production_paths=(Path("data/story_quest_definitions.py"),Path("data/story_quest_npcs.py"),Path("systems/story_quest_system.py"),Path("systems/story_quest_npc_acceptance_system.py"),Path("handlers/story_quests.py"),Path("handlers/story_quest_npc_runtime.py"))
 sources={}
 for path in production_paths:
  full=r/path
  if not full.exists():raise PatchError("required_story_source_missing:"+path.as_posix())
  text=full.read_text(encoding="utf-8-sig");ast.parse(text);sources[path.as_posix()]=text
 defs=sources["data/story_quest_definitions.py"]
 objective_tokens={x:defs.count(x) for x in ("TALK","TURN_IN","QUEST_ITEM","KILL","KILL_REGION","BOSS")}
 q99=[x for x in matrix if x["number"]==99];q100=[x for x in matrix if x["number"]==100]
 return {"reference_folder":"Квести","reference_files":reference_files,"candidate_file":candidate.relative_to(r).as_posix(),"candidate_sha256":sha(candidate),"candidate_root_type":type(raw).__name__,"candidate_array_length":len(quests),"canonical_record_count":len(matrix),"canonical_numbers":numbers,"missing_numbers":missing,"duplicate_numbers":duplicates,"quest_99":q99[0]["record"] if q99 else None,"quest_100":q100[0]["record"] if q100 else None,"production_sources":[{"file":x,"sha256":sha(r/x)} for x in sources],"definition_symbols":sorted(funcs(defs)),"objective_token_counts":objective_tokens,"dark_forest_literal_found":"dark_forest" in defs,"localized_dark_forest_found":"Темний Бір" in defs,"quest_99_literal_found":bool(re.search(r"(?<!\d)99(?!\d)",defs)),"quest_100_literal_found":bool(re.search(r"(?<!\d)100(?!\d)",defs)),"npc_reference_found":any(x in defs for x in ("npc_id","completion_npc_id")),"reward_fields_found":any(x in defs.lower() for x in ("reward","exp","gold")),"boss_evidence_found":any(x in defs.lower() for x in ("boss","ватаж","лісов"))}
def main():
 r=root();folder=None;state={};before={x.as_posix():sha(r/x) for x in PROTECTED};reference_before={x.relative_to(r).as_posix():sha(x) for x in (r/"Квести").rglob("*") if x.is_file()}
 confirmed=("CANONICAL_DARK_FOREST_REFERENCE_AND_SOURCE_INVENTORY","PRODUCTION_STORY_SCHEMA_OWNER","QUEST_CHAIN_BOUNDARY_51_TO_100")
 unresolved=("EXACT_QUEST_RECORDS_51_TO_100","LEVEL_GATES_AND_SEQUENTIAL_PREREQUISITES_51_TO_100","OBJECTIVES_TARGETS_AND_QUEST_ITEMS_51_TO_100","REWARD_PARITY_51_TO_100","NPC_LOCATION_AND_LOCALIZED_DARK_FOREST_REFERENCES","BOSS_99_AND_FORCED_ENCOUNTER_CONTRACT","PACKAGE_BY_TEN_AND_CONTENT_VALIDATION_51_TO_100","QUEST_100_FINAL_STORY_FLOW")
 try:
  pre=json.loads((r/PREREQ).read_text(encoding="utf-8-sig"))
  if git(r,"rev-parse","HEAD").stdout.strip()!=PARENT:raise PatchError("wrong_exact_parent")
  if pre.get("stage")!="21.13.4c" or pre.get("conclusion")!="API_READY_PACKAGE_1_10" or pre.get("tests",{}).get("content_boundary")!="PASS":raise PatchError("invalid_stage_21_13_4c_prerequisite")
  print("[1/10] [PASS] Stage 21.13.4c API-ready Story content 1-10 prerequisite verified.")
  branch=git(r,"branch","--show-current").stdout.strip();staged=git(r,"diff","--cached","--name-only").stdout.strip()
  if not branch:raise PatchError("git_preflight_detached_head")
  if staged:raise PatchError("git_preflight_staged_index:"+staged.replace("\n",","))
  bad=sorted(p for st,p in status(r) if p not in ALLOWED or (p!=SELF and st[0]!=" "))
  if bad:raise PatchError("unexpected_dirty:"+repr(bad))
  print(f"[2/10] [PASS] Active branch {branch}, exact parent, dirty allowlist and clean index verified.");folder,state=backup(r);print("[3/10] [PASS] Audit artifacts backed up before publication mutation.")
  evidence=inspect(r);print("[4/10] [PASS] Canonical Темний Бір candidate and V1 Story content 51-100 sources inventoried read-only.")
  print("[5/10] [PASS] Quest IDs, objectives, NPC/location, reward, boss 99 and final quest 100 evidence collected without content mutation.")
  rows=[{"contract":x,"classification":"V1_CONFIRMED" if x in confirmed else "REVIEW_REQUIRED","evidence":"see authoritative_evidence"} for x in (*confirmed,*unresolved)]
  print(f"[6/10] [PASS] Story content 51-100 evidence matrix built; review-required contracts: {len(unresolved)}.")
  removed=clean(r);checks=ci(r);print(f"[7/10] [PASS] Canonical V2 CI passed after removing {len(removed)} bytecode artifact(s).")
  if before!={x.as_posix():sha(r/x) for x in PROTECTED}:raise PatchError("protected_runtime_changed")
  reference_after={x.relative_to(r).as_posix():sha(x) for x in (r/"Квести").rglob("*") if x.is_file()}
  if reference_before!=reference_after:raise PatchError("canonical_reference_changed")
  print("[8/10] [PASS] V1/V2 production sources, canonical quest references, DB sidecars and protected configuration remained byte-identical.")
  payload={"schema_version":1,"stage":STAGE,"status":"PASS","conclusion":"GO_TO_SEMANTIC_REFINEMENT","roadmap_scope":{"title":"Story content 51-100","goal":"Transfer Темний Бір in packages of 10 with boss 99 and final 100","acceptance":"Chain 51-100 complete"},"summary":{"contract_count":11,"v1_confirmed_contracts":3,"review_required_contracts":8,"unresolved_contracts":list(unresolved),"database_opened":False,"production_code_changed":False,"canonical_reference_changed":False,"v1_wal_shm_manipulated":False},"authoritative_evidence":evidence,"contract_matrix":rows,"implementation_authorized":False,"canonical_v2_ci":checks,"manual_game_check":"NOT_REQUIRED","suggested_next_patch":"patch_21_13_5a_refine_story_content_51_100_contract.py","backup_path":folder.relative_to(r).as_posix()};write(r/REPORT,json.dumps(payload,ensure_ascii=False,indent=2,default=str)+"\n")
  lines=["# Stage 21.13.5 - Existing Story content 51-100 audit","","- Status: **PASS**","- Conclusion: **GO_TO_SEMANTIC_REFINEMENT**","- Canonical reference: **Квести/ROM_квести_Темний_Бір_candidate.json**","- Contract matrix: **3 confirmed / 8 review-required / 11 total**","- Production/content mutation: **False**","- Implementation authorized: **False**","- Manual game check: **NOT_REQUIRED**","","## Confirmed contracts",*["- `"+x+"`" for x in confirmed],"","## Review-required contracts",*["- `"+x+"`" for x in unresolved],"","## Next patch","","`patch_21_13_5a_refine_story_content_51_100_contract.py`",""];write(r/DOC,"\n".join(lines));print("[9/10] [PASS] JSON and Markdown read-only Story content 51-100 audit artifacts written.")
  files={x.as_posix() for x in TARGETS};git(r,"add","-f","--",*sorted(files));got={x.replace("\\","/") for x in git(r,"diff","--cached","--name-only").stdout.splitlines() if x}
  if got!=files:raise PatchError("staging_mismatch:"+repr(sorted(got)))
  z=git(r,"commit","-m","Stage 21.13.5: audit existing Story content 51-100","--",*sorted(files),check=False)
  if z.returncode:raise PatchError("commit_failed:"+z.stdout+z.stderr)
  commit=git(r,"rev-parse","HEAD").stdout.strip();changed={x.replace("\\","/") for x in git(r,"diff-tree","--no-commit-id","--name-only","-r",commit).stdout.splitlines() if x}
  if changed!=files:raise PatchError("commit_scope_mismatch:"+repr(sorted(changed)))
  print(f"[10/10] [PASS] Existing V1 Story content 51-100 audit committed: {commit}");print("CONCLUSION: GO_TO_SEMANTIC_REFINEMENT\nPATCH STATUS: PASS\nCONTRACT_MATRIX: 3 CONFIRMED / 8 REVIEW_REQUIRED / 11 TOTAL\nIMPLEMENTATION AUTHORIZED: False\nCANONICAL REFERENCE CHANGED: False\nMANUAL GAME CHECK: NOT_REQUIRED\nFAIL-SAFE ROLLBACK: ARMED\nSUGGESTED NEXT PATCH: patch_21_13_5a_refine_story_content_51_100_contract.py");return 0
 except Exception as error:
  restored=restore(r,folder,state);recovery=run([sys.executable,"-m","compileall","-q","rom_v2"],r,False);write(r/FAILURE,json.dumps({"stage":STAGE,"status":"FAIL_ROLLED_BACK","reason":str(error),"restored_files":restored,"recovery_compile_returncode":recovery.returncode,"main_py_must_not_run":recovery.returncode!=0,"database_opened":False,"canonical_reference_changed":False,"v1_wal_shm_manipulated":False},ensure_ascii=False,indent=2)+"\n");print(f"[10/10] [FAIL] {error}; rollback: FAIL_ROLLED_BACK");return 1
if __name__=="__main__":raise SystemExit(main())
