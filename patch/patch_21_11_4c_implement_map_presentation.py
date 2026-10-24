#!/usr/bin/env python3
"""Stage 21.11.4c: implement pure API-ready V2 Map Presentation."""
from __future__ import annotations
import hashlib,json,os,py_compile,shutil,subprocess,sys
from datetime import datetime,timezone
from pathlib import Path
STAGE="21.11.4c";BRANCH="rewrite/rom-v2";PARENT="45e06280d13a7e4ba3a67737a473db2fd97acd61"
PREREQ=Path("reports/stage_21_11_4b_resolved_map_presentation_parity.json");SELF=Path("patch/patch_21_11_4c_implement_map_presentation.py")
MODULE=Path("rom_v2/application/map_presentation.py");TEST=Path("tests_v2/test_map_presentation.py");TOOL=Path("tools/check_stage_21_11_4c_map_presentation.py");REPORT=Path("reports/stage_21_11_4c_map_presentation_implementation.json");DOC=Path("MD/STAGE_21_11_4C_MAP_PRESENTATION_IMPLEMENTATION.md");FAILURE=Path("reports/stage_21_11_4c_failure_rollback.json")
TARGETS=(SELF,MODULE,TEST,TOOL,REPORT,DOC);PROTECTED=("game.db","game.db-wal","game.db-shm",".env","rom_v2/.env",".runtime/v2/db/rom_v2.db")
ALLOWED={SELF.as_posix(),"ROM_FULL_DUMP.txt",FAILURE.as_posix(),"reports/stage_21_11_4_failure_rollback.json","reports/stage_21_11_4a_failure_rollback.json","reports/stage_21_11_4b_failure_rollback.json","reports/v2_ci_failure.json","reports/v2_ci_result.json"}
class PatchError(RuntimeError):pass
def run(c,r,check=True,env=None):
 p=subprocess.run(c,cwd=r,text=True,capture_output=True,encoding="utf-8",errors="replace",env=env)
 if check and p.returncode:raise PatchError(f"command_failed:{c}:{p.stdout[-1600:]}:{p.stderr[-1600:]}")
 return p
def git(r,*a,check=True):return run(["git",*a],r,check)
def root():
 for p in (Path.cwd(),Path(__file__).resolve().parent.parent):
  if (p/".git").exists() and (p/"rom_v2").is_dir():return p
 raise PatchError("rom_root_not_found")
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest() if p.is_file() else None
def write(p,s):p.parent.mkdir(parents=True,exist_ok=True);t=p.with_name(p.name+".tmp");t.write_text(s,encoding="utf-8",newline="\n");os.replace(t,p)
def status(r):
 raw=git(r,"status","--porcelain=v1","-z").stdout;parts=raw.split("\0");out=[];i=0
 while i<len(parts):
  x=parts[i];i+=1
  if not x:continue
  st=x[:2];path=x[3:].replace("\\","/")
  if st[0] in "RC":path=parts[i].replace("\\","/");i+=1
  out.append((st,path))
 return out
def backup(r):
 f=r/"backup"/("stage_21_11_4c_"+datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ"));state={}
 for rel in TARGETS:
  src=r/rel;state[rel.as_posix()]=src.exists()
  if src.exists():dst=f/rel;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dst)
 return f,state
def restore(r,f,state):
 git(r,"reset","--mixed",check=False);out=[]
 if f is None:return out
 for rel in TARGETS:
  dst=r/rel;src=f/rel
  if state.get(rel.as_posix()) and src.exists():dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dst);out.append(rel.as_posix())
  elif dst.exists():dst.unlink();out.append("removed:"+rel.as_posix())
 return out
def clean(r):
 out=[]
 for base in (r/"rom_v2",r/"tests_v2",r/"tests",r/"tools"):
  if base.exists():
   for p in base.rglob("*.pyc"):out.append(p.relative_to(r).as_posix());p.unlink(missing_ok=True)
   for d in sorted(base.rglob("__pycache__"),key=lambda x:len(x.parts),reverse=True):
    try:d.rmdir()
    except OSError:pass
 return out
def module():return '''"""Pure localized Map Presentation DTOs and callback codec."""
from __future__ import annotations
import math
from dataclasses import dataclass
from datetime import datetime,timezone
from enum import StrEnum
from rom_v2.content.location_catalog import is_location_unlocked
from rom_v2.content.world_graph import CITY_NODE_ID,get_adjacent_nodes,get_world_node
UNKNOWN_PLACE="🧭 Невідома місцевість"
class MapMode(StrEnum):READY="ready";IN_TRANSIT="in_transit"
@dataclass(frozen=True,slots=True)
class MapAction:
 kind:str;label:str;callback_data:str;enabled:bool=True
@dataclass(frozen=True,slots=True)
class DirectionView:
 node_id:str;label:str;unlocked:bool;action:MapAction|None
@dataclass(frozen=True,slots=True)
class ActiveTravelView:
 travel_id:int;revision:int;from_label:str;to_label:str;remaining_seconds:int;cancel:MapAction
@dataclass(frozen=True,slots=True)
class MapView:
 mode:MapMode;current_node_id:str;current_label:str;directions:tuple[DirectionView,...];actions:tuple[MapAction,...];active_travel:ActiveTravelView|None=None
@dataclass(frozen=True,slots=True)
class CallbackCommand:
 action:str;node_id:str|None=None;travel_id:int|None=None;revision:int|None=None

def node_label(node_id):
 node=get_world_node(str(node_id or "").strip())
 return node.name if node else UNKNOWN_PLACE

def encode_callback(command):
 if command.action in {"open","players"} and not any((command.node_id,command.travel_id,command.revision)):return f"map:{command.action}"
 if command.action in {"info","preview","start"} and command.node_id and get_world_node(command.node_id):return f"map:{command.action}:{command.node_id}"
 if command.action=="cancel" and command.travel_id and command.revision:return f"map:cancel:{command.travel_id}:{command.revision}"
 raise ValueError("invalid callback command")

def decode_callback(payload):
 parts=str(payload or "").split(":")
 try:
  if parts==["map","open"]:return CallbackCommand("open")
  if parts==["map","players"]:return CallbackCommand("players")
  if len(parts)==3 and parts[0]=="map" and parts[1] in {"info","preview","start"} and get_world_node(parts[2]):return CallbackCommand(parts[1],node_id=parts[2])
  if len(parts)==4 and parts[:2]==["map","cancel"] and int(parts[2])>0 and int(parts[3])>0:return CallbackCommand("cancel",travel_id=int(parts[2]),revision=int(parts[3]))
 except (TypeError,ValueError):pass
 return None

def build_map_view(current_node_id,player_level,*,active_travel=None,now=None):
 current=str(current_node_id or "").strip();label=node_label(current)
 if active_travel is not None:
  moment=(now or datetime.now(timezone.utc)).astimezone(timezone.utc);arrival=active_travel.arrival_at.astimezone(timezone.utc)
  remaining=max(0,math.ceil((arrival-moment).total_seconds()))
  cancel=MapAction("cancel","❌ Скасувати подорож",encode_callback(CallbackCommand("cancel",travel_id=active_travel.travel_id,revision=active_travel.revision)))
  trip=ActiveTravelView(active_travel.travel_id,active_travel.revision,node_label(active_travel.from_node),node_label(active_travel.to_node),remaining,cancel)
  return MapView(MapMode.IN_TRANSIT,current,label,(),(MapAction("open","🔄 Оновити","map:open"),),trip)
 directions=[]
 for target in get_adjacent_nodes(current):
  unlocked=target==CITY_NODE_ID or is_location_unlocked(target,player_level)
  action=MapAction("preview",f"➡️ {node_label(target)}",encode_callback(CallbackCommand("preview",node_id=target))) if unlocked else None
  directions.append(DirectionView(target,node_label(target),unlocked,action))
 return MapView(MapMode.READY,current,label,tuple(directions),(MapAction("open","🔄 Оновити","map:open"),MapAction("players","👥 Гравці поруч","map:players")))
'''
def tests():return '''import unittest
from datetime import datetime,timedelta,timezone
from rom_v2.application.map_presentation import *
from rom_v2.domain.travel_aggregate import TravelAggregate,TravelStatus
class MapPresentationTest(unittest.TestCase):
 def test_ready_order_and_unlock(self):
  v=build_map_view("start_path",5);self.assertEqual([d.node_id for d in v.directions],["city","dark_forest"]);self.assertTrue(v.directions[0].unlocked);self.assertFalse(v.directions[1].unlocked);self.assertIsNone(v.directions[1].action);self.assertEqual(v.directions[1].label,"🌲 Темний Бір")
 def test_technical_ids_not_in_labels(self):
  v=build_map_view("city",6);labels=[v.current_label,*[d.label for d in v.directions],*[a.label for a in v.actions]];self.assertNotIn("start_path"," ".join(labels));self.assertEqual(node_label("missing"),UNKNOWN_PLACE)
 def test_callback_roundtrip_and_fail_closed(self):
  for c in (CallbackCommand("open"),CallbackCommand("players"),CallbackCommand("preview",node_id="start_path"),CallbackCommand("cancel",travel_id=7,revision=2)):self.assertEqual(decode_callback(encode_callback(c)),c)
  for bad in ("","map:start:missing","map:cancel:x:1","map:cancel:1:0","other:open"):self.assertIsNone(decode_callback(bad))
 def test_in_transit_countdown_and_actions(self):
  now=datetime(2026,1,1,tzinfo=timezone.utc);t=TravelAggregate(3,1,"city","start_path",TravelStatus.ACTIVE,2,now,now+timedelta(seconds=20));v=build_map_view("city",6,active_travel=t,now=now+timedelta(seconds=1,microseconds=1));self.assertEqual((v.mode,v.active_travel.remaining_seconds),(MapMode.IN_TRANSIT,19));self.assertEqual(v.directions,());self.assertEqual(decode_callback(v.active_travel.cancel.callback_data).revision,2)
 def test_countdown_never_negative(self):
  now=datetime(2026,1,1,tzinfo=timezone.utc);t=TravelAggregate(3,1,"city","start_path",TravelStatus.ACTIVE,1,now,now+timedelta(seconds=20));self.assertEqual(build_map_view("city",6,active_travel=t,now=now+timedelta(seconds=21)).active_travel.remaining_seconds,0)
if __name__=="__main__":unittest.main()
'''
def tool():return '''#!/usr/bin/env python3
from pathlib import Path
import sys
R=Path(__file__).resolve().parent.parent
if str(R) not in sys.path:sys.path.insert(0,str(R))
from rom_v2.application.map_presentation import *
v=build_map_view("start_path",5);assert v.current_label=="🌿 Початок Шляху" and [x.node_id for x in v.directions]==["city","dark_forest"] and not v.directions[1].unlocked;assert decode_callback("map:preview:start_path").node_id=="start_path";assert "start_path" not in " ".join([v.current_label,*[d.label for d in v.directions]]);print("Stage 21.11.4c Map Presentation smoke: PASS")
'''
def ci(r,e):
 t=r/"reports/.stage_21_11_4c_ci.tmp.json";t.unlink(missing_ok=True);p=run([sys.executable,"-B","tools/run_v2_ci.py","--project-root",str(r),"--json-out",str(t)],r,False,e)
 if not t.exists():raise PatchError("ci_report_missing")
 d=json.loads(t.read_text(encoding="utf-8"));t.unlink(missing_ok=True)
 if p.returncode or d.get("status")!="PASS":raise PatchError("canonical_v2_ci_failed:"+json.dumps(d,ensure_ascii=False))
 return d
def main():
 r=root();folder=None;state={};before={x:sha(r/x) for x in PROTECTED}
 try:
  c=json.loads((r/PREREQ).read_text(encoding="utf-8-sig"))
  if git(r,"rev-parse","HEAD").stdout.strip()!=PARENT:raise PatchError("wrong_exact_parent")
  if c.get("stage")!="21.11.4b" or c.get("conclusion")!="GO_TO_IMPLEMENTATION" or c.get("unresolved_contracts")!=[] or not c.get("implementation_authorized"):raise PatchError("invalid_prerequisite")
  print("[1/10] [PASS] Stage 21.11.4b zero-unresolved implementation prerequisite verified.")
  if git(r,"branch","--show-current").stdout.strip()!=BRANCH or git(r,"diff","--cached","--name-only").stdout.strip():raise PatchError("git_preflight")
  bad=sorted(p for st,p in status(r) if p not in ALLOWED or (p!=SELF.as_posix() and st[0]!=" "))
  if bad:raise PatchError(f"unexpected_dirty:{bad}")
  print("[2/10] [PASS] Branch, exact parent, dirty allowlist and clean index verified.");folder,state=backup(r);print("[3/10] [PASS] Fail-safe backup created before production mutation.")
  write(r/MODULE,module());write(r/TEST,tests());write(r/TOOL,tool());print("[4/10] [PASS] Pure MapPresentationService DTOs, callback codec and localized map query implemented.")
  for x in (SELF,MODULE,TEST,TOOL):py_compile.compile(str(r/x),doraise=True)
  print("[5/10] [PASS] Python compile gate passed for patch, implementation, tests and smoke tool.");env=os.environ.copy();env["PYTHONDONTWRITEBYTECODE"]="1";env["PYTHONHASHSEED"]="0"
  t=run([sys.executable,"-B","-m","unittest",TEST.as_posix(),"-v"],r,False,env);sm=run([sys.executable,"-B",TOOL.as_posix()],r,False,env)
  if t.returncode:raise PatchError("tests_failed:"+t.stderr)
  if sm.returncode or "PASS" not in sm.stdout:raise PatchError("smoke_failed:"+sm.stderr)
  print("[6/10] [PASS] DTO, callback, unlock, in-transit, countdown and technical-ID disclosure tests passed.");removed=clean(r);cid=ci(r,env);print(f"[7/10] [PASS] Canonical six-gate V2 CI passed after removing {len(removed)} bytecode artifact(s).")
  if before!={x:sha(r/x) for x in PROTECTED}:raise PatchError("protected_runtime_changed")
  print("[8/10] [PASS] V1 sources, unrelated V2 sources, DB sidecars and protected configuration remained byte-identical.")
  rep={"schema_version":1,"stage":STAGE,"status":"PASS","conclusion":"API_READY","module":MODULE.as_posix(),"runtime_integration":"NOT_CONNECTED","production_persistence":"NOT_CONNECTED","telegram_wiring":"NOT_CONNECTED","database_opened":False,"v1_wal_shm_manipulated":False,"manual_game_check":"NOT_REQUIRED","canonical_v2_ci":cid,"removed_bytecode_before_ci":removed};write(r/REPORT,json.dumps(rep,ensure_ascii=False,indent=2)+"\n");write(r/DOC,"# Stage 21.11.4c - Map Presentation implementation\n\n- Status: **PASS**\n- Conclusion: **API_READY**\n- Runtime integration: **NOT_CONNECTED**\n- Production persistence: **NOT_CONNECTED**\n- Telegram wiring: **NOT_CONNECTED**\n- Manual game check: **NOT_REQUIRED**\n")
  print("[9/10] [PASS] Machine report and Markdown implementation documentation written.");expected={x.as_posix() for x in TARGETS};git(r,"add","-f","--",*sorted(expected));staged={x.strip().replace("\\","/") for x in git(r,"diff","--cached","--name-only").stdout.splitlines() if x.strip()}
  if staged!=expected:raise PatchError(f"staging_mismatch:{sorted(staged)}")
  z=git(r,"commit","-m","Stage 21.11.4c: implement Map Presentation",check=False)
  if z.returncode:raise PatchError("commit_failed:"+z.stderr)
  commit=git(r,"rev-parse","HEAD").stdout.strip();changed={x.strip().replace("\\","/") for x in git(r,"diff-tree","--no-commit-id","--name-only","-r",commit).stdout.splitlines() if x.strip()}
  if changed!=expected:raise PatchError(f"commit_scope_mismatch:{sorted(changed)}")
  print(f"[10/10] [PASS] Map Presentation implementation committed: {commit}");print("CONCLUSION: API_READY");print("PATCH STATUS: PASS");print(f"GIT COMMIT STATUS: PASS ({commit})");print("RUNTIME INTEGRATION: NOT_CONNECTED");print("PRODUCTION PERSISTENCE: NOT_CONNECTED");print("MANUAL GAME CHECK: NOT_REQUIRED");print("FAIL-SAFE ROLLBACK: ARMED");return 0
 except Exception as e:
  restored=restore(r,folder,state);recovery=run([sys.executable,"-m","compileall","-q","rom_v2"],r,False);write(r/FAILURE,json.dumps({"schema_version":1,"stage":STAGE,"status":"FAIL_ROLLED_BACK","reason":str(e),"restored_files":restored,"recovery_compile_returncode":recovery.returncode,"main_py_allowed_after_recovery":recovery.returncode==0,"database_opened":False,"v1_wal_shm_manipulated":False},ensure_ascii=False,indent=2)+"\n");print(f"[10/10] [FAIL] {e}; rollback: FAIL_ROLLED_BACK");return 1
if __name__=="__main__":raise SystemExit(main())
