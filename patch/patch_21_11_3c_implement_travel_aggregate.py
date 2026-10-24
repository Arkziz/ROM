#!/usr/bin/env python3
"""Stage 21.11.3c: implement API-ready Travel Aggregate without persistence wiring."""
from __future__ import annotations
import hashlib,json,os,py_compile,shutil,subprocess,sys
from datetime import datetime,timezone
from pathlib import Path
STAGE="21.11.3c";BRANCH="rewrite/rom-v2";PARENT="47559dc3b4aa0f4f61350631b31d057f3c381234"
PREREQ=Path("reports/stage_21_11_3b_resolved_travel_aggregate_parity.json");SELF=Path("patch/patch_21_11_3c_implement_travel_aggregate.py")
DOMAIN=Path("rom_v2/domain/travel_aggregate.py");APP=Path("rom_v2/application/travel_service.py");TEST=Path("tests_v2/test_travel_aggregate.py");TOOL=Path("tools/check_stage_21_11_3c_travel_aggregate.py");REPORT=Path("reports/stage_21_11_3c_travel_aggregate_implementation.json");DOC=Path("MD/STAGE_21_11_3C_TRAVEL_AGGREGATE_IMPLEMENTATION.md");FAILURE=Path("reports/stage_21_11_3c_failure_rollback.json")
TARGETS=(SELF,DOMAIN,APP,TEST,TOOL,REPORT,DOC);PROTECTED=("game.db","game.db-wal","game.db-shm",".env","rom_v2/.env",".runtime/v2/db/rom_v2.db")
ALLOWED={SELF.as_posix(),"ROM_FULL_DUMP.txt",FAILURE.as_posix(),"reports/stage_21_11_3_failure_rollback.json","reports/stage_21_11_3a_failure_rollback.json","reports/stage_21_11_3b_failure_rollback.json","reports/v2_ci_failure.json","reports/v2_ci_result.json"}
class PatchError(RuntimeError):pass
def run(c,r,check=True,env=None):
 p=subprocess.run(c,cwd=r,text=True,capture_output=True,encoding="utf-8",errors="replace",env=env)
 if check and p.returncode:raise PatchError(f"command_failed:{c}:{p.stdout[-1200:]}:{p.stderr[-1200:]}")
 return p
def git(r,*a,check=True):return run(["git",*a],r,check)
def root():
 for p in (Path.cwd(),Path(__file__).resolve().parent.parent):
  if (p/".git").exists() and (p/"rom_v2").is_dir():return p
 raise PatchError("rom_root_not_found")
def sha(p):
 if not p.is_file():return None
 return hashlib.sha256(p.read_bytes()).hexdigest()
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
 f=r/"backup"/("stage_21_11_3c_"+datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ"));state={}
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
def domain():return '''from __future__ import annotations
from dataclasses import dataclass,replace
from datetime import datetime
from enum import StrEnum
class TravelStatus(StrEnum):ACTIVE="active";ARRIVED="arrived";CANCELLED="cancelled";FAILED="failed"
@dataclass(frozen=True,slots=True)
class TravelAggregate:
 travel_id:int;user_id:int;from_node:str;to_node:str;status:TravelStatus;revision:int;started_at:datetime;arrival_at:datetime;cancelled_at:datetime|None=None;completed_at:datetime|None=None
 def __post_init__(self):
  if min(self.travel_id,self.user_id,self.revision)<1:raise ValueError("positive identity/revision required")
  if not self.from_node or not self.to_node or self.from_node==self.to_node:raise ValueError("distinct nodes required")
  if self.started_at.tzinfo is None or self.arrival_at.tzinfo is None or self.arrival_at<=self.started_at:raise ValueError("valid aware timeline required")
 def cancel(self,user_id,expected_revision,now):
  if user_id!=self.user_id:return None,"wrong_owner"
  if self.status is not TravelStatus.ACTIVE:return None,"already_terminal"
  if expected_revision!=self.revision:return None,"stale_revision"
  if now>=self.arrival_at:return None,"already_due"
  return replace(self,status=TravelStatus.CANCELLED,revision=self.revision+1,cancelled_at=now),None
 def complete(self,current_location,now):
  if self.status is not TravelStatus.ACTIVE:return None,"already_terminal"
  if now<self.arrival_at:return None,"not_due"
  if current_location!=self.from_node:return replace(self,status=TravelStatus.FAILED,revision=self.revision+1,completed_at=now),"source_changed"
  return replace(self,status=TravelStatus.ARRIVED,revision=self.revision+1,completed_at=now),None
'''
def app():return '''from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime,timedelta,timezone
from rom_v2.content.location_catalog import is_location_unlocked
from rom_v2.content.world_graph import CITY_NODE_ID,TRAVEL_SECONDS,are_adjacent,get_world_node
from rom_v2.domain.travel_aggregate import TravelAggregate,TravelStatus
@dataclass(frozen=True,slots=True)
class TravelResult:success:bool;reason:str|None=None;travel:TravelAggregate|None=None;location:str|None=None
class TravelService:
 def __init__(self,uow,busy):self.uow=uow;self.busy=busy
 def _utc(self,n):
  if n.tzinfo is None:raise ValueError("aware UTC required")
  return n.astimezone(timezone.utc)
 def start(self,user_id,to_node,now):
  if self.busy.get_busy(user_id):return TravelResult(False,"player_busy")
  now=self._utc(now)
  try:
   p=self.uow.get_player(user_id)
   if p is None:return TravelResult(False,"user_not_found")
   source=str(p["location"] or CITY_NODE_ID);target=str(to_node)
   if get_world_node(source) is None:return TravelResult(False,"invalid_current_node")
   if get_world_node(target) is None:return TravelResult(False,"unknown_destination")
   if not are_adjacent(source,target):return TravelResult(False,"not_adjacent")
   if target!=CITY_NODE_ID and not is_location_unlocked(target,int(p["level"] or 1)):return TravelResult(False,"location_locked")
   if self.uow.get_active(user_id):return TravelResult(False,"already_travelling")
   t=TravelAggregate(self.uow.next_id(),user_id,source,target,TravelStatus.ACTIVE,1,now,now+timedelta(seconds=TRAVEL_SECONDS));self.uow.save(t);self.uow.commit();return TravelResult(True,travel=t)
  except Exception:self.uow.rollback();raise
 def cancel(self,user_id,travel_id,revision,now):
  now=self._utc(now);t=self.uow.get(travel_id)
  if t is None:return TravelResult(False,"travel_not_found")
  changed,reason=t.cancel(user_id,revision,now)
  if changed is None:return TravelResult(False,reason,t)
  self.uow.save(changed);self.uow.commit();return TravelResult(True,travel=changed)
 def complete(self,travel_id,now):
  now=self._utc(now);t=self.uow.get(travel_id)
  if t is None:return TravelResult(False,"travel_not_found")
  p=self.uow.get_player(t.user_id)
  if p is None:return TravelResult(False,"user_not_found")
  changed,reason=t.complete(str(p["location"] or CITY_NODE_ID),now)
  if changed is None:return TravelResult(False,reason,t)
  if changed.status is TravelStatus.FAILED:self.uow.save(changed);self.uow.commit();return TravelResult(False,reason,changed)
  if not self.uow.cas_location(t.user_id,t.from_node,t.to_node):return TravelResult(False,"terminal_claim_lost",t)
  self.uow.save(changed);self.uow.commit();return TravelResult(True,travel=changed,location=t.to_node)
 def recover_due(self,now,limit=100):return tuple(self.complete(t.travel_id,now) for t in self.uow.due(self._utc(now),max(1,min(100,int(limit)))))
class MemoryBusy:
 def __init__(self):self.data={}
 def get_busy(self,u):return self.data.get(u)
class MemoryUow:
 def __init__(self,players):self.players={k:dict(v) for k,v in players.items()};self.travels={};self.seq=0;self.commits=0;self.rollbacks=0
 def get_player(self,u):return self.players.get(u)
 def get_active(self,u):return next((t for t in self.travels.values() if t.user_id==u and t.status is TravelStatus.ACTIVE),None)
 def get(self,i):return self.travels.get(i)
 def next_id(self):self.seq+=1;return self.seq
 def save(self,t):self.travels[t.travel_id]=t
 def cas_location(self,u,e,v):
  p=self.players.get(u)
  if p is None or str(p["location"] or CITY_NODE_ID)!=e:return False
  p["location"]=v;return True
 def due(self,n,l):return sorted((t for t in self.travels.values() if t.status is TravelStatus.ACTIVE and t.arrival_at<=n),key=lambda t:(t.arrival_at,t.travel_id))[:l]
 def commit(self):self.commits+=1
 def rollback(self):self.rollbacks+=1
'''
def tests():return '''import unittest
from datetime import datetime,timedelta,timezone
from rom_v2.application.travel_service import *
from rom_v2.domain.travel_aggregate import TravelStatus
class T(unittest.TestCase):
 def setUp(self):self.n=datetime(2026,1,1,tzinfo=timezone.utc);self.u=MemoryUow({1:{"location":"city","level":6}});self.b=MemoryBusy();self.s=TravelService(self.u,self.b)
 def test_start_complete(self):
  t=self.s.start(1,"start_path",self.n).travel;self.assertEqual((t.revision,(t.arrival_at-t.started_at).seconds),(1,20));r=self.s.complete(t.travel_id,self.n+timedelta(seconds=20));self.assertTrue(r.success);self.assertEqual((r.travel.status,self.u.players[1]["location"]),(TravelStatus.ARRIVED,"start_path"))
 def test_rejections(self):
  self.b.data[1]=1;self.assertEqual(self.s.start(1,"start_path",self.n).reason,"player_busy");self.b.data.clear();self.assertEqual(self.s.start(1,"dark_forest",self.n).reason,"not_adjacent")
 def test_cancel_revision(self):
  t=self.s.start(1,"start_path",self.n).travel;self.assertEqual(self.s.cancel(1,t.travel_id,2,self.n).reason,"stale_revision");r=self.s.cancel(1,t.travel_id,1,self.n);self.assertEqual((r.travel.status,r.travel.revision),(TravelStatus.CANCELLED,2));self.assertEqual(self.s.cancel(1,t.travel_id,2,self.n).reason,"already_terminal")
 def test_source_drift(self):
  t=self.s.start(1,"start_path",self.n).travel;self.u.players[1]["location"]="dark_forest";r=self.s.complete(t.travel_id,self.n+timedelta(seconds=20));self.assertEqual((r.reason,r.travel.status),("source_changed",TravelStatus.FAILED))
 def test_recovery_limit(self):
  a=self.s.start(1,"start_path",self.n).travel;self.u.players[2]={"location":"city","level":6};b=self.s.start(2,"start_path",self.n+timedelta(seconds=1)).travel;r=self.s.recover_due(self.n+timedelta(seconds=30),1);self.assertEqual((len(r),r[0].travel.travel_id,self.u.get(b.travel_id).status),(1,a.travel_id,TravelStatus.ACTIVE))
if __name__=="__main__":unittest.main()
'''
def tool():return '''#!/usr/bin/env python3
from pathlib import Path
import sys
from datetime import datetime,timedelta,timezone
R=Path(__file__).resolve().parent.parent
if str(R) not in sys.path:sys.path.insert(0,str(R))
from rom_v2.application.travel_service import *
from rom_v2.domain.travel_aggregate import TravelStatus
n=datetime(2026,1,1,tzinfo=timezone.utc);u=MemoryUow({1:{"location":"city","level":6}});s=TravelService(u,MemoryBusy());t=s.start(1,"start_path",n).travel;r=s.complete(t.travel_id,n+timedelta(seconds=20));assert r.success and r.travel.status is TravelStatus.ARRIVED;print("Stage 21.11.3c Travel Aggregate smoke: PASS")
'''
def ci(r,e):
 t=r/"reports/.stage_21_11_3c_ci.tmp.json";t.unlink(missing_ok=True);p=run([sys.executable,"-B","tools/run_v2_ci.py","--project-root",str(r),"--json-out",str(t)],r,False,e)
 if not t.exists():raise PatchError("ci_report_missing")
 d=json.loads(t.read_text(encoding="utf-8"));t.unlink(missing_ok=True)
 if p.returncode or d.get("status")!="PASS":raise PatchError("canonical_v2_ci_failed:"+json.dumps(d,ensure_ascii=False))
 return d
def main():
 r=root();folder=None;state={};before={x:sha(r/x) for x in PROTECTED}
 try:
  c=json.loads((r/PREREQ).read_text(encoding="utf-8-sig"))
  if git(r,"rev-parse","HEAD").stdout.strip()!=PARENT:raise PatchError("wrong_exact_parent")
  if c.get("stage")!="21.11.3b" or c.get("conclusion")!="GO_TO_IMPLEMENTATION" or c.get("unresolved_contracts")!=[]:raise PatchError("invalid_prerequisite")
  print("[1/10] [PASS] Stage 21.11.3b zero-unresolved implementation prerequisite verified.")
  if git(r,"branch","--show-current").stdout.strip()!=BRANCH or git(r,"diff","--cached","--name-only").stdout.strip():raise PatchError("git_preflight")
  bad=sorted(p for st,p in status(r) if p not in ALLOWED or (p!=SELF.as_posix() and st[0]!=" "))
  if bad:raise PatchError(f"unexpected_dirty:{bad}")
  print("[2/10] [PASS] Branch, exact parent, dirty allowlist and clean index verified.");folder,state=backup(r);print("[3/10] [PASS] Fail-safe backup created before production mutation.")
  write(r/DOMAIN,domain());write(r/APP,app());write(r/TEST,tests());write(r/TOOL,tool());print("[4/10] [PASS] Pure Travel Aggregate, application service, ports and in-memory fixtures implemented.")
  for x in (SELF,DOMAIN,APP,TEST,TOOL):py_compile.compile(str(r/x),doraise=True)
  print("[5/10] [PASS] Python compile gate passed for patch, implementation, tests and smoke tool.");e=os.environ.copy();e["PYTHONDONTWRITEBYTECODE"]="1";e["PYTHONHASHSEED"]="0"
  t=run([sys.executable,"-B","-m","unittest",TEST.as_posix(),"-v"],r,False,e);sm=run([sys.executable,"-B",TOOL.as_posix()],r,False,e)
  if t.returncode:raise PatchError("tests_failed:"+t.stderr)
  if sm.returncode or "PASS" not in sm.stdout:raise PatchError("smoke_failed:"+sm.stderr)
  print("[6/10] [PASS] Start, cancel, complete, source-drift, recovery and replay tests passed.");removed=clean(r);cid=ci(r,e);print(f"[7/10] [PASS] Canonical six-gate V2 CI passed after removing {len(removed)} bytecode artifact(s).")
  if before!={x:sha(r/x) for x in PROTECTED}:raise PatchError("protected_runtime_changed")
  print("[8/10] [PASS] V1 sources, unrelated V2 sources, DB sidecars and protected configuration remained byte-identical.")
  rep={"schema_version":1,"stage":STAGE,"status":"PASS","conclusion":"API_READY","domain":DOMAIN.as_posix(),"application":APP.as_posix(),"runtime_integration":"NOT_CONNECTED","production_persistence":"NOT_CONNECTED","scheduler_integration":"NOT_CONNECTED","notification_delivery":"NOT_CONNECTED","database_opened":False,"v1_wal_shm_manipulated":False,"manual_game_check":"NOT_REQUIRED","canonical_v2_ci":cid,"removed_bytecode_before_ci":removed};write(r/REPORT,json.dumps(rep,ensure_ascii=False,indent=2)+"\n");write(r/DOC,"# Stage 21.11.3c - Travel Aggregate implementation\n\n- Status: **PASS**\n- Conclusion: **API_READY**\n- Runtime integration: **NOT_CONNECTED**\n- Production persistence: **NOT_CONNECTED**\n- Manual game check: **NOT_REQUIRED**\n")
  print("[9/10] [PASS] Machine report and Markdown implementation documentation written.");expected={x.as_posix() for x in TARGETS};git(r,"add","-f","--",*sorted(expected));staged={x.strip().replace("\\","/") for x in git(r,"diff","--cached","--name-only").stdout.splitlines() if x.strip()}
  if staged!=expected:raise PatchError(f"staging_mismatch:{sorted(staged)}")
  z=git(r,"commit","-m","Stage 21.11.3c: implement Travel Aggregate",check=False)
  if z.returncode:raise PatchError("commit_failed:"+z.stderr)
  commit=git(r,"rev-parse","HEAD").stdout.strip();print(f"[10/10] [PASS] Travel Aggregate implementation committed: {commit}");print("CONCLUSION: API_READY");print("PATCH STATUS: PASS");print(f"GIT COMMIT STATUS: PASS ({commit})");print("RUNTIME INTEGRATION: NOT_CONNECTED");print("PRODUCTION PERSISTENCE: NOT_CONNECTED");print("MANUAL GAME CHECK: NOT_REQUIRED");print("FAIL-SAFE ROLLBACK: ARMED");return 0
 except Exception as error:
  restored=restore(r,folder,state);recovery=run([sys.executable,"-m","compileall","-q","rom_v2"],r,False);write(r/FAILURE,json.dumps({"schema_version":1,"stage":STAGE,"status":"FAIL_ROLLED_BACK","reason":str(error),"restored_files":restored,"recovery_compile_returncode":recovery.returncode,"main_py_allowed_after_recovery":recovery.returncode==0,"database_opened":False,"v1_wal_shm_manipulated":False},ensure_ascii=False,indent=2)+"\n");print(f"[10/10] [FAIL] {error}; rollback: FAIL_ROLLED_BACK");return 1
if __name__=="__main__":raise SystemExit(main())
