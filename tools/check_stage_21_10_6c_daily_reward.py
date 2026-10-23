#!/usr/bin/env python3
"""Targeted Stage 21.10.6c Daily Reward verifier."""
import ast
from pathlib import Path

root=Path(__file__).resolve().parents[1]
app=root/"rom_v2/application/daily_reward.py"
test=root/"tests_v2/test_daily_reward.py"
for path in (app,test): ast.parse(path.read_text(encoding="utf-8"),filename=str(path))
source=app.read_text(encoding="utf-8")
required=("class DailyRewardService","class DailyRewardClaimCommand","class DailyRewardReceipt","operation_key_payload_conflict","already_claimed","stale_period")
missing=[token for token in required if token not in source]
if missing: raise SystemExit(f"missing_contract_tokens:{missing}")
for forbidden in ("sqlite3","aiogram","telegram"):
    if forbidden in source.lower(): raise SystemExit(f"forbidden_dependency:{forbidden}")
print("STAGE_21_10_6C_DAILY_REWARD_SMOKE: PASS")
