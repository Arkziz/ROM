#!/usr/bin/env python3
"""Verify Stage 21.14.2a refined contract artifacts."""
import hashlib
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
REPORT=ROOT/'reports/stage_21_14_2a_refined_event_schedules_rewards_contract.json'
DOC=ROOT/'MD/STAGE_21_14_2A_REFINED_EVENT_SCHEDULES_REWARDS_CONTRACT.md'
AUDIT=ROOT/'reports/stage_21_14_2_existing_event_schedules_rewards_audit.json'
data=json.loads(REPORT.read_text(encoding="utf-8"))
assert DOC.is_file()
assert AUDIT.is_file()
assert hashlib.sha256(AUDIT.read_bytes()).hexdigest()=='a98db02871359e49d80da1d646bbeac814725c408331a81e4ff961a30627d085'
assert data["stage"]=="21.14.2a"
assert data["status"]=="PASS"
assert data["preflight"]["starting_head"]=='4cec994c90cd6eaad45b33f6370a33b11ca39c9d'
assert data["preflight"]["audit_sha256"]=='a98db02871359e49d80da1d646bbeac814725c408331a81e4ff961a30627d085'
assert data["safety"]=={"database_opened":False,"v1_runtime_imported":False,"telegram_started":False,"runtime_started":False,"production_source_modified":False,"wal_shm_manipulated":False,"main_py_started":False}
assert data["decision"] in ("GO_TO_PARITY_RESOLUTION","GO_TO_PARITY_RESOLUTION_WITH_OPEN_QUESTIONS")
assert data["contract"]["decision"]==data["decision"]
assert len(data["refined_evidence"])>0
print("[PASS] Stage 21.14.2a refined contract artifacts verified.")
