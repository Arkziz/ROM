#!/usr/bin/env python3
import json
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "reports/stage_21_14_5a_about_links_support_contract_refinement.json"
data = json.loads(REPORT.read_text(encoding="utf-8"))
assert data["stage"] == "21.14.5a"
assert data["status"] == "PASS"
assert data["decision"] == "REFINED_CONTRACT_READY_FOR_PARITY_RESOLUTION"
assert data["next_action"] == "GO_TO_PARITY_RESOLUTION"
assert data["implementation_authorized"] is False
assert data["no_go"] is False
assert {item["area"] for item in data["contracts"]} == {
    "about_content", "useful_links", "support", "validation",
    "configuration", "navigation", "availability",
}
assert all(item["status"] == "REFINED" for item in data["contracts"])
print("PASS: Stage 21.14.5a About/links/support refinement contract")
