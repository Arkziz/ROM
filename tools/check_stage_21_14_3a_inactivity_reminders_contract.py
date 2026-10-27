#!/usr/bin/env python3
import json
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "reports/stage_21_14_3a_inactivity_reminders_contract_refinement.json"
data = json.loads(REPORT.read_text(encoding="utf-8"))
assert data["stage"] == "21.14.3a"
assert data["decision"] == "GO_TO_PARITY_RESOLUTION"
assert data["status"] in ("PASS", "PASS_REVIEW_REQUIRED")
areas = {item["area"] for item in data["refined_contract"]}
assert areas == {"threshold", "clock", "cycle_identity", "new_cycle", "persistence", "delivery_boundary", "scheduler_scope", "v2_scope"}
assert data["manual_verification"]["required"] is False
assert data["unresolved"] == [] if data["decision"] == "GO_TO_PARITY_RESOLUTION" else data["unresolved"]
print("PASS: Stage 21.14.3a inactivity reminders refined contract")
