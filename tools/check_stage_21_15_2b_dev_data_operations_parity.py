#!/usr/bin/env python3
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
data=json.loads((ROOT/"reports/stage_21_15_2b_dev_data_operations_parity_resolution.json").read_text(encoding="utf-8"))
assert data["stage"]=="21.15.2b" and data["status"]=="PASS"
assert data["decision"]=="PARITY_RESOLVED_IMPLEMENTATION_AUTHORIZED"
assert data["unresolved"]==[]
assert len(data["resolutions"])>=11 and all(x["status"]=="RESOLVED" for x in data["resolutions"])
contract=data["implementation_contract"]
assert contract["module"]=="rom_v2/domain/dev_data_operations.py"
assert contract["nested_package_authorized"] is False
assert contract["direct_sql_authorized"] is False
assert contract["unit_of_work_required"] is True
assert data["dev_operations_executed"] is False
assert data["game_db_wal_shm"]=="NOT_MANIPULATED"
print("PASS: Stage 21.15.2b DEV data operations parity resolution")
