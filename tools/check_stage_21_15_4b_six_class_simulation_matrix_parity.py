#!/usr/bin/env python3
import json
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "reports/stage_21_15_4b_six_class_simulation_matrix_parity_resolution.json"
data = json.loads(REPORT.read_text(encoding="utf-8"))
assert data["stage"] == "21.15.4b"
assert data["status"] == "PASS"
assert data["decision"] == "PARITY_RESOLVED_IMPLEMENTATION_AUTHORIZED"
assert [item["key"] for item in data["classes"]] == ["warrior", "knight", "scout", "rogue", "mage", "priest"]
assert data["matrix_cardinality"] == 6
assert data["unresolved"] == []
assert data["simulator_executed"] is False
assert data["long_simulation_executed"] is False
assert data["production_sqlite_opened"] is False
assert data["environment_file_opened"] is False
assert data["game_db_wal_shm"] == "NOT_MANIPULATED"
for item in data["refinement_scope_checks"].values():
    assert item is True
print("PASS: Stage 21.15.4b six-class simulation matrix parity resolution")
