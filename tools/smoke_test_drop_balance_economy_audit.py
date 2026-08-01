#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def fail(message):
    print(f"[FAIL] {message}")
    raise SystemExit(1)


def main():
    report_path = ROOT / "CENTRAL_DROP_11_11_0_BALANCE_ECONOMY_AUDIT.json"
    markdown_path = ROOT / "CENTRAL_DROP_11_11_0_BALANCE_ECONOMY_AUDIT.md"
    if not report_path.is_file() or not markdown_path.is_file():
        fail("audit artifacts missing")
    data = json.loads(report_path.read_text(encoding="utf-8"))
    if data.get("verdict") not in ("PASS", "REVIEW"):
        fail(f"audit verdict={data.get('verdict')}")
    if not data.get("schema_valid"):
        fail("schema safety contract failed")
    critical_findings = [
        item for item in data.get("findings", ())
        if item.get("severity") == "critical"
    ]
    if critical_findings:
        fail(f"critical audit findings: {critical_findings}")
    if data.get("victory_rule_order") != [
        "trophy", "equipment", "refine_stone", "rune", "potion"
    ]:
        fail(f"victory order mismatch: {data.get('victory_rule_order')}")
    if data.get("protected_simulation_results") != 0:
        fail("protected materials produced simulated drops")
    expected_outputs = {"normal": 0.89, "elite": 1.66, "boss": 2.50}
    for enemy, expected in expected_outputs.items():
        simulation = data["simulations"][enemy]
        if abs(simulation["expected_item_results_per_kill"] - expected) > 1e-12:
            fail(f"{enemy} expected output mismatch")
        for rule, details in simulation["deviations"].items():
            if not details["within_tolerance"]:
                fail(f"{enemy}/{rule} outside 5 sigma")
    markdown = markdown_path.read_text(encoding="utf-8")
    for marker in (
        "89 expected item results per 100 victories",
        "166 expected item results per 100 victories",
        "250 expected item results per 100 victories",
        "No gameplay coefficients are changed by 11.11.0",
    ):
        if marker not in markdown:
            fail(f"markdown marker missing: {marker}")
    print("[OK] Drop balance/economy audit contracts")
    print("- schema safety and read-only audit contract: OK")
    print("- five production rules and order: OK")
    print("- normal/elite/boss rates within 5 sigma: OK")
    print("- expected aggregate outputs 89/166/250 per 100: OK")
    print("- protected materials 0 drops: OK")
    print("- audit artifacts complete: OK")
    print("- gameplay balance changes: 0")


if __name__ == "__main__":
    main()
