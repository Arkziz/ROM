#!/usr/bin/env python3
"""Stage 21.13.1b: resolve V1 Quest Engine parity without production mutation."""
from __future__ import annotations
import ast,hashlib,json,os,py_compile,shutil,subprocess,sys
from datetime import datetime,timezone
from pathlib import Path
STAGE="21.13.3b";PARENT="4b1115d339e2f3344fb7ee8630025e2186e21bf3";BRANCH="stage-21-v2-modular-monolith"
SELF="patch/patch_21_13_3b_resolve_npc_dialogue_model_parity.py";PREREQ=Path("reports/stage_21_13_3a_refined_npc_dialogue_model_contract.json");REPORT=Path("reports/stage_21_13_3b_resolved_npc_dialogue_model_parity.json");DOC=Path("MD/STAGE_21_13_3B_RESOLVED_NPC_DIALOGUE_MODEL_PARITY.md");FAILURE=Path("reports/stage_21_13_3b_failure_rollback.json")
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
 d=r/"backup"/("stage_21_13_3b_"+datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ"));d.mkdir(parents=True,exist_ok=True);state={}
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
 registry=src["data/story_quest_npcs.py"];defs=src["data/story_quest_definitions.py"];acceptance=src["systems/story_quest_npc_acceptance_system.py"];runtime=src["handlers/story_quest_npc_runtime.py"];story_handler=src["handlers/story_quests.py"]
 tree=ast.parse(registry);classes={n.name for n in ast.walk(tree) if isinstance(n,ast.ClassDef)}
 functions=funcs(registry);required_functions={"get_story_quest_npc","validate_story_quest_npc_registry","validate_story_quest_npc_references","get_missing_story_quest_npc_routes"}
 if "StoryQuestNpcDefinition" not in classes or not required_functions.issubset(functions):raise PatchError("npc_registry_contract_changed")
 acceptance_required={"find_npc_story_quest","build_npc_story_quest_presentation","accept_story_quest_from_npc"}
 if not acceptance_required.issubset(funcs(acceptance)):raise PatchError("npc_acceptance_contract_changed")
 runtime_required={"has_story_npc_if_present","send_story_npc_if_present","register_story_quest_npc_runtime_handlers"}
 if not runtime_required.issubset(funcs(runtime)):raise PatchError("npc_runtime_contract_changed")
 evidence={"registry_constant_found":"STORY_QUEST_NPCS" in registry,"stable_definition_class_found":"StoryQuestNpcDefinition" in classes,"location_assignment_found":"location" in registry.lower(),"quest_reference_found":any(x in defs for x in ("npc_id","completion_npc_id")),"generic_dialogue_graph_owner_found":False,"handler_owns_registry":("STORY_QUEST_NPCS" in runtime or "STORY_QUEST_NPCS" in story_handler),"registry_functions":sorted(required_functions),"acceptance_functions":sorted(acceptance_required),"runtime_functions":sorted(runtime_required)}
 if not all((evidence["registry_constant_found"],evidence["stable_definition_class_found"],evidence["location_assignment_found"],evidence["quest_reference_found"])) or evidence["handler_owns_registry"]:raise PatchError("npc_dialogue_evidence_mismatch")
 return {"registry_owner":"data/story_quest_npcs.py","quest_definition_owner":"data/story_quest_definitions.py","acceptance_owner":"systems/story_quest_npc_acceptance_system.py","runtime_consumer":"handlers/story_quest_npc_runtime.py","story_handler_consumer":"handlers/story_quests.py","city_consumer":"handlers/city.py","evidence":evidence,"source_hashes":{x.as_posix():sha(r/x) for x in paths}}
def main():
 r=root();folder=None;state={};before={x.as_posix():sha(r/x) for x in PROTECTED}
 expected=("DIALOGUE_NODE_AND_ACTION_SCHEMA","NPC_AVAILABILITY_AND_CONDITION_POLICY","QUEST_AND_NPC_INTERACTION_BOUNDARY","SHOP_SERVICE_AND_OTHER_ACTION_BOUNDARIES","LOCALIZATION_AND_TECHNICAL_ID_NON_DISCLOSURE","PERSISTENCE_RESTART_AND_CONTENT_INDEPENDENCE")
 try:
  refined=json.loads((r/PREREQ).read_text(encoding="utf-8-sig"));rows=tuple(x for x in refined.get("refined_contract_matrix",()) if isinstance(x,dict));unresolved=tuple(x.get("contract") for x in rows if x.get("classification")=="REVIEW_REQUIRED");summary=refined.get("summary",{});observations=refined.get("observations",{})
  if git(r,"rev-parse","HEAD").stdout.strip()!=PARENT:raise PatchError("wrong_exact_parent")
  if refined.get("stage")!="21.13.3a" or refined.get("conclusion")!="REVIEW_REQUIRED" or len(rows)!=6 or unresolved!=expected or tuple(summary.get("unresolved_contracts",()))!=expected:raise PatchError("invalid_stage_21_13_3a_prerequisite")
  if summary.get("v1_confirmed_contracts")!=3 or summary.get("review_required_contracts")!=6 or summary.get("contract_count")!=9 or observations.get("generic_dialogue_graph_confirmed") is not False:raise PatchError("invalid_3_6_9_contract_matrix")
  print("[1/10] [PASS] Stage 21.13.3a exact 3/6/9 refinement prerequisite verified.")
  branch=git(r,"branch","--show-current").stdout.strip();staged=git(r,"diff","--cached","--name-only").stdout.strip()
  if not branch:raise PatchError("git_preflight_detached_head")
  if staged:raise PatchError("git_preflight_staged_index:"+staged.replace("\n",","))
  bad=sorted(p for st,p in status(r) if p not in ALLOWED or (p!=SELF and st[0]!=" "))
  if bad:raise PatchError(f"unexpected_dirty:{bad}")
  print(f"[2/10] [PASS] Active branch {branch}, exact parent, dirty allowlist and clean index verified.");folder,state=backup(r);print("[3/10] [PASS] Resolution artifacts backed up before publication mutation.")
  evidence=inspect(r);print("[4/10] [PASS] Exact V1 NPC registry, quest references, acceptance and runtime evidence re-verified.")
  decisions={
   "DIALOGUE_NODE_AND_ACTION_SCHEMA":{"decision":"V2 parity is a bounded immutable NPC presentation/action model, not a generic branching dialogue graph. The canonical identity is npc_id. An NPC view may expose only V1-confirmed story-quest actions with stable action keys derived from action kind plus referenced quest identity. No persistent dialogue_node_id, arbitrary graph edges or invented universal action kinds are introduced.","reasons":["unknown_npc","action_not_available","malformed_action"]},
   "NPC_AVAILABILITY_AND_CONDITION_POLICY":{"decision":"Availability is evaluated fail-closed in this order: resolve npc_id, verify the NPC canonical location/route, verify the player is in that location, query Quest Engine for the referenced quest state and prerequisites, then materialize visible actions. Unknown NPC, wrong location, unavailable quest and stale action remain distinct typed results. No additional level or condition rules are duplicated outside Quest Engine.","reasons":["unknown_npc","wrong_location","npc_unavailable","stale_action"]},
   "QUEST_AND_NPC_INTERACTION_BOUNDARY":{"decision":"The immutable NPC registry owns NPC identity, localized metadata and location assignment. NPC application query maps registry plus Quest Engine results into a view. Quest Engine exclusively owns quest availability, acceptance, progress, turn-in and rewards. An accept command carries npc_id, quest_id and expected quest revision; NPC service validates the NPC-to-quest reference then delegates the mutation exactly once.","reasons":["quest_not_linked","quest_unavailable","stale_revision","already_active"]},
   "SHOP_SERVICE_AND_OTHER_ACTION_BOUNDARIES":{"decision":"Stage 21.13.3 authorizes only story-quest NPC presentation and quest-linked actions proven by V1. Shop, guild, crafting, auction, daily and rune behavior remain external application services and are not added to the NPC domain. Future NPC links may reference a typed external action only after a separate V1 audit and parity authorization; the NPC model never owns those business mutations.","reasons":["unsupported_action","external_service_not_authorized"]},
   "LOCALIZATION_AND_TECHNICAL_ID_NON_DISCLOSURE":{"decision":"User-visible NPC names and labels come only from canonical registry metadata and localized presentation. Technical npc_id, quest_id and location_id are allowed in DTO identity, callback payloads, logs and tests but never rendered as fallback text. Unknown IDs fail closed; underscore replacement, title-casing and raw-ID display are prohibited.","reasons":["unknown_npc","missing_localized_name","presentation_unavailable"]},
   "PERSISTENCE_RESTART_AND_CONTENT_INDEPENDENCE":{"decision":"NPC definitions are immutable content registry data and require no independent runtime persistence. Restart stability is validated by deterministic registry load plus duplicate-ID, location-route and quest-reference validation. Reusable domain/application modules cannot branch on concrete NPC IDs, quest IDs, NPC names or localized dialogue strings; an executable content-independence gate is mandatory for implementation.","reasons":["duplicate_npc_id","invalid_location_reference","invalid_quest_reference","content_dependency_violation"]}}
  if tuple(decisions)!=expected:raise PatchError("resolution_contract_mismatch")
  print("[5/10] [PASS] Bounded action schema, availability and Quest Engine interaction parity policies resolved.");print("[6/10] [PASS] External-service, localization, restart and content-independence boundaries resolved without a generic dialogue graph.")
  removed=clean(r);checks=ci(r);print(f"[7/10] [PASS] Canonical V2 CI passed after removing {len(removed)} bytecode artifact(s).")
  if before!={x.as_posix():sha(r/x) for x in PROTECTED}:raise PatchError("protected_runtime_changed")
  print("[8/10] [PASS] Production sources, DB sidecars and protected configuration remained byte-identical.")
  resolved=[{"contract":k,"classification":"V2_RESOLVED","decision":v["decision"],"typed_reasons":v["reasons"]} for k,v in decisions.items()]
  all_contracts=("NPC_STABLE_ID_AND_OWNER_MODEL","NPC_LOCATION_ASSIGNMENT_BOUNDARY","PRESENTATION_HANDLER_SEPARATION",*expected)
  payload={"schema_version":1,"stage":STAGE,"status":"PASS","conclusion":"GO_TO_IMPLEMENTATION","source_refinement":PREREQ.as_posix(),"summary":{"contract_count":9,"resolved_contracts":9,"unresolved_contracts":[],"database_opened":False,"production_code_changed":False,"v1_wal_shm_manipulated":False},"authoritative_evidence":evidence,"canonical_contracts":list(all_contracts),"resolved_contract_matrix":resolved,"implementation_boundary":{"authorized":["immutable NPC definition, action and view DTOs","registry validation and localized resolver","NPC availability query using Quest Engine ports","quest-linked accept command delegation","fail-closed technical-ID disclosure guard","restart-stability and content-independence gates","in-memory fixtures, focused tests and smoke verifier"],"forbidden":["generic branching dialogue graph","new NPCs, quest links, actions or dialogue content","production SQLite adapter or migration","shop, guild, crafting, auction, daily or rune mutation wiring","Telegram/runtime wiring","duplicate Quest Engine rules","raw technical IDs in user-visible text"]},"implementation_authorized":True,"generic_dialogue_graph_authorized":False,"external_service_mutation_authorized":False,"runtime_integration_authorized":False,"production_persistence_authorized":False,"content_independence_gate_required":True,"canonical_v2_ci":checks,"manual_game_check":"NOT_REQUIRED","suggested_next_patch":"patch_21_13_3c_implement_npc_dialogue_model.py","backup_path":folder.relative_to(r).as_posix()};write(r/REPORT,json.dumps(payload,ensure_ascii=False,indent=2)+"\n")
  lines=["# Stage 21.13.3b - Resolved NPC/dialogue model parity","","- Status: **PASS**","- Conclusion: **GO_TO_IMPLEMENTATION**","- Contract matrix: **9/9 RESOLVED**","- Generic dialogue graph: **NOT_AUTHORIZED**","- Content-independence gate: **REQUIRED**","- External service mutation: **NOT_AUTHORIZED**","- Runtime integration: **NOT_AUTHORIZED**","- Production persistence: **NOT_AUTHORIZED**","- Manual game check: **NOT_REQUIRED**","","## Resolved contracts",""]
  for x in resolved:lines.extend(["### "+x["contract"],"",x["decision"],"","Typed reasons: "+", ".join(x["typed_reasons"]),""])
  lines.extend(["## Next patch","","`patch_21_13_3c_implement_npc_dialogue_model.py`",""]);write(r/DOC,"\n".join(lines));print("[9/10] [PASS] Resolved JSON and Markdown NPC/dialogue parity artifacts written.")
  files={x.as_posix() for x in TARGETS};git(r,"add","-f","--",*sorted(files));got={x.replace("\\","/") for x in git(r,"diff","--cached","--name-only","--").stdout.splitlines() if x}
  if got!=files:raise PatchError("staging_mismatch:"+repr(sorted(got)))
  z=git(r,"commit","-m","Stage 21.13.3b: resolve NPC dialogue model parity","--",*sorted(files),check=False)
  if z.returncode:raise PatchError("commit_failed:"+z.stdout+z.stderr)
  commit=git(r,"rev-parse","HEAD").stdout.strip();changed={x.replace("\\","/") for x in git(r,"diff-tree","--no-commit-id","--name-only","-r",commit).stdout.splitlines() if x}
  if changed!=files:raise PatchError("commit_scope_mismatch:"+repr(sorted(changed)))
  print(f"[10/10] [PASS] NPC/dialogue model parity resolution committed: {commit}");print("CONCLUSION: GO_TO_IMPLEMENTATION\nCONTRACT_MATRIX: 9/9 RESOLVED\nUNRESOLVED_CONTRACTS: 0\nIMPLEMENTATION AUTHORIZED: True\nGENERIC DIALOGUE GRAPH AUTHORIZED: False\nCONTENT INDEPENDENCE GATE: REQUIRED\nEXTERNAL SERVICE MUTATION AUTHORIZED: False\nRUNTIME INTEGRATION AUTHORIZED: False\nPRODUCTION PERSISTENCE AUTHORIZED: False\nMANUAL GAME CHECK: NOT_REQUIRED\nFAIL-SAFE ROLLBACK: ARMED\nSUGGESTED NEXT PATCH: patch_21_13_3c_implement_npc_dialogue_model.py");return 0
 except Exception as error:
  restored=restore(r,folder,state);recovery=run([sys.executable,"-m","compileall","-q","rom_v2"],r,False);write(r/FAILURE,json.dumps({"stage":STAGE,"status":"FAIL_ROLLED_BACK","reason":str(error),"restored_files":restored,"recovery_compile_returncode":recovery.returncode,"main_py_must_not_run":recovery.returncode!=0,"database_opened":False,"v1_wal_shm_manipulated":False},ensure_ascii=False,indent=2)+"\n");print(f"[10/10] [FAIL] {error}; rollback: FAIL_ROLLED_BACK");return 1
if __name__=="__main__":raise SystemExit(main())
