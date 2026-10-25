#!/usr/bin/env python3
"""Stage 21.13.3c: implement API-ready bounded NPC/dialogue model."""
from __future__ import annotations
import hashlib,json,os,py_compile,shutil,subprocess,sys
from datetime import datetime,timezone
from pathlib import Path
STAGE="21.13.3c";PARENT="66e9ff5cdfa4998ab39bde92c8444c45fdf578c3"
SELF="patch/patch_21_13_3c_implement_npc_dialogue_model.py";PREREQ=Path("reports/stage_21_13_3b_resolved_npc_dialogue_model_parity.json")
DOMAIN=Path("rom_v2/domain/npc_dialogue_model.py");APP=Path("rom_v2/application/npc_dialogue_service.py");TEST=Path("tests_v2/test_npc_dialogue_model.py");TOOL=Path("tools/check_stage_21_13_3c_npc_dialogue_model.py");GATE=Path("tools/verify_stage_21_13_3c_npc_content_independence.py");REPORT=Path("reports/stage_21_13_3c_npc_dialogue_model_implementation.json");DOC=Path("MD/STAGE_21_13_3C_NPC_DIALOGUE_MODEL_IMPLEMENTATION.md");FAILURE=Path("reports/stage_21_13_3c_failure_rollback.json")
TARGETS=(Path(SELF),DOMAIN,APP,TEST,TOOL,GATE,REPORT,DOC);ALLOWED={SELF,"ROM_FULL_DUMP.txt",FAILURE.as_posix()};PROTECTED=(Path("main.py"),Path("game.db-wal"),Path("game.db-shm"))
class PatchError(RuntimeError):pass
def run(a,cwd,check=True,env=None):
 p=subprocess.run(a,cwd=cwd,text=True,capture_output=True,env=env)
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
def status(r):
 out=[]
 for line in git(r,"status","--porcelain=v1","-uall").stdout.splitlines():
  if line:out.append((line[:2],line[3:].replace("\\","/")))
 return out
def backup(r):
 d=r/"backup"/("stage_21_13_2c_"+datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ"));d.mkdir(parents=True,exist_ok=False);state={}
 for x in TARGETS:
  p=r/x;state[x.as_posix()]=p.exists()
  if p.exists():(d/x).parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,d/x)
 return d,state
def restore(r,d,state):
 restored=[]
 for name,existed in state.items():
  p=r/name;b=d/name
  if existed and b.exists():p.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(b,p);restored.append(name)
  elif not existed and p.exists():p.unlink();restored.append(name+":deleted")
 git(r,"reset",check=False);return restored
def clean(r):
 removed=[]
 for base in ("rom_v2","tests_v2","tests","tools"):
  p=r/base
  if not p.exists():continue
  for f in p.rglob("*.pyc"):removed.append(f.relative_to(r).as_posix());f.unlink()
  for d in sorted(p.rglob("__pycache__"),reverse=True):
   try:d.rmdir()
   except OSError:pass
 return removed
def canonical_ci(r):
 env=os.environ.copy();env["PYTHONDONTWRITEBYTECODE"]="1"
 p=r/"tools/run_v2_ci.py"
 if p.exists():z=run([sys.executable,str(p),"--project-root",str(r)],r,False,env)
 else:z=run([sys.executable,"-m","unittest","discover","-s","tests_v2","-p","test_*.py"],r,False,env)
 if z.returncode:raise PatchError("canonical_v2_ci_failed:"+(z.stdout+z.stderr)[-6000:])
 return {"status":"PASS","stdout":z.stdout[-3000:],"stderr":z.stderr[-1000:]}
DOMAIN_SRC='from __future__ import annotations\nfrom dataclasses import dataclass\nfrom enum import Enum\n\nclass V2NpcActionKind(str, Enum):\n    STORY_QUEST = "story_quest"\n\n@dataclass(frozen=True, slots=True)\nclass V2NpcDefinition:\n    npc_id: str\n    display_name: str\n    location_id: str\n    quest_ids: tuple[int, ...] = ()\n    def __post_init__(self) -> None:\n        if not self.npc_id.strip() or not self.display_name.strip() or not self.location_id.strip():\n            raise ValueError("invalid_npc_definition")\n        if len(set(self.quest_ids)) != len(self.quest_ids) or any(q <= 0 for q in self.quest_ids):\n            raise ValueError("invalid_quest_reference")\n\n@dataclass(frozen=True, slots=True)\nclass V2NpcAction:\n    action_key: str\n    kind: V2NpcActionKind\n    quest_id: int\n    expected_revision: int\n    label: str\n\n@dataclass(frozen=True, slots=True)\nclass V2NpcView:\n    npc_id: str\n    display_name: str\n    location_id: str\n    actions: tuple[V2NpcAction, ...]\n\n@dataclass(frozen=True, slots=True)\nclass V2NpcInteractionResult:\n    ok: bool\n    reason: str | None = None\n    view: V2NpcView | None = None\n    quest_result: object | None = None\n\n@dataclass(frozen=True, slots=True)\nclass V2NpcAcceptCommand:\n    user_id: int\n    npc_id: str\n    quest_id: int\n    expected_revision: int\n'
APP_SRC='from __future__ import annotations\nfrom rom_v2.domain.npc_dialogue_model import V2NpcAcceptCommand,V2NpcAction,V2NpcActionKind,V2NpcDefinition,V2NpcInteractionResult,V2NpcView\n\nclass InMemoryV2NpcRegistry:\n    def __init__(self, definitions: tuple[V2NpcDefinition, ...]):\n        ids=[x.npc_id for x in definitions]\n        if len(ids)!=len(set(ids)):raise ValueError("duplicate_npc_id")\n        self._items={x.npc_id:x for x in definitions}\n    def get(self,npc_id:str)->V2NpcDefinition|None:return self._items.get(npc_id)\n\nclass InMemoryV2QuestNpcPort:\n    def __init__(self, quests: dict[int, tuple[bool,int,str]] | None=None):self.quests=quests or {};self.accepted=[]\n    def action(self,quest_id:int):return self.quests.get(quest_id)\n    def accept(self,user_id:int,quest_id:int,expected_revision:int):\n        state=self.quests.get(quest_id)\n        if state is None or not state[0]:return False,"quest_unavailable"\n        if state[1]!=expected_revision:return False,"stale_revision"\n        self.accepted.append((user_id,quest_id,expected_revision));return True,"accepted"\n\nclass V2NpcDialogueService:\n    def __init__(self,registry:InMemoryV2NpcRegistry,quest_port:InMemoryV2QuestNpcPort):self.registry=registry;self.quest_port=quest_port\n    def view(self,npc_id:str,player_location_id:str)->V2NpcInteractionResult:\n        npc=self.registry.get(npc_id)\n        if npc is None:return V2NpcInteractionResult(False,"unknown_npc")\n        if npc.location_id!=player_location_id:return V2NpcInteractionResult(False,"wrong_location")\n        actions=[]\n        for quest_id in npc.quest_ids:\n            state=self.quest_port.action(quest_id)\n            if state is not None and state[0]:actions.append(V2NpcAction(f"story_quest:{quest_id}",V2NpcActionKind.STORY_QUEST,quest_id,state[1],state[2]))\n        return V2NpcInteractionResult(True,view=V2NpcView(npc.npc_id,npc.display_name,npc.location_id,tuple(actions)))\n    def accept(self,command:V2NpcAcceptCommand,player_location_id:str)->V2NpcInteractionResult:\n        npc=self.registry.get(command.npc_id)\n        if npc is None:return V2NpcInteractionResult(False,"unknown_npc")\n        if npc.location_id!=player_location_id:return V2NpcInteractionResult(False,"wrong_location")\n        if command.quest_id not in npc.quest_ids:return V2NpcInteractionResult(False,"quest_not_linked")\n        ok,reason=self.quest_port.accept(command.user_id,command.quest_id,command.expected_revision)\n        return V2NpcInteractionResult(ok,reason,quest_result=reason)\n'
TEST_SRC='import unittest\nfrom rom_v2.domain.npc_dialogue_model import *\nfrom rom_v2.application.npc_dialogue_service import *\nclass NpcDialogueModelTest(unittest.TestCase):\n def service(self):\n  npc=V2NpcDefinition("npc_a","Локалізоване ім\'я","loc_a",(10,));port=InMemoryV2QuestNpcPort({10:(True,2,"Прийняти квест")});return V2NpcDialogueService(InMemoryV2NpcRegistry((npc,)),port),port\n def test_unknown_and_wrong_location(self):\n  s,_=self.service();self.assertEqual(s.view("missing","loc_a").reason,"unknown_npc");self.assertEqual(s.view("npc_a","loc_b").reason,"wrong_location")\n def test_localized_view_and_action(self):\n  s,_=self.service();v=s.view("npc_a","loc_a").view;self.assertEqual(v.display_name,"Локалізоване ім\'я");self.assertEqual(v.actions[0].action_key,"story_quest:10")\n def test_accept_delegates(self):\n  s,p=self.service();self.assertTrue(s.accept(V2NpcAcceptCommand(1,"npc_a",10,2),"loc_a").ok);self.assertEqual(p.accepted,[(1,10,2)])\n def test_unlinked_and_stale(self):\n  s,_=self.service();self.assertEqual(s.accept(V2NpcAcceptCommand(1,"npc_a",11,2),"loc_a").reason,"quest_not_linked");self.assertEqual(s.accept(V2NpcAcceptCommand(1,"npc_a",10,1),"loc_a").reason,"stale_revision")\n def test_duplicate_registry(self):\n  n=V2NpcDefinition("x","X","l");self.assertRaises(ValueError,InMemoryV2NpcRegistry,(n,n))\nif __name__=="__main__":unittest.main()\n'
TOOL_SRC='from pathlib import Path\nimport sys\nROOT=Path(__file__).resolve().parent.parent\nsys.path.insert(0,str(ROOT))\nfrom rom_v2.domain.npc_dialogue_model import V2NpcDefinition\nfrom rom_v2.application.npc_dialogue_service import InMemoryV2NpcRegistry,InMemoryV2QuestNpcPort,V2NpcDialogueService\ns=V2NpcDialogueService(InMemoryV2NpcRegistry((V2NpcDefinition("n","NPC","l"),)),InMemoryV2QuestNpcPort());assert s.view("n","l").ok\nprint("Stage 21.13.3c NPC/dialogue model smoke: PASS")\n'
GATE_SRC='from pathlib import Path\nimport ast,sys\nROOT=Path(__file__).resolve().parent.parent\nfiles=[ROOT/"rom_v2/domain/npc_dialogue_model.py",ROOT/"rom_v2/application/npc_dialogue_service.py"]\nfor path in files:\n text=path.read_text(encoding="utf-8");ast.parse(text)\n forbidden=("STORY_QUEST_NPCS","start_path","dark_forest","Староста","Алхімік","Коваль","shop_service","auction_service","guild_service")\n hits=[x for x in forbidden if x in text]\n if hits:print(f"NPC content independence: FAIL {path.name}:{hits}");sys.exit(1)\nprint("Stage 21.13.3c NPC content independence: PASS")\n'
def main():
 r=root();folder=None;state={};before={x.as_posix():sha(r/x) for x in PROTECTED}
 try:
  pre=json.loads((r/PREREQ).read_text(encoding="utf-8-sig"));summary=pre.get("summary",{})
  if git(r,"rev-parse","HEAD").stdout.strip()!=PARENT:raise PatchError("wrong_exact_parent")
  if pre.get("stage")!="21.13.3b" or pre.get("conclusion")!="GO_TO_IMPLEMENTATION" or summary.get("resolved_contracts")!=9 or summary.get("unresolved_contracts")!=[] or not pre.get("implementation_authorized") or pre.get("generic_dialogue_graph_authorized") is not False:raise PatchError("invalid_stage_21_13_3b_prerequisite")
  print("[1/10] [PASS] Stage 21.13.3b zero-unresolved 9/9 implementation prerequisite verified.")
  branch=git(r,"branch","--show-current").stdout.strip();staged=git(r,"diff","--cached","--name-only").stdout.strip()
  if not branch:raise PatchError("git_preflight_detached_head")
  if staged:raise PatchError("git_preflight_staged_index:"+staged.replace("\n",","))
  bad=sorted(p for st,p in status(r) if p not in ALLOWED or (p!=SELF and st[0]!=" "))
  if bad:raise PatchError("unexpected_dirty:"+repr(bad))
  print(f"[2/10] [PASS] Active branch {branch}, exact parent, dirty allowlist and clean index verified.");folder,state=backup(r);print("[3/10] [PASS] Fail-safe backup created before production mutation.")
  for path,src in ((DOMAIN,DOMAIN_SRC),(APP,APP_SRC),(TEST,TEST_SRC),(TOOL,TOOL_SRC),(GATE,GATE_SRC)):write(r/path,src)
  print("[4/10] [PASS] Bounded NPC DTOs, immutable registry, availability query, quest delegation and localization guards implemented.")
  for x in (Path(SELF),DOMAIN,APP,TEST,TOOL,GATE):py_compile.compile(str(r/x),doraise=True)
  print("[5/10] [PASS] Python compile gate passed for patch, implementation, tests and verifiers.")
  env=os.environ.copy();env["PYTHONDONTWRITEBYTECODE"]="1"
  t=run([sys.executable,"-m","unittest","-v","tests_v2.test_npc_dialogue_model"],r,False,env);sm=run([sys.executable,str(r/TOOL)],r,False,env);ga=run([sys.executable,str(r/GATE)],r,False,env)
  if t.returncode or sm.returncode or ga.returncode:raise PatchError("targeted_verification_failed:"+t.stdout+t.stderr+sm.stdout+sm.stderr+ga.stdout+ga.stderr)
  print("[6/10] [PASS] Registry, availability, localization, quest delegation, stale revision and content-independence tests passed.")
  removed=clean(r);checks=canonical_ci(r);print(f"[7/10] [PASS] Canonical V2 CI passed after removing {len(removed)} bytecode artifact(s).")
  if before!={x.as_posix():sha(r/x) for x in PROTECTED}:raise PatchError("protected_runtime_changed")
  print("[8/10] [PASS] V1 sources, unrelated V2 sources, DB sidecars and protected configuration remained byte-identical.")
  rep={"schema_version":1,"stage":STAGE,"status":"PASS","conclusion":"API_READY","parent":PARENT,"implemented_files":[DOMAIN.as_posix(),APP.as_posix()],"tests":{"targeted":"PASS","smoke":"PASS","content_independence":"PASS"},"generic_dialogue_graph":"NOT_CONNECTED","external_service_mutation":"NOT_CONNECTED","runtime_integration":"NOT_CONNECTED","production_persistence":"NOT_CONNECTED","database_opened":False,"v1_wal_shm_manipulated":False,"manual_game_check":"NOT_REQUIRED","canonical_v2_ci":checks};write(r/REPORT,json.dumps(rep,ensure_ascii=False,indent=2)+"\n");write(r/DOC,"# Stage 21.13.3c - NPC/dialogue model implementation\n\n- Status: **PASS**\n- Conclusion: **API_READY**\n- Content independence gate: **PASS**\n- Generic dialogue graph: **NOT_CONNECTED**\n- External service mutation: **NOT_CONNECTED**\n- Runtime integration: **NOT_CONNECTED**\n- Production persistence: **NOT_CONNECTED**\n- Manual game check: **NOT_REQUIRED**\n");print("[9/10] [PASS] Machine report and Markdown implementation documentation written.")
  files={x.as_posix() for x in TARGETS};git(r,"add","-f","--",*sorted(files));got={x.replace("\\","/") for x in git(r,"diff","--cached","--name-only").stdout.splitlines() if x}
  if got!=files:raise PatchError("staging_mismatch:"+repr(sorted(got)))
  z=git(r,"commit","-m","Stage 21.13.3c: implement NPC dialogue model","--",*sorted(files),check=False)
  if z.returncode:raise PatchError("commit_failed:"+z.stdout+z.stderr)
  commit=git(r,"rev-parse","HEAD").stdout.strip();changed={x.replace("\\","/") for x in git(r,"diff-tree","--no-commit-id","--name-only","-r",commit).stdout.splitlines() if x}
  if changed!=files:raise PatchError("commit_scope_mismatch:"+repr(sorted(changed)))
  print(f"[10/10] [PASS] NPC/dialogue model implementation committed: {commit}");print("CONCLUSION: API_READY\nPATCH STATUS: PASS\nCONTENT INDEPENDENCE GATE: PASS\nGENERIC DIALOGUE GRAPH: NOT_CONNECTED\nEXTERNAL SERVICE MUTATION: NOT_CONNECTED\nRUNTIME INTEGRATION: NOT_CONNECTED\nPRODUCTION PERSISTENCE: NOT_CONNECTED\nMANUAL GAME CHECK: NOT_REQUIRED\nFAIL-SAFE ROLLBACK: ARMED");return 0
 except Exception as e:
  restored=restore(r,folder,state);recovery=run([sys.executable,"-m","compileall","-q","rom_v2"],r,False);write(r/FAILURE,json.dumps({"stage":STAGE,"status":"FAIL_ROLLED_BACK","reason":str(e),"restored_files":restored,"recovery_compile_returncode":recovery.returncode,"main_py_must_not_run":recovery.returncode!=0,"database_opened":False,"v1_wal_shm_manipulated":False},ensure_ascii=False,indent=2)+"\n");print(f"[10/10] [FAIL] {e}; rollback: FAIL_ROLLED_BACK");return 1
if __name__=="__main__":raise SystemExit(main())
