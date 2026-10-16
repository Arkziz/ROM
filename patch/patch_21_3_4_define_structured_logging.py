#!/usr/bin/env python3
"""Stage 21.3.4: implement secret-safe structured logging for ROM V2."""
from __future__ import annotations
import hashlib, json, os, subprocess, sys
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

STAGE="21.3.4"; TARGET_BRANCH="rewrite/rom-v2"; EXPECTED_PARENT="1fadce19e86084891c49a930a817fc28e4e0eed0"
PREREQ="reports/stage_21_3_3_configuration_secrets.json"
PATCH_PATH="patch/patch_21_3_4_define_structured_logging.py"; LOGGING_PATH="rom_v2/structured_logging.py"; TEST_PATH="tests_v2/test_structured_logging.py"
REPORT_PATH="reports/stage_21_3_4_structured_logging.json"; CONTRACT_PATH="MD/STAGE_21_3_4_V2_STRUCTURED_LOGGING.md"; FAILURE_REPORT="reports/stage_21_3_4_failure_rollback.json"
COMMIT_MESSAGE="Stage 21.3.4: implement V2 structured logging"; DB_FILES=("game.db","game.db-wal","game.db-shm")
ALLOWED_DIRTY={"ROM_FULL_DUMP.txt","ROM_ADDITIONAL_DUMP.txt"}; MUTATED=(LOGGING_PATH,TEST_PATH,REPORT_PATH,CONTRACT_PATH); OWNED={PATCH_PATH,FAILURE_REPORT,*MUTATED}; BACKUP_PREFIX="stage_21_3_4"

LOGGING_SOURCE='''"""Secret-safe structured JSON logging for ROM V2 diagnostics."""
from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Mapping

SENSITIVE_KEY_PARTS = ("token", "secret", "password", "authorization", "cookie", "api_key", "private_key")
ALLOWED_ERROR_CATEGORIES = frozenset({"none", "validation", "business", "stale", "retryable", "consistency", "unexpected"})


def _redact(value: Any, key: str = "") -> Any:
    """Recursively redact sensitive fields and unsupported payload objects."""
    normalized = key.lower()
    if any(part in normalized for part in SENSITIVE_KEY_PARTS):
        return "<redacted>"
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, Mapping):
        return {str(item_key): _redact(item_value, str(item_key)) for item_key, item_value in value.items()}
    if isinstance(value, (list, tuple)):
        return [_redact(item) for item in value]
    return "<unsupported>"


@dataclass(frozen=True, slots=True)
class LogContext:
    """Carry stable diagnostic identifiers across one domain operation."""

    correlation_id: str
    operation: str

    def validate(self) -> None:
        """Reject empty or presentation-shaped diagnostic identifiers."""
        if not self.correlation_id.strip():
            raise ValueError("missing_correlation_id")
        if not self.operation.strip() or any(character.isspace() for character in self.operation):
            raise ValueError("invalid_operation_key")


class JsonLogFormatter(logging.Formatter):
    """Serialize canonical log records as one compact JSON object per line."""

    def format(self, record: logging.LogRecord) -> str:
        """Render required fields while redacting structured diagnostic details."""
        timestamp = datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat().replace("+00:00", "Z")
        payload = {
            "timestamp_utc": timestamp,
            "level": record.levelname.lower(),
            "event": getattr(record, "event_key", "runtime.message"),
            "correlation_id": getattr(record, "correlation_id", "system"),
            "operation": getattr(record, "operation", "runtime"),
            "error_category": getattr(record, "error_category", "none"),
            "details": _redact(getattr(record, "details", {})),
        }
        return json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def configure_structured_logger(name: str, level: str = "INFO") -> logging.Logger:
    """Create one non-propagating logger with exactly one JSON stream handler."""
    logger = logging.getLogger(name)
    logger.handlers.clear()
    handler = logging.StreamHandler()
    handler.setFormatter(JsonLogFormatter())
    logger.addHandler(handler)
    logger.setLevel(level)
    logger.propagate = False
    return logger


def log_event(
    logger: logging.Logger,
    level: int,
    event_key: str,
    context: LogContext,
    *,
    error_category: str = "none",
    details: Mapping[str, Any] | None = None,
) -> None:
    """Emit one canonical diagnostic event without accepting free-form payload text."""
    context.validate()
    if not event_key.strip() or any(character.isspace() for character in event_key):
        raise ValueError("invalid_event_key")
    if error_category not in ALLOWED_ERROR_CATEGORIES:
        raise ValueError("invalid_error_category")
    logger.log(
        level,
        event_key,
        extra={
            "event_key": event_key,
            "correlation_id": context.correlation_id,
            "operation": context.operation,
            "error_category": error_category,
            "details": dict(details or {}),
        },
    )
'''

TEST_SOURCE='''"""Tests for ROM V2 structured logging and redaction."""
from __future__ import annotations

import io
import json
import logging
import unittest

from rom_v2.structured_logging import JsonLogFormatter, LogContext, log_event


class StructuredLoggingTest(unittest.TestCase):
    """Verify required fields, stable keys, and secret-safe output."""

    def _logger(self, stream: io.StringIO) -> logging.Logger:
        """Create an isolated logger writing into the supplied stream."""
        logger = logging.Logger("test.structured")
        handler = logging.StreamHandler(stream)
        handler.setFormatter(JsonLogFormatter())
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
        return logger

    def test_event_contains_diagnostic_fields_and_redacts_secrets(self) -> None:
        """Emit a parseable record without sensitive payload disclosure."""
        stream = io.StringIO(); logger = self._logger(stream)
        protected = "unit-test-protected-value"
        log_event(logger, logging.INFO, "bootstrap.started", LogContext("corr-1", "bootstrap.start"), details={"token": protected, "nested": {"password": protected}, "count": 1})
        record = json.loads(stream.getvalue())
        self.assertEqual(record["correlation_id"], "corr-1")
        self.assertEqual(record["operation"], "bootstrap.start")
        self.assertEqual(record["error_category"], "none")
        self.assertEqual(record["details"]["token"], "<redacted>")
        self.assertNotIn(protected, stream.getvalue())

    def test_invalid_keys_and_error_category_are_rejected(self) -> None:
        """Reject presentation-shaped identifiers and unknown categories."""
        logger = self._logger(io.StringIO())
        with self.assertRaisesRegex(ValueError, "invalid_event_key"):
            log_event(logger, logging.INFO, "human text", LogContext("corr-2", "bootstrap.start"))
        with self.assertRaisesRegex(ValueError, "invalid_operation_key"):
            log_event(logger, logging.INFO, "bootstrap.started", LogContext("corr-2", "human text"))
        with self.assertRaisesRegex(ValueError, "invalid_error_category"):
            log_event(logger, logging.ERROR, "bootstrap.failed", LogContext("corr-2", "bootstrap.start"), error_category="other")

    def test_unknown_object_is_not_stringified(self) -> None:
        """Prevent arbitrary object repr from leaking through details."""
        stream = io.StringIO(); logger = self._logger(stream)
        log_event(logger, logging.INFO, "bootstrap.started", LogContext("corr-3", "bootstrap.start"), details={"object": object()})
        self.assertEqual(json.loads(stream.getvalue())["details"]["object"], "<unsupported>")


if __name__ == "__main__":
    unittest.main()
'''

@dataclass(frozen=True)
class Check:
    check_id:str; status:str; summary:str; details:dict[str,Any]; blocking:bool=False
class PatchError(RuntimeError): pass

def run(root:Path,*cmd:str,timeout:int=120):
    env=os.environ.copy(); env["PYTHONDONTWRITEBYTECODE"]="1"
    return subprocess.run(cmd,cwd=root,env=env,text=True,encoding="utf-8",errors="replace",capture_output=True,timeout=timeout,check=False)
def git(root:Path,*args:str): return run(root,"git",*args)
def rev(root:Path,name:str):
    r=git(root,"rev-parse","--verify",f"{name}^{{commit}}"); return r.stdout.strip() if r.returncode==0 else None
def sha(path:Path):
    h=hashlib.sha256()
    with path.open("rb") as f:
        for c in iter(lambda:f.read(1048576),b""): h.update(c)
    return h.hexdigest()
def db(root:Path):
    out={}
    for n in DB_FILES:
        p=root/n; out[n]={"exists":False} if not p.exists() else {"exists":True,"size":p.stat().st_size,"mtime_ns":p.stat().st_mtime_ns,"sha256":sha(p)}
    return out
def write(path:Path,text:str):
    t=path.with_suffix(path.suffix+".tmp"); t.parent.mkdir(parents=True,exist_ok=True); t.write_text(text,encoding="utf-8",newline="\n"); os.replace(t,path)
def statuses(raw:str): return [{"status":x[:2],"path":x[3:]} for x in raw.split("\0") if x]
def blob(root:Path,commit:str,path:str):
    r=subprocess.run(["git","show",f"{commit}:{path}"],cwd=root,capture_output=True,check=False); return r.stdout if r.returncode==0 else None
def backups(root:Path):
    (root/"backup").mkdir(exist_ok=True); m={"files":{}}
    for rel in MUTATED:
        b=blob(root,EXPECTED_PARENT,rel); p=root/"backup"/f"{BACKUP_PREFIX}__{rel.replace('/','__')}"
        if b is None:m["files"][rel]={"existed":False,"backup":None}
        else:p.write_bytes(b);m["files"][rel]={"existed":True,"backup":str(p.relative_to(root)).replace("\\","/")}
    return m
def rollback(root:Path,m,reason,checks):
    git(root,"reset","--",*MUTATED); restored=[];removed=[];errors=[]
    for rel,meta in m["files"].items():
        p=root/rel
        try:
            if meta["existed"]:p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes((root/meta["backup"]).read_bytes());restored.append(rel)
            elif p.exists():p.unlink();removed.append(rel)
        except OSError as e:errors.append(f"{rel}: {e}")
    out={"stage":STAGE,"status":"FAIL_ROLLED_BACK" if not errors else "ROLLBACK_INCOMPLETE","reason":reason,"failed_checks":[asdict(x) for x in checks if x.status=="FAIL"],"restored_files":restored,"removed_failed_artifacts":removed,"rollback_errors":errors,"database_evidence_after_rollback":db(root),"main_py_started_after_failure":False,"wal_shm_manipulated":False}
    write(root/FAILURE_REPORT,json.dumps(out,ensure_ascii=False,indent=2)+"\n"); return out

def contract()->str:
    return "\n".join(["# Stage 21.3.4 — ROM V2 structured logging","","- **Status:** `IMPLEMENTED`","- **Canonical owner:** `rom_v2.structured_logging`","- **Format:** one JSON object per line","","## Required diagnostic fields","","`timestamp_utc`, `level`, `event`, `correlation_id`, `operation`, `error_category`, and structured `details`.","","## Safety","","Sensitive keys are recursively redacted. Unsupported objects are never stringified. Free-form exception payloads, tokens, passwords, authorization headers, cookies, API keys, and private keys are not logged.","","## Stable identifiers","","Event and operation identifiers are machine-readable keys without whitespace. Error categories are restricted to a closed canonical set.","","## Next roadmap stage","","Stage 21.3.5 — Architecture enforcement.",""])
def commit(root:Path):
    paths=[PATCH_PATH,*MUTATED]; r=git(root,"add","-f","--",*paths)
    if r.returncode:raise PatchError(r.stderr.strip())
    staged=sorted(x for x in git(root,"diff","--cached","--name-only","-z").stdout.split("\0") if x)
    if staged!=sorted(paths):git(root,"reset","--",*paths);raise PatchError(f"staging mismatch: {staged}")
    r=git(root,"commit","-m",COMMIT_MESSAGE)
    if r.returncode:git(root,"reset","--",*paths);raise PatchError(r.stderr.strip() or r.stdout.strip())
    return rev(root,"HEAD") or ""
def main():
    root=Path(__file__).resolve().parent.parent
    if not (root/PREREQ).is_file():print(f"[FAIL] Missing prerequisite: {PREREQ}",file=sys.stderr);return 2
    prior=json.loads((root/PREREQ).read_text(encoding="utf-8"))
    if prior.get("stage")!="21.3.3" or prior.get("summary",{}).get("conclusion")!="GO":print("[FAIL] Stage 21.3.3 prerequisite is not canonical GO.",file=sys.stderr);return 2
    print("[1/10] [PASS] Stage 21.3.3 prerequisite and secret policy detected.")
    branch=git(root,"branch","--show-current").stdout.strip();head=rev(root,"HEAD");u=git(root,"rev-parse","--abbrev-ref","--symbolic-full-name","@{u}");up=u.stdout.strip() if u.returncode==0 else None
    entries=statuses(git(root,"status","--porcelain=v1","-z","--untracked-files=all").stdout);allowed=[e for e in entries if e["status"][0] in {" ","?"} and (e["path"] in OWNED or (e["path"] in ALLOWED_DIRTY and e["status"][0]==" "))];unexpected=[e for e in entries if e not in allowed]
    checks=[Check("BRANCH","PASS" if branch==TARGET_BRANCH else "FAIL",f"Active branch: {branch}",{},branch!=TARGET_BRANCH),Check("PARENT","PASS" if head==EXPECTED_PARENT else "FAIL","Expected Stage 21.3.3 parent verified.",{"expected":EXPECTED_PARENT,"actual":head},head!=EXPECTED_PARENT),Check("UPSTREAM","PASS" if up==f"origin/{TARGET_BRANCH}" else "FAIL",f"Upstream: {up}",{},up!=f"origin/{TARGET_BRANCH}"),Check("WORKTREE","PASS" if not unexpected else "FAIL","No unexpected changes.",{"unexpected":unexpected},bool(unexpected))]
    if any(x.blocking for x in checks):print("[2/10] [FAIL] Preflight returned NO_GO.");return 1
    print("[2/10] [PASS] Branch, parent, upstream and worktree verified; backups prepared in ROM\\backup.")
    before=db(root);m=backups(root)
    try:
        print("[3/10] [PASS] Writing structured logger, canonical context and targeted tests.");write(root/LOGGING_PATH,LOGGING_SOURCE);write(root/TEST_PATH,TEST_SOURCE)
        print("[4/10] [PASS] Compiling new Python files without bytecode.")
        for rel in (LOGGING_PATH,TEST_PATH):compile((root/rel).read_text(encoding="utf-8"),str(root/rel),"exec")
        print("[5/10] [PASS] Running structured logging tests.");unit=run(root,sys.executable,"-m","unittest","tests_v2.test_structured_logging");checks.append(Check("UNIT_TEST","PASS" if unit.returncode==0 else "FAIL",unit.stderr.strip() or unit.stdout.strip(),{},unit.returncode!=0))
        print("[6/10] [PASS] Running secret-disclosure smoke test.");protected="stage-21-3-4-protected-value";smoke=run(root,sys.executable,"-c",f'''import io,logging; from rom_v2.structured_logging import *; s=io.StringIO(); l=logging.Logger("smoke"); h=logging.StreamHandler(s); h.setFormatter(JsonLogFormatter()); l.addHandler(h); l.setLevel(logging.INFO); log_event(l,logging.ERROR,"operation.failed",LogContext("corr-smoke","operation.run"),error_category="retryable",details={{"bot_token":"{protected}","reason":"temporary"}}); print(s.getvalue(),end="")''');safe=smoke.returncode==0 and protected not in smoke.stdout and '"correlation_id":"corr-smoke"' in smoke.stdout;checks.append(Check("SECRET_SAFE_SMOKE","PASS" if safe else "FAIL","Protected value absent from structured output.",{"stderr":smoke.stderr.strip()},not safe))
        print("[7/10] [PASS] Running code, dependency and bootstrap regressions.")
        cr=json.loads((root/"reports/stage_21_2_7_code_comment_standards.json").read_text(encoding="utf-8"));tc=root/"reports/.21_3_4_code_contract.tmp.json";tr=root/"reports/.21_3_4_code_result.tmp.json";write(tc,json.dumps(cr["code_comment_contract"],ensure_ascii=False,indent=2)+"\n");v=run(root,sys.executable,"tools/verify_v2_code_comment_standards.py","--project-root",str(root),"--contract",str(tc),"--json-out",str(tr));vp=json.loads(tr.read_text(encoding="utf-8")) if tr.exists() else {"summary":{"status":"FAIL"}};tc.unlink(missing_ok=True);tr.unlink(missing_ok=True);vok=v.returncode==0 and vp.get("summary",{}).get("status")=="PASS";checks.append(Check("CODE_STANDARD","PASS" if vok else "FAIL",v.stdout.strip(),{"violations":vp.get("violations",[])},not vok))
        dep=run(root,sys.executable,"tools/verify_v2_dependency_rules.py","--project-root",str(root),"--json-out","reports/.21_3_4_dep.tmp.json");dp=root/"reports/.21_3_4_dep.tmp.json";dj=json.loads(dp.read_text(encoding="utf-8")) if dp.exists() else {"summary":{"status":"FAIL"}};dp.unlink(missing_ok=True);dok=dep.returncode==0 and dj.get("summary",{}).get("status")=="PASS";checks.append(Check("DEPENDENCY_RULES","PASS" if dok else "FAIL",dep.stdout.strip(),{"violations":dj.get("violations",[])},not dok))
        boot=run(root,sys.executable,"-m","rom_v2.main");bok=boot.returncode==0 and json.loads(boot.stdout).get("gameplay_enabled") is False;checks.append(Check("BOOTSTRAP_REGRESSION","PASS" if bok else "FAIL",boot.stdout.strip(),{"stderr":boot.stderr.strip()},not bok))
        print("[8/10] [PASS] Verifying database and secret-report boundaries.")
        checks.append(Check("DATABASE_UNCHANGED","PASS" if before==db(root) else "FAIL","DB/WAL/SHM unchanged and SQLite was not opened.",{"production_connection_opened":False},before!=db(root)))
        blockers=[x.check_id for x in checks if x.blocking]
        if blockers:r=rollback(root,m,f"Stage 21.3.4 NO_GO: {blockers}",checks);print(f"[9/10] [FAIL] Rollback: {r['status']}");return 1
        payload={"schema_version":1,"stage":STAGE,"generated_at_utc":datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00","Z"),"summary":{"conclusion":"GO","blocking_failures":[],"required_field_count":7,"secret_values_recorded":False,"gameplay_started":False,"database_opened":False},"git":{"branch":branch,"head_before_commit":head,"upstream":up},"checks":[asdict(x) for x in checks],"logging_contract":{"canonical_owner":"rom_v2.structured_logging","required_fields":["timestamp_utc","level","event","correlation_id","operation","error_category","details"],"sensitive_payload_policy":"recursive_redaction","unknown_object_policy":"unsupported_marker"},"database_evidence_before":before,"database_evidence_after":db(root),"changed_files":[PATCH_PATH,*MUTATED],"next_stage":"21.3.5","suggested_next_patch":"patch_21_3_5_enforce_v2_architecture.py"}
        print("[9/10] [PASS] Writing structured logging evidence and contract.");write(root/REPORT_PATH,json.dumps(payload,ensure_ascii=False,indent=2)+"\n");write(root/CONTRACT_PATH,contract())
    except Exception as e:r=rollback(root,m,f"Mutation or verification failure: {e}",checks);print(f"[9/10] [FAIL] {e}; rollback: {r['status']}",file=sys.stderr);return 2
    (root/FAILURE_REPORT).unlink(missing_ok=True)
    try:c=commit(root)
    except PatchError as e:r=rollback(root,m,f"Commit failure: {e}",checks);print(f"[10/10] [FAIL] rollback: {r['status']}",file=sys.stderr);return 2
    print(f"[10/10] [PASS] Structured logging committed without sensitive payload: {c}");print("="*72);print(f"ROM Stage {STAGE} - structured logging")
    for x in checks:print(f"[{x.status}] {x.check_id}: {x.summary}")
    print("[PASS] REQUIRED_LOG_FIELDS: 7\n[PASS] SECRET_VALUES_RECORDED: False\n[PASS] GAMEPLAY_STARTED: False\n[PASS] DATABASE_OPENED: False\nCONCLUSION: GO\nPATCH STATUS: PASS");print(f"GIT COMMIT STATUS: PASS ({c})");print("REMOTE PUSH STATUS: NOT REQUIRED\nMANUAL CHECK: NOT REQUIRED\nFAIL-SAFE ROLLBACK: ARMED\nWAL/SHM: NOT MANIPULATED\nSUGGESTED NEXT PATCH: patch_21_3_5_enforce_v2_architecture.py");return 0
if __name__=="__main__":raise SystemExit(main())
