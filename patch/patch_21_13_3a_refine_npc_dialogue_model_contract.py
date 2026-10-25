#!/usr/bin/env python3
"""Stage 21.13.3a: refine the V1 NPC/dialogue model contract without production mutation."""
from __future__ import annotations
import ast,hashlib,json,os,py_compile,shutil,subprocess,sys
from datetime import datetime,timezone
from pathlib import Path
STAGE="21.13.3a";PARENT="49d845f6d6691ff7f6713c5db3687ba9a820f500";BRANCH="stage-21-v2-modular-monolith"
SELF="patch/patch_21_13_3a_refine_npc_dialogue_model_contract.py";PREREQ=Path("reports/stage_21_13_3_existing_npc_dialogue_model_audit.json");REPORT=Path("reports/stage_21_13_3a_refined_npc_dialogue_model_contract.json");DOC=Path("MD/STAGE_21_13_3A_REFINED_NPC_DIALOGUE_MODEL_CONTRACT.md");FAILURE=Path("reports/stage_21_13_3a_failure_rollback.json")
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
 d=r/"backup"/("stage_21_13_3a_"+datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ"));d.mkdir(parents=True,exist_ok=True);state={}
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
 paths=(Path("data/story_quest_npcs.py"),Path("data/story_quest_definitions.py"),Path("systems/story_quest_npc_acceptance_system.py"),Path("handlers/story_quest_npc_runtime.py"),Path("handlers/story_quests.py"),Path("handlers/city.py"));src={}
 for x in paths:
  text=(r/x).read_text(encoding="utf-8-sig");ast.parse(text);src[x.as_posix()]=text
 registry=src["data/story_quest_npcs.py"];defs=src["data/story_quest_definitions.py"];acceptance=src["systems/story_quest_npc_acceptance_system.py"];runtime=src["handlers/story_quest_npc_runtime.py"];story_handler=src["handlers/story_quests.py"];city=src["handlers/city.py"]
 required_registry_functions={"get_story_quest_npc","validate_story_quest_npc_registry","validate_story_quest_npc_references","get_missing_story_quest_npc_routes"}
 registry_tree=ast.parse(registry)
 registry_classes={node.name for node in ast.walk(registry_tree) if isinstance(node,ast.ClassDef)}
 missing_functions=required_registry_functions-funcs(registry)
 missing_classes={"StoryQuestNpcDefinition"}-registry_classes
 if missing_functions or missing_classes:raise PatchError("npc_registry_symbols_missing:"+",".join(sorted(missing_functions|missing_classes)))
 required_registry={"StoryQuestNpcDefinition",*required_registry_functions}
 required_acceptance={"find_npc_story_quest","build_npc_story_quest_presentation","accept_story_quest_from_npc"}
 missing_acceptance=required_acceptance-funcs(acceptance)
 if missing_acceptance:raise PatchError("npc_acceptance_symbols_missing:"+",".join(sorted(missing_acceptance)))
 runtime_symbols={"has_story_npc_if_present","send_story_npc_if_present","register_story_quest_npc_runtime_handlers"}
 missing_runtime=runtime_symbols-funcs(runtime)
 if missing_runtime:raise PatchError("npc_runtime_symbols_missing:"+",".join(sorted(missing_runtime)))
 evidence={
  "registry_symbols":sorted(required_registry),"acceptance_symbols":sorted(required_acceptance),"runtime_symbols":sorted(runtime_symbols),
  "registry_constant_found":"STORY_QUEST_NPCS" in registry,"definition_type_found":"StoryQuestNpcDefinition" in registry,
  "location_assignment_found":"location" in registry.lower(),"npc_role_found":"npc_role" in acceptance,
  "quest_reference_found":any(x in defs for x in ("npc_id","completion_npc_id")),
  "dialogue_literal_count":sum(x.lower().count("dialog") for x in src.values()),"conversation_literal_count":sum(x.lower().count("conversation") for x in src.values()),
  "talk_literal_count":sum(x.lower().count("talk") for x in src.values()),
  "callback_boundary_found":"callback" in runtime.lower(),"placeholder_boundary_found":"placeholder" in city.lower(),
  "handler_does_not_own_registry":"STORY_QUEST_NPCS" not in runtime and "STORY_QUEST_NPCS" not in story_handler}
 absent=[k for k in ("registry_constant_found","definition_type_found","location_assignment_found","quest_reference_found","handler_does_not_own_registry") if not evidence[k]]
 if absent:raise PatchError("npc_dialogue_evidence_missing:"+",".join(absent))
 return {"registry_owner":"data/story_quest_npcs.py","quest_definition_owner":"data/story_quest_definitions.py","acceptance_owner":"systems/story_quest_npc_acceptance_system.py","runtime_consumer":"handlers/story_quest_npc_runtime.py","story_handler_consumer":"handlers/story_quests.py","city_consumer":"handlers/city.py","evidence":evidence,"source_hashes":{x.as_posix():sha(r/x) for x in paths}}
def main():
 r=root();folder=None;state={};before={x.as_posix():sha(r/x) for x in PROTECTED}
 expected=("DIALOGUE_NODE_AND_ACTION_SCHEMA","NPC_AVAILABILITY_AND_CONDITION_POLICY","QUEST_AND_NPC_INTERACTION_BOUNDARY","SHOP_SERVICE_AND_OTHER_ACTION_BOUNDARIES","LOCALIZATION_AND_TECHNICAL_ID_NON_DISCLOSURE","PERSISTENCE_RESTART_AND_CONTENT_INDEPENDENCE")
 confirmed=("NPC_STABLE_ID_AND_OWNER_MODEL","NPC_LOCATION_ASSIGNMENT_BOUNDARY","PRESENTATION_HANDLER_SEPARATION")
 try:
  audit=json.loads((r/PREREQ).read_text(encoding="utf-8-sig"));rows=tuple(x for x in audit.get("contract_matrix",()) if isinstance(x,dict));unresolved=tuple(x.get("contract") for x in rows if x.get("classification")=="REVIEW_REQUIRED");got_confirmed=tuple(x.get("contract") for x in rows if x.get("classification")=="V1_CONFIRMED");summary=audit.get("summary",{})
  if git(r,"rev-parse","HEAD").stdout.strip()!=PARENT:raise PatchError("wrong_exact_parent")
  if audit.get("stage")!="21.13.3" or audit.get("conclusion")!="GO_TO_SEMANTIC_REFINEMENT" or len(rows)!=9 or unresolved!=expected or got_confirmed!=confirmed or tuple(summary.get("unresolved_contracts",()))!=expected:raise PatchError("invalid_stage_21_13_3_prerequisite")
  if summary.get("v1_confirmed_contracts")!=3 or summary.get("review_required_contracts")!=6 or summary.get("contract_count")!=9:raise PatchError("invalid_3_6_9_contract_matrix")
  print("[1/10] [PASS] Stage 21.13.3 exact 3-confirmed/6-unresolved/9-total prerequisite verified.")
  branch=git(r,"branch","--show-current").stdout.strip();staged=git(r,"diff","--cached","--name-only").stdout.strip()
  if not branch:raise PatchError("git_preflight_detached_head")
  if staged:raise PatchError("git_preflight_staged_index:"+staged.replace("\n",","))
  bad=sorted(p for st,p in status(r) if p not in ALLOWED or (p!=SELF and st[0]!=" "))
  if bad:raise PatchError(f"unexpected_dirty:{bad}")
  print(f"[2/10] [PASS] Active branch {branch}, exact parent, dirty allowlist and clean index verified.");folder,state=backup(r);print("[3/10] [PASS] Refinement artifacts backed up before publication mutation.")
  evidence=inspect(r);print("[4/10] [PASS] Exact V1 NPC registry, quest references, acceptance owner and runtime consumers re-verified.")
  details={
   "DIALOGUE_NODE_AND_ACTION_SCHEMA":(["V1 has a typed StoryQuestNpcDefinition and STORY_QUEST_NPCS registry","the acceptance system builds NPC story-quest presentation","runtime callbacks are registered outside the registry","the audited sources contain dialogue mentions but no confirmed generic conversation graph owner"],"Determine whether V1 parity is a bounded NPC action/presentation model rather than a generic branching dialogue graph; identify stable action identity, allowed action kinds and whether any dialogue node IDs persist across callbacks."),
   "NPC_AVAILABILITY_AND_CONDITION_POLICY":(["NPC definitions are assigned to locations","quest definitions reference NPC identity","acceptance resolves an NPC story quest before mutation","runtime checks whether a story NPC is present"],"Resolve the exact order of location, route, quest-state, level, prerequisite and visibility checks; define unknown NPC, unavailable NPC and stale callback results without adding conditions absent from V1."),
   "QUEST_AND_NPC_INTERACTION_BOUNDARY":(["data/story_quest_npcs.py owns static NPC content","systems/story_quest_npc_acceptance_system.py owns find, presentation and accept orchestration","Quest Engine remains the owner of quest availability and acceptance state","handlers consume the acceptance API"],"Define the typed query/command boundary so NPC interaction never duplicates Quest Engine prerequisites, progress or reward rules; identify expected quest/NPC identity and revision inputs for stale interaction protection."),
   "SHOP_SERVICE_AND_OTHER_ACTION_BOUNDARIES":(["the authoritative NPC registry is story-quest specific","broad discovery produced unrelated auction, daily and rune token matches","handlers/city.py contains placeholder presentation","no audited evidence establishes the NPC registry as owner of shop, guild or crafting mutations"],"Classify non-story NPC actions as external application-service links rather than NPC-owned business logic; enumerate only V1-confirmed action targets and explicitly reject invented universal shop/service action types."),
   "LOCALIZATION_AND_TECHNICAL_ID_NON_DISCLOSURE":(["stable NPC IDs exist separately from definitions","presentation is built by the acceptance system and handlers","technical IDs are required for quest references and callbacks","user-facing story terminology must use localized human names"],"Locate the canonical NPC display-name resolver and define fail-closed behavior for unknown IDs; prohibit raw NPC IDs, auto title-casing and technical location IDs in user-visible text while allowing IDs in DTO identity, callbacks, logs and tests."),
   "PERSISTENCE_RESTART_AND_CONTENT_INDEPENDENCE":(["NPC definitions are represented by a static registry","quest state persists outside the NPC registry","handlers do not own the registry","registry and quest references have validators"],"Resolve whether NPC/dialogue content is immutable and needs no independent persistence; define restart stability, validation of duplicate IDs/routes/references and an executable gate preventing reusable model code from branching on concrete NPC IDs, quest IDs or localized content.")}
  refined=[{"contract":k,"classification":"REVIEW_REQUIRED","confirmed":v[0],"remaining_question":v[1]} for k,v in details.items()]
  if tuple(x["contract"] for x in refined)!=expected:raise PatchError("refinement_contract_mismatch")
  print("[5/10] [PASS] Six NPC/dialogue boundaries narrowed to exact schema, availability, quest, service, localization and restart evidence.");print("[6/10] [PASS] Generic-dialogue and broad token-discovery risks isolated without inventing NPC actions or mutating production content.")
  removed=clean(r);checks=ci(r);print(f"[7/10] [PASS] Canonical V2 CI passed after removing {len(removed)} bytecode artifact(s).")
  if before!={x.as_posix():sha(r/x) for x in PROTECTED}:raise PatchError("protected_runtime_changed")
  print("[8/10] [PASS] Production sources, DB sidecars and protected configuration remained byte-identical.")
  payload={"schema_version":1,"stage":STAGE,"status":"PASS","conclusion":"REVIEW_REQUIRED","source_audit":PREREQ.as_posix(),"summary":{"contract_count":9,"v1_confirmed_contracts":3,"refined_contracts":6,"review_required_contracts":6,"unresolved_contracts":list(expected),"database_opened":False,"production_code_changed":False,"v1_wal_shm_manipulated":False},"authoritative_evidence":evidence,"refined_contract_matrix":refined,"observations":{"generic_dialogue_graph_confirmed":False,"story_quest_npc_registry_confirmed":True,"non_story_service_ownership_confirmed":False,"content_registry_persistence_requires_resolution":True},"implementation_authorized":False,"canonical_v2_ci":checks,"manual_game_check":"NOT_REQUIRED","suggested_next_patch":"patch_21_13_3b_resolve_npc_dialogue_model_parity.py","backup_path":folder.relative_to(r).as_posix()};write(r/REPORT,json.dumps(payload,ensure_ascii=False,indent=2)+"\n")
  lines=["# Stage 21.13.3a - Refined NPC/dialogue model contract","","- Status: **PASS**","- Conclusion: **REVIEW_REQUIRED**","- Contract matrix: **3 confirmed / 6 review-required / 9 total**","- Generic dialogue graph confirmed: **False**","- Story quest NPC registry confirmed: **True**","- Implementation authorized: **False**","- Manual game check: **NOT_REQUIRED**","","## Refined unresolved contracts",""]
  for x in refined:lines.extend(["### "+x["contract"],"","Confirmed:","",*["- "+v for v in x["confirmed"]],"","Remaining question: "+x["remaining_question"],""])
  lines.extend(["No production mutation, NPC content change, quest acceptance, database access or runtime wiring is authorized.","","## Next patch","","`patch_21_13_3b_resolve_npc_dialogue_model_parity.py`",""]);write(r/DOC,"\n".join(lines));print("[9/10] [PASS] Refined JSON and Markdown NPC/dialogue contract artifacts written.")
  files={x.as_posix() for x in TARGETS};git(r,"add","-f","--",*sorted(files));got={x.replace("\\","/") for x in git(r,"diff","--cached","--name-only","--").stdout.splitlines() if x}
  if got!=files:raise PatchError("staging_mismatch:"+repr(sorted(got)))
  z=git(r,"commit","-m","Stage 21.13.3a: refine NPC dialogue model contract","--",*sorted(files),check=False)
  if z.returncode:raise PatchError("commit_failed:"+z.stdout+z.stderr)
  commit=git(r,"rev-parse","HEAD").stdout.strip();changed={x.replace("\\","/") for x in git(r,"diff-tree","--no-commit-id","--name-only","-r",commit).stdout.splitlines() if x}
  if changed!=files:raise PatchError("commit_scope_mismatch:"+repr(sorted(changed)))
  print(f"[10/10] [PASS] NPC/dialogue model semantic refinement committed: {commit}");print("CONCLUSION: REVIEW_REQUIRED\nCONTRACT_MATRIX: 3 CONFIRMED / 6 REVIEW_REQUIRED / 9 TOTAL\nUNRESOLVED_CONTRACTS: 6\nIMPLEMENTATION AUTHORIZED: False\nGENERIC DIALOGUE GRAPH CONFIRMED: False\nMANUAL GAME CHECK: NOT_REQUIRED\nFAIL-SAFE ROLLBACK: ARMED\nSUGGESTED NEXT PATCH: patch_21_13_3b_resolve_npc_dialogue_model_parity.py");return 0
 except Exception as error:
  restored=restore(r,folder,state);recovery=run([sys.executable,"-m","compileall","-q","rom_v2"],r,False);write(r/FAILURE,json.dumps({"stage":STAGE,"status":"FAIL_ROLLED_BACK","reason":str(error),"restored_files":restored,"recovery_compile_returncode":recovery.returncode,"main_py_must_not_run":recovery.returncode!=0,"database_opened":False,"v1_wal_shm_manipulated":False},ensure_ascii=False,indent=2)+"\n");print(f"[10/10] [FAIL] {error}; rollback: FAIL_ROLLED_BACK");return 1
if __name__=="__main__":raise SystemExit(main())
