#!/usr/bin/env python3
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from rom_v2.domain.central_loot import CentralLootPlanner, LootRandomSource
assert CentralLootPlanner and LootRandomSource
print("STAGE_21_9_4C_CENTRAL_LOOT_SMOKE: PASS")
