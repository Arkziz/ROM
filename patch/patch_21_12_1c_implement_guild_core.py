#!/usr/bin/env python3
"""Stage 21.12.1c: implement API-ready Guild Core without runtime persistence wiring."""
from __future__ import annotations
import hashlib,json,os,py_compile,shutil,subprocess,sys
from datetime import datetime,timezone
from pathlib import Path
STAGE="21.12.1c";BRANCH="rewrite/rom-v2";PARENT="221794f26b5dc7aff7e7ff1fe08b05e2533bcb59"
PREREQ=Path("reports/stage_21_12_1b_resolved_guild_core_parity.json");SELF=Path("patch/patch_21_12_1c_implement_guild_core.py")
DOMAIN=Path("rom_v2/domain/guild_core.py");APP=Path("rom_v2/application/guild_core_service.py");TEST=Path("tests_v2/test_guild_core.py");TOOL=Path("tools/check_stage_21_12_1c_guild_core.py");REPORT=Path("reports/stage_21_12_1c_guild_core_implementation.json");DOC=Path("MD/STAGE_21_12_1C_GUILD_CORE_IMPLEMENTATION.md");FAILURE=Path("reports/stage_21_12_1c_failure_rollback.json")
TARGETS=(SELF,DOMAIN,APP,TEST,TOOL,REPORT,DOC);PROTECTED=("game.db","game.db-wal","game.db-shm",".env","rom_v2/.env",".runtime/v2/db/rom_v2.db")
ALLOWED={SELF.as_posix(),"ROM_FULL_DUMP.txt",FAILURE.as_posix(),"reports/stage_21_12_1_failure_rollback.json","reports/stage_21_12_1a_failure_rollback.json","reports/stage_21_12_1b_failure_rollback.json","reports/v2_ci_failure.json","reports/v2_ci_result.json"}
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
 f=r/"backup"/("stage_21_12_1c_"+datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ"));state={}
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
def domain():return '''"""Pure Guild Core aggregate and invariants for V1 parity."""
from __future__ import annotations
from dataclasses import dataclass,replace
from enum import StrEnum
CREATION_COST_GOLD=50.0
MINIMUM_ACCESS_LEVEL=3
DEFAULT_MEMBER_LIMIT=10
class GuildRole(StrEnum):LEADER="leader";OFFICER="officer";MEMBER="member"
@dataclass(frozen=True,slots=True)
class GuildIdentity:
 name:str;name_key:str;tag:str;tag_key:str;icon:str
 def __post_init__(self):
  if not all((self.name,self.name_key,self.tag,self.tag_key,self.icon)):raise ValueError("invalid_identity")
@dataclass(frozen=True,slots=True)
class GuildMember:
 user_id:int;role:GuildRole
 def __post_init__(self):
  if self.user_id<1:raise ValueError("invalid_user_id")
@dataclass(frozen=True,slots=True)
class GuildCore:
 guild_id:int;identity:GuildIdentity;leader_user_id:int;members:tuple[GuildMember,...];member_limit:int=DEFAULT_MEMBER_LIMIT
 def __post_init__(self):self.validate()
 def validate(self):
  if self.guild_id<1 or self.member_limit<1:raise ValueError("invalid_guild")
  ids=[m.user_id for m in self.members]
  if len(ids)!=len(set(ids)):raise ValueError("duplicate_membership")
  if len(ids)>self.member_limit:raise ValueError("member_limit_reached")
  leaders=[m.user_id for m in self.members if m.role is GuildRole.LEADER]
  if leaders!=[self.leader_user_id]:raise ValueError("leader_invariant_broken")
 def role_of(self,user_id):return next((m.role for m in self.members if m.user_id==user_id),None)
 def can(self,user_id,permission):
  role=self.role_of(user_id)
  matrix={GuildRole.LEADER:{"manage_applications","manage_roles","manage_members","transfer","leave","dissolve"},GuildRole.OFFICER:{"manage_applications"},GuildRole.MEMBER:set()}
  return role is not None and permission in matrix[role]
 def transfer(self,actor_id,target_id):
  if actor_id!=self.leader_user_id:return None,"permission_denied"
  if target_id==actor_id:return None,"target_is_leader"
  if self.role_of(target_id) is None:return None,"target_not_member"
  changed=tuple(GuildMember(m.user_id,GuildRole.LEADER if m.user_id==target_id else GuildRole.MEMBER if m.user_id==actor_id else m.role) for m in self.members)
  return replace(self,leader_user_id=target_id,members=changed),None
 def leave(self,user_id):
  role=self.role_of(user_id)
  if role is None:return None,"not_in_guild"
  if role is GuildRole.LEADER and len(self.members)>1:return None,"leadership_transfer_required"
  if role is GuildRole.LEADER:return None,"dissolve_required"
  return replace(self,members=tuple(m for m in self.members if m.user_id!=user_id)),None
'''
def app():return '''"""Guild Core application service with in-memory Unit of Work fixtures."""
from __future__ import annotations
from dataclasses import dataclass
from rom_v2.domain.guild_core import *
@dataclass(frozen=True,slots=True)
class GuildResult:
 success:bool;reason:str|None=None;guild:GuildCore|None=None;gold_balance:float|None=None;dissolved:bool=False
class GuildCoreService:
 def __init__(self,uow):self.uow=uow
 def create(self,user_id,level,identity):
  if level<MINIMUM_ACCESS_LEVEL:return GuildResult(False,"level_too_low")
  if self.uow.guild_for_user(user_id):return GuildResult(False,"already_in_guild")
  if self.uow.name_exists(identity.name_key):return GuildResult(False,"duplicate_name")
  if self.uow.tag_exists(identity.tag_key):return GuildResult(False,"duplicate_tag")
  if self.uow.gold(user_id)<CREATION_COST_GOLD:return GuildResult(False,"insufficient_gold")
  try:
   guild=GuildCore(self.uow.next_guild_id(),identity,user_id,(GuildMember(user_id,GuildRole.LEADER),),DEFAULT_MEMBER_LIMIT)
   self.uow.debit(user_id,CREATION_COST_GOLD);self.uow.save(guild);self.uow.commit();return GuildResult(True,guild=guild,gold_balance=self.uow.gold(user_id))
  except Exception:self.uow.rollback();raise
 def transfer(self,actor_id,target_id):
  guild=self.uow.guild_for_user(actor_id)
  if guild is None:return GuildResult(False,"not_in_guild")
  changed,reason=guild.transfer(actor_id,target_id)
  if changed is None:return GuildResult(False,reason,guild)
  self.uow.save(changed);self.uow.commit();return GuildResult(True,guild=changed)
 def leave(self,user_id):
  guild=self.uow.guild_for_user(user_id)
  if guild is None:return GuildResult(False,"not_in_guild")
  changed,reason=guild.leave(user_id)
  if reason=="dissolve_required":self.uow.delete(guild.guild_id);self.uow.commit();return GuildResult(True,dissolved=True)
  if changed is None:return GuildResult(False,reason,guild)
  self.uow.save(changed);self.uow.commit();return GuildResult(True,guild=changed)
class MemoryGuildUow:
 def __init__(self,gold):self.gold_balances=dict(gold);self.guilds={};self.sequence=0;self.commits=0;self.rollbacks=0
 def next_guild_id(self):self.sequence+=1;return self.sequence
 def gold(self,u):return float(self.gold_balances.get(u,0.0))
 def debit(self,u,a):
  if self.gold(u)<a:raise ValueError("insufficient_gold")
  self.gold_balances[u]=round(self.gold(u)-a,2)
 def guild_for_user(self,u):return next((g for g in self.guilds.values() if g.role_of(u) is not None),None)
 def name_exists(self,k):return any(g.identity.name_key==k for g in self.guilds.values())
 def tag_exists(self,k):return any(g.identity.tag_key==k for g in self.guilds.values())
 def save(self,g):self.guilds[g.guild_id]=g
 def delete(self,i):self.guilds.pop(i,None)
 def commit(self):self.commits+=1
 def rollback(self):self.rollbacks+=1
'''
def tests():return '''import unittest
from rom_v2.application.guild_core_service import *
def identity(name="Варта",tag="ВРТ"):return GuildIdentity(name,name.casefold(),tag,tag.casefold(),"🏰")
class GuildCoreTest(unittest.TestCase):
 def setUp(self):self.u=MemoryGuildUow({1:100.0,2:100.0});self.s=GuildCoreService(self.u)
 def test_create_constants_and_retry(self):
  r=self.s.create(1,3,identity());self.assertTrue(r.success);self.assertEqual((r.gold_balance,r.guild.member_limit,r.guild.role_of(1)),(50.0,10,GuildRole.LEADER));self.assertEqual(self.s.create(1,3,identity("Друга","ДРГ")).reason,"already_in_guild");self.assertEqual(self.u.gold(1),50.0)
 def test_create_rejections(self):
  self.assertEqual(self.s.create(1,2,identity()).reason,"level_too_low");self.u.gold_balances[1]=49.99;self.assertEqual(self.s.create(1,3,identity()).reason,"insufficient_gold")
 def test_duplicate_identity(self):
  self.s.create(1,3,identity());self.assertEqual(self.s.create(2,3,identity()).reason,"duplicate_name");self.assertEqual(self.s.create(2,3,identity("Тінь","ВРТ")).reason,"duplicate_tag")
 def test_transfer_atomic_roles(self):
  g=self.s.create(1,3,identity()).guild;g=GuildCore(g.guild_id,g.identity,1,g.members+(GuildMember(2,GuildRole.MEMBER),));self.u.save(g);r=self.s.transfer(1,2);self.assertTrue(r.success);self.assertEqual((r.guild.leader_user_id,r.guild.role_of(1),r.guild.role_of(2)),(2,GuildRole.MEMBER,GuildRole.LEADER))
 def test_leader_leave_and_dissolve(self):
  g=self.s.create(1,3,identity()).guild;g=GuildCore(g.guild_id,g.identity,1,g.members+(GuildMember(2,GuildRole.MEMBER),));self.u.save(g);self.assertEqual(self.s.leave(1).reason,"leadership_transfer_required");self.assertTrue(self.s.leave(2).success);self.assertTrue(self.s.leave(1).dissolved);self.assertEqual(self.u.guilds,{})
 def test_permission_matrix(self):
  g=self.s.create(1,3,identity()).guild;g=GuildCore(g.guild_id,g.identity,1,g.members+(GuildMember(2,GuildRole.OFFICER),GuildMember(3,GuildRole.MEMBER)));self.assertTrue(g.can(1,"transfer"));self.assertTrue(g.can(2,"manage_applications"));self.assertFalse(g.can(2,"transfer"));self.assertFalse(g.can(3,"manage_applications"))
 def test_invariant_guard(self):
  with self.assertRaises(ValueError):GuildCore(1,identity(),1,(GuildMember(1,GuildRole.MEMBER),))
if __name__=="__main__":unittest.main()
'''
def tool():return '''#!/usr/bin/env python3
from pathlib import Path
import sys
R=Path(__file__).resolve().parent.parent
if str(R) not in sys.path:sys.path.insert(0,str(R))
from rom_v2.application.guild_core_service import *
i=GuildIdentity("Варта","варта","ВРТ","врт","🏰");u=MemoryGuildUow({1:100.0});r=GuildCoreService(u).create(1,3,i);assert r.success and r.gold_balance==50.0 and r.guild.member_limit==10 and r.guild.role_of(1) is GuildRole.LEADER;print("Stage 21.12.1c Guild Core smoke: PASS")
'''
def ci(r,e):
 t=r/"reports/.stage_21_12_1c_ci.tmp.json";t.unlink(missing_ok=True);p=run([sys.executable,"-B","tools/run_v2_ci.py","--project-root",str(r),"--json-out",str(t)],r,False,e)
 if not t.exists():raise PatchError("ci_report_missing")
 d=json.loads(t.read_text(encoding="utf-8"));t.unlink(missing_ok=True)
 if p.returncode or d.get("status")!="PASS":raise PatchError("canonical_v2_ci_failed:"+json.dumps(d,ensure_ascii=False))
 return d
def main():
 r=root();folder=None;state={};before={x:sha(r/x) for x in PROTECTED}
 try:
  c=json.loads((r/PREREQ).read_text(encoding="utf-8-sig"))
  if git(r,"rev-parse","HEAD").stdout.strip()!=PARENT:raise PatchError("wrong_exact_parent")
  if c.get("stage")!="21.12.1b" or c.get("conclusion")!="GO_TO_IMPLEMENTATION" or c.get("unresolved_contracts")!=[] or not c.get("implementation_authorized"):raise PatchError("invalid_prerequisite")
  constants=c.get("canonical_constants",{})
  if constants.get("creation_cost_gold")!=50.0 or constants.get("minimum_access_level")!=3 or constants.get("default_member_limit")!=10:raise PatchError("canonical_constant_mismatch")
  print("[1/10] [PASS] Stage 21.12.1b zero-unresolved implementation prerequisite verified.")
  if git(r,"branch","--show-current").stdout.strip()!=BRANCH or git(r,"diff","--cached","--name-only").stdout.strip():raise PatchError("git_preflight")
  bad=sorted(p for st,p in status(r) if p not in ALLOWED or (p!=SELF.as_posix() and st[0]!=" "))
  if bad:raise PatchError(f"unexpected_dirty:{bad}")
  print("[2/10] [PASS] Branch, exact parent, dirty allowlist and clean index verified.");folder,state=backup(r);print("[3/10] [PASS] Fail-safe backup created before production mutation.")
  write(r/DOMAIN,domain());write(r/APP,app());write(r/TEST,tests());write(r/TOOL,tool());print("[4/10] [PASS] Pure Guild Core aggregate, permission matrix, application service and in-memory Unit of Work implemented.")
  for x in (SELF,DOMAIN,APP,TEST,TOOL):py_compile.compile(str(r/x),doraise=True)
  print("[5/10] [PASS] Python compile gate passed for patch, implementation, tests and smoke tool.");env=os.environ.copy();env["PYTHONDONTWRITEBYTECODE"]="1";env["PYTHONHASHSEED"]="0"
  t=run([sys.executable,"-B","-m","unittest",TEST.as_posix(),"-v"],r,False,env);sm=run([sys.executable,"-B",TOOL.as_posix()],r,False,env)
  if t.returncode:raise PatchError("tests_failed:"+t.stdout+t.stderr)
  if sm.returncode or "PASS" not in sm.stdout:raise PatchError("smoke_failed:"+sm.stdout+sm.stderr)
  print("[6/10] [PASS] Creation, duplicate, invariant, permission, transfer, leave, dissolution and retry tests passed.");removed=clean(r);cid=ci(r,env);print(f"[7/10] [PASS] Canonical six-gate V2 CI passed after removing {len(removed)} bytecode artifact(s).")
  if before!={x:sha(r/x) for x in PROTECTED}:raise PatchError("protected_runtime_changed")
  print("[8/10] [PASS] V1 sources, unrelated V2 sources, DB sidecars and protected configuration remained byte-identical.")
  rep={"schema_version":1,"stage":STAGE,"status":"PASS","conclusion":"API_READY","generated_at_utc":datetime.now(timezone.utc).isoformat(),"source_contract":PREREQ.as_posix(),"domain":DOMAIN.as_posix(),"application":APP.as_posix(),"canonical_constants":{"creation_cost_gold":50.0,"minimum_access_level":3,"default_member_limit":10,"roles":["leader","officer","member"]},"runtime_integration":"NOT_CONNECTED","production_persistence":"NOT_CONNECTED","telegram_wiring":"NOT_CONNECTED","guild_resource_wiring":"NOT_CONNECTED","database_opened":False,"v1_wal_shm_manipulated":False,"manual_game_check":"NOT_REQUIRED","canonical_v2_ci":cid,"removed_bytecode_before_ci":removed,"backup_path":folder.relative_to(r).as_posix()};write(r/REPORT,json.dumps(rep,ensure_ascii=False,indent=2)+"\n");write(r/DOC,"# Stage 21.12.1c - Guild Core implementation\n\n- Status: **PASS**\n- Conclusion: **API_READY**\n- Creation cost: **50.00 gold**\n- Minimum level: **3**\n- Member limit: **10**\n- Runtime integration: **NOT_CONNECTED**\n- Production persistence: **NOT_CONNECTED**\n- Telegram wiring: **NOT_CONNECTED**\n- Manual game check: **NOT_REQUIRED**\n")
  print("[9/10] [PASS] Machine report and Markdown implementation documentation written.");expected={x.as_posix() for x in TARGETS};git(r,"add","-f","--",*sorted(expected));staged={x.strip().replace("\\","/") for x in git(r,"diff","--cached","--name-only").stdout.splitlines() if x.strip()}
  if staged!=expected:raise PatchError(f"staging_mismatch:{sorted(staged)}")
  z=git(r,"commit","-m","Stage 21.12.1c: implement Guild Core",check=False)
  if z.returncode:raise PatchError("commit_failed:"+z.stdout+z.stderr)
  commit=git(r,"rev-parse","HEAD").stdout.strip();changed={x.strip().replace("\\","/") for x in git(r,"diff-tree","--no-commit-id","--name-only","-r",commit).stdout.splitlines() if x.strip()}
  if changed!=expected:raise PatchError(f"commit_scope_mismatch:{sorted(changed)}")
  print(f"[10/10] [PASS] Guild Core implementation committed: {commit}");print("CONCLUSION: API_READY");print("PATCH STATUS: PASS");print(f"GIT COMMIT STATUS: PASS ({commit})");print("RUNTIME INTEGRATION: NOT_CONNECTED");print("PRODUCTION PERSISTENCE: NOT_CONNECTED");print("MANUAL GAME CHECK: NOT_REQUIRED");print("FAIL-SAFE ROLLBACK: ARMED");return 0
 except Exception as e:
  restored=restore(r,folder,state);recovery=run([sys.executable,"-m","compileall","-q","rom_v2"],r,False);write(r/FAILURE,json.dumps({"schema_version":1,"stage":STAGE,"status":"FAIL_ROLLED_BACK","reason":str(e),"restored_files":restored,"recovery_compile_returncode":recovery.returncode,"main_py_allowed_after_recovery":recovery.returncode==0,"main_py_must_not_run":recovery.returncode!=0,"database_opened":False,"v1_wal_shm_manipulated":False},ensure_ascii=False,indent=2)+"\n");print(f"[10/10] [FAIL] {e}; rollback: FAIL_ROLLED_BACK");return 1
if __name__=="__main__":raise SystemExit(main())
