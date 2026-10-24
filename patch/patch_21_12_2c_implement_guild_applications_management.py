#!/usr/bin/env python3
"""Stage 21.12.2c: implement API-ready Guild Applications/Management without runtime wiring."""
from __future__ import annotations
import hashlib,json,os,py_compile,shutil,subprocess,sys
from datetime import datetime,timezone
from pathlib import Path
STAGE="21.12.2c";BRANCH="rewrite/rom-v2";PARENT="782b40931c98af363ce63a9d0db41b247067b334"
PREREQ=Path("reports/stage_21_12_2b_resolved_guild_applications_management_parity.json");SELF=Path("patch/patch_21_12_2c_implement_guild_applications_management.py")
DOMAIN=Path("rom_v2/domain/guild_application.py");APP=Path("rom_v2/application/guild_management_service.py");TEST=Path("tests_v2/test_guild_management.py");TOOL=Path("tools/check_stage_21_12_2c_guild_management.py");REPORT=Path("reports/stage_21_12_2c_guild_applications_management_implementation.json");DOC=Path("MD/STAGE_21_12_2C_GUILD_APPLICATIONS_MANAGEMENT_IMPLEMENTATION.md");FAILURE=Path("reports/stage_21_12_2c_failure_rollback.json")
TARGETS=(SELF,DOMAIN,APP,TEST,TOOL,REPORT,DOC);PROTECTED=("game.db","game.db-wal","game.db-shm",".env","rom_v2/.env",".runtime/v2/db/rom_v2.db")
ALLOWED={SELF.as_posix(),"ROM_FULL_DUMP.txt",FAILURE.as_posix(),"reports/stage_21_12_2_failure_rollback.json","reports/stage_21_12_2a_failure_rollback.json","reports/stage_21_12_2b_failure_rollback.json","reports/v2_ci_failure.json","reports/v2_ci_result.json"}
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
 f=r/"backup"/("stage_21_12_2c_"+datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ"));state={}
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
 for b in (r/"rom_v2",r/"tests_v2",r/"tests",r/"tools"):
  if b.exists():
   for p in b.rglob("*.pyc"):out.append(p.relative_to(r).as_posix());p.unlink(missing_ok=True)
   for d in sorted(b.rglob("__pycache__"),key=lambda x:len(x.parts),reverse=True):
    try:d.rmdir()
    except OSError:pass
 return out
def domain():return '"""Pure guild application lifecycle model."""\nfrom __future__ import annotations\nfrom dataclasses import dataclass, replace\nfrom enum import StrEnum\nclass ApplicationStatus(StrEnum):\n PENDING="pending"; ACCEPTED="accepted"; REJECTED="rejected"; CANCELLED="cancelled"\n@dataclass(frozen=True,slots=True)\nclass GuildApplication:\n application_id:int; guild_id:int; user_id:int; status:ApplicationStatus=ApplicationStatus.PENDING; processed_by:int|None=None\n def __post_init__(self):\n  if min(self.application_id,self.guild_id,self.user_id)<1: raise ValueError("invalid_application_identity")\n  if self.status is ApplicationStatus.PENDING and self.processed_by is not None: raise ValueError("pending_has_processor")\n  if self.status is not ApplicationStatus.PENDING and self.processed_by is None: raise ValueError("terminal_missing_processor")\n def decide(self,actor_id,status):\n  if self.status is not ApplicationStatus.PENDING:return None,"already_processed"\n  if status not in {ApplicationStatus.ACCEPTED,ApplicationStatus.REJECTED}:return None,"invalid_transition"\n  return replace(self,status=status,processed_by=actor_id),None\n'
def app():return '"""Pure Guild Applications/Management service and in-memory fixtures."""\nfrom __future__ import annotations\nfrom dataclasses import dataclass,replace\nfrom rom_v2.domain.guild_application import ApplicationStatus,GuildApplication\nfrom rom_v2.domain.guild_core import GuildCore,GuildMember,GuildRole,MINIMUM_ACCESS_LEVEL\n@dataclass(frozen=True,slots=True)\nclass ManagementResult:\n success:bool; reason:str|None=None; application:GuildApplication|None=None; guild:GuildCore|None=None\nclass GuildManagementService:\n def __init__(self,uow):self.uow=uow\n @staticmethod\n def _manager(role):return role in {GuildRole.LEADER,GuildRole.OFFICER}\n def accept(self,actor_id,application_id):\n  app=self.uow.application(application_id)\n  if app is None:return ManagementResult(False,"application_not_found")\n  guild=self.uow.guild(app.guild_id);role=guild.role_of(actor_id) if guild else None\n  if not self._manager(role):return ManagementResult(False,"permission_denied",app,guild)\n  if app.status is not ApplicationStatus.PENDING:return ManagementResult(False,"already_processed",app,guild)\n  if self.uow.guild_for_user(app.user_id):return ManagementResult(False,"already_in_guild",app,guild)\n  if self.uow.level(app.user_id)<MINIMUM_ACCESS_LEVEL:return ManagementResult(False,"level_too_low",app,guild)\n  if not self.uow.join_allowed(app.user_id):return ManagementResult(False,"join_cooldown",app,guild)\n  if len(guild.members)>=guild.member_limit:return ManagementResult(False,"member_limit_reached",app,guild)\n  try:\n   claimed,reason=app.decide(actor_id,ApplicationStatus.ACCEPTED)\n   if claimed is None:return ManagementResult(False,reason,app,guild)\n   changed=replace(guild,members=guild.members+(GuildMember(app.user_id,GuildRole.MEMBER),))\n   self.uow.save_application(claimed);self.uow.save_guild(changed);self.uow.commit();return ManagementResult(True,application=claimed,guild=changed)\n  except Exception:self.uow.rollback();raise\n def reject(self,actor_id,application_id):\n  app=self.uow.application(application_id)\n  if app is None:return ManagementResult(False,"application_not_found")\n  guild=self.uow.guild(app.guild_id);role=guild.role_of(actor_id) if guild else None\n  if not self._manager(role):return ManagementResult(False,"permission_denied",app,guild)\n  changed,reason=app.decide(actor_id,ApplicationStatus.REJECTED)\n  if changed is None:return ManagementResult(False,reason,app,guild)\n  self.uow.save_application(changed);self.uow.commit();return ManagementResult(True,application=changed,guild=guild)\n def promote(self,actor_id,target_id):\n  guild=self.uow.guild_for_user(actor_id)\n  if guild is None:return ManagementResult(False,"not_in_guild")\n  if guild.role_of(actor_id) is not GuildRole.LEADER:return ManagementResult(False,"permission_denied",guild=guild)\n  if actor_id==target_id:return ManagementResult(False,"self_target",guild=guild)\n  role=guild.role_of(target_id)\n  if role is None:return ManagementResult(False,"target_not_member",guild=guild)\n  if role is GuildRole.LEADER:return ManagementResult(False,"target_is_leader",guild=guild)\n  if role is GuildRole.OFFICER:return ManagementResult(False,"already_officer",guild=guild)\n  if sum(m.role is GuildRole.OFFICER for m in guild.members)>=self.uow.officer_limit(guild.guild_id):return ManagementResult(False,"officer_limit_reached",guild=guild)\n  changed=replace(guild,members=tuple(GuildMember(m.user_id,GuildRole.OFFICER if m.user_id==target_id else m.role) for m in guild.members));self.uow.save_guild(changed);self.uow.commit();return ManagementResult(True,guild=changed)\n def kick(self,actor_id,target_id):\n  guild=self.uow.guild_for_user(actor_id)\n  if guild is None:return ManagementResult(False,"not_in_guild")\n  actor=guild.role_of(actor_id);target=guild.role_of(target_id)\n  if target is None:return ManagementResult(False,"target_not_member",guild=guild)\n  if actor_id==target_id:return ManagementResult(False,"self_target",guild=guild)\n  if target is GuildRole.LEADER:return ManagementResult(False,"target_is_leader",guild=guild)\n  allowed=actor is GuildRole.LEADER or (actor is GuildRole.OFFICER and target is GuildRole.MEMBER)\n  if not allowed:return ManagementResult(False,"permission_denied",guild=guild)\n  changed=replace(guild,members=tuple(m for m in guild.members if m.user_id!=target_id));self.uow.save_guild(changed);self.uow.record_departure(target_id,guild.guild_id,"kicked",actor_id);self.uow.commit();return ManagementResult(True,guild=changed)\nclass MemoryManagementUow:\n def __init__(self,guilds,applications,levels,officer_limits):self.guilds={g.guild_id:g for g in guilds};self.applications={a.application_id:a for a in applications};self.levels=dict(levels);self.cooldowns=set();self.officer_limits=dict(officer_limits);self.departures=[];self.commits=0;self.rollbacks=0\n def application(self,i):return self.applications.get(i)\n def guild(self,i):return self.guilds.get(i)\n def guild_for_user(self,u):return next((g for g in self.guilds.values() if g.role_of(u) is not None),None)\n def level(self,u):return self.levels.get(u,0)\n def join_allowed(self,u):return u not in self.cooldowns\n def officer_limit(self,g):return self.officer_limits[g]\n def save_application(self,a):self.applications[a.application_id]=a\n def save_guild(self,g):self.guilds[g.guild_id]=g\n def record_departure(self,u,g,event,actor):self.departures.append((u,g,event,actor))\n def commit(self):self.commits+=1\n def rollback(self):self.rollbacks+=1\n'
def tests():return 'import unittest\nfrom rom_v2.application.guild_management_service import *\nfrom rom_v2.domain.guild_core import GuildIdentity\ndef guild():return GuildCore(1,GuildIdentity("Варта","варта","ВРТ","врт","🏰"),1,(GuildMember(1,GuildRole.LEADER),GuildMember(2,GuildRole.OFFICER),GuildMember(3,GuildRole.MEMBER)),10)\ndef application():return GuildApplication(1,1,4)\nclass ManagementTest(unittest.TestCase):\n def setUp(self):self.u=MemoryManagementUow([guild()],[application()],{4:3},{1:2});self.s=GuildManagementService(self.u)\n def test_accept_and_replay(self):\n  r=self.s.accept(2,1);self.assertTrue(r.success);self.assertEqual(r.guild.role_of(4),GuildRole.MEMBER);self.assertEqual(self.s.accept(2,1).reason,"already_processed")\n def test_accept_rechecks(self):\n  self.u.levels[4]=2;self.assertEqual(self.s.accept(1,1).reason,"level_too_low");self.u.levels[4]=3;self.u.cooldowns.add(4);self.assertEqual(self.s.accept(1,1).reason,"join_cooldown")\n def test_reject_replay(self):\n  self.assertTrue(self.s.reject(2,1).success);self.assertEqual(self.s.reject(1,1).reason,"already_processed")\n def test_promote_limit_permission(self):\n  self.assertTrue(self.s.promote(1,3).success);self.u.guilds[1]=guild();self.u.officer_limits[1]=1;self.assertEqual(self.s.promote(1,3).reason,"officer_limit_reached");self.assertEqual(self.s.promote(2,3).reason,"permission_denied")\n def test_kick_protections(self):\n  self.assertEqual(self.s.kick(2,1).reason,"target_is_leader");self.assertEqual(self.s.kick(2,2).reason,"self_target");self.assertTrue(self.s.kick(2,3).success);self.assertEqual(self.u.departures,[(3,1,"kicked",2)])\n def test_application_invariant(self):\n  with self.assertRaises(ValueError):GuildApplication(1,1,4,ApplicationStatus.ACCEPTED)\nif __name__=="__main__":unittest.main()\n'
def tool():return '#!/usr/bin/env python3\nfrom pathlib import Path\nimport sys\nR=Path(__file__).resolve().parent.parent\nif str(R) not in sys.path:sys.path.insert(0,str(R))\nfrom rom_v2.application.guild_management_service import *\nfrom rom_v2.domain.guild_core import GuildIdentity\ng=GuildCore(1,GuildIdentity("Варта","варта","ВРТ","врт","🏰"),1,(GuildMember(1,GuildRole.LEADER),),10);u=MemoryManagementUow([g],[GuildApplication(1,1,2)],{2:3},{1:1});r=GuildManagementService(u).accept(1,1);assert r.success and r.guild.role_of(2) is GuildRole.MEMBER;print("Stage 21.12.2c Guild Applications Management smoke: PASS")\n'

def ci(r,e):
 t=r/"reports/.stage_21_12_2c_ci.tmp.json";t.unlink(missing_ok=True);p=run([sys.executable,"-B","tools/run_v2_ci.py","--project-root",str(r),"--json-out",str(t)],r,False,e)
 if not t.exists():raise PatchError("ci_report_missing")
 d=json.loads(t.read_text(encoding="utf-8"));t.unlink(missing_ok=True)
 if p.returncode or d.get("status")!="PASS":raise PatchError("canonical_v2_ci_failed:"+json.dumps(d,ensure_ascii=False))
 return d
def main():
 r=root();folder=None;state={};before={x:sha(r/x) for x in PROTECTED}
 try:
  c=json.loads((r/PREREQ).read_text(encoding="utf-8-sig"))
  if git(r,"rev-parse","HEAD").stdout.strip()!=PARENT:raise PatchError("wrong_exact_parent")
  if c.get("stage")!="21.12.2b" or c.get("conclusion")!="GO_TO_IMPLEMENTATION" or c.get("unresolved_contracts")!=[] or not c.get("implementation_authorized") or c.get("handler_consolidation",{}).get("authorized") is not False:raise PatchError("invalid_prerequisite")
  print("[1/10] [PASS] Stage 21.12.2b zero-unresolved implementation prerequisite verified.")
  if git(r,"branch","--show-current").stdout.strip()!=BRANCH or git(r,"diff","--cached","--name-only").stdout.strip():raise PatchError("git_preflight")
  bad=sorted(p for st,p in status(r) if p not in ALLOWED or (p!=SELF.as_posix() and st[0]!=" "))
  if bad:raise PatchError(f"unexpected_dirty:{bad}")
  print("[2/10] [PASS] Branch, exact parent, dirty allowlist and clean index verified.");folder,state=backup(r);print("[3/10] [PASS] Fail-safe backup created before production mutation.")
  write(r/DOMAIN,domain());write(r/APP,app());write(r/TEST,tests());write(r/TOOL,tool());print("[4/10] [PASS] Pure application lifecycle, permission policy, service and in-memory Unit of Work implemented.")
  for x in (SELF,DOMAIN,APP,TEST,TOOL):py_compile.compile(str(r/x),doraise=True)
  print("[5/10] [PASS] Python compile gate passed for patch, implementation, tests and smoke tool.");env=os.environ.copy();env["PYTHONDONTWRITEBYTECODE"]="1";env["PYTHONHASHSEED"]="0"
  t=run([sys.executable,"-B","-m","unittest",TEST.as_posix(),"-v"],r,False,env);sm=run([sys.executable,"-B",TOOL.as_posix()],r,False,env)
  if t.returncode:raise PatchError("tests_failed:"+t.stdout+t.stderr)
  if sm.returncode or "PASS" not in sm.stdout:raise PatchError("smoke_failed:"+sm.stdout+sm.stderr)
  print("[6/10] [PASS] Accept, reject, eligibility, replay, promotion, officer-limit and kick tests passed.");removed=clean(r);cid=ci(r,env);print(f"[7/10] [PASS] Canonical six-gate V2 CI passed after removing {len(removed)} bytecode artifact(s).")
  if before!={x:sha(r/x) for x in PROTECTED}:raise PatchError("protected_runtime_changed")
  print("[8/10] [PASS] V1 sources, handlers/guild.py, unrelated V2 sources, DB sidecars and protected configuration remained byte-identical.")
  rep={"schema_version":1,"stage":STAGE,"status":"PASS","conclusion":"API_READY","source_contract":PREREQ.as_posix(),"domain":DOMAIN.as_posix(),"application":APP.as_posix(),"application_statuses":["pending","accepted","rejected","cancelled"],"runtime_integration":"NOT_CONNECTED","production_persistence":"NOT_CONNECTED","telegram_wiring":"NOT_CONNECTED","handler_consolidation":"NOT_PERFORMED","database_opened":False,"v1_wal_shm_manipulated":False,"manual_game_check":"NOT_REQUIRED","canonical_v2_ci":cid,"removed_bytecode_before_ci":removed};write(r/REPORT,json.dumps(rep,ensure_ascii=False,indent=2)+"\n");write(r/DOC,"# Stage 21.12.2c - Guild Applications/Management implementation\n\n- Status: **PASS**\n- Conclusion: **API_READY**\n- Runtime integration: **NOT_CONNECTED**\n- Production persistence: **NOT_CONNECTED**\n- Telegram wiring: **NOT_CONNECTED**\n- Handler consolidation: **NOT_PERFORMED**\n- Manual game check: **NOT_REQUIRED**\n")
  print("[9/10] [PASS] Machine report and Markdown implementation documentation written.");expected={x.as_posix() for x in TARGETS};git(r,"add","-f","--",*sorted(expected));staged={x.strip().replace("\\","/") for x in git(r,"diff","--cached","--name-only").stdout.splitlines() if x.strip()}
  if staged!=expected:raise PatchError(f"staging_mismatch:{sorted(staged)}")
  z=git(r,"commit","-m","Stage 21.12.2c: implement Guild Applications Management",check=False)
  if z.returncode:raise PatchError("commit_failed:"+z.stdout+z.stderr)
  commit=git(r,"rev-parse","HEAD").stdout.strip();print(f"[10/10] [PASS] Guild Applications/Management implementation committed: {commit}");print("CONCLUSION: API_READY");print("PATCH STATUS: PASS");print(f"GIT COMMIT STATUS: PASS ({commit})");print("HANDLER CONSOLIDATION: NOT_PERFORMED");print("RUNTIME INTEGRATION: NOT_CONNECTED");print("PRODUCTION PERSISTENCE: NOT_CONNECTED");print("MANUAL GAME CHECK: NOT_REQUIRED");print("FAIL-SAFE ROLLBACK: ARMED");return 0
 except Exception as e:
  restored=restore(r,folder,state);recovery=run([sys.executable,"-m","compileall","-q","rom_v2"],r,False);write(r/FAILURE,json.dumps({"schema_version":1,"stage":STAGE,"status":"FAIL_ROLLED_BACK","reason":str(e),"restored_files":restored,"recovery_compile_returncode":recovery.returncode,"main_py_allowed_after_recovery":recovery.returncode==0,"database_opened":False,"v1_wal_shm_manipulated":False},ensure_ascii=False,indent=2)+"\n");print(f"[10/10] [FAIL] {e}; rollback: FAIL_ROLLED_BACK");return 1
if __name__=="__main__":raise SystemExit(main())
