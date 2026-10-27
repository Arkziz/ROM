#!/usr/bin/env python3
import json
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "reports/stage_21_15_3a_simulator_adapters_contract_refinement.json"
data = json.loads(REPORT.read_text(encoding="utf-8"))
assert data["stage"] == "21.15.3a"
assert data["status"] == "PASS"
assert data["decision"] == "REFINED_PARITY_RESOLUTION_REQUIRED"
assert data["next_action"] == "GO_TO_PARITY_RESOLUTION"
assert len(data["refined_contract"]) >= 10
assert len(data["unresolved_for_parity"]) >= 7
assert data["flat_domain_policy"]["future_module"] == "rom_v2/domain/simulator_adapters.py"
assert data["flat_domain_policy"]["nested_package_authorized"] is False
assert data["production_mutation"] is False
assert data["simulator_executed"] is False
assert data["production_sqlite_opened"] is False
assert data["environment_file_opened"] is False
assert data["main_started"] is False
assert data["game_db_wal_shm"] == "NOT_MANIPULATED"
print("PASS: Stage 21.15.3a simulator adapters contract refinement")
