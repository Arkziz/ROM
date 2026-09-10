#!/usr/bin/env python3
import json,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1]
report=json.loads((R/"reports/stage_18_16_10e_rebirth_sphere_distribution_audit.json").read_text(encoding="utf-8"))
assert report["read_only"] is True
assert report["database"]["quick_check"]=="ok" and report["database"]["foreign_key_violations"]==[]
assert report["economic_policy"]["mob_drop_eligible"] is True
assert report["economic_policy"]["crystal_shop_eligible"] is False
assert report["current_state"]["configured_for_drop"] is False
assert set(report["scenarios"])=={"A_very_rare","B_balanced","C_boss_focused"}
for scenario in report["scenarios"].values():
 assert 0<scenario["probability_at_least_one_per_month"]<1
 assert scenario["monthly_supply_per_100_active_players"]>0
print("[PASS] Stage 18.16.10e read-only audit report contract")
