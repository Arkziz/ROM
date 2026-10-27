#!/usr/bin/env python3
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
data=json.loads((ROOT/"reports/stage_21_15_3b_simulator_adapters_parity_resolution.json").read_text(encoding="utf-8"))
assert data["stage"]=="21.15.3b" and data["status"]=="PASS"
assert data["decision"]=="PARITY_RESOLVED_IMPLEMENTATION_AUTHORIZED"
assert data["unresolved"]==[]
required_keys = {
    "clock_adapter_mapping",
    "rng_adapter_coverage",
    "sandbox_repository_inventory",
    "formula_reuse_matrix",
    "fixture_contract",
    "determinism_contract",
    "production_state_isolation",
    "candidate_sandbox_boundary",
}
by_key = {item["key"]: item for item in data["resolutions"]}
assert required_keys.issubset(by_key), sorted(required_keys - set(by_key))
assert all(by_key[key]["status"] == "RESOLVED" for key in required_keys)
assert all(set(("key", "status", "contract", "owners")).issubset(item) for item in data["resolutions"])
contract=data["implementation_contract"]
assert contract["module"]=="rom_v2/domain/simulator_adapters.py"
assert contract["nested_package_authorized"] is False
assert contract["direct_sql_authorized"] is False
assert contract["unit_of_work_required"] is True
assert data["simulator_executed"] is False
assert data["game_db_wal_shm"]=="NOT_MANIPULATED"
print("PASS: Stage 21.15.3b simulator adapters parity resolution")
