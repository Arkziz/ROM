#!/usr/bin/env python3
"""Targeted Stage 21.10.7c Bag Expansion verifier."""
import ast
from pathlib import Path

root=Path(__file__).resolve().parents[1]
app=root/"rom_v2/application/bag_expansion.py"
test=root/"tests_v2/test_bag_expansion.py"
for path in (app,test): ast.parse(path.read_text(encoding="utf-8"),filename=str(path))
source=app.read_text(encoding="utf-8")
required=("class BagExpansionService","class BagExpansionCommand","class BagExpansionReceipt","operation_key_payload_conflict","maximum_capacity","stale_capacity","stale_price","invalid_sequential_transition")
missing=[token for token in required if token not in source]
if missing: raise SystemExit(f"missing_contract_tokens:{missing}")
for forbidden in ("sqlite3","aiogram","telegram"):
    if forbidden in source.lower(): raise SystemExit(f"forbidden_dependency:{forbidden}")
print("STAGE_21_10_7C_BAG_EXPANSION_SMOKE: PASS")
