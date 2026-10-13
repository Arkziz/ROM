#!/usr/bin/env python3
from __future__ import annotations
import ast, json
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
REPORTS = (
    "reports/stage_20_2_6_class_combat_acceptance.json",
    "reports/stage_20_3_9_hybrid_mana_economy_acceptance.json",
    "reports/stage_20_4_7_general_economy_acceptance.json",
    "reports/stage_20_5_7_premium_admin_crystals_acceptance.json",
    "reports/stage_20_6_6_travel_equipment_acceptance.json",
    "reports/stage_20_7_1_full_regression.json",
    "reports/stage_20_7_2_manual_acceptance.json",
    "reports/stage_20_7_3_stage_20_closure.json",
)
DOCS = (
    "MD/STAGE_20_7_2_MANUAL_ACCEPTANCE.md",
    "MD/STAGE_20_FULL_DOCUMENTATION.md",
    "MD/STAGE_20_7_3_STAGE_20_CLOSURE.md",
)
def ok(data):
    text = " ".join(str(data.get(k, "")) for k in ("status", "decision", "acceptance_decision", "closure_readiness", "stage_20_status")).upper()
    return any(x in text for x in ("PASS", "ACCEPTED", "GO", "CLOSED"))
def main():
    for rel in REPORTS:
        p = ROOT / rel
        assert p.is_file(), rel
        data = json.loads(p.read_text(encoding="utf-8-sig"))
        assert ok(data), (rel, data)
    for rel in DOCS:
        p = ROOT / rel
        text = p.read_text(encoding="utf-8")
        assert len(text) > 500, rel
    full = (ROOT / DOCS[1]).read_text(encoding="utf-8")
    for token in (
        "Stage 20.2", "Stage 20.3", "Stage 20.4", "Stage 20.5", "Stage 20.6", "Stage 20.7",
        "Level-up gold", "Premium", "admin crystals", "travel", "equipment",
        "20.6.4a", "20.6.5d", "Stage 19 invariants", "Known nuances",
    ):
        assert token.lower() in full.lower(), token
    closure = json.loads((ROOT / REPORTS[-1]).read_text(encoding="utf-8"))
    assert closure["stage_20_status"] == "CLOSED"
    assert closure["manual_acceptance"] == "ACCEPTED"
    assert closure["critical_gaps"] == 0 and closure["high_gaps"] == 0
    print("[OK] Stage 20.7.3 documentation and closure contracts PASS")
if __name__ == "__main__":
    main()
