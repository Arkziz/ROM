"""Standalone Stage 21.7.6b contract checker.

Python sets sys.path[0] to the script directory when a file under tools/ is run
by path. Add the repository root explicitly before importing rom_v2.
"""
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from rom_v2.domain.durability import *
from rom_v2.application.durability_service import DurabilityService
assert MAX_DURABILITY==100 and MIN_DURABILITY==0 and DEATH_DURABILITY_LOSS==5
assert RARITY_REPAIR_MULTIPLIERS=={"common":Decimal("1.0"),"uncommon":Decimal("2.5"),"rare":Decimal("7.0"),"epic":Decimal("18.0")}
assert calculate_repair_cost(0,"epic")==90
assert not contributes_stats(0) and contributes_stats(1)
print("[PASS] Stage 21.7.6b durability and repair contract")
