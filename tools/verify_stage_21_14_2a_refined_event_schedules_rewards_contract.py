#!/usr/bin/env python3
"""Verify Stage 21.14.2a refined contract without opening a database."""
import hashlib
import json
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
AUDIT = ROOT / 'reports/stage_21_14_2_existing_event_schedules_rewards_audit.json'
REPORT = ROOT / 'reports/stage_21_14_2a_refined_event_schedules_rewards_contract.json'
DOC = ROOT / 'MD/STAGE_21_14_2A_REFINED_EVENT_SCHEDULES_REWARDS_CONTRACT.md'
def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()
data = json.loads(REPORT.read_text(encoding="utf-8"))
contract = data["refined_contract"]
assert DOC.is_file()
assert digest(AUDIT) == 'a98db02871359e49d80da1d646bbeac814725c408331a81e4ff961a30627d085'
assert data["stage"] == "21.14.2a"
assert data["status"] == "PASS"
assert contract["contract_state"] == "REFINED_EVIDENCE_BOUND_UNRESOLVED"
assert contract["implementation_authorized"] is False
assert contract["decision"] in ("GO_TO_PARITY_RESOLUTION", "REVIEW_REQUIRED")
assert contract["candidate_count"] == len(contract["candidate_contracts"])
assert len({row["candidate_id"] for row in contract["candidate_contracts"]}) == contract["candidate_count"]
assert all(row["canonical_status"] == "UNRESOLVED" for row in contract["candidate_contracts"])
assert all(row["implementation_authorized"] is False for row in contract["candidate_contracts"])
assert data["safety"] == {
    "database_opened": False,
    "production_source_modified": False,
    "runtime_started": False,
    "telegram_started": False,
    "wal_shm_manipulated": False,
    "main_py_started": False,
}
print("[PASS] Stage 21.14.2a refined event schedules/rewards contract verified.")
