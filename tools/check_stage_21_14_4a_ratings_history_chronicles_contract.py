#!/usr/bin/env python3
import json
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "reports/stage_21_14_4a_ratings_history_chronicles_contract_refinement.json"
data = json.loads(REPORT.read_text(encoding="utf-8"))
assert data["stage"] == "21.14.4a"
assert data["status"] == "PASS"
assert data["decision"] == 'GO_TO_PARITY_RESOLUTION'
assert len(data["refined_areas"]) == 5
assert data["unresolved_questions"]
assert data["manual_verification"]["required"] is False
assert any("Do not invent" in item for item in data["prohibitions"])
print("PASS: Stage 21.14.4a refined ratings/history/chronicles contract")
