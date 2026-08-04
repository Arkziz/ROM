from __future__ import annotations

import hashlib
import json
from pathlib import Path

from systems.simulation.canonical_rules import call_rule, rule_manifest
from systems.simulation.production_parity import run_required_parity, source_dependency_report
from systems.simulation.rng import SimulationRng


def main():
    first = run_required_parity()
    second = run_required_parity()
    assert first["verdict"] == "PASS", [x for x in first["results"] if not x["passed"]][:5]
    assert first == second
    assert first["cases"] >= 100
    manifest = rule_manifest()
    assert len(manifest) >= 15
    assert all(item["callable"] for item in manifest)
    a = call_rule("player_attack", 50, 20, 30, 30, 10, "physical", 5, 10, rng=SimulationRng(777))
    b = call_rule("player_attack", 50, 20, 30, 30, 10, "physical", 5, 10, rng=SimulationRng(777))
    assert a == b
    report = source_dependency_report()
    assert all(item["source_file"] for item in report["rules"])
    print("[OK] Simulation canonical rules parity smoke test")
    print(f"- parity cases: {first['cases']}")
    print(f"- passed: {first['passed']}")
    print(f"- failed: {first['failed']}")
    print(f"- canonical rules: {len(manifest)}")
    print("- same-seed deterministic attack: PASS")
    print("- production sources resolved: PASS")


if __name__ == "__main__":
    main()
