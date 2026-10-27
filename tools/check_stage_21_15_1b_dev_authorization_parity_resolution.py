#!/usr/bin/env python3
import json
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "reports/stage_21_15_1b_dev_authorization_parity_resolution.json"
data = json.loads(REPORT.read_text(encoding="utf-8"))
assert data["stage"] == "21.15.1b"
assert data["status"] == "PASS"
assert data["decision"] == "PARITY_RESOLVED_IMPLEMENTATION_AUTHORIZED"
assert not data["failed_checks"]
expected = {
    "canonical_dev_identity_policy",
    "effective_register_dev_handlers_chain",
    "command_inventory_and_risk_class",
    "audit_requirements_per_command",
    "separate_auction_admin_policy",
}
assert {item["key"] for item in data["resolutions"]} == expected
assert all(item["status"].startswith("RESOLVED") for item in data["resolutions"])
assert data["authorization"]["authorized"] is True
assert data["authorization"]["next_stage"] == "21.15.1c"
assert data["production_sqlite_opened"] is False
assert data["environment_file_opened"] is False
assert data["main_started"] is False
assert data["game_db_wal_shm"] == "NOT_MANIPULATED"
print("PASS: Stage 21.15.1b DEV authorization parity resolution")
