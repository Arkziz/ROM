from __future__ import annotations
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))
from data.player_progression import get_base_exp_for_level
from systems.contract_system import get_contract_exp_for_level,get_contract_mobs_equivalent,create_daily_contract
from db import get_contract_exp_for_level as compatibility
for level in (1,5,8,10):
    expected=int(get_base_exp_for_level(level))*int(get_contract_mobs_equivalent())
    assert get_contract_exp_for_level(level)==expected,(level,get_contract_exp_for_level(level),expected)
    assert compatibility(level)==expected
assert callable(create_daily_contract)
print("[PASS] contract EXP runtime formula restored")
