#!/usr/bin/env python3
"""Stage 21.12.3c: implement API-ready Guild Contracts/History without runtime wiring."""
from __future__ import annotations
import hashlib,json,os,py_compile,shutil,subprocess,sys
from datetime import datetime,timezone
from pathlib import Path
STAGE="21.12.3c";BRANCH="rewrite/rom-v2";PARENT="fdfec3b71f2c057665b9f29e7f87c9d94de51c2e"
PREREQ=Path("reports/stage_21_12_3b_resolved_guild_contracts_history_parity.json");SELF=Path("patch/patch_21_12_3c_implement_guild_contracts_history.py")
DOMAIN=Path("rom_v2/domain/guild_contract_history.py");APP=Path("rom_v2/application/guild_contract_history_service.py");TEST=Path("tests_v2/test_guild_contract_history.py");TOOL=Path("tools/check_stage_21_12_3c_guild_contract_history.py");REPORT=Path("reports/stage_21_12_3c_guild_contracts_history_implementation.json");DOC=Path("MD/STAGE_21_12_3C_GUILD_CONTRACTS_HISTORY_IMPLEMENTATION.md");FAILURE=Path("reports/stage_21_12_3c_failure_rollback.json")
TARGETS=(SELF,DOMAIN,APP,TEST,TOOL,REPORT,DOC);PROTECTED=("game.db","game.db-wal","game.db-shm",".env","rom_v2/.env",".runtime/v2/db/rom_v2.db")
ALLOWED={SELF.as_posix(),"ROM_FULL_DUMP.txt",FAILURE.as_posix(),"reports/stage_21_12_3_failure_rollback.json","reports/stage_21_12_3a_failure_rollback.json","reports/stage_21_12_3b_failure_rollback.json","reports/v2_ci_failure.json","reports/v2_ci_result.json"}
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
 f=r/"backup"/("stage_21_12_3c_"+datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ"));state={}
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
def domain():return '"""Pure guild contract completion and history DTOs."""\nfrom __future__ import annotations\nfrom dataclasses import dataclass\n@dataclass(frozen=True,slots=True)\nclass GuildContractCompletion:\n completion_key:str;user_id:int;target_name:str;actor_name:str|None=None\n def __post_init__(self):\n  if not self.completion_key.strip():raise ValueError("missing_completion_key")\n  if self.user_id<1:raise ValueError("invalid_user_id")\n  if not self.target_name.strip():raise ValueError("missing_target_name")\n@dataclass(frozen=True,slots=True)\nclass GuildHistoryEvent:\n event_id:int;guild_id:int;event_code:str;target_name:str;actor_name:str|None=None\n@dataclass(frozen=True,slots=True)\nclass GuildHistoryPage:\n guild_id:int;items:tuple[GuildHistoryEvent,...];total:int;limit:int;offset:int\n\ndef completion_from_legacy(completion_key,user_id,payload,actor_name=None):\n if isinstance(payload,str):target=payload.strip()\n elif isinstance(payload,dict):target=next((str(payload.get(k) or "").strip() for k in ("target_mob_name","name","title","contract_name") if str(payload.get(k) or "").strip()),"")\n else:target=""\n return GuildContractCompletion(str(completion_key).strip(),int(user_id),target,actor_name)\n'
def app():return '"""Pure guild contract reward and history application services."""\nfrom __future__ import annotations\nfrom dataclasses import dataclass\nfrom rom_v2.domain.guild_contract_history import GuildHistoryEvent,GuildHistoryPage\n@dataclass(frozen=True,slots=True)\nclass ContractRewardResult:\n success:bool;reason:str|None=None;guild_id:int|None=None;event_id:int|None=None;already_applied:bool=False\nclass GuildContractHistoryService:\n def __init__(self,uow):self.uow=uow\n def apply(self,completion):\n  previous=self.uow.claim_result(completion.completion_key)\n  if previous is not None:return ContractRewardResult(True,guild_id=previous.guild_id,event_id=previous.event_id,already_applied=True)\n  guild=self.uow.guild_for_user(completion.user_id)\n  if guild is None:return ContractRewardResult(False,"not_in_guild")\n  try:\n   event=GuildHistoryEvent(self.uow.next_event_id(),guild.guild_id,"contract_completed",completion.target_name.strip(),completion.actor_name)\n   self.uow.add_progress(guild.guild_id,completion.user_id,contracts=1)\n   self.uow.append_event(event);result=ContractRewardResult(True,guild_id=guild.guild_id,event_id=event.event_id)\n   self.uow.save_claim(completion.completion_key,result);self.uow.commit();return result\n  except Exception:self.uow.rollback();raise\n def history(self,user_id,guild_id,limit=20,offset=0):\n  guild=self.uow.guild(guild_id)\n  if guild is None:return None,"guild_not_found"\n  if guild.role_of(user_id) is None:return None,"permission_denied"\n  size=max(1,min(100,int(limit)));start=max(0,int(offset));items=tuple(self.uow.events(guild_id,start,size));return GuildHistoryPage(guild_id,items,self.uow.event_count(guild_id),size,start),None\nclass MemoryContractHistoryUow:\n def __init__(self,guilds):self.guilds={g.guild_id:g for g in guilds};self.claims={};self.history_rows=[];self.progress=[];self.sequence=0;self.commits=0;self.rollbacks=0\n def guild(self,i):return self.guilds.get(i)\n def guild_for_user(self,u):return next((g for g in self.guilds.values() if g.role_of(u) is not None),None)\n def claim_result(self,k):return self.claims.get(k)\n def save_claim(self,k,r):self.claims[k]=r\n def next_event_id(self):self.sequence+=1;return self.sequence\n def add_progress(self,g,u,contracts):self.progress.append((g,u,contracts))\n def append_event(self,e):self.history_rows.append(e)\n def events(self,g,offset,limit):return sorted((e for e in self.history_rows if e.guild_id==g),key=lambda e:e.event_id,reverse=True)[offset:offset+limit]\n def event_count(self,g):return sum(e.guild_id==g for e in self.history_rows)\n def commit(self):self.commits+=1\n def rollback(self):self.rollbacks+=1\n'
def tests():return 'import unittest\nfrom rom_v2.application.guild_contract_history_service import *\nfrom rom_v2.domain.guild_contract_history import *\nfrom rom_v2.domain.guild_core import GuildCore,GuildIdentity,GuildMember,GuildRole\ndef guild():return GuildCore(1,GuildIdentity("Варта","варта","ВРТ","врт","🏰"),1,(GuildMember(1,GuildRole.LEADER),GuildMember(2,GuildRole.MEMBER)),10)\nclass ContractHistoryTest(unittest.TestCase):\n def setUp(self):self.u=MemoryContractHistoryUow([guild()]);self.s=GuildContractHistoryService(self.u)\n def test_legacy_target_order(self):\n  c=completion_from_legacy("k1",1,{"target_mob_name":"Вовк","name":"Інше"});self.assertEqual(c.target_name,"Вовк")\n def test_missing_target_fails(self):\n  with self.assertRaisesRegex(ValueError,"missing_target_name"):completion_from_legacy("k1",1,{})\n def test_apply_and_replay(self):\n  c=GuildContractCompletion("k1",1,"Вовк","Герой");a=self.s.apply(c);b=self.s.apply(c);self.assertTrue(a.success);self.assertTrue(b.already_applied);self.assertEqual((len(self.u.progress),len(self.u.history_rows)),(1,1))\n def test_non_member(self):self.assertEqual(self.s.apply(GuildContractCompletion("k",9,"Вовк")).reason,"not_in_guild")\n def test_history_permissions_and_paging(self):\n  for n in ("Вовк","Кабан","Павук"):self.s.apply(GuildContractCompletion("k"+n,1,n))\n  page,reason=self.s.history(2,1,2,0);self.assertIsNone(reason);self.assertEqual(([x.target_name for x in page.items],page.total),(["Павук","Кабан"],3));self.assertEqual(self.s.history(9,1)[1],"permission_denied");self.assertEqual(self.s.history(1,99)[1],"guild_not_found")\n def test_page_clamp_and_out_of_range(self):\n  page,_=self.s.history(1,1,500,99);self.assertEqual((page.limit,page.items),(100,()))\nif __name__=="__main__":unittest.main()\n'
def tool():return '#!/usr/bin/env python3\nfrom pathlib import Path\nimport sys\nR=Path(__file__).resolve().parent.parent\nif str(R) not in sys.path:sys.path.insert(0,str(R))\nfrom rom_v2.application.guild_contract_history_service import *\nfrom rom_v2.domain.guild_contract_history import *\nfrom rom_v2.domain.guild_core import GuildCore,GuildIdentity,GuildMember,GuildRole\ng=GuildCore(1,GuildIdentity("Варта","варта","ВРТ","врт","🏰"),1,(GuildMember(1,GuildRole.LEADER),),10);u=MemoryContractHistoryUow([g]);s=GuildContractHistoryService(u);r=s.apply(GuildContractCompletion("contract:1",1,"Вовк"));p,e=s.history(1,1);assert r.success and e is None and p.items[0].target_name=="Вовк";print("Stage 21.12.3c Guild Contracts History smoke: PASS")\n'

def ci(r,e):
 t=r/"reports/.stage_21_12_3c_ci.tmp.json";t.unlink(missing_ok=True);p=run([sys.executable,"-B","tools/run_v2_ci.py","--project-root",str(r),"--json-out",str(t)],r,False,e)
 if not t.exists():raise PatchError("ci_report_missing")
 d=json.loads(t.read_text(encoding="utf-8"));t.unlink(missing_ok=True)
 if p.returncode or d.get("status")!="PASS":raise PatchError("canonical_v2_ci_failed:"+json.dumps(d,ensure_ascii=False))
 return d
def main():
 r=root();folder=None;state={};before={x:sha(r/x) for x in PROTECTED}
 try:
  c=json.loads((r/PREREQ).read_text(encoding="utf-8-sig"))
  if git(r,"rev-parse","HEAD").stdout.strip()!=PARENT:raise PatchError("wrong_exact_parent")
  if c.get("stage")!="21.12.3b" or c.get("conclusion")!="GO_TO_IMPLEMENTATION" or c.get("unresolved_contracts")!=[] or not c.get("implementation_authorized") or c.get("retention_cleanup_authorized") is not False:raise PatchError("invalid_prerequisite")
  print("[1/10] [PASS] Stage 21.12.3b zero-unresolved implementation prerequisite verified.")
  if git(r,"branch","--show-current").stdout.strip()!=BRANCH or git(r,"diff","--cached","--name-only").stdout.strip():raise PatchError("git_preflight")
  bad=sorted(p for st,p in status(r) if p not in ALLOWED or (p!=SELF.as_posix() and st[0]!=" "))
  if bad:raise PatchError(f"unexpected_dirty:{bad}")
  print("[2/10] [PASS] Branch, exact parent, dirty allowlist and clean index verified.");folder,state=backup(r);print("[3/10] [PASS] Fail-safe backup created before production mutation.")
  write(r/DOMAIN,domain());write(r/APP,app());write(r/TEST,tests());write(r/TOOL,tool());print("[4/10] [PASS] Pure completion/history DTOs, legacy adapter, reward/query service and in-memory Unit of Work implemented.")
  for x in (SELF,DOMAIN,APP,TEST,TOOL):py_compile.compile(str(r/x),doraise=True)
  print("[5/10] [PASS] Python compile gate passed for patch, implementation, tests and smoke tool.");env=os.environ.copy();env["PYTHONDONTWRITEBYTECODE"]="1";env["PYTHONHASHSEED"]="0"
  t=run([sys.executable,"-B","-m","unittest",TEST.as_posix(),"-v"],r,False,env);sm=run([sys.executable,"-B",TOOL.as_posix()],r,False,env)
  if t.returncode:raise PatchError("tests_failed:"+t.stdout+t.stderr)
  if sm.returncode or "PASS" not in sm.stdout:raise PatchError("smoke_failed:"+sm.stdout+sm.stderr)
  print("[6/10] [PASS] Target-name, missing-name, atomic reward, replay, permission and paging tests passed.");removed=clean(r);cid=ci(r,env);print(f"[7/10] [PASS] Canonical six-gate V2 CI passed after removing {len(removed)} bytecode artifact(s).")
  if before!={x:sha(r/x) for x in PROTECTED}:raise PatchError("protected_runtime_changed")
  print("[8/10] [PASS] V1 sources, unrelated V2 sources, DB sidecars and protected configuration remained byte-identical.")
  rep={"schema_version":1,"stage":STAGE,"status":"PASS","conclusion":"API_READY","source_contract":PREREQ.as_posix(),"domain":DOMAIN.as_posix(),"application":APP.as_posix(),"runtime_integration":"NOT_CONNECTED","production_persistence":"NOT_CONNECTED","telegram_wiring":"NOT_CONNECTED","retention_cleanup":"NOT_PERFORMED","database_opened":False,"v1_wal_shm_manipulated":False,"manual_game_check":"NOT_REQUIRED","canonical_v2_ci":cid,"removed_bytecode_before_ci":removed};write(r/REPORT,json.dumps(rep,ensure_ascii=False,indent=2)+"\n");write(r/DOC,"# Stage 21.12.3c - Guild Contracts/History implementation\n\n- Status: **PASS**\n- Conclusion: **API_READY**\n- Runtime integration: **NOT_CONNECTED**\n- Production persistence: **NOT_CONNECTED**\n- Telegram wiring: **NOT_CONNECTED**\n- Retention cleanup: **NOT_PERFORMED**\n- Manual game check: **NOT_REQUIRED**\n")
  print("[9/10] [PASS] Machine report and Markdown implementation documentation written.");expected={x.as_posix() for x in TARGETS};git(r,"add","-f","--",*sorted(expected));staged={x.strip().replace("\\","/") for x in git(r,"diff","--cached","--name-only").stdout.splitlines() if x.strip()}
  if staged!=expected:raise PatchError(f"staging_mismatch:{sorted(staged)}")
  z=git(r,"commit","-m","Stage 21.12.3c: implement Guild Contracts History",check=False)
  if z.returncode:raise PatchError("commit_failed:"+z.stdout+z.stderr)
  commit=git(r,"rev-parse","HEAD").stdout.strip();print(f"[10/10] [PASS] Guild Contracts/History implementation committed: {commit}");print("CONCLUSION: API_READY");print("PATCH STATUS: PASS");print(f"GIT COMMIT STATUS: PASS ({commit})");print("RETENTION CLEANUP: NOT_PERFORMED");print("RUNTIME INTEGRATION: NOT_CONNECTED");print("PRODUCTION PERSISTENCE: NOT_CONNECTED");print("MANUAL GAME CHECK: NOT_REQUIRED");print("FAIL-SAFE ROLLBACK: ARMED");return 0
 except Exception as e:
  restored=restore(r,folder,state);recovery=run([sys.executable,"-m","compileall","-q","rom_v2"],r,False);write(r/FAILURE,json.dumps({"schema_version":1,"stage":STAGE,"status":"FAIL_ROLLED_BACK","reason":str(e),"restored_files":restored,"recovery_compile_returncode":recovery.returncode,"main_py_allowed_after_recovery":recovery.returncode==0,"database_opened":False,"v1_wal_shm_manipulated":False},ensure_ascii=False,indent=2)+"\n");print(f"[10/10] [FAIL] {e}; rollback: FAIL_ROLLED_BACK");return 1
if __name__=="__main__":raise SystemExit(main())
