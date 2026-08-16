from __future__ import annotations
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))
from db import set_player_level_for_test,reset_player_level_for_test,set_gold_for_test,create_dev_armor_item_for_test,create_dev_weapon_item_for_test,reset_hero_for_test,seed_class_reset_sphere_item
for fn in (set_player_level_for_test,reset_player_level_for_test,set_gold_for_test,create_dev_armor_item_for_test,create_dev_weapon_item_for_test,reset_hero_for_test,seed_class_reset_sphere_item): assert callable(fn),fn
print("[PASS] DEV handler DB API restored")
