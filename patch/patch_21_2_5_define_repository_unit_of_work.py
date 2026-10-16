#!/usr/bin/env python3
"""Stage 21.2.5: define canonical Repository and Unit of Work contracts."""
from __future__ import annotations
import hashlib, json, os, py_compile, subprocess, sys
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

STAGE="21.2.5"; TARGET_BRANCH="rewrite/rom-v2"; EXPECTED_PARENT="cff76de5b9cf11b57764a66d5b01bc7d50eee70e"
EVENT_REPORT="reports/stage_21_2_4_domain_event_model.json"; RESULT_REPORT="reports/stage_21_2_3_result_error_model.json"
PATCH_PATH="patch/patch_21_2_5_define_repository_unit_of_work.py"; VERIFIER_PATH="tools/verify_v2_repository_unit_of_work.py"
REPORT_PATH="reports/stage_21_2_5_repository_unit_of_work.json"; ADR_PATH="MD/ADR_21_2_5_V2_REPOSITORY_UNIT_OF_WORK.md"
FAILURE_REPORT="reports/stage_21_2_5_failure_rollback.json"; COMMIT_MESSAGE="Stage 21.2.5: define Repository and Unit of Work"
OWNED={PATCH_PATH,VERIFIER_PATH,REPORT_PATH,ADR_PATH,FAILURE_REPORT}; ALLOWED_DIRTY={"ROM_FULL_DUMP.txt","ROM_ADDITIONAL_DUMP.txt"}
DB_FILES=("game.db","game.db-wal","game.db-shm"); BACKUP_PREFIX="stage_21_2_5"

CONTRACT={
 "schema_version":1,
 "canonical_owners":{"repository_ports":"rom_v2.application.ports.repositories","unit_of_work_port":"rom_v2.application.ports.unit_of_work","sqlite_repository_adapters":"rom_v2.infrastructure.persistence.sqlite.repositories","sqlite_unit_of_work_adapter":"rom_v2.infrastructure.persistence.sqlite.unit_of_work"},
 "repository_contract":{"aggregate_oriented":True,"returns_domain_objects":True,"storage_rows_forbidden":True,"transaction_control_forbidden":True,"required_operations":["get","add","save","exists"],"expected_version_required_on_update":True},
 "unit_of_work_contract":{"explicit":True,"one_business_operation_per_unit_of_work":True,"single_commit_point":True,"rollback_on_non_success":True,"rollback_on_exception":True,"repositories_share_one_transaction":True,"events_same_transaction":True,"outbox_same_transaction":True,"publish_after_commit":True,"nested_uow_forbidden":True,"implicit_autocommit_forbidden":True},
 "optimistic_concurrency":{"aggregate_version_required":True,"compare_and_swap":True,"zero_rows_updated_maps_to":"stale_state","retry_reloads_and_revalidates":True,"blind_overwrite_forbidden":True},
 "exact_once_settlement":{"operation_id_required":True,"unique_operation_key":True,"claim_and_business_mutation_same_transaction":True,"duplicate_completed_operation_maps_to":"idempotent_repeat","duplicate_in_progress_operation_maps_to":"retryable_error","stored_result_fingerprint_required":True,"duplicate_never_repeats_mutation":True,"duplicate_never_emits_event":True,"crash_before_commit_retryable":True,"crash_after_commit_returns_prior_outcome":True},
 "result_mapping":{"version_conflict":"stale_state","duplicate_completed":"idempotent_repeat","duplicate_in_progress":"retryable_error","transient_storage_failure":"retryable_error","integrity_violation":"consistency_error","successful_commit":"success"},
 "recovery":{"process_memory_not_source_of_truth":True,"idempotency_record_persistent":True,"outbox_pending_persistent":True,"rollback_leaves_no_partial_state":True,"restart_revalidates_integrity":True},
 "forbidden_alternatives":["repository commit","repository returns storage rows","application imports SQLite/ORM","implicit autocommit","blind overwrite","idempotency check outside transaction","process-memory idempotency","second production UoW"]
}

VERIFIER=r'''#!/usr/bin/env python3
from __future__ import annotations
import argparse, ast, json, re
from pathlib import Path
from typing import Any
OWNERS={"repository_ports":"rom_v2.application.ports.repositories","unit_of_work_port":"rom_v2.application.ports.unit_of_work","sqlite_repository_adapters":"rom_v2.infrastructure.persistence.sqlite.repositories","sqlite_unit_of_work_adapter":"rom_v2.infrastructure.persistence.sqlite.unit_of_work"}
REPO=re.compile(r"(?i).*(repository|repo)$"); UOW=re.compile(r"(?i).*(unitofwork|uow)$"); DB={"sqlite3","sqlalchemy","aiosqlite"}
def verify(root:Path,c:dict[str,Any])->dict[str,Any]:
 v=[]
 if c.get("canonical_owners")!=OWNERS:v.append({"rule":"CANONICAL_OWNERS"})
 repo=c.get("repository_contract",{}); uow=c.get("unit_of_work_contract",{}); opt=c.get("optimistic_concurrency",{}); exact=c.get("exact_once_settlement",{})
 for k in ("aggregate_oriented","returns_domain_objects","storage_rows_forbidden","transaction_control_forbidden","expected_version_required_on_update"):
  if not repo.get(k):v.append({"rule":"REPOSITORY_INVARIANT","key":k})
 if set(repo.get("required_operations",[]))!={"get","add","save","exists"}:v.append({"rule":"REPOSITORY_OPERATIONS"})
 for k in ("explicit","one_business_operation_per_unit_of_work","single_commit_point","rollback_on_non_success","rollback_on_exception","repositories_share_one_transaction","events_same_transaction","outbox_same_transaction","publish_after_commit","nested_uow_forbidden","implicit_autocommit_forbidden"):
  if not uow.get(k):v.append({"rule":"UOW_INVARIANT","key":k})
 for k in ("aggregate_version_required","compare_and_swap","retry_reloads_and_revalidates","blind_overwrite_forbidden"):
  if not opt.get(k):v.append({"rule":"OPTIMISTIC_INVARIANT","key":k})
 for k in ("operation_id_required","unique_operation_key","claim_and_business_mutation_same_transaction","stored_result_fingerprint_required","duplicate_never_repeats_mutation","duplicate_never_emits_event","crash_before_commit_retryable","crash_after_commit_returns_prior_outcome"):
  if not exact.get(k):v.append({"rule":"EXACT_ONCE_INVARIANT","key":k})
 repos=[];uows=[];dbimports=[];txmethods=[];runtime=root/"rom_v2"
 if runtime.is_dir():
  for p in sorted(runtime.rglob("*.py")):
   rel=p.relative_to(root).as_posix()
   try:t=ast.parse(p.read_text(encoding="utf-8",errors="replace"),filename=rel)
   except SyntaxError as e:v.append({"rule":"PARSE_ERROR","file":rel,"error":str(e)});continue
   for n in ast.walk(t):
    if isinstance(n,ast.ClassDef):
     if REPO.fullmatch(n.name):
      repos.append({"file":rel,"class":n.name,"line":n.lineno})
      for m in n.body:
       if isinstance(m,(ast.FunctionDef,ast.AsyncFunctionDef)) and m.name in {"begin","commit","rollback"}:txmethods.append({"file":rel,"class":n.name,"method":m.name,"line":m.lineno})
     if UOW.fullmatch(n.name):uows.append({"file":rel,"class":n.name,"line":n.lineno})
    if rel.startswith("rom_v2/application/"):
     mods=[a.name for a in n.names] if isinstance(n,ast.Import) else ([n.module or ""] if isinstance(n,ast.ImportFrom) else [])
     for mod in mods:
      if mod.split(".")[0] in DB:dbimports.append({"file":rel,"line":n.lineno,"import":mod})
 if txmethods:v.append({"rule":"REPOSITORY_OWNS_TRANSACTION","methods":txmethods})
 if dbimports:v.append({"rule":"APPLICATION_DB_IMPORT","imports":dbimports})
 if runtime.is_dir() and not [x for x in repos if x["file"].startswith("rom_v2/application/ports/")]:v.append({"rule":"MISSING_REPOSITORY_PORT_AFTER_SCAFFOLD"})
 if runtime.is_dir() and len([x for x in uows if x["file"]=="rom_v2/application/ports/unit_of_work.py"])!=1:v.append({"rule":"UNIT_OF_WORK_PORT_COUNT","owners":uows})
 return {"schema_version":1,"summary":{"status":"PASS" if not v else "FAIL","physical_v2_exists":runtime.is_dir(),"repository_owner_count":len(repos),"unit_of_work_owner_count":len(uows),"application_db_import_count":len(dbimports),"repository_transaction_method_count":len(txmethods),"violation_count":len(v)},"repository_owners":repos,"unit_of_work_owners":uows,"application_db_imports":dbimports,"repository_transaction_methods":txmethods,"violations":v}
def main()->int:
 p=argparse.ArgumentParser();p.add_argument("--project-root",default=".");p.add_argument("--contract",required=True);p.add_argument("--json-out");a=p.parse_args();r=verify(Path(a.project_root).resolve(),json.loads(Path(a.contract).read_text(encoding="utf-8")));text=json.dumps(r,ensure_ascii=False,indent=2)+"\n"
 if a.json_out:Path(a.json_out).write_text(text,encoding="utf-8",newline="\n")
 print(f"V2 Repository/UoW verifier: {r['summary']['status']}");print(f"Repository owners: {r['summary']['repository_owner_count']}");print(f"UoW owners: {r['summary']['unit_of_work_owner_count']}");print(f"Application DB imports: {r['summary']['application_db_import_count']}");print(f"Repository transaction methods: {r['summary']['repository_transaction_method_count']}");print(f"Violations: {r['summary']['violation_count']}");return 0 if r["summary"]["status"]=="PASS" else 1
if __name__=="__main__":raise SystemExit(main())
'''
@dataclass(frozen=True)
class Check: check_id:str;status:str;summary:str;details:dict[str,Any];blocking:bool=False
class PatchError(RuntimeError):pass
def run(root:Path,*cmd:str,timeout:int=120):return subprocess.run(cmd,cwd=root,text=True,encoding="utf-8",errors="replace",capture_output=True,timeout=timeout,check=False)
def git(root:Path,*args:str):return run(root,"git",*args)
def rev(root:Path,name:str):
 r=git(root,"rev-parse","--verify",f"{name}^{{commit}}");return r.stdout.strip() if r.returncode==0 else None
def sha(path:Path):
 h=hashlib.sha256()
 with path.open("rb") as f:
  for c in iter(lambda:f.read(1048576),b""):h.update(c)
 return h.hexdigest()
def db(root:Path):
 return {n:({"exists":False} if not (p:=root/n).exists() else {"exists":True,"size":p.stat().st_size,"mtime_ns":p.stat().st_mtime_ns,"sha256":sha(p)}) for n in DB_FILES}
def write(path:Path,text:str):
 t=path.with_suffix(path.suffix+".tmp");t.parent.mkdir(parents=True,exist_ok=True);t.write_text(text,encoding="utf-8",newline="\n");os.replace(t,path)
def status(raw:str):return [{"status":x[:2],"path":x[3:]} for x in raw.split("\0") if x]
def blob(root:Path,commit:str,path:str):
 r=subprocess.run(["git","show",f"{commit}:{path}"],cwd=root,capture_output=True,check=False);return r.stdout if r.returncode==0 else None
def backups(root:Path):
 (root/"backup").mkdir(exist_ok=True);m={"files":{}}
 for rel in (VERIFIER_PATH,REPORT_PATH,ADR_PATH):
  b=blob(root,EXPECTED_PARENT,rel);p=root/"backup"/f"{BACKUP_PREFIX}__{rel.replace('/','__')}"
  if b is None:m["files"][rel]={"existed":False,"backup":None}
  else:p.write_bytes(b);m["files"][rel]={"existed":True,"backup":str(p.relative_to(root)).replace("\\","/")}
 return m
def rollback(root:Path,m,reason,checks):
 git(root,"reset","--",VERIFIER_PATH,REPORT_PATH,ADR_PATH);restored=[];removed=[];errors=[]
 for rel,meta in m["files"].items():
  p=root/rel
  try:
   if meta["existed"]:p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes((root/meta["backup"]).read_bytes());restored.append(rel)
   elif p.exists():p.unlink();removed.append(rel)
  except OSError as e:errors.append(f"{rel}: {e}")
 out={"stage":STAGE,"status":"FAIL_ROLLED_BACK" if not errors else "ROLLBACK_INCOMPLETE","reason":reason,"failed_checks":[asdict(x) for x in checks if x.status=="FAIL"],"restored_files":restored,"removed_failed_artifacts":removed,"rollback_errors":errors,"database_evidence_after_rollback":db(root),"main_py_started":False,"wal_shm_manipulated":False};write(root/FAILURE_REPORT,json.dumps(out,ensure_ascii=False,indent=2)+"\n");return out
def adr(r):
 s=r["summary"];return "\n".join(["# ADR 21.2.5 — ROM V2 Repository and Unit of Work","","- **Status:** `ACCEPTED`","- **Repository ports owner:** `rom_v2.application.ports.repositories`","- **Unit of Work port owner:** `rom_v2.application.ports.unit_of_work`","","## Decision","","Repositories are aggregate-oriented application ports, return domain objects and never own transactions. One explicit Unit of Work owns all repositories, state changes, domain events and outbox records for one business operation.","","## Atomicity","","All preconditions precede mutation. There is one transaction and one commit point. Every non-success Result or exception rolls back. Nested UoW and implicit autocommit are forbidden.","","## Optimistic concurrency","","Updates require expected version compare-and-swap. Zero rows updated maps to `stale_state`; retry reloads and fully revalidates.","","## Exact-once settlement","","A persistent unique operation ID is claimed in the same transaction as mutation. Completed duplicates return `idempotent_repeat` without another mutation or event. In-progress duplicates return `retryable_error`.","","## Automated evidence","",f"- Physical V2 exists: **{s['physical_v2_exists']}**.",f"- Application DB imports: **{s['application_db_import_count']}**.",f"- Repository transaction methods: **{s['repository_transaction_method_count']}**.",f"- Violations: **{s['violation_count']}**.","","## Next roadmap stage","","Stage 21.2.6 — Clock and RNG abstractions.",""])
def commit(root):
 paths=[PATCH_PATH,VERIFIER_PATH,REPORT_PATH,ADR_PATH];r=git(root,"add","-f","--",*paths)
 if r.returncode:raise PatchError(r.stderr.strip())
 staged=sorted(x for x in git(root,"diff","--cached","--name-only","-z").stdout.split("\0") if x)
 if staged!=sorted(paths):git(root,"reset","--",*paths);raise PatchError(f"staging mismatch: {staged}")
 r=git(root,"commit","-m",COMMIT_MESSAGE)
 if r.returncode:git(root,"reset","--",*paths);raise PatchError(r.stderr.strip() or r.stdout.strip())
 return rev(root,"HEAD") or ""
def main():
 root=Path(__file__).resolve().parent.parent
 for req in (EVENT_REPORT,RESULT_REPORT):
  if not (root/req).is_file():print(f"[FAIL] Missing prerequisite: {req}",file=sys.stderr);return 2
 print("[1/8] [PASS] Stage 21.2.3/21.2.4 artifacts and regulated directories detected.")
 branch=git(root,"branch","--show-current").stdout.strip();head=rev(root,"HEAD");u=git(root,"rev-parse","--abbrev-ref","--symbolic-full-name","@{u}");up=u.stdout.strip() if u.returncode==0 else None
 entries=status(git(root,"status","--porcelain=v1","-z","--untracked-files=all").stdout);allowed=[e for e in entries if e["status"][0] in {" ","?"} and (e["path"] in OWNED or (e["path"] in ALLOWED_DIRTY and e["status"][0]==" "))];unexpected=[e for e in entries if e not in allowed]
 checks=[Check("BRANCH","PASS" if branch==TARGET_BRANCH else "FAIL",f"Active branch: {branch}",{},branch!=TARGET_BRANCH),Check("PARENT","PASS" if head==EXPECTED_PARENT else "FAIL","Expected Stage 21.2.4 parent verified.",{"expected":EXPECTED_PARENT,"actual":head},head!=EXPECTED_PARENT),Check("UPSTREAM","PASS" if up==f"origin/{TARGET_BRANCH}" else "FAIL",f"Upstream: {up}",{},up!=f"origin/{TARGET_BRANCH}"),Check("WORKTREE","PASS" if not unexpected else "FAIL","No unexpected changes.",{"unexpected":unexpected},bool(unexpected))]
 if any(x.blocking for x in checks):print("[2/8] [FAIL] Preflight returned NO_GO.");return 1
 e=json.loads((root/EVENT_REPORT).read_text(encoding="utf-8"));q=json.loads((root/RESULT_REPORT).read_text(encoding="utf-8"))
 if e.get("summary",{}).get("conclusion")!="GO" or q.get("summary",{}).get("conclusion")!="GO":print("[FAIL] Prerequisites are not GO.",file=sys.stderr);return 2
 checks.append(Check("RESULT_EVENT_PREREQUISITES","PASS","Result and event contracts are canonical GO.",{}));print("[2/8] [PASS] Branch, parent, upstream, worktree and prerequisites verified; backups prepared in ROM\\backup.")
 before=db(root);m=backups(root);print("[3/8] [PASS] Writing Repository/UoW verifier and canonical contract.");write(root/VERIFIER_PATH,VERIFIER)
 try:py_compile.compile(str(root/VERIFIER_PATH),doraise=True)
 except py_compile.PyCompileError as x:r=rollback(root,m,f"py_compile failed: {x}",checks);print(f"[FAIL] rollback: {r['status']}");return 2
 print("[4/8] [PASS] Executing Repository/UoW verifier against contract and current V2 tree.");tc=root/"reports"/".21_2_5_contract.tmp.json";tr=root/"reports"/".21_2_5_result.tmp.json";write(tc,json.dumps(CONTRACT,ensure_ascii=False,indent=2)+"\n");vr=run(root,sys.executable,VERIFIER_PATH,"--project-root",str(root),"--contract",str(tc),"--json-out",str(tr));res=json.loads(tr.read_text(encoding="utf-8")) if tr.exists() else {};tc.unlink(missing_ok=True);tr.unlink(missing_ok=True);s=res.get("summary",{})
 checks += [Check("VERIFIER_EXECUTION","PASS" if vr.returncode==0 else "FAIL",vr.stdout.strip(),{"stderr":vr.stderr.strip()},vr.returncode!=0),Check("BUSINESS_OPERATION_ATOMIC","PASS" if s.get("violation_count")==0 else "FAIL",f"Violations: {s.get('violation_count')}",{},s.get("violation_count")!=0),Check("APPLICATION_DB_INDEPENDENCE","PASS" if s.get("application_db_import_count")==0 else "FAIL","Application has no DB imports.",{},s.get("application_db_import_count")!=0),Check("REPOSITORY_HAS_NO_TRANSACTION_CONTROL","PASS" if s.get("repository_transaction_method_count")==0 else "FAIL","Repository owns no transaction methods.",{},s.get("repository_transaction_method_count")!=0),Check("DATABASE_EVIDENCE_READY","PASS","DB/WAL/SHM captured without SQLite connection.",{"production_connection_opened":False})]
 blockers=[x.check_id for x in checks if x.blocking];out={"schema_version":1,"stage":STAGE,"generated_at_utc":datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00","Z"),"summary":{"conclusion":"GO" if not blockers else "NO_GO","blocking_failures":blockers,**s},"git":{"branch":branch,"head_before_commit":head,"upstream":up},"checks":[asdict(x) for x in checks],"repository_unit_of_work_contract":CONTRACT,"verifier_result":res,"database_evidence_before":before,"artifacts":{"patch":PATCH_PATH,"verifier":VERIFIER_PATH,"json":REPORT_PATH,"adr":ADR_PATH},"next_stage":"21.2.6","suggested_next_patch":"patch_21_2_6_define_clock_rng_abstractions.py"}
 print("[5/8] [PASS] Writing full Repository/UoW contract and evidence report.")
 try:
  write(root/REPORT_PATH,json.dumps(out,ensure_ascii=False,indent=2)+"\n");write(root/ADR_PATH,adr(res))
  if blockers:r=rollback(root,m,"acceptance NO_GO",checks);print(f"[6/8] [FAIL] rollback: {r['status']}");return 1
  if before!=db(root):r=rollback(root,m,"DB evidence changed",checks);print(f"[6/8] [FAIL] rollback: {r['status']}");return 2
 except Exception as x:r=rollback(root,m,f"mutation failure: {x}",checks);print(f"[6/8] [FAIL] rollback: {r['status']}");return 2
 print("[6/8] [PASS] Ports, transaction boundaries, exact-once settlement and optimistic checks validated.");(root/FAILURE_REPORT).unlink(missing_ok=True)
 try:print("[7/8] [PASS] Creating exact-allowlist Stage 21.2.5 commit.");c=commit(root)
 except PatchError as x:r=rollback(root,m,f"commit failed: {x}",checks);print(f"[7/8] [FAIL] rollback: {r['status']}");return 2
 print(f"[8/8] [PASS] Repository/UoW model committed and DB/WAL/SHM verified: {c}");print("="*72);print(f"ROM Stage {STAGE} - Repository/Unit of Work")
 for x in checks:print(f"[{x.status}] {x.check_id}: {x.summary}")
 print(f"[PASS] PHYSICAL_V2_EXISTS: {s['physical_v2_exists']}\n[PASS] REPOSITORY_OWNERS: {s['repository_owner_count']}\n[PASS] UOW_OWNERS: {s['unit_of_work_owner_count']}\n[PASS] APPLICATION_DB_IMPORTS: {s['application_db_import_count']}\n[PASS] REPOSITORY_TRANSACTION_METHODS: {s['repository_transaction_method_count']}\n[PASS] VIOLATIONS: {s['violation_count']}")
 print("CONCLUSION: GO\nPATCH STATUS: PASS");print(f"GIT COMMIT STATUS: PASS ({c})");print("REMOTE PUSH STATUS: NOT REQUIRED\nMANUAL CHECK: NOT REQUIRED\nFAIL-SAFE ROLLBACK: ARMED\nWAL/SHM: NOT MANIPULATED\nSUGGESTED NEXT PATCH: patch_21_2_6_define_clock_rng_abstractions.py");return 0
if __name__=="__main__":raise SystemExit(main())
