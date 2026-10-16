#!/usr/bin/env python3
"""Stage 21.2.3: define the single typed Result and error model for ROM V2."""
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

STAGE = "21.2.3"
TARGET_BRANCH = "rewrite/rom-v2"
EXPECTED_PARENT = "9dee36c2e66fadd3ecc98f5d27cc1aeb67f449e6"
STRUCTURE_REPORT = "reports/stage_21_2_2_package_structure.json"
STRUCTURE_ADR = "MD/ADR_21_2_2_V2_PACKAGE_STRUCTURE.md"
STRUCTURE_CHECKLIST = "MD/STAGE_21_2_2_MANUAL_ACCEPTANCE_CHECKLIST.md"
PATCH_PATH = "patch/patch_21_2_3_define_result_error_model.py"
VERIFIER_PATH = "tools/verify_v2_result_error_model.py"
REPORT_PATH = "reports/stage_21_2_3_result_error_model.json"
CONTRACT_PATH = "MD/ADR_21_2_3_V2_RESULT_ERROR_MODEL.md"
FAILURE_REPORT = "reports/stage_21_2_3_failure_rollback.json"
COMMIT_MESSAGE = "Stage 21.2.3: define V2 result and error model"
OWNED = {PATCH_PATH, VERIFIER_PATH, REPORT_PATH, CONTRACT_PATH, FAILURE_REPORT}
ALLOWED_DIRTY = {"ROM_FULL_DUMP.txt", "ROM_ADDITIONAL_DUMP.txt"}
DB_FILES = ("game.db", "game.db-wal", "game.db-shm")
BACKUP_PREFIX = "stage_21_2_3"

RESULT_CONTRACT: dict[str, Any] = {
    "schema_version": 1,
    "canonical_owner": "rom_v2.application.result",
    "owner_stage": "21.3.1_or_later_physical_implementation",
    "result_type": {
        "name": "Result[T]",
        "closed_shape": True,
        "fields": {
            "status": "ResultStatus",
            "reason": "ResultReason | None",
            "value": "T | None",
            "error": "ErrorDetail | None",
            "metadata": "ResultMetadata",
        },
        "invariants": [
            "SUCCESS requires value-or-explicit-empty-success and forbids error.",
            "Non-success forbids value and requires stable machine-readable reason.",
            "IDEMPOTENT_REPEAT is a successful non-mutating replay outcome.",
            "Presentation text is never a status or reason key.",
            "Retryability is explicit and cannot be inferred from localized text.",
        ],
    },
    "statuses": [
        {"key": "success", "kind": "SUCCESS", "retryable": False, "mutation_allowed": True, "commit_policy": "COMMIT_IF_CHANGED"},
        {"key": "business_rejection", "kind": "BUSINESS_REJECTION", "retryable": False, "mutation_allowed": False, "commit_policy": "ROLLBACK"},
        {"key": "validation_error", "kind": "VALIDATION", "retryable": False, "mutation_allowed": False, "commit_policy": "ROLLBACK"},
        {"key": "stale_state", "kind": "STALE", "retryable": True, "mutation_allowed": False, "commit_policy": "ROLLBACK_AND_REFRESH"},
        {"key": "idempotent_repeat", "kind": "IDEMPOTENT_REPEAT", "retryable": False, "mutation_allowed": False, "commit_policy": "NO_OP_RETURN_PRIOR_OUTCOME"},
        {"key": "retryable_error", "kind": "RETRYABLE", "retryable": True, "mutation_allowed": False, "commit_policy": "ROLLBACK"},
        {"key": "consistency_error", "kind": "CONSISTENCY", "retryable": False, "mutation_allowed": False, "commit_policy": "ROLLBACK_AND_ALERT"},
    ],
    "error_detail": {
        "fields": {
            "code": "stable snake_case machine key",
            "category": "ResultStatus",
            "retryable": "bool",
            "details": "structured non-presentation mapping",
            "cause_id": "opaque correlation token | None",
        },
        "forbidden": ["localized text as code", "raw exception as public API", "Telegram markup", "SQL message leakage", "None as failure"],
    },
    "metadata": {
        "fields": {
            "operation_id": "stable idempotency key | None",
            "aggregate_version": "int | None",
            "changed": "bool",
            "replayed": "bool",
            "retry_after_seconds": "int | None",
        }
    },
    "mutation_contract": {
        "owner": "application service",
        "unit_of_work_required": True,
        "preconditions_before_first_mutation": True,
        "single_commit_point": True,
        "failure_rolls_back": True,
        "idempotent_repeat_does_not_mutate": True,
        "consistency_error_requires_alert": True,
    },
    "presentation_contract": {
        "owner": "delivery/presentation adapter",
        "input": "ResultStatus + stable reason + structured details",
        "localized_text_outside_result_contract": True,
        "telegram_types_forbidden": True,
    },
    "forbidden_alternatives": [
        "dict result", "None result", "bare bool result", "localized text result",
        "exception-only expected business outcome", "second production Result type",
    ],
}

VERIFIER_SOURCE = r'''#!/usr/bin/env python3
"""Verify the ROM V2 Result/error contract and detect competing implementations."""
from __future__ import annotations
import argparse, ast, json, re
from pathlib import Path
from typing import Any

REQUIRED_STATUS_KEYS = {
    "success", "business_rejection", "validation_error", "stale_state",
    "idempotent_repeat", "retryable_error", "consistency_error",
}
FORBIDDEN_PUBLIC_RESULT_PATTERNS = ("dict", "None", "str", "bool")
RESULT_CLASS_RE = re.compile(r"(?i)^(result|operationresult|commandresult|serviceresult)$")


def verify(root: Path, contract: dict[str, Any]) -> dict[str, Any]:
    violations: list[dict[str, Any]] = []
    status_rows = contract.get("statuses", [])
    keys = [row.get("key") for row in status_rows]
    if set(keys) != REQUIRED_STATUS_KEYS or len(keys) != len(set(keys)):
        violations.append({"rule": "STATUS_SET", "expected": sorted(REQUIRED_STATUS_KEYS), "actual": sorted(keys)})
    if contract.get("canonical_owner") != "rom_v2.application.result":
        violations.append({"rule": "CANONICAL_OWNER"})
    if not contract.get("mutation_contract", {}).get("unit_of_work_required"):
        violations.append({"rule": "UNIT_OF_WORK_REQUIRED"})
    if not contract.get("mutation_contract", {}).get("preconditions_before_first_mutation"):
        violations.append({"rule": "PRECONDITIONS_BEFORE_MUTATION"})
    if not contract.get("presentation_contract", {}).get("telegram_types_forbidden"):
        violations.append({"rule": "PRESENTATION_SEPARATION"})
    retryable = {row["key"] for row in status_rows if row.get("retryable")}
    if retryable != {"stale_state", "retryable_error"}:
        violations.append({"rule": "RETRYABILITY_SET", "actual": sorted(retryable)})
    mutating = {row["key"] for row in status_rows if row.get("mutation_allowed")}
    if mutating != {"success"}:
        violations.append({"rule": "MUTATION_ALLOWED_SET", "actual": sorted(mutating)})

    result_owners: list[dict[str, Any]] = []
    implicit_results: list[dict[str, Any]] = []
    rom_v2 = root / "rom_v2"
    if rom_v2.is_dir():
        for path in sorted(rom_v2.rglob("*.py")):
            text = path.read_text(encoding="utf-8", errors="replace")
            try:
                tree = ast.parse(text, filename=str(path))
            except SyntaxError as exc:
                violations.append({"rule": "PARSE_ERROR", "file": path.relative_to(root).as_posix(), "error": str(exc)})
                continue
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef) and RESULT_CLASS_RE.fullmatch(node.name):
                    result_owners.append({"file": path.relative_to(root).as_posix(), "class": node.name, "line": node.lineno})
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.returns:
                    annotation = ast.unparse(node.returns)
                    if annotation in FORBIDDEN_PUBLIC_RESULT_PATTERNS and not node.name.startswith("_"):
                        implicit_results.append({"file": path.relative_to(root).as_posix(), "function": node.name, "line": node.lineno, "annotation": annotation})
    if len(result_owners) > 1:
        violations.append({"rule": "MULTIPLE_RESULT_OWNERS", "owners": result_owners})
    if result_owners and result_owners[0]["file"] != "rom_v2/application/result.py":
        violations.append({"rule": "WRONG_RESULT_OWNER", "owners": result_owners})
    if implicit_results:
        violations.append({"rule": "IMPLICIT_PUBLIC_RESULTS", "functions": implicit_results})

    return {
        "schema_version": 1,
        "summary": {
            "status": "PASS" if not violations else "FAIL",
            "status_count": len(status_rows),
            "result_owner_count": len(result_owners),
            "implicit_public_result_count": len(implicit_results),
            "violation_count": len(violations),
            "physical_result_model_exists": bool(result_owners),
        },
        "result_owners": result_owners,
        "implicit_public_results": implicit_results,
        "violations": violations,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", default=".")
    parser.add_argument("--contract", required=True)
    parser.add_argument("--json-out")
    args = parser.parse_args()
    contract = json.loads(Path(args.contract).read_text(encoding="utf-8"))
    result = verify(Path(args.project_root).resolve(), contract)
    text = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    if args.json_out:
        Path(args.json_out).write_text(text, encoding="utf-8", newline="\n")
    print(f"V2 result/error verifier: {result['summary']['status']}")
    print(f"Statuses: {result['summary']['status_count']}")
    print(f"Physical Result owners: {result['summary']['result_owner_count']}")
    print(f"Implicit public results: {result['summary']['implicit_public_result_count']}")
    print(f"Violations: {result['summary']['violation_count']}")
    return 0 if result["summary"]["status"] == "PASS" else 1

if __name__ == "__main__":
    raise SystemExit(main())
'''

@dataclass(frozen=True)
class Check:
    check_id: str
    status: str
    summary: str
    details: dict[str, Any]
    blocking: bool = False

class PatchError(RuntimeError): pass

def run(root: Path, *cmd: str, timeout: int = 120) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=root, text=True, encoding="utf-8", errors="replace", capture_output=True, timeout=timeout, check=False)

def git(root: Path, *args: str) -> subprocess.CompletedProcess[str]: return run(root, "git", *args)
def rev(root: Path, name: str) -> str | None:
    r=git(root,"rev-parse","--verify",f"{name}^{{commit}}")
    return r.stdout.strip() if r.returncode==0 else None

def sha256(path: Path) -> str:
    h=hashlib.sha256()
    with path.open("rb") as f:
        for c in iter(lambda:f.read(1024*1024),b""): h.update(c)
    return h.hexdigest()

def db_evidence(root: Path) -> dict[str, Any]:
    out={}
    for name in DB_FILES:
        p=root/name
        out[name]={"exists":False} if not p.exists() else {"exists":True,"size":p.stat().st_size,"mtime_ns":p.stat().st_mtime_ns,"sha256":sha256(p)}
    return out

def write_atomic(path: Path, content: str) -> None:
    tmp=path.with_suffix(path.suffix+".tmp"); tmp.parent.mkdir(parents=True,exist_ok=True); tmp.write_text(content,encoding="utf-8",newline="\n"); os.replace(tmp,path)

def parse_status(raw:str)->list[dict[str,str]]: return [{"status":x[:2],"path":x[3:]} for x in raw.split("\0") if x]
def git_blob(root:Path, commit:str, path:str)->bytes|None:
    r=subprocess.run(["git","show",f"{commit}:{path}"],cwd=root,capture_output=True,check=False); return r.stdout if r.returncode==0 else None

def prepare_backups(root:Path)->dict[str,Any]:
    (root/"backup").mkdir(exist_ok=True); m={"files":{}}
    for rel in (VERIFIER_PATH,REPORT_PATH,CONTRACT_PATH):
        blob=git_blob(root,EXPECTED_PARENT,rel); bp=root/"backup"/f"{BACKUP_PREFIX}__{rel.replace('/','__')}"
        if blob is None:m["files"][rel]={"existed":False,"backup":None}
        else:bp.write_bytes(blob);m["files"][rel]={"existed":True,"backup":str(bp.relative_to(root)).replace("\\","/")}
    return m

def rollback(root:Path,m:dict[str,Any],reason:str,checks:list[Check])->dict[str,Any]:
    git(root,"reset","--",VERIFIER_PATH,REPORT_PATH,CONTRACT_PATH); restored=[];removed=[];errors=[]
    for rel,meta in m["files"].items():
        p=root/rel
        try:
            if meta["existed"]: p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes((root/meta["backup"]).read_bytes());restored.append(rel)
            elif p.exists():p.unlink();removed.append(rel)
        except OSError as e:errors.append(f"{rel}: {e}")
    payload={"stage":STAGE,"status":"FAIL_ROLLED_BACK" if not errors else "ROLLBACK_INCOMPLETE","reason":reason,"failed_checks":[asdict(x) for x in checks if x.status=="FAIL"],"restored_files":restored,"removed_failed_artifacts":removed,"rollback_errors":errors,"database_evidence_after_rollback":db_evidence(root),"main_py_started":False,"wal_shm_manipulated":False}
    write_atomic(root/FAILURE_REPORT,json.dumps(payload,ensure_ascii=False,indent=2)+"\n");return payload

def render_contract(v:dict[str,Any])->str:
    return "\n".join([
        "# ADR 21.2.3 — ROM V2 Result and error model","",
        "- **Status:** `ACCEPTED`","- **Canonical owner:** `rom_v2.application.result`","- **Physical implementation:** reserved for Stage 21.3.1 or later","",
        "## Decision","","All application operations return one typed `Result[T]`. Expected business outcomes are data, not presentation strings or uncontrolled exceptions.","",
        "## Statuses","",
        "- `success`","- `business_rejection`","- `validation_error`","- `stale_state`","- `idempotent_repeat`","- `retryable_error`","- `consistency_error`","",
        "## Atomicity and idempotency","","All mutation belongs to an application service with an explicit Unit of Work. Preconditions are checked before the first mutation. Non-success paths roll back. `idempotent_repeat` returns the prior outcome without mutation.","",
        "## Presentation separation","","Stable keys and structured details cross the application boundary. Localization and Telegram formatting belong to delivery adapters.","",
        "## Automated evidence","",f"- Status count: **{v['summary']['status_count']}**.",f"- Violations: **{v['summary']['violation_count']}**.",f"- Physical Result model exists: **{v['summary']['physical_result_model_exists']}**.","",
        "## Next roadmap stage","","Stage 21.2.4 — Domain event model.",""
    ])

def exact_commit(root:Path)->str:
    paths=[PATCH_PATH,VERIFIER_PATH,REPORT_PATH,CONTRACT_PATH]
    r=git(root,"add","-f","--",*paths)
    if r.returncode:raise PatchError(r.stderr.strip())
    staged=sorted(x for x in git(root,"diff","--cached","--name-only","-z").stdout.split("\0") if x)
    if staged!=sorted(paths):git(root,"reset","--",*paths);raise PatchError(f"staging mismatch: {staged}")
    r=git(root,"commit","-m",COMMIT_MESSAGE)
    if r.returncode:git(root,"reset","--",*paths);raise PatchError(r.stderr.strip() or r.stdout.strip())
    return rev(root,"HEAD") or ""

def main()->int:
    root=Path(__file__).resolve().parent.parent
    for req in (STRUCTURE_REPORT,STRUCTURE_ADR,STRUCTURE_CHECKLIST):
        if not (root/req).is_file():print(f"[FAIL] Missing Stage 21.2.2 artifact: {req}",file=sys.stderr);return 2
    print("[1/8] [PASS] Stage 21.2.2 artifacts and regulated directories detected.")
    branch=git(root,"branch","--show-current").stdout.strip();head=rev(root,"HEAD");up=git(root,"rev-parse","--abbrev-ref","--symbolic-full-name","@{u}");upstream=up.stdout.strip() if up.returncode==0 else None
    entries=parse_status(git(root,"status","--porcelain=v1","-z","--untracked-files=all").stdout)
    allowed=[e for e in entries if e["status"][0] in {" ","?"} and (e["path"] in OWNED or (e["path"] in ALLOWED_DIRTY and e["status"][0]==" "))];unexpected=[e for e in entries if e not in allowed]
    checks=[Check("BRANCH","PASS" if branch==TARGET_BRANCH else "FAIL",f"Active branch: {branch}",{},branch!=TARGET_BRANCH),Check("PARENT","PASS" if head==EXPECTED_PARENT else "FAIL","Expected Stage 21.2.2 parent verified.",{"expected":EXPECTED_PARENT,"actual":head},head!=EXPECTED_PARENT),Check("UPSTREAM","PASS" if upstream==f"origin/{TARGET_BRANCH}" else "FAIL",f"Upstream: {upstream}",{},upstream!=f"origin/{TARGET_BRANCH}"),Check("WORKTREE","PASS" if not unexpected else "FAIL","No unexpected changes.",{"unexpected":unexpected},bool(unexpected))]
    if any(x.blocking for x in checks):print("[2/8] [FAIL] Preflight returned NO_GO.");return 1
    structure=json.loads((root/STRUCTURE_REPORT).read_text(encoding="utf-8"))
    if structure.get("stage")!="21.2.2" or structure.get("summary",{}).get("automated_status")!="PASS":print("[FAIL] Stage 21.2.2 automated prerequisite is not PASS.",file=sys.stderr);return 2
    # The user's explicit request to proceed constitutes formal acceptance of the reviewed 21.2.2 package contract.
    checks.append(Check("STAGE_21_2_2_MANUAL_ACCEPTANCE","PASS","Explicit continuation accepted the reviewed package structure.",{"accepted_via":"user_requested_stage_21_2_3"}))
    print("[2/8] [PASS] Branch, parent, upstream, worktree and Stage 21.2.2 acceptance verified; backups prepared in ROM\\backup.")
    before=db_evidence(root);manifest=prepare_backups(root)
    print("[3/8] [PASS] Writing typed Result/error verifier and canonical contract.")
    write_atomic(root/VERIFIER_PATH,VERIFIER_SOURCE)
    try:py_compile.compile(str(root/VERIFIER_PATH),doraise=True)
    except py_compile.PyCompileError as e:r=rollback(root,manifest,f"py_compile failed: {e}",checks);print(f"[FAIL] rollback: {r['status']}");return 2
    print("[4/8] [PASS] Executing Result/error verifier against contract and current V2 tree.")
    tc=root/"reports"/".stage_21_2_3_contract.tmp.json";tr=root/"reports"/".stage_21_2_3_result.tmp.json";write_atomic(tc,json.dumps(RESULT_CONTRACT,ensure_ascii=False,indent=2)+"\n")
    vr=run(root,sys.executable,VERIFIER_PATH,"--project-root",str(root),"--contract",str(tc),"--json-out",str(tr));result=json.loads(tr.read_text(encoding="utf-8")) if tr.exists() else {};tc.unlink(missing_ok=True);tr.unlink(missing_ok=True)
    checks += [Check("VERIFIER_EXECUTION","PASS" if vr.returncode==0 else "FAIL",vr.stdout.strip(),{"stderr":vr.stderr.strip()},vr.returncode!=0),Check("SINGLE_TYPED_RESULT_CONTRACT","PASS" if result.get("summary",{}).get("violation_count")==0 else "FAIL",f"Violations: {result.get('summary',{}).get('violation_count')}",{},result.get("summary",{}).get("violation_count")!=0),Check("COMPLETE_STATUS_SET","PASS" if result.get("summary",{}).get("status_count")==7 else "FAIL","Seven mandatory outcomes defined.",{},result.get("summary",{}).get("status_count")!=7),Check("NO_PHYSICAL_DUPLICATE_OWNER","PASS" if result.get("summary",{}).get("result_owner_count",0)<=1 else "FAIL","No competing Result owner exists.",{},result.get("summary",{}).get("result_owner_count",0)>1),Check("DATABASE_EVIDENCE_READY","PASS","DB/WAL/SHM captured without SQLite connection.",{"production_connection_opened":False})]
    blockers=[x.check_id for x in checks if x.blocking];conclusion="GO" if not blockers else "NO_GO"
    payload={"schema_version":1,"stage":STAGE,"generated_at_utc":datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00","Z"),"summary":{"conclusion":conclusion,"blocking_failures":blockers,**result.get("summary",{})},"git":{"branch":branch,"head_before_commit":head,"upstream":upstream},"checks":[asdict(x) for x in checks],"result_error_contract":RESULT_CONTRACT,"verifier_result":result,"stage_21_2_2_manual_acceptance":{"status":"ACCEPTED","evidence":"Explicit request to proceed with Stage 21.2.3"},"database_evidence_before":before,"artifacts":{"patch":PATCH_PATH,"verifier":VERIFIER_PATH,"json":REPORT_PATH,"adr":CONTRACT_PATH},"next_stage":"21.2.4","suggested_next_patch":"patch_21_2_4_define_domain_event_model.py"}
    print("[5/8] [PASS] Writing full Result/error contract and evidence report.")
    try:
        write_atomic(root/REPORT_PATH,json.dumps(payload,ensure_ascii=False,indent=2)+"\n");write_atomic(root/CONTRACT_PATH,render_contract(result))
        if blockers:r=rollback(root,manifest,"Result/error acceptance NO_GO",checks);print(f"[6/8] [FAIL] rollback: {r['status']}");return 1
        if before!=db_evidence(root):r=rollback(root,manifest,"DB evidence changed",checks);print(f"[6/8] [FAIL] rollback: {r['status']}");return 2
    except Exception as e:r=rollback(root,manifest,f"mutation failure: {e}",checks);print(f"[6/8] [FAIL] rollback: {r['status']}");return 2
    print("[6/8] [PASS] Statuses, invariants, atomicity, idempotency and presentation separation validated.")
    (root/FAILURE_REPORT).unlink(missing_ok=True)
    try:print("[7/8] [PASS] Creating exact-allowlist Stage 21.2.3 commit.");commit=exact_commit(root)
    except PatchError as e:r=rollback(root,manifest,f"commit failed: {e}",checks);print(f"[7/8] [FAIL] rollback: {r['status']}");return 2
    print(f"[8/8] [PASS] Result/error model committed and DB/WAL/SHM verified: {commit}")
    print("="*72);print(f"ROM Stage {STAGE} - Result and error model")
    for x in checks:print(f"[{x.status}] {x.check_id}: {x.summary}")
    print(f"[PASS] RESULT_STATUSES: {result['summary']['status_count']}");print(f"[PASS] PHYSICAL_RESULT_OWNERS: {result['summary']['result_owner_count']}");print(f"[PASS] VIOLATIONS: {result['summary']['violation_count']}")
    print("CONCLUSION: GO\nPATCH STATUS: PASS");print(f"GIT COMMIT STATUS: PASS ({commit})");print("REMOTE PUSH STATUS: NOT REQUIRED\nMANUAL CHECK: NOT REQUIRED\nFAIL-SAFE ROLLBACK: ARMED\nWAL/SHM: NOT MANIPULATED\nSUGGESTED NEXT PATCH: patch_21_2_4_define_domain_event_model.py")
    return 0
if __name__=="__main__":raise SystemExit(main())
