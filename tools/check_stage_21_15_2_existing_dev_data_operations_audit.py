#!/usr/bin/env python3
import json
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "reports/stage_21_15_2_existing_dev_data_operations_audit.json"
data = json.loads(REPORT.read_text(encoding="utf-8"))
assert data["stage"] == "21.15.2"
assert data["status"] == "PASS"
assert data["summary"]["next_action"] == "GO_TO_SEMANTIC_REFINEMENT_AFTER_HUMAN_REVIEW"
assert data["production_mutation"] is False
assert data["dev_operations_executed"] is False
assert data["production_sqlite_opened"] is False
assert data["environment_file_opened"] is False
assert data["main_started"] is False
assert data["game_db_wal_shm"] == "NOT_MANIPULATED"
print("PASS: Stage 21.15.2 existing DEV data operations audit")
