#!/usr/bin/env python3
import json
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "reports/stage_21_15_4a_six_class_simulation_matrix_contract_refinement.json"
data = json.loads(REPORT.read_text(encoding="utf-8"))
expected = ["warrior", "knight", "scout", "rogue", "mage", "priest"]
assert data["stage"] == "21.15.4a"
assert data["status"] == "PASS"
assert data["decision"] == "REFINED_SIX_CLASS_PARITY_RESOLUTION_REQUIRED"
assert data["canonical_classes"] == expected
assert [row["class_key"] for row in data["matrix"]] == expected
assert all(row["long_progression_run_required_now"] is False for row in data["matrix"])
assert data["simulator_executed"] is False
assert data["long_simulation_executed"] is False
assert data["production_sqlite_opened"] is False
assert data["environment_file_opened"] is False
assert data["flat_domain_required"] is True
assert data["game_db_wal_shm"] == "NOT_MANIPULATED"
print("PASS: Stage 21.15.4a six-class simulation matrix refinement")
