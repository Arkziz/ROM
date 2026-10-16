#!/usr/bin/env python3
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
