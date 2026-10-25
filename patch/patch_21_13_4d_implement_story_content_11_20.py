#!/usr/bin/env python3
"""Stage 21.13.4d: implement API-ready Story content package 11-20."""
from __future__ import annotations
import hashlib,json,os,py_compile,shutil,subprocess,sys
from datetime import datetime,timezone
from pathlib import Path
STAGE="21.13.4d";PARENT="9530c6b113abe01461d6fdf08d7e1e59e1c55284"
SELF="patch/patch_21_13_4d_implement_story_content_11_20.py";PREREQ=Path("reports/stage_21_13_4b_resolved_story_content_1_50_parity.json");CURRENT=Path("reports/stage_21_13_5c_story_content_51_60_implementation.json")
DOMAIN=Path("rom_v2/domain/story_content.py");CONTENT=Path("rom_v2/content/story_start_path_11_20.py");TEST=Path("tests_v2/test_story_content_11_20.py");TOOL=Path("tools/check_stage_21_13_4d_story_content_11_20.py");GATE=Path("tools/verify_stage_21_13_4d_story_content_11_20.py");REPORT=Path("reports/stage_21_13_4d_story_content_11_20_implementation.json");DOC=Path("MD/STAGE_21_13_4D_STORY_CONTENT_11_20_IMPLEMENTATION.md");FAILURE=Path("reports/stage_21_13_4d_failure_rollback.json")
TARGETS=(Path(SELF),CONTENT,TEST,TOOL,GATE,REPORT,DOC);ALLOWED={SELF,"ROM_FULL_DUMP.txt",FAILURE.as_posix()};PROTECTED=(Path("main.py"),Path("game.db-wal"),Path("game.db-shm"))
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
DOMAIN_SRC='from __future__ import annotations\nfrom dataclasses import dataclass\nfrom types import MappingProxyType\nfrom typing import Any, Mapping\n\n@dataclass(frozen=True, slots=True)\nclass V2StoryQuestContentRecord:\n    quest_id: str\n    number: int\n    title: str\n    quest_type: str\n    location_id: str\n    unlock_level: int\n    previous_quest_id: str | None\n    giver_npc_id: str\n    turn_in_npc_id: str\n    target_quantity: int\n    description: str\n    objective_text: str\n    acceptance_text: str\n    completion_text: str\n    reward_exp: int\n    reward_gold: float\n    metadata: Mapping[str, Any]\n    def __post_init__(self) -> None:\n        if not self.quest_id.strip() or not (1 <= self.number <= 100): raise ValueError("invalid_quest_identity")\n        if not self.title.strip() or not self.quest_type.strip(): raise ValueError("invalid_quest_text")\n        if not self.location_id.strip() or self.unlock_level <= 0 or self.target_quantity <= 0: raise ValueError("invalid_quest_contract")\n        if not self.giver_npc_id.strip() or not self.turn_in_npc_id.strip(): raise ValueError("invalid_npc_reference")\n        if self.reward_exp < 0 or self.reward_gold < 0: raise ValueError("invalid_reward")\n        object.__setattr__(self,"metadata",MappingProxyType(dict(self.metadata)))\n'
CONTENT_HEADER='from __future__ import annotations\nfrom rom_v2.domain.story_content import V2StoryQuestContentRecord\n\n'
TEST_SRC='import unittest\nfrom rom_v2.content.story_start_path_11_20 import STORY_START_PATH_11_20,validate_story_start_path_11_20\nclass TestStory1120(unittest.TestCase):\n def test_manifest(self): validate_story_start_path_11_20();self.assertEqual([q.number for q in STORY_START_PATH_11_20],list(range(11,21)))\n def test_bridge_chain(self):\n  self.assertEqual(STORY_START_PATH_11_20[0].previous_quest_id,"start_path_010_investigation_begins")\n  for a,b in zip(STORY_START_PATH_11_20,STORY_START_PATH_11_20[1:]):self.assertEqual(b.previous_quest_id,a.quest_id)\n def test_contract(self):\n  for q in STORY_START_PATH_11_20:self.assertEqual((q.unlock_level,q.location_id,q.reward_exp,q.reward_gold),(2,"start_path",36,0.43))\n def test_text(self):\n  for q in STORY_START_PATH_11_20:\n   t=" ".join((q.title,q.description,q.objective_text,q.acceptance_text,q.completion_text));self.assertNotIn("start_path",t);self.assertNotIn("глава",t.lower())\n def test_turn_in_14(self): self.assertEqual(STORY_START_PATH_11_20[3].quest_type,"TURN_IN")\nif __name__=="__main__":unittest.main()\n'
TOOL_SRC='from pathlib import Path\nimport sys\nROOT=Path(__file__).resolve().parent.parent;sys.path.insert(0,str(ROOT))\nfrom rom_v2.content.story_start_path_11_20 import STORY_START_PATH_11_20,validate_story_start_path_11_20\nvalidate_story_start_path_11_20();assert len(STORY_START_PATH_11_20)==10\nprint("Stage 21.13.4d Story content 11-20 smoke: PASS")\n'
GATE_SRC='from pathlib import Path\nimport ast,sys\nROOT=Path(__file__).resolve().parent.parent;path=ROOT/"rom_v2/content/story_start_path_11_20.py";text=path.read_text(encoding="utf-8");ast.parse(text)\nhits=[x for x in ("глава","start_path_021","dark_forest_051") if x.lower() in text.lower()]\nif hits:print("Story content 11-20 boundary: FAIL",hits);sys.exit(1)\nprint("Stage 21.13.4d Story content 11-20 boundary: PASS")\n'
def main():
 r=root();folder=None;state={};before={x.as_posix():sha(r/x) for x in PROTECTED};reference_before={x.relative_to(r).as_posix():sha(x) for x in (r/"Квести").rglob("*") if x.is_file()}
 try:
  pre=json.loads((r/PREREQ).read_text(encoding="utf-8-sig"));summary=pre.get("summary",{});current=json.loads((r/CURRENT).read_text(encoding="utf-8-sig"))
  if git(r,"rev-parse","HEAD").stdout.strip()!=PARENT:raise PatchError("wrong_exact_parent")
  if pre.get("stage")!="21.13.4b" or pre.get("conclusion")!="GO_TO_IMPLEMENTATION" or summary.get("resolved_contracts")!=11 or summary.get("canonical_record_count")!=50:raise PatchError("invalid_stage_21_13_4b_prerequisite")
  if current.get("stage")!="21.13.5c" or current.get("conclusion")!="API_READY_PACKAGE_51_60" or current.get("tests",{}).get("content_boundary")!="PASS":raise PatchError("invalid_current_head_prerequisite")
  print("[1/10] [PASS] Stage 21.13.4b 11/11 parity and current API-ready head prerequisites verified.")
  branch=git(r,"branch","--show-current").stdout.strip();staged=git(r,"diff","--cached","--name-only").stdout.strip()
  if not branch:raise PatchError("git_preflight_detached_head")
  if staged:raise PatchError("git_preflight_staged_index:"+staged.replace("\n",","))
  bad=sorted(p for st,p in status(r) if p not in ALLOWED or (p!=SELF and st[0]!=" "))
  if bad:raise PatchError("unexpected_dirty:"+repr(bad))
  print(f"[2/10] [PASS] Active branch {branch}, exact parent, dirty allowlist and clean index verified.");folder,state=backup(r);print("[3/10] [PASS] Fail-safe backup created before production mutation.")
  candidate=r/"Квести/ROM_квести_Початок_Шляху_candidate.json";data=json.loads(candidate.read_text(encoding="utf-8-sig"));quests=data.get("quests")
  if not isinstance(quests,list) or len(quests)!=50:raise PatchError("canonical_candidate_not_50")
  package=quests[10:20]
  if [q.get("number") for q in package]!=list(range(11,21)):raise PatchError("package_11_20_identity_mismatch")
  if package[0].get("previous_quest_id")!="start_path_010_investigation_begins":raise PatchError("bridge_10_11_mismatch")
  records=[]
  rewards=[]
  for q in package:
   reward=q.get("reward") or {};rewards.append((reward.get("exp"),reward.get("gold")));known={"quest_id","number","title","quest_type","location_id","unlock_level","previous_quest_id","giver_npc_id","turn_in_npc_id","target_quantity","description","objective_text","acceptance_text","completion_text","reward"};metadata={k:v for k,v in q.items() if k not in known}
   records.append("V2StoryQuestContentRecord("+", ".join([repr(q.get("quest_id")),repr(q.get("number")),repr(q.get("title")),repr(q.get("quest_type")),repr(q.get("location_id")),repr(q.get("unlock_level")),repr(q.get("previous_quest_id")),repr(q.get("giver_npc_id")),repr(q.get("turn_in_npc_id")),repr(q.get("target_quantity")),repr(q.get("description")),repr(q.get("objective_text")),repr(q.get("acceptance_text")),repr(q.get("completion_text")),repr(reward.get("exp")),repr(reward.get("gold")),repr({"reward_formula":reward.get("formula"),**metadata})])+")")
  if len(set(rewards))!=1:raise PatchError("package_11_20_reward_matrix_not_uniform:"+repr(rewards))
  reward_exp,reward_gold=rewards[0]
  content=CONTENT_HEADER+"STORY_START_PATH_11_20 = (\n    "+",\n    ".join(records)+",\n)\n\ndef validate_story_start_path_11_20() -> None:\n    quests=STORY_START_PATH_11_20\n    if len(quests)!=10 or [q.number for q in quests]!=list(range(11,21)): raise ValueError('invalid_package_identity')\n    if len({q.quest_id for q in quests})!=10: raise ValueError('duplicate_quest_id')\n    if quests[0].previous_quest_id!='start_path_010_investigation_begins': raise ValueError('invalid_story_bridge')\n    for previous,current in zip(quests,quests[1:]):\n        if current.previous_quest_id!=previous.quest_id: raise ValueError('invalid_predecessor_chain')\n    for quest in quests:\n        if quest.unlock_level!=2 or quest.location_id!='start_path': raise ValueError('invalid_level_or_location')\n        if quest.reward_exp!="+repr(reward_exp)+" or abs(quest.reward_gold-"+repr(reward_gold)+")>1e-9: raise ValueError('invalid_reward_parity')\n\nvalidate_story_start_path_11_20()\n"
  for path,src in ((CONTENT,content),(TEST,TEST_SRC),(TOOL,TOOL_SRC),(GATE,GATE_SRC)):write(r/path,src)
  print("[4/10] [PASS] Canonical Start Path package 11-20 generated from candidate JSON using existing Story content DTO.")
  for x in (Path(SELF),CONTENT,TEST,TOOL,GATE):py_compile.compile(str(r/x),doraise=True)
  print("[5/10] [PASS] Python compile gate passed for patch, content, tests and verifiers.")
  env=os.environ.copy();env["PYTHONDONTWRITEBYTECODE"]="1"
  t=run([sys.executable,"-m","unittest","-v","tests_v2.test_story_content_11_20"],r,False,env);sm=run([sys.executable,str(r/TOOL)],r,False,env);ga=run([sys.executable,str(r/GATE)],r,False,env)
  if t.returncode or sm.returncode or ga.returncode:raise PatchError("targeted_verification_failed:"+t.stdout+t.stderr+sm.stdout+sm.stderr+ga.stdout+ga.stderr)
  print("[6/10] [PASS] IDs, 10-to-11 bridge, chain, level, exact rewards, localization and package-boundary tests passed.")
  removed=clean(r);checks=canonical_ci(r);print(f"[7/10] [PASS] Canonical V2 CI passed after removing {len(removed)} bytecode artifact(s).")
  if before!={x.as_posix():sha(r/x) for x in PROTECTED}:raise PatchError("protected_runtime_changed")
  reference_after={x.relative_to(r).as_posix():sha(x) for x in (r/"Квести").rglob("*") if x.is_file()}
  if reference_before!=reference_after:raise PatchError("canonical_reference_changed")
  print("[8/10] [PASS] Existing V1/V2 sources, canonical references, DB sidecars and protected configuration remained byte-identical except authorized package files.")
  rep={"schema_version":1,"stage":STAGE,"status":"PASS","conclusion":"API_READY_PACKAGE_11_20","parent":PARENT,"candidate_sha256":sha(candidate),"implemented_files":[CONTENT.as_posix()],"reused_owner":DOMAIN.as_posix(),"package":{"range":"11-20","count":10,"numbers":list(range(11,21)),"level":2,"location_id":"start_path","bridge_predecessor":"start_path_010_investigation_begins","reward_exp_each":reward_exp,"reward_gold_each":reward_gold},"tests":{"targeted":"PASS","smoke":"PASS","content_boundary":"PASS"},"packages_21_50":"NOT_CONNECTED","runtime_integration":"NOT_CONNECTED","production_persistence":"NOT_CONNECTED","canonical_reference_changed":False,"database_opened":False,"v1_wal_shm_manipulated":False,"manual_game_check":"NOT_REQUIRED_API_ONLY","canonical_v2_ci":checks};write(r/REPORT,json.dumps(rep,ensure_ascii=False,indent=2)+"\n");write(r/DOC,"# Stage 21.13.4d - Story content 11-20 implementation\n\n- Status: **PASS**\n- Conclusion: **API_READY_PACKAGE_11_20**\n- Canonical records: **10/10**\n- Bridge 10-11: **PASS**\n- Level gate: **2**\n- Reward parity: **"+str(reward_exp)+" EXP / "+str(reward_gold)+" gold each**\n- Packages 21-50: **NOT_CONNECTED**\n- Runtime integration: **NOT_CONNECTED**\n- Production persistence: **NOT_CONNECTED**\n- Manual game check: **NOT_REQUIRED_API_ONLY**\n");print("[9/10] [PASS] Machine report and Markdown package documentation written.")
  files={x.as_posix() for x in TARGETS};git(r,"add","-f","--",*sorted(files));got={x.replace("\\","/") for x in git(r,"diff","--cached","--name-only").stdout.splitlines() if x}
  if got!=files:raise PatchError("staging_mismatch:"+repr(sorted(got)))
  z=git(r,"commit","-m","Stage 21.13.4d: implement Story content 11-20","--",*sorted(files),check=False)
  if z.returncode:raise PatchError("commit_failed:"+z.stdout+z.stderr)
  commit=git(r,"rev-parse","HEAD").stdout.strip();changed={x.replace("\\","/") for x in git(r,"diff-tree","--no-commit-id","--name-only","-r",commit).stdout.splitlines() if x}
  if changed!=files:raise PatchError("commit_scope_mismatch:"+repr(sorted(changed)))
  print(f"[10/10] [PASS] Story content package 11-20 committed: {commit}");print("CONCLUSION: API_READY_PACKAGE_11_20\nPATCH STATUS: PASS\nCANONICAL RECORDS: 10/10\nBRIDGE 10-11: PASS\nPACKAGES 21-50: NOT_CONNECTED\nRUNTIME INTEGRATION: NOT_CONNECTED\nPRODUCTION PERSISTENCE: NOT_CONNECTED\nMANUAL GAME CHECK: NOT_REQUIRED_API_ONLY\nFAIL-SAFE ROLLBACK: ARMED\nSUGGESTED NEXT PATCH: patch_21_13_4e_implement_story_content_21_30.py");return 0
 except Exception as e:
  restored=restore(r,folder,state);recovery=run([sys.executable,"-m","compileall","-q","rom_v2"],r,False);write(r/FAILURE,json.dumps({"stage":STAGE,"status":"FAIL_ROLLED_BACK","reason":str(e),"restored_files":restored,"recovery_compile_returncode":recovery.returncode,"main_py_must_not_run":recovery.returncode!=0,"database_opened":False,"canonical_reference_changed":False,"v1_wal_shm_manipulated":False},ensure_ascii=False,indent=2)+"\n");print(f"[10/10] [FAIL] {e}; rollback: FAIL_ROLLED_BACK");return 1
if __name__=="__main__":raise SystemExit(main())
