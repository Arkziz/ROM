#!/usr/bin/env python3
"""Stage 21.2.4: define the canonical ROM V2 domain-event model."""
from __future__ import annotations

import hashlib
import json
import os
import py_compile
import subprocess
import sys
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

STAGE = "21.2.4"
TARGET_BRANCH = "rewrite/rom-v2"
EXPECTED_PARENT = "33e799344221bda43a249463920ff101e3572a44"
RESULT_REPORT = "reports/stage_21_2_3_result_error_model.json"
RESULT_ADR = "MD/ADR_21_2_3_V2_RESULT_ERROR_MODEL.md"
PATCH_PATH = "patch/patch_21_2_4_define_domain_event_model.py"
VERIFIER_PATH = "tools/verify_v2_domain_event_model.py"
REPORT_PATH = "reports/stage_21_2_4_domain_event_model.json"
CONTRACT_PATH = "MD/ADR_21_2_4_V2_DOMAIN_EVENT_MODEL.md"
FAILURE_REPORT = "reports/stage_21_2_4_failure_rollback.json"
COMMIT_MESSAGE = "Stage 21.2.4: define V2 domain event model"
OWNED = {PATCH_PATH, VERIFIER_PATH, REPORT_PATH, CONTRACT_PATH, FAILURE_REPORT}
ALLOWED_DIRTY = {"ROM_FULL_DUMP.txt", "ROM_ADDITIONAL_DUMP.txt"}
DB_FILES = ("game.db", "game.db-wal", "game.db-shm")
BACKUP_PREFIX = "stage_21_2_4"

EVENT_CONTRACT: dict[str, Any] = {
    "schema_version": 1,
    "canonical_owner": "rom_v2.domain.events",
    "physical_owner_stage": "21.3.1_or_later",
    "event_type": {
        "name": "DomainEvent",
        "immutable": True,
        "fields": {
            "event_id": "EventId",
            "event_key": "DomainEventKey",
            "aggregate_type": "AggregateTypeKey",
            "aggregate_id": "AggregateId",
            "aggregate_version": "positive int",
            "sequence": "positive int",
            "occurred_at_utc": "timezone-aware UTC datetime",
            "payload": "typed immutable payload",
            "correlation_id": "CorrelationId | None",
            "causation_id": "EventId | None",
            "schema_version": "positive int",
        },
    },
    "naming": {
        "event_key_format": "lowercase_dot_separated_past_tense",
        "examples_are_non_authoritative": True,
        "stable_machine_key_required": True,
        "localized_text_forbidden": True,
        "renaming_policy": "never rename published key; introduce a new versioned event key",
    },
    "payload": {
        "typed": True,
        "immutable": True,
        "json_serializable_at_persistence_boundary": True,
        "stable_field_names": True,
        "optional_fields_explicit": True,
        "forbidden": [
            "Telegram objects", "buttons or markup", "localized presentation text",
            "database connections", "repository objects", "mutable aggregate references",
            "raw exceptions", "secrets or access tokens",
        ],
    },
    "ordering": {
        "scope": "per aggregate stream",
        "primary_order": ["aggregate_version", "sequence"],
        "event_id_unique": True,
        "aggregate_version_monotonic": True,
        "sequence_monotonic_within_transaction": True,
        "occurred_at_utc_not_an_ordering_authority": True,
        "consumer_deduplication_key": "event_id",
    },
    "persistence": {
        "append_only": True,
        "inside_same_unit_of_work_as_state_change": True,
        "publish_after_commit": True,
        "rollback_discards_uncommitted_events": True,
        "outbox_required_for_external_delivery": True,
        "at_least_once_delivery": True,
        "consumer_idempotency_required": True,
        "restart_reloads_unpublished_outbox": True,
        "retention": "indefinite unless a later ADR defines archive policy",
    },
    "presentation": {
        "owner": "application projection or app delivery adapter",
        "domain_event_contains_presentation": False,
        "telegram_types_forbidden": True,
        "localization_resolves_from_event_key_and_payload": True,
        "presentation_failure_does_not_rollback_committed_domain_state": True,
    },
    "emission": {
        "domain_records_event": True,
        "application_collects_and_persists": True,
        "infrastructure_outbox_publishes": True,
        "app_formats_and_delivers": True,
        "direct_telegram_send_from_domain": False,
        "direct_sql_from_domain": False,
    },
    "error_integration": {
        "result_contract_stage": "21.2.3",
        "failed_operation_persists_events": False,
        "idempotent_repeat_emits_duplicate_event": False,
        "retryable_delivery_error_keeps_outbox_pending": True,
        "consistency_error_blocks_commit": True,
    },
    "forbidden_alternatives": [
        "dict-only event without typed contract", "localized text as event key",
        "timestamp-only ordering", "publish before commit", "best-effort event loss",
        "second production event abstraction", "Telegram presentation in domain payload",
    ],
}

VERIFIER_SOURCE = r'''#!/usr/bin/env python3
"""Verify the ROM V2 domain-event contract without importing runtime code."""
from __future__ import annotations
import argparse, ast, json, re
from pathlib import Path
from typing import Any

REQUIRED_FIELDS = {
    "event_id", "event_key", "aggregate_type", "aggregate_id", "aggregate_version",
    "sequence", "occurred_at_utc", "payload", "correlation_id", "causation_id", "schema_version",
}
EVENT_CLASS_RE = re.compile(r"(?i)^(domainevent|eventenvelope|eventrecord)$")
PRESENTATION_ROOTS = {"aiogram", "telebot", "telegram"}
DATABASE_ROOTS = {"sqlite3", "sqlalchemy", "aiosqlite"}


def verify(root: Path, contract: dict[str, Any]) -> dict[str, Any]:
    violations: list[dict[str, Any]] = []
    fields = set(contract.get("event_type", {}).get("fields", {}))
    if fields != REQUIRED_FIELDS:
        violations.append({"rule": "EVENT_FIELD_SET", "missing": sorted(REQUIRED_FIELDS-fields), "extra": sorted(fields-REQUIRED_FIELDS)})
    if contract.get("canonical_owner") != "rom_v2.domain.events":
        violations.append({"rule": "CANONICAL_OWNER"})
    naming = contract.get("naming", {})
    if naming.get("event_key_format") != "lowercase_dot_separated_past_tense" or not naming.get("localized_text_forbidden"):
        violations.append({"rule": "STABLE_EVENT_NAMING"})
    ordering = contract.get("ordering", {})
    if ordering.get("primary_order") != ["aggregate_version", "sequence"]:
        violations.append({"rule": "EVENT_ORDERING"})
    if not ordering.get("occurred_at_utc_not_an_ordering_authority"):
        violations.append({"rule": "TIMESTAMP_NOT_ORDERING_AUTHORITY"})
    persistence = contract.get("persistence", {})
    for key in ("append_only", "inside_same_unit_of_work_as_state_change", "publish_after_commit", "rollback_discards_uncommitted_events", "outbox_required_for_external_delivery", "consumer_idempotency_required", "restart_reloads_unpublished_outbox"):
        if not persistence.get(key): violations.append({"rule": "PERSISTENCE_INVARIANT", "key": key})
    presentation = contract.get("presentation", {})
    if presentation.get("domain_event_contains_presentation") or not presentation.get("telegram_types_forbidden"):
        violations.append({"rule": "PRESENTATION_SEPARATION"})
    integration = contract.get("error_integration", {})
    if integration.get("failed_operation_persists_events") or integration.get("idempotent_repeat_emits_duplicate_event"):
        violations.append({"rule": "RESULT_EVENT_INTEGRATION"})

    owners: list[dict[str, Any]] = []
    forbidden_imports: list[dict[str, Any]] = []
    rom_v2 = root / "rom_v2"
    if rom_v2.is_dir():
        for path in sorted(rom_v2.rglob("*.py")):
            text = path.read_text(encoding="utf-8", errors="replace")
            try: tree = ast.parse(text, filename=str(path))
            except SyntaxError as exc:
                violations.append({"rule": "PARSE_ERROR", "file": path.relative_to(root).as_posix(), "error": str(exc)}); continue
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef) and EVENT_CLASS_RE.fullmatch(node.name):
                    owners.append({"file": path.relative_to(root).as_posix(), "class": node.name, "line": node.lineno})
                if path.relative_to(root).as_posix().startswith("rom_v2/domain/"):
                    modules=[]
                    if isinstance(node, ast.Import): modules=[a.name for a in node.names]
                    elif isinstance(node, ast.ImportFrom): modules=[node.module or ""]
                    for module in modules:
                        top=module.split(".")[0]
                        if top in PRESENTATION_ROOTS|DATABASE_ROOTS:
                            forbidden_imports.append({"file":path.relative_to(root).as_posix(),"line":node.lineno,"import":module})
    if len(owners)>1: violations.append({"rule":"MULTIPLE_EVENT_OWNERS","owners":owners})
    if owners and owners[0]["file"]!="rom_v2/domain/events.py": violations.append({"rule":"WRONG_EVENT_OWNER","owners":owners})
    if forbidden_imports: violations.append({"rule":"DOMAIN_FRAMEWORK_OR_DB_IMPORT","imports":forbidden_imports})
    return {"schema_version":1,"summary":{"status":"PASS" if not violations else "FAIL","required_field_count":len(fields),"physical_event_owner_count":len(owners),"forbidden_domain_import_count":len(forbidden_imports),"violation_count":len(violations),"physical_event_model_exists":bool(owners)},"event_owners":owners,"forbidden_domain_imports":forbidden_imports,"violations":violations}


def main() -> int:
    p=argparse.ArgumentParser();p.add_argument("--project-root",default=".");p.add_argument("--contract",required=True);p.add_argument("--json-out");a=p.parse_args()
    result=verify(Path(a.project_root).resolve(),json.loads(Path(a.contract).read_text(encoding="utf-8")))
    text=json.dumps(result,ensure_ascii=False,indent=2)+"\n"
    if a.json_out:Path(a.json_out).write_text(text,encoding="utf-8",newline="\n")
    print(f"V2 domain-event verifier: {result['summary']['status']}");print(f"Fields: {result['summary']['required_field_count']}");print(f"Physical event owners: {result['summary']['physical_event_owner_count']}");print(f"Forbidden domain imports: {result['summary']['forbidden_domain_import_count']}");print(f"Violations: {result['summary']['violation_count']}")
    return 0 if result["summary"]["status"]=="PASS" else 1
if __name__=="__main__":raise SystemExit(main())
'''

@dataclass(frozen=True)
class Check:
    check_id:str; status:str; summary:str; details:dict[str,Any]; blocking:bool=False
class PatchError(RuntimeError):pass

def run(root:Path,*cmd:str,timeout:int=120)->subprocess.CompletedProcess[str]:return subprocess.run(cmd,cwd=root,text=True,encoding="utf-8",errors="replace",capture_output=True,timeout=timeout,check=False)
def git(root:Path,*args:str)->subprocess.CompletedProcess[str]:return run(root,"git",*args)
def rev(root:Path,name:str)->str|None:
    r=git(root,"rev-parse","--verify",f"{name}^{{commit}}");return r.stdout.strip() if r.returncode==0 else None

def sha256(path:Path)->str:
    h=hashlib.sha256()
    with path.open("rb") as f:
        for c in iter(lambda:f.read(1048576),b""):h.update(c)
    return h.hexdigest()
def db_evidence(root:Path)->dict[str,Any]:
    out={}
    for n in DB_FILES:
        p=root/n;out[n]={"exists":False} if not p.exists() else {"exists":True,"size":p.stat().st_size,"mtime_ns":p.stat().st_mtime_ns,"sha256":sha256(p)}
    return out
def write_atomic(path:Path,content:str)->None:
    t=path.with_suffix(path.suffix+".tmp");t.parent.mkdir(parents=True,exist_ok=True);t.write_text(content,encoding="utf-8",newline="\n");os.replace(t,path)
def parse_status(raw:str)->list[dict[str,str]]:return [{"status":x[:2],"path":x[3:]} for x in raw.split("\0") if x]
def git_blob(root:Path,commit:str,path:str)->bytes|None:
    r=subprocess.run(["git","show",f"{commit}:{path}"],cwd=root,capture_output=True,check=False);return r.stdout if r.returncode==0 else None

def prepare_backups(root:Path)->dict[str,Any]:
    (root/"backup").mkdir(exist_ok=True);m={"files":{}}
    for rel in (VERIFIER_PATH,REPORT_PATH,CONTRACT_PATH):
        b=git_blob(root,EXPECTED_PARENT,rel);bp=root/"backup"/f"{BACKUP_PREFIX}__{rel.replace('/','__')}"
        if b is None:m["files"][rel]={"existed":False,"backup":None}
        else:bp.write_bytes(b);m["files"][rel]={"existed":True,"backup":str(bp.relative_to(root)).replace("\\","/")}
    return m
def rollback(root:Path,m:dict[str,Any],reason:str,checks:list[Check])->dict[str,Any]:
    git(root,"reset","--",VERIFIER_PATH,REPORT_PATH,CONTRACT_PATH);restored=[];removed=[];errors=[]
    for rel,meta in m["files"].items():
        p=root/rel
        try:
            if meta["existed"]:p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes((root/meta["backup"]).read_bytes());restored.append(rel)
            elif p.exists():p.unlink();removed.append(rel)
        except OSError as e:errors.append(f"{rel}: {e}")
    q={"stage":STAGE,"status":"FAIL_ROLLED_BACK" if not errors else "ROLLBACK_INCOMPLETE","reason":reason,"failed_checks":[asdict(x) for x in checks if x.status=="FAIL"],"restored_files":restored,"removed_failed_artifacts":removed,"rollback_errors":errors,"database_evidence_after_rollback":db_evidence(root),"main_py_started":False,"wal_shm_manipulated":False};write_atomic(root/FAILURE_REPORT,json.dumps(q,ensure_ascii=False,indent=2)+"\n");return q

def render_contract(r:dict[str,Any])->str:
    return "\n".join(["# ADR 21.2.4 — ROM V2 Domain event model","","- **Status:** `ACCEPTED`","- **Canonical owner:** `rom_v2.domain.events`","- **Physical implementation:** reserved for Stage 21.3.1 or later","","## Decision","","Domain events are immutable, typed, stable-key records. Events contain domain facts, not Telegram presentation.","","## Naming and payload","","Event keys use lowercase dot-separated past-tense machine keys. Published keys are never renamed. Payloads are typed, immutable, schema-versioned and presentation-free.","","## Ordering","","Ordering is authoritative per aggregate stream by `aggregate_version` and transaction-local `sequence`. UTC occurrence time is metadata, not ordering authority. Consumers deduplicate by `event_id`.","","## Persistence and delivery","","Events are appended in the same Unit of Work as state changes. External publication occurs after commit through an outbox with at-least-once delivery. Consumers are idempotent. Restart reloads unpublished outbox records.","","## Presentation separation","","Application projections or app delivery adapters localize and format events. Telegram objects, markup and text do not enter domain event payloads.","","## Result integration","","Failed operations persist no events. Idempotent repeats emit no duplicate event. Retryable delivery keeps the outbox pending. Consistency errors block commit.","","## Automated evidence","",f"- Required fields: **{r['summary']['required_field_count']}**.",f"- Violations: **{r['summary']['violation_count']}**.",f"- Physical event model exists: **{r['summary']['physical_event_model_exists']}**.","","## Next roadmap stage","","Stage 21.2.5 — Repository/Unit of Work.",""])

def exact_commit(root:Path)->str:
    paths=[PATCH_PATH,VERIFIER_PATH,REPORT_PATH,CONTRACT_PATH];r=git(root,"add","-f","--",*paths)
    if r.returncode:raise PatchError(r.stderr.strip())
    staged=sorted(x for x in git(root,"diff","--cached","--name-only","-z").stdout.split("\0") if x)
    if staged!=sorted(paths):git(root,"reset","--",*paths);raise PatchError(f"staging mismatch: {staged}")
    r=git(root,"commit","-m",COMMIT_MESSAGE)
    if r.returncode:git(root,"reset","--",*paths);raise PatchError(r.stderr.strip() or r.stdout.strip())
    return rev(root,"HEAD") or ""

def main()->int:
    root=Path(__file__).resolve().parent.parent
    for req in (RESULT_REPORT,RESULT_ADR):
        if not (root/req).is_file():print(f"[FAIL] Missing Stage 21.2.3 artifact: {req}",file=sys.stderr);return 2
    print("[1/8] [PASS] Stage 21.2.3 artifacts and regulated directories detected.")
    branch=git(root,"branch","--show-current").stdout.strip();head=rev(root,"HEAD");u=git(root,"rev-parse","--abbrev-ref","--symbolic-full-name","@{u}");up=u.stdout.strip() if u.returncode==0 else None
    entries=parse_status(git(root,"status","--porcelain=v1","-z","--untracked-files=all").stdout);allowed=[e for e in entries if e["status"][0] in {" ","?"} and (e["path"] in OWNED or (e["path"] in ALLOWED_DIRTY and e["status"][0]==" "))];unexpected=[e for e in entries if e not in allowed]
    checks=[Check("BRANCH","PASS" if branch==TARGET_BRANCH else "FAIL",f"Active branch: {branch}",{},branch!=TARGET_BRANCH),Check("PARENT","PASS" if head==EXPECTED_PARENT else "FAIL","Expected Stage 21.2.3 parent verified.",{"expected":EXPECTED_PARENT,"actual":head},head!=EXPECTED_PARENT),Check("UPSTREAM","PASS" if up==f"origin/{TARGET_BRANCH}" else "FAIL",f"Upstream: {up}",{},up!=f"origin/{TARGET_BRANCH}"),Check("WORKTREE","PASS" if not unexpected else "FAIL","No unexpected changes.",{"unexpected":unexpected},bool(unexpected))]
    if any(x.blocking for x in checks):print("[2/8] [FAIL] Preflight returned NO_GO.");return 1
    prior=json.loads((root/RESULT_REPORT).read_text(encoding="utf-8"))
    if prior.get("stage")!="21.2.3" or prior.get("summary",{}).get("conclusion")!="GO":print("[FAIL] Stage 21.2.3 prerequisite is not canonical GO.",file=sys.stderr);return 2
    checks.append(Check("STAGE_21_2_3_PREREQUISITE","PASS","Result/error contract is canonical GO.",{"report":RESULT_REPORT}))
    print("[2/8] [PASS] Branch, parent, upstream, worktree and Result/error prerequisite verified; backups prepared in ROM\\backup.")
    before=db_evidence(root);manifest=prepare_backups(root)
    print("[3/8] [PASS] Writing domain-event verifier and canonical contract.");write_atomic(root/VERIFIER_PATH,VERIFIER_SOURCE)
    try:py_compile.compile(str(root/VERIFIER_PATH),doraise=True)
    except py_compile.PyCompileError as e:q=rollback(root,manifest,f"py_compile failed: {e}",checks);print(f"[FAIL] rollback: {q['status']}");return 2
    print("[4/8] [PASS] Executing domain-event verifier against contract and current V2 tree.")
    tc=root/"reports"/".stage_21_2_4_contract.tmp.json";tr=root/"reports"/".stage_21_2_4_result.tmp.json";write_atomic(tc,json.dumps(EVENT_CONTRACT,ensure_ascii=False,indent=2)+"\n");vr=run(root,sys.executable,VERIFIER_PATH,"--project-root",str(root),"--contract",str(tc),"--json-out",str(tr));result=json.loads(tr.read_text(encoding="utf-8")) if tr.exists() else {};tc.unlink(missing_ok=True);tr.unlink(missing_ok=True)
    summary=result.get("summary",{});checks += [Check("VERIFIER_EXECUTION","PASS" if vr.returncode==0 else "FAIL",vr.stdout.strip(),{"stderr":vr.stderr.strip()},vr.returncode!=0),Check("SINGLE_TYPED_EVENT_CONTRACT","PASS" if summary.get("violation_count")==0 else "FAIL",f"Violations: {summary.get('violation_count')}",{},summary.get("violation_count")!=0),Check("EVENT_FIELD_SET","PASS" if summary.get("required_field_count")==11 else "FAIL","Eleven mandatory envelope fields defined.",{},summary.get("required_field_count")!=11),Check("NO_TELEGRAM_PRESENTATION","PASS" if summary.get("forbidden_domain_import_count")==0 else "FAIL","No Telegram/DB import in domain event scope.",{},summary.get("forbidden_domain_import_count")!=0),Check("NO_PHYSICAL_DUPLICATE_OWNER","PASS" if summary.get("physical_event_owner_count",0)<=1 else "FAIL","No competing event owner exists.",{},summary.get("physical_event_owner_count",0)>1),Check("DATABASE_EVIDENCE_READY","PASS","DB/WAL/SHM captured without SQLite connection.",{"production_connection_opened":False})]
    blockers=[x.check_id for x in checks if x.blocking];conclusion="GO" if not blockers else "NO_GO"
    payload={"schema_version":1,"stage":STAGE,"generated_at_utc":datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00","Z"),"summary":{"conclusion":conclusion,"blocking_failures":blockers,**summary},"git":{"branch":branch,"head_before_commit":head,"upstream":up},"checks":[asdict(x) for x in checks],"domain_event_contract":EVENT_CONTRACT,"verifier_result":result,"database_evidence_before":before,"artifacts":{"patch":PATCH_PATH,"verifier":VERIFIER_PATH,"json":REPORT_PATH,"adr":CONTRACT_PATH},"next_stage":"21.2.5","suggested_next_patch":"patch_21_2_5_define_repository_unit_of_work.py"}
    print("[5/8] [PASS] Writing full domain-event contract and evidence report.")
    try:
        write_atomic(root/REPORT_PATH,json.dumps(payload,ensure_ascii=False,indent=2)+"\n");write_atomic(root/CONTRACT_PATH,render_contract(result))
        if blockers:q=rollback(root,manifest,"Domain-event acceptance NO_GO",checks);print(f"[6/8] [FAIL] rollback: {q['status']}");return 1
        if before!=db_evidence(root):q=rollback(root,manifest,"DB evidence changed",checks);print(f"[6/8] [FAIL] rollback: {q['status']}");return 2
    except Exception as e:q=rollback(root,manifest,f"mutation failure: {e}",checks);print(f"[6/8] [FAIL] rollback: {q['status']}");return 2
    print("[6/8] [PASS] Naming, payload, ordering, persistence, outbox and presentation separation validated.");(root/FAILURE_REPORT).unlink(missing_ok=True)
    try:print("[7/8] [PASS] Creating exact-allowlist Stage 21.2.4 commit.");commit=exact_commit(root)
    except PatchError as e:q=rollback(root,manifest,f"commit failed: {e}",checks);print(f"[7/8] [FAIL] rollback: {q['status']}");return 2
    print(f"[8/8] [PASS] Domain-event model committed and DB/WAL/SHM verified: {commit}");print("="*72);print(f"ROM Stage {STAGE} - Domain event model")
    for x in checks:print(f"[{x.status}] {x.check_id}: {x.summary}")
    print(f"[PASS] EVENT_FIELDS: {summary['required_field_count']}");print(f"[PASS] PHYSICAL_EVENT_OWNERS: {summary['physical_event_owner_count']}");print(f"[PASS] FORBIDDEN_DOMAIN_IMPORTS: {summary['forbidden_domain_import_count']}");print(f"[PASS] VIOLATIONS: {summary['violation_count']}")
    print("CONCLUSION: GO\nPATCH STATUS: PASS");print(f"GIT COMMIT STATUS: PASS ({commit})");print("REMOTE PUSH STATUS: NOT REQUIRED\nMANUAL CHECK: NOT REQUIRED\nFAIL-SAFE ROLLBACK: ARMED\nWAL/SHM: NOT MANIPULATED\nSUGGESTED NEXT PATCH: patch_21_2_5_define_repository_unit_of_work.py");return 0
if __name__=="__main__":raise SystemExit(main())
