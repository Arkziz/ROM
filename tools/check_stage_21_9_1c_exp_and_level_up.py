#!/usr/bin/env python3
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from rom_v2.domain.player_progression import apply_player_exp_award,get_player_exp_to_next_level
amount=get_player_exp_to_next_level(1)+3
result=apply_player_exp_award(1,0,amount,30)
assert (result.level,result.exp,result.level_ups)==(2,3,1)
print("STAGE_21_9_1C_EXP_LEVEL_UP_SMOKE: PASS")
