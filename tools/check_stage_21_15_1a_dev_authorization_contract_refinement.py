#!/usr/bin/env python3
import json
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "reports/stage_21_15_1a_dev_authorization_contract_refinement.json"
data = json.loads(REPORT.read_text(encoding="utf-8"))
assert data["stage"] == "21.15.1a"
assert data["status"] == "PASS"
assert data["decision"] == "REFINED_PARITY_RESOLUTION_REQUIRED"
assert data["next_action"] == "GO_TO_PARITY_RESOLUTION"
assert len(data["refined_contract"]) >= 8
assert len(data["unresolved_for_parity"]) >= 5
assert data["production_sqlite_opened"] is False
assert data["environment_file_opened"] is False
assert data["main_started"] is False
assert data["game_db_wal_shm"] == "NOT_MANIPULATED"
print("PASS: Stage 21.15.1a DEV authorization contract refinement")
