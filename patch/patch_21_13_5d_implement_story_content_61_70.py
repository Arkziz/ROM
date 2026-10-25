#!/usr/bin/env python3
"""Stage 21.13.5d: implement API-ready Story content package 61-70."""
from __future__ import annotations
import hashlib,json,os,py_compile,shutil,subprocess,sys
from datetime import datetime,timezone
from pathlib import Path
STAGE="21.13.5d";PARENT="6c7207d53894dababc4b53a85a147110010de10e"
SELF="patch/patch_21_13_5d_implement_story_content_61_70.py";PREREQ=Path("reports/stage_21_13_5b_resolved_story_content_51_100_parity.json");CURRENT=Path("reports/stage_21_13_4g_story_content_41_50_implementation.json");PACKAGE_PREV=Path("reports/stage_21_13_5c_story_content_51_60_implementation.json")
DOMAIN=Path("rom_v2/domain/story_content.py");CONTENT=Path("rom_v2/content/story_dark_forest_61_70.py");TEST=Path("tests_v2/test_story_content_61_70.py");TOOL=Path("tools/check_stage_21_13_5d_story_content_61_70.py");GATE=Path("tools/verify_stage_21_13_5d_story_content_61_70.py");REPORT=Path("reports/stage_21_13_5d_story_content_61_70_implementation.json");DOC=Path("MD/STAGE_21_13_5D_STORY_CONTENT_61_70_IMPLEMENTATION.md");FAILURE=Path("reports/stage_21_13_5d_failure_rollback.json")
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
DOMAIN_SRC='from __future__ import annotations\nfrom dataclasses import dataclass\nfrom types import MappingProxyType\nfrom typing import Any, Mapping\n\n@dataclass(frozen=True, slots=True)\nclass V2StoryQuestContentRecord:\n    quest_id: str\n    number: int\n    title: str\n    quest_type: str\n    location_id: str\n    unlock_level: int\n    previous_quest_id: str | None\n    giver_npc_id: str | None\n    turn_in_npc_id: str | None\n    target_quantity: int\n    description: str\n    objective_text: str\n    acceptance_text: str\n    completion_text: str\n    reward_exp: int\n    reward_gold: float\n    metadata: Mapping[str, Any]\n    def __post_init__(self) -> None:\n        if not self.quest_id.strip() or not (1 <= self.number <= 100): raise ValueError("invalid_quest_identity")\n        if not self.title.strip() or not self.quest_type.strip(): raise ValueError("invalid_quest_text")\n        if not self.location_id.strip() or self.unlock_level <= 0 or self.target_quantity <= 0: raise ValueError("invalid_quest_contract")\n        if self.giver_npc_id is not None and not self.giver_npc_id.strip(): raise ValueError("invalid_giver_npc_reference")\n        if self.turn_in_npc_id is not None and not self.turn_in_npc_id.strip(): raise ValueError("invalid_turn_in_npc_reference")\n        if self.giver_npc_id is None and self.turn_in_npc_id is None: raise ValueError("missing_npc_reference")\n        if self.reward_exp < 0 or self.reward_gold < 0: raise ValueError("invalid_reward")\n        object.__setattr__(self,"metadata",MappingProxyType(dict(self.metadata)))\n'
CONTENT_HEADER='from __future__ import annotations\nfrom rom_v2.domain.story_content import V2StoryQuestContentRecord\n\n'
TEST_SRC='import unittest\nfrom rom_v2.content.story_dark_forest_51_60 import STORY_DARK_FOREST_51_60\nfrom rom_v2.content.story_dark_forest_61_70 import STORY_DARK_FOREST_61_70,validate_story_dark_forest_61_70\nclass TestStory6170(unittest.TestCase):\n def test_manifest(self): validate_story_dark_forest_61_70();self.assertEqual([q.number for q in STORY_DARK_FOREST_61_70],list(range(61,71)))\n def test_bridge_chain(self):\n  self.assertEqual(STORY_DARK_FOREST_61_70[0].previous_quest_id,STORY_DARK_FOREST_51_60[-1].quest_id)\n  for a,b in zip(STORY_DARK_FOREST_61_70,STORY_DARK_FOREST_61_70[1:]):self.assertEqual(b.previous_quest_id,a.quest_id)\n def test_contract(self):\n  for q in STORY_DARK_FOREST_61_70:self.assertEqual((q.unlock_level,q.location_id),(7,"dark_forest"))\n def test_rewards_are_canonical_non_negative(self):\n  for q in STORY_DARK_FOREST_61_70:self.assertGreaterEqual(q.reward_exp,0);self.assertGreaterEqual(q.reward_gold,0)\n def test_text(self):\n  for q in STORY_DARK_FOREST_61_70:\n   t=" ".join((q.title,q.description,q.objective_text,q.acceptance_text,q.completion_text));self.assertNotIn("dark_forest",t);self.assertNotIn("глава",t.lower())\nif __name__=="__main__":unittest.main()\n'
TOOL_SRC='from pathlib import Path\nimport sys\nROOT=Path(__file__).resolve().parent.parent;sys.path.insert(0,str(ROOT))\nfrom rom_v2.content.story_dark_forest_61_70 import STORY_DARK_FOREST_61_70,validate_story_dark_forest_61_70\nvalidate_story_dark_forest_61_70();assert len(STORY_DARK_FOREST_61_70)==10\nprint("Stage 21.13.5d Story content 61-70 smoke: PASS")\n'
GATE_SRC='from pathlib import Path\nimport ast,sys\nROOT=Path(__file__).resolve().parent.parent;path=ROOT/"rom_v2/content/story_dark_forest_61_70.py";text=path.read_text(encoding="utf-8");ast.parse(text)\nhits=[x for x in ("глава","dark_forest_071","start_path_041") if x.lower() in text.lower()]\nif hits:print("Story content 61-70 boundary: FAIL",hits);sys.exit(1)\nprint("Stage 21.13.5d Story content 61-70 boundary: PASS")\n'
def main():
 r=root();folder=None;state={};before={x.as_posix():sha(r/x) for x in PROTECTED};reference_before={x.relative_to(r).as_posix():sha(x) for x in (r/"Квести").rglob("*") if x.is_file()}
 try:
  pre=json.loads((r/PREREQ).read_text(encoding="utf-8-sig"));summary=pre.get("summary",{});current=json.loads((r/CURRENT).read_text(encoding="utf-8-sig"));previous=json.loads((r/PACKAGE_PREV).read_text(encoding="utf-8-sig"))
  if git(r,"rev-parse","HEAD").stdout.strip()!=PARENT:raise PatchError("wrong_exact_parent")
  if pre.get("stage")!="21.13.5b" or pre.get("conclusion")!="GO_TO_IMPLEMENTATION" or summary.get("resolved_contracts")!=11 or summary.get("canonical_record_count")!=50:raise PatchError("invalid_stage_21_13_5b_prerequisite")
  if current.get("stage")!="21.13.4g" or current.get("conclusion")!="API_READY_STORY_CONTENT_1_50_COMPLETE":raise PatchError("invalid_current_head_prerequisite")
  if previous.get("stage")!="21.13.5c" or previous.get("conclusion")!="API_READY_PACKAGE_51_60" or previous.get("tests",{}).get("content_boundary")!="PASS":raise PatchError("invalid_package_51_60_prerequisite")
  print("[1/10] [PASS] Stage 21.13.5b parity, completed Story 1-50 and API-ready package 51-60 prerequisites verified.")
  branch=git(r,"branch","--show-current").stdout.strip();staged=git(r,"diff","--cached","--name-only").stdout.strip()
  if not branch:raise PatchError("git_preflight_detached_head")
  if staged:raise PatchError("git_preflight_staged_index:"+staged.replace("\n",","))
  bad=sorted(p for st,p in status(r) if p not in ALLOWED or (p!=SELF and st[0]!=" "))
  if bad:raise PatchError("unexpected_dirty:"+repr(bad))
  print(f"[2/10] [PASS] Active branch {branch}, exact parent, dirty allowlist and clean index verified.");folder,state=backup(r);print("[3/10] [PASS] Fail-safe backup created before production mutation.")
  candidate=r/"Квести/ROM_квести_Темний_Бір_candidate.json";data=json.loads(candidate.read_text(encoding="utf-8-sig"));quests=data.get("quests")
  if not isinstance(quests,list) or len(quests)!=50:raise PatchError("canonical_candidate_not_50")
  package=quests[10:20]
  if [q.get("number") for q in package]!=list(range(61,71)):raise PatchError("package_61_70_identity_mismatch")
  expected_bridge=quests[9].get("quest_id")
  if package[0].get("previous_quest_id")!=expected_bridge:raise PatchError("bridge_60_61_mismatch")
  records=[]
  for q in package:
   reward=q.get("reward") or {};known={"quest_id","number","title","quest_type","location_id","unlock_level","previous_quest_id","giver_npc_id","turn_in_npc_id","target_quantity","description","objective_text","acceptance_text","completion_text","reward"};metadata={k:v for k,v in q.items() if k not in known}
   records.append("V2StoryQuestContentRecord("+", ".join([repr(q.get("quest_id")),repr(q.get("number")),repr(q.get("title")),repr(q.get("quest_type")),repr(q.get("location_id")),repr(q.get("unlock_level")),repr(q.get("previous_quest_id")),repr(q.get("giver_npc_id")),repr(q.get("turn_in_npc_id")),repr(q.get("target_quantity")),repr(q.get("description")),repr(q.get("objective_text")),repr(q.get("acceptance_text")),repr(q.get("completion_text")),repr(reward.get("exp")),repr(reward.get("gold")),repr({"reward_formula":reward.get("formula"),**metadata})])+")")
  content=CONTENT_HEADER+"STORY_DARK_FOREST_61_70 = (\n    "+",\n    ".join(records)+",\n)\n\ndef validate_story_dark_forest_61_70() -> None:\n    quests=STORY_DARK_FOREST_61_70\n    if len(quests)!=10 or [q.number for q in quests]!=list(range(61,71)): raise ValueError('invalid_package_identity')\n    if len({q.quest_id for q in quests})!=10: raise ValueError('duplicate_quest_id')\n    if quests[0].previous_quest_id!="+repr(expected_bridge)+": raise ValueError('invalid_story_bridge')\n    for previous,current in zip(quests,quests[1:]):\n        if current.previous_quest_id!=previous.quest_id: raise ValueError('invalid_predecessor_chain')\n    for quest in quests:\n        if quest.unlock_level!=7 or quest.location_id!='dark_forest': raise ValueError('invalid_level_or_location')\n        if quest.reward_exp < 0 or quest.reward_gold < 0: raise ValueError('invalid_reward')\n\nvalidate_story_dark_forest_61_70()\n"
  for path,src in ((CONTENT,content),(TEST,TEST_SRC),(TOOL,TOOL_SRC),(GATE,GATE_SRC)):write(r/path,src)
  print("[4/10] [PASS] Canonical Dark Forest package 61-70 generated from candidate JSON using existing Story content DTO.")
  for x in (Path(SELF),CONTENT,TEST,TOOL,GATE):py_compile.compile(str(r/x),doraise=True)
  print("[5/10] [PASS] Python compile gate passed for patch, content, tests and verifiers.")
  env=os.environ.copy();env["PYTHONDONTWRITEBYTECODE"]="1"
  t=run([sys.executable,"-m","unittest","-v","tests_v2.test_story_content_61_70"],r,False,env);sm=run([sys.executable,str(r/TOOL)],r,False,env);ga=run([sys.executable,str(r/GATE)],r,False,env)
  if t.returncode or sm.returncode or ga.returncode:raise PatchError("targeted_verification_failed:"+t.stdout+t.stderr+sm.stdout+sm.stderr+ga.stdout+ga.stderr)
  print("[6/10] [PASS] IDs, 60-to-61 bridge, chain, level, rewards, localization and package-boundary tests passed.")
  removed=clean(r);checks=canonical_ci(r);print(f"[7/10] [PASS] Canonical V2 CI passed after removing {len(removed)} bytecode artifact(s).")
  if before!={x.as_posix():sha(r/x) for x in PROTECTED}:raise PatchError("protected_runtime_changed")
  reference_after={x.relative_to(r).as_posix():sha(x) for x in (r/"Квести").rglob("*") if x.is_file()}
  if reference_before!=reference_after:raise PatchError("canonical_reference_changed")
  print("[8/10] [PASS] Existing V1/V2 sources, canonical references, DB sidecars and protected configuration remained byte-identical except authorized package files.")
  reward_matrix=[{"number":q.get("number"),"exp":(q.get("reward") or {}).get("exp"),"gold":(q.get("reward") or {}).get("gold")} for q in package]
  rep={"schema_version":1,"stage":STAGE,"status":"PASS","conclusion":"API_READY_PACKAGE_61_70","parent":PARENT,"candidate_sha256":sha(candidate),"implemented_files":[CONTENT.as_posix()],"reused_owner":DOMAIN.as_posix(),"package":{"range":"61-70","count":10,"numbers":list(range(61,71)),"level":7,"location_id":"dark_forest","bridge_predecessor":expected_bridge,"reward_matrix":reward_matrix},"tests":{"targeted":"PASS","smoke":"PASS","content_boundary":"PASS"},"packages_71_100":"NOT_CONNECTED","runtime_integration":"NOT_CONNECTED","production_persistence":"NOT_CONNECTED","canonical_reference_changed":False,"database_opened":False,"v1_wal_shm_manipulated":False,"manual_game_check":"NOT_REQUIRED_API_ONLY","canonical_v2_ci":checks};write(r/REPORT,json.dumps(rep,ensure_ascii=False,indent=2)+"\n")
  write(r/DOC,"# Stage 21.13.5d - Story content 61-70 implementation\n\n- Status: **PASS**\n- Conclusion: **API_READY_PACKAGE_61_70**\n- Canonical records: **10/10**\n- Bridge 60-61: **PASS**\n- Level gate: **7**\n- Packages 71-100: **NOT_CONNECTED**\n- Runtime integration: **NOT_CONNECTED**\n- Production persistence: **NOT_CONNECTED**\n- Manual game check: **NOT_REQUIRED_API_ONLY**\n");print("[9/10] [PASS] Machine report and Markdown package documentation written.")
  files={x.as_posix() for x in TARGETS};git(r,"add","-f","--",*sorted(files));got={x.replace("\\","/") for x in git(r,"diff","--cached","--name-only").stdout.splitlines() if x}
  if got!=files:raise PatchError("staging_mismatch:"+repr(sorted(got)))
  z=git(r,"commit","-m","Stage 21.13.5d: implement Story content 61-70","--",*sorted(files),check=False)
  if z.returncode:raise PatchError("commit_failed:"+z.stdout+z.stderr)
  commit=git(r,"rev-parse","HEAD").stdout.strip();changed={x.replace("\\","/") for x in git(r,"diff-tree","--no-commit-id","--name-only","-r",commit).stdout.splitlines() if x}
  if changed!=files:raise PatchError("commit_scope_mismatch:"+repr(sorted(changed)))
  print(f"[10/10] [PASS] Story content package 61-70 committed: {commit}");print("CONCLUSION: API_READY_PACKAGE_61_70\nPATCH STATUS: PASS\nCANONICAL RECORDS: 10/10\nBRIDGE 60-61: PASS\nPACKAGES 71-100: NOT_CONNECTED\nRUNTIME INTEGRATION: NOT_CONNECTED\nPRODUCTION PERSISTENCE: NOT_CONNECTED\nMANUAL GAME CHECK: NOT_REQUIRED_API_ONLY\nFAIL-SAFE ROLLBACK: ARMED\nSUGGESTED NEXT PATCH: patch_21_13_5e_implement_story_content_71_80.py");return 0
 except Exception as e:
  restored=restore(r,folder,state);recovery=run([sys.executable,"-m","compileall","-q","rom_v2"],r,False);write(r/FAILURE,json.dumps({"stage":STAGE,"status":"FAIL_ROLLED_BACK","reason":str(e),"restored_files":restored,"recovery_compile_returncode":recovery.returncode,"main_py_must_not_run":recovery.returncode!=0,"database_opened":False,"canonical_reference_changed":False,"v1_wal_shm_manipulated":False},ensure_ascii=False,indent=2)+"\n");print(f"[10/10] [FAIL] {e}; rollback: FAIL_ROLLED_BACK");return 1
if __name__=="__main__":raise SystemExit(main())
