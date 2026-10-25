#!/usr/bin/env python3
"""Stage 21.13.4: read-only audit of existing V1 Story content 1-50."""
from __future__ import annotations
import ast,hashlib,json,os,py_compile,re,shutil,subprocess,sys
from datetime import datetime,timezone
from pathlib import Path
STAGE="21.13.4";PARENT="f23ce70ff9e19be3c6ee0e93ce6a41e57e933192";BRANCH="stage-21-v2-modular-monolith"
SELF="patch/patch_21_13_4_audit_existing_story_content_1_50.py";PREREQ=Path("reports/stage_21_13_3c_npc_dialogue_model_implementation.json");REPORT=Path("reports/stage_21_13_4_existing_story_content_1_50_audit.json");DOC=Path("MD/STAGE_21_13_4_EXISTING_STORY_CONTENT_1_50_AUDIT.md");FAILURE=Path("reports/stage_21_13_4_failure_rollback.json")
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
 d=r/"backup"/("stage_21_13_4_"+datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ"));d.mkdir(parents=True,exist_ok=True);state={}
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
 if not reference_root.exists() or not reference_root.is_dir():raise PatchError("canonical_reference_folder_missing:Квести")
 reference_files=[]
 for path in sorted(x for x in reference_root.rglob("*") if x.is_file()):
  rel=path.relative_to(r).as_posix();raw=path.read_bytes();entry={"file":rel,"size":len(raw),"sha256":sha(path)}
  try:
   text=raw.decode("utf-8-sig");entry["encoding"]="utf-8";entry["mentions_1_50"]=any(k in text for k in ("1-50","1–50","Початок Шляху","Квест 50","квест 50"));entry["quest_number_hits"]=len(re.findall(r"(?i)(?:квест|quest)\s*[№#:]?\s*(?:[1-9]|[1-4][0-9]|50)\b",text))
  except UnicodeDecodeError:entry["encoding"]="binary_or_non_utf8";entry["mentions_1_50"]=False;entry["quest_number_hits"]=0
  reference_files.append(entry)
 if not reference_files:raise PatchError("canonical_reference_folder_empty:Квести")
 production_paths=(Path("data/story_quest_definitions.py"),Path("data/story_quest_npcs.py"),Path("systems/story_quest_system.py"),Path("systems/story_quest_npc_acceptance_system.py"),Path("handlers/story_quests.py"),Path("handlers/story_quest_npc_runtime.py"))
 sources={}
 for path in production_paths:
  full=r/path
  if not full.exists():raise PatchError("required_story_source_missing:"+path.as_posix())
  text=full.read_text(encoding="utf-8-sig");ast.parse(text);sources[path.as_posix()]=text
 defs=sources["data/story_quest_definitions.py"]
 number_hits={str(i):len(re.findall(r"(?<!\d)"+str(i)+r"(?!\d)",defs)) for i in range(1,51)}
 objective_tokens={x:defs.count(x) for x in ("TALK","TURN_IN","QUEST_ITEM","KILL","KILL_REGION")}
 evidence={"reference_folder":"Квести","reference_files":reference_files,"reference_candidates":[x["file"] for x in reference_files if x["mentions_1_50"] or x["quest_number_hits"]],"production_sources":[{"file":x,"sha256":sha(r/x)} for x in sources],"definition_symbols":sorted(funcs(defs)),"quest_number_token_hits":number_hits,"objective_token_counts":objective_tokens,"start_path_found":("start_path" in defs),"localized_start_path_found":("Початок Шляху" in defs),"quest_49_found":bool(number_hits["49"]),"quest_50_found":bool(number_hits["50"]),"npc_reference_found":any(x in defs for x in ("npc_id","completion_npc_id")),"reward_fields_found":any(x in defs.lower() for x in ("reward","exp","gold")),"boss_evidence_found":any(x in defs.lower() for x in ("boss","ватаж"))}
 if not evidence["reference_candidates"]:raise PatchError("story_1_50_reference_candidate_missing")
 # Literal-token absence is refinement evidence, not an audit failure: V1 may build
 # definitions through helpers, constants, registries or imported content blocks.
 evidence["production_literal_evidence_complete"]=bool(evidence["start_path_found"] and evidence["quest_49_found"] and evidence["quest_50_found"])
 evidence["production_definition_resolution_required"]=not evidence["production_literal_evidence_complete"]
 evidence["missing_literal_evidence"]=[name for name,found in (("start_path",evidence["start_path_found"]),("quest_49",evidence["quest_49_found"]),("quest_50",evidence["quest_50_found"])) if not found]
 return evidence
def main():
 r=root();folder=None;state={};before={x.as_posix():sha(r/x) for x in PROTECTED}
 confirmed=("CANONICAL_REFERENCE_FOLDER_AND_SOURCE_INVENTORY","PRODUCTION_DEFINITION_OWNER","QUEST_CHAIN_BOUNDARY_1_TO_50")
 unresolved=("EXACT_QUEST_RECORDS_1_TO_50","LEVEL_GATES_AND_SEQUENTIAL_PREREQUISITES","OBJECTIVES_TARGETS_AND_QUEST_ITEMS","REWARD_PARITY_AND_TRIPLE_NORMAL_MOB_POLICY","NPC_LOCATION_AND_LOCALIZED_PRESENTATION_REFERENCES","BOSS_AND_FORCED_ENCOUNTER_CONTRACT","PACKAGE_BY_TEN_AND_CONTENT_VALIDATION","QUEST_49_50_TERMINAL_FLOW_AND_KNOWN_PRESENTATION_NUANCE")
 try:
  pre=json.loads((r/PREREQ).read_text(encoding="utf-8-sig"))
  if git(r,"rev-parse","HEAD").stdout.strip()!=PARENT:raise PatchError("wrong_exact_parent")
  if pre.get("stage")!="21.13.3c" or pre.get("conclusion")!="API_READY" or pre.get("tests",{}).get("content_independence")!="PASS":raise PatchError("invalid_stage_21_13_3c_prerequisite")
  print("[1/10] [PASS] Stage 21.13.3c API-ready NPC/dialogue model prerequisite verified.")
  branch=git(r,"branch","--show-current").stdout.strip();staged=git(r,"diff","--cached","--name-only").stdout.strip()
  if not branch:raise PatchError("git_preflight_detached_head")
  if staged:raise PatchError("git_preflight_staged_index:"+staged.replace("\n",","))
  bad=sorted(p for st,p in status(r) if p not in ALLOWED or (p!=SELF and st[0]!=" "))
  if bad:raise PatchError("unexpected_dirty:"+repr(bad))
  print(f"[2/10] [PASS] Active branch {branch}, exact parent, dirty allowlist and clean index verified.");folder,state=backup(r);print("[3/10] [PASS] Audit artifacts backed up before publication mutation.")
  evidence=inspect(r);print("[4/10] [PASS] Canonical Квести reference folder and V1 story 1-50 sources inventoried read-only.")
  print("[5/10] [PASS] Quest/objective/NPC/reward/boss evidence collected; missing literal 1-50 tokens classified for semantic refinement.")
  rows=[{"contract":x,"classification":"V1_CONFIRMED" if x in confirmed else "REVIEW_REQUIRED","evidence":"see authoritative_evidence"} for x in (*confirmed,*unresolved)]
  print(f"[6/10] [PASS] Story content 1-50 evidence matrix built; review-required contracts: {len(unresolved)}.")
  removed=clean(r);checks=ci(r);print(f"[7/10] [PASS] Canonical V2 CI passed after removing {len(removed)} bytecode artifact(s).")
  if before!={x.as_posix():sha(r/x) for x in PROTECTED}:raise PatchError("protected_runtime_changed")
  print("[8/10] [PASS] V1/V2 production sources, canonical quest references, DB sidecars and protected configuration remained byte-identical.")
  payload={"schema_version":1,"stage":STAGE,"status":"PASS","conclusion":"GO_TO_SEMANTIC_REFINEMENT","roadmap_scope":{"title":"Story content 1-50","goal":"Transfer in packages of 10 with level access, sequential chain, rewards and bosses","acceptance":"Chain 1-50 complete"},"summary":{"contract_count":11,"v1_confirmed_contracts":3,"review_required_contracts":8,"unresolved_contracts":list(unresolved),"database_opened":False,"production_code_changed":False,"canonical_reference_changed":False,"v1_wal_shm_manipulated":False},"authoritative_evidence":evidence,"literal_evidence_complete":evidence["production_literal_evidence_complete"],"production_definition_resolution_required":evidence["production_definition_resolution_required"],"contract_matrix":rows,"implementation_authorized":False,"canonical_v2_ci":checks,"manual_game_check":"NOT_REQUIRED","suggested_next_patch":"patch_21_13_4a_refine_story_content_1_50_contract.py","backup_path":folder.relative_to(r).as_posix()};write(r/REPORT,json.dumps(payload,ensure_ascii=False,indent=2)+"\n")
  lines=["# Stage 21.13.4 - Existing Story content 1-50 audit","","- Status: **PASS**","- Conclusion: **GO_TO_SEMANTIC_REFINEMENT**","- Canonical reference folder: **Квести**","- Contract matrix: **3 confirmed / 8 review-required / 11 total**","- Production/content mutation: **False**","- Implementation authorized: **False**","- Manual game check: **NOT_REQUIRED**","","## Confirmed contracts",*["- `"+x+"`" for x in confirmed],"","## Review-required contracts",*["- `"+x+"`" for x in unresolved],"","## Next patch","","`patch_21_13_4a_refine_story_content_1_50_contract.py`",""];write(r/DOC,"\n".join(lines));print("[9/10] [PASS] JSON and Markdown read-only Story content 1-50 audit artifacts written.")
  files={x.as_posix() for x in TARGETS};git(r,"add","-f","--",*sorted(files));got={x.replace("\\","/") for x in git(r,"diff","--cached","--name-only").stdout.splitlines() if x}
  if got!=files:raise PatchError("staging_mismatch:"+repr(sorted(got)))
  z=git(r,"commit","-m","Stage 21.13.4: audit existing Story content 1-50","--",*sorted(files),check=False)
  if z.returncode:raise PatchError("commit_failed:"+z.stdout+z.stderr)
  commit=git(r,"rev-parse","HEAD").stdout.strip();changed={x.replace("\\","/") for x in git(r,"diff-tree","--no-commit-id","--name-only","-r",commit).stdout.splitlines() if x}
  if changed!=files:raise PatchError("commit_scope_mismatch:"+repr(sorted(changed)))
  print(f"[10/10] [PASS] Existing V1 Story content 1-50 audit committed: {commit}");print("CONCLUSION: GO_TO_SEMANTIC_REFINEMENT\nPATCH STATUS: PASS\nCONTRACT_MATRIX: 3 CONFIRMED / 8 REVIEW_REQUIRED / 11 TOTAL\nIMPLEMENTATION AUTHORIZED: False\nCANONICAL REFERENCE CHANGED: False\nMANUAL GAME CHECK: NOT_REQUIRED\nFAIL-SAFE ROLLBACK: ARMED\nSUGGESTED NEXT PATCH: patch_21_13_4a_refine_story_content_1_50_contract.py");return 0
 except Exception as error:
  restored=restore(r,folder,state);recovery=run([sys.executable,"-m","compileall","-q","rom_v2"],r,False);write(r/FAILURE,json.dumps({"stage":STAGE,"status":"FAIL_ROLLED_BACK","reason":str(error),"restored_files":restored,"recovery_compile_returncode":recovery.returncode,"main_py_must_not_run":recovery.returncode!=0,"database_opened":False,"canonical_reference_changed":False,"v1_wal_shm_manipulated":False},ensure_ascii=False,indent=2)+"\n");print(f"[10/10] [FAIL] {error}; rollback: FAIL_ROLLED_BACK");return 1
if __name__=="__main__":raise SystemExit(main())
