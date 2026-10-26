#!/usr/bin/env python3
"""Verify immutable Stage 21.14.2b parity-resolution artifacts."""
import hashlib, json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
REPORT=ROOT/'reports/stage_21_14_2b_event_schedules_rewards_parity.json'
data=json.loads(REPORT.read_text(encoding="utf-8"))
assert (ROOT/'MD/STAGE_21_14_2B_EVENT_SCHEDULES_REWARDS_PARITY.md').is_file()
assert data["stage"]=="21.14.2b"
assert data["mode"]=="EVIDENCE_ONLY_PARITY_RESOLUTION"
assert data["preflight"]["starting_head"]=='af3828a6bef2d619a076968cdb7ca28f7e2d78e0'
for key in ("audit_report","refinement_report"):
    path=ROOT/data["preflight"][key]
    digest=hashlib.sha256(path.read_bytes()).hexdigest()
    assert digest==data["preflight"][key.replace("report","sha256")]
assert data["summary"]["claims_total"]==len(data["claims"])
blockers=[r for r in data["claims"] if r["status"] in ("UNRESOLVED","CONFLICT")]
assert data["summary"]["implementation_authorized"]==(not blockers and data["summary"]["resolved"]>0)
assert data["safety"]=={"database_opened":False,"runtime_started":False,"telegram_started":False,"production_source_modified":False,"wal_shm_manipulated":False,"main_py_started":False}
print("[PASS] Stage 21.14.2b parity artifacts verified.")
