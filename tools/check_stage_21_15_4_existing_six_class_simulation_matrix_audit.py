#!/usr/bin/env python3
import json
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "reports/stage_21_15_4_existing_six_class_simulation_matrix_audit.json"
data = json.loads(REPORT.read_text(encoding="utf-8"))
assert data["stage"] == "21.15.4"
assert data["status"] == "PASS"
assert data["summary"]["required_class_count"] == 6
assert set(data["summary"]["required_classes"]) == {"warrior", "knight", "scout", "rogue", "mage", "priest"}
assert set(data["class_matrix"]) == set(data["summary"]["required_classes"])
assert data["summary"]["long_simulation_executed"] is False
assert data["simulator_executed"] is False
assert data["production_sqlite_opened"] is False
assert data["environment_file_opened"] is False
assert data["main_started"] is False
assert data["game_db_wal_shm"] == "NOT_MANIPULATED"
print("PASS: Stage 21.15.4 existing six-class simulation matrix audit")
