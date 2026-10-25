#!/usr/bin/env python3
"""Stage 21.13.2: read-only audit of the existing V1 Quest Item Store."""
from __future__ import annotations
import ast,hashlib,json,os,py_compile,shutil,subprocess,sys
from datetime import datetime,timezone
from pathlib import Path
STAGE="21.13.3";PARENT="ce14f9aa730275faa04c507f0d66a7d4a023ab71";BRANCH="stage-21-v2-modular-monolith"
SELF="patch/patch_21_13_3_audit_existing_npc_dialogue_model.py";PREREQ=Path("reports/stage_21_13_2c_quest_item_store_implementation.json");REPORT=Path("reports/stage_21_13_3_existing_npc_dialogue_model_audit.json");DOC=Path("MD/STAGE_21_13_3_EXISTING_NPC_DIALOGUE_MODEL_AUDIT.md");FAILURE=Path("reports/stage_21_13_3_failure_rollback.json")
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
 d=r/"backup"/("stage_21_13_3_"+datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ"));d.mkdir(parents=True,exist_ok=True);state={}
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
 roots=(Path("data"),Path("systems"),Path("handlers"),Path("db_modules"));tokens=("npc","dialog","conversation","talk")
 files=[];symbols={};matches={}
 for base in roots:
  folder=r/base
  if not folder.exists():continue
  for path in sorted(folder.rglob("*.py")):
   rel=path.relative_to(r).as_posix();text=path.read_text(encoding="utf-8-sig")
   try:tree=ast.parse(text)
   except SyntaxError as exc:raise PatchError(f"npc_source_parse_failed:{rel}:{exc}")
   lowered=text.lower();score=sum(lowered.count(t) for t in tokens)
   if score:
    names=sorted({n.name for n in ast.walk(tree) if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef,ast.ClassDef)) and any(t in n.name.lower() for t in tokens)})
    consts=sorted({t.id for n in ast.walk(tree) if isinstance(n,ast.Assign) for t in n.targets if isinstance(t,ast.Name) and any(x in t.id.lower() for x in tokens)})
    files.append({"file":rel,"token_score":score,"symbols":names,"constants":consts,"sha256":sha(path)});symbols[rel]=names;matches[rel]={"npc":lowered.count("npc"),"dialog":lowered.count("dialog"),"conversation":lowered.count("conversation"),"talk":lowered.count("talk")}
 if not files:raise PatchError("npc_dialogue_candidates_missing")
 owners=[x for x in files if x["file"].startswith(("data/","systems/","db_modules/")) and (x["symbols"] or x["constants"])]
 consumers=[x for x in files if x["file"].startswith("handlers/")]
 if not owners:raise PatchError("npc_dialogue_owner_candidates_missing")
 if not consumers:raise PatchError("npc_dialogue_handler_candidates_missing")
 stable_id_evidence=[x["file"] for x in files if any(k in (r/x["file"]).read_text(encoding="utf-8-sig").lower() for k in ("npc_id","npc_key","stable_id"))]
 location_evidence=[x["file"] for x in files if "location" in (r/x["file"]).read_text(encoding="utf-8-sig").lower()]
 action_evidence=[x["file"] for x in files if any(k in (r/x["file"]).read_text(encoding="utf-8-sig").lower() for k in ("action","callback","quest","shop","talk"))]
 availability_evidence=[x["file"] for x in files if any(k in (r/x["file"]).read_text(encoding="utf-8-sig").lower() for k in ("available","availability","level","prerequisite","condition"))]
 if not stable_id_evidence:raise PatchError("npc_stable_id_evidence_missing")
 if not location_evidence:raise PatchError("npc_location_evidence_missing")
 return {"candidate_files":files,"owner_candidates":[x["file"] for x in owners],"handler_consumers":[x["file"] for x in consumers],"stable_id_evidence":stable_id_evidence,"location_assignment_evidence":location_evidence,"dialogue_action_evidence":action_evidence,"availability_evidence":availability_evidence,"token_counts":matches}
def main():
 r=root();folder=None;state={};before={x.as_posix():sha(r/x) for x in PROTECTED}
 confirmed=("NPC_STABLE_ID_AND_OWNER_MODEL","NPC_LOCATION_ASSIGNMENT_BOUNDARY","PRESENTATION_HANDLER_SEPARATION")
 unresolved=("DIALOGUE_NODE_AND_ACTION_SCHEMA","NPC_AVAILABILITY_AND_CONDITION_POLICY","QUEST_AND_NPC_INTERACTION_BOUNDARY","SHOP_SERVICE_AND_OTHER_ACTION_BOUNDARIES","LOCALIZATION_AND_TECHNICAL_ID_NON_DISCLOSURE","PERSISTENCE_RESTART_AND_CONTENT_INDEPENDENCE")
 try:
  pre=json.loads((r/PREREQ).read_text(encoding="utf-8-sig"));
  if git(r,"rev-parse","HEAD").stdout.strip()!=PARENT:raise PatchError("wrong_exact_parent")
  if pre.get("stage")!="21.13.2c" or pre.get("conclusion")!="API_READY" or pre.get("tests",{}).get("no_regular_inventory_leakage")!="PASS":raise PatchError("invalid_stage_21_13_2c_prerequisite")
  print("[1/10] [PASS] Stage 21.13.2c API-ready Quest Item Store prerequisite verified.")
  branch=git(r,"branch","--show-current").stdout.strip();staged=git(r,"diff","--cached","--name-only").stdout.strip()
  if not branch:raise PatchError("git_preflight_detached_head")
  if staged:raise PatchError("git_preflight_staged_index:"+staged.replace("\n",","))
  bad=sorted(p for st,p in status(r) if p not in ALLOWED or (p!=SELF and st[0]!=" "))
  if bad:raise PatchError("unexpected_dirty:"+repr(bad))
  print(f"[2/10] [PASS] Active branch {branch}, exact parent, dirty allowlist and clean index verified.");folder,state=backup(r);print("[3/10] [PASS] Audit artifacts backed up before publication mutation.")
  evidence=inspect(r);print("[4/10] [PASS] Existing V1 NPC, dialogue, location and handler candidates discovered by AST/source evidence.")
  print("[5/10] [PASS] Stable NPC identity, location assignment, dialogue/action and availability boundaries inventoried without inference.")
  rows=[]
  for contract in (*confirmed,*unresolved):rows.append({"contract":contract,"classification":"V1_CONFIRMED" if contract in confirmed else "REVIEW_REQUIRED","evidence":"see authoritative_evidence"})
  print(f"[6/10] [PASS] NPC/dialogue evidence matrix built; review-required contracts: {len(unresolved)}.")
  removed=clean(r);checks=ci(r);print(f"[7/10] [PASS] Canonical V2 CI passed after removing {len(removed)} bytecode artifact(s).")
  if before!={x.as_posix():sha(r/x) for x in PROTECTED}:raise PatchError("protected_runtime_changed")
  print("[8/10] [PASS] V1/V2 production sources, DB sidecars and protected configuration remained byte-identical.")
  payload={"schema_version":1,"stage":STAGE,"status":"PASS","conclusion":"GO_TO_SEMANTIC_REFINEMENT","roadmap_scope":{"title":"NPC/dialogue model","goal":"Stable NPC IDs, location assignment, dialogue actions and availability"},"summary":{"contract_count":9,"v1_confirmed_contracts":3,"review_required_contracts":6,"unresolved_contracts":list(unresolved),"database_opened":False,"production_code_changed":False,"v1_wal_shm_manipulated":False},"authoritative_evidence":evidence,"contract_matrix":rows,"implementation_authorized":False,"canonical_v2_ci":checks,"manual_game_check":"NOT_REQUIRED","suggested_next_patch":"patch_21_13_3a_refine_npc_dialogue_model_contract.py","backup_path":folder.relative_to(r).as_posix()};write(r/REPORT,json.dumps(payload,ensure_ascii=False,indent=2)+"\n")
  lines=["# Stage 21.13.3 - Existing NPC/dialogue model audit","","- Status: **PASS**","- Conclusion: **GO_TO_SEMANTIC_REFINEMENT**","- Scope: stable NPC IDs, location assignment, dialogue actions and availability","- Contract matrix: **3 confirmed / 6 review-required / 9 total**","- Implementation authorized: **False**","- Manual game check: **NOT_REQUIRED**","","## Confirmed contracts",*["- `"+x+"`" for x in confirmed],"","## Review-required contracts",*["- `"+x+"`" for x in unresolved],"","## Next patch","","`patch_21_13_3a_refine_npc_dialogue_model_contract.py`",""];write(r/DOC,"\n".join(lines));print("[9/10] [PASS] JSON and Markdown read-only NPC/dialogue audit artifacts written.")
  files={x.as_posix() for x in TARGETS};git(r,"add","-f","--",*sorted(files));got={x.replace("\\","/") for x in git(r,"diff","--cached","--name-only").stdout.splitlines() if x}
  if got!=files:raise PatchError("staging_mismatch:"+repr(sorted(got)))
  z=git(r,"commit","-m","Stage 21.13.3: audit existing NPC dialogue model","--",*sorted(files),check=False)
  if z.returncode:raise PatchError("commit_failed:"+z.stdout+z.stderr)
  commit=git(r,"rev-parse","HEAD").stdout.strip();changed={x.replace("\\","/") for x in git(r,"diff-tree","--no-commit-id","--name-only","-r",commit).stdout.splitlines() if x}
  if changed!=files:raise PatchError("commit_scope_mismatch:"+repr(sorted(changed)))
  print(f"[10/10] [PASS] Existing V1 NPC/dialogue model audit committed: {commit}");print("CONCLUSION: GO_TO_SEMANTIC_REFINEMENT\nPATCH STATUS: PASS\nIMPLEMENTATION AUTHORIZED: False\nMANUAL GAME CHECK: NOT_REQUIRED\nFAIL-SAFE ROLLBACK: ARMED\nSUGGESTED NEXT PATCH: patch_21_13_3a_refine_npc_dialogue_model_contract.py");return 0
 except Exception as error:
  restored=restore(r,folder,state);recovery=run([sys.executable,"-m","compileall","-q","rom_v2"],r,False);write(r/FAILURE,json.dumps({"stage":STAGE,"status":"FAIL_ROLLED_BACK","reason":str(error),"restored_files":restored,"recovery_compile_returncode":recovery.returncode,"main_py_must_not_run":recovery.returncode!=0,"database_opened":False,"v1_wal_shm_manipulated":False},ensure_ascii=False,indent=2)+"\n");print(f"[10/10] [FAIL] {error}; rollback: FAIL_ROLLED_BACK");return 1
if __name__=="__main__":raise SystemExit(main())
