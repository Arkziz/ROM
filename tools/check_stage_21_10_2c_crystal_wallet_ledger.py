#!/usr/bin/env python3
"""Targeted Stage 21.10.2c Crystal Wallet/Ledger verifier."""
import ast
from pathlib import Path

root=Path(__file__).resolve().parents[1]
app=root/"rom_v2/application/crystal_wallet_ledger.py"
test=root/"tests_v2/test_crystal_wallet_ledger.py"
for path in (app,test): ast.parse(path.read_text(encoding="utf-8"),filename=str(path))
source=app.read_text(encoding="utf-8")
required=("class CrystalWalletLedgerService","class CrystalLedgerTransaction","class CrystalWalletCommand","idempotency_key_payload_conflict","original_already_compensated","insufficient_crystals")
missing=[token for token in required if token not in source]
if missing: raise SystemExit(f"missing_contract_tokens:{missing}")
for forbidden in ("sqlite3","aiogram","telegram"):
    if forbidden in source.lower(): raise SystemExit(f"forbidden_dependency:{forbidden}")
print("STAGE_21_10_1C_CRYSTAL_WALLET_LEDGER_SMOKE: PASS")
