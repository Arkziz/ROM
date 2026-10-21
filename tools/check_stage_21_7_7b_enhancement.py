from pathlib import Path
import sys
R=Path(__file__).resolve().parents[1]
if str(R) not in sys.path:sys.path.insert(0,str(R))
from rom_v2.domain.enhancement import *
assert REFINE_STONE_ITEM_ID==601 and SUCCESS_RUNE_ITEM_ID==602
assert WEAPON_MAX_REFINE_LEVEL==10 and ARMOR_MAX_REFINE_LEVEL==6
assert get_refine_success_chance("weapon",9)==20 and get_refine_success_chance("armor",5)==20
assert get_weapon_refine_damage_multiplier(10)==2.0
print("[PASS] Stage 21.7.7b enhancement contract")
