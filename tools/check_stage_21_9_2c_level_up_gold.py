#!/usr/bin/env python3
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from rom_v2.domain.level_up_gold import calculate_v2_level_up_rewards
result=calculate_v2_level_up_rewards(1,3)
assert result["reached_levels"]==[2,3] and abs(result["gold"]-1.88)<1e-9
print("STAGE_21_9_2C_LEVEL_UP_GOLD_SMOKE: PASS")
