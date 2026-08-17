from __future__ import annotations
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))
import db_modules.equipment as equipment
from db import get_equipped_slot
assert callable(get_equipped_slot)
original=equipment.get_all_equipped_slots
try:
    equipment.get_all_equipped_slots=lambda user_id:{"main_hand":77,"off_hand":None}
    assert equipment.get_equipped_slot(1,"main_hand")==77
    assert equipment.get_equipped_slot(1,"off_hand") is None
    assert equipment.get_equipped_slot(1,"invalid_slot") is None
finally:
    equipment.get_all_equipped_slots=original
from db_modules.player import get_player_attack_profile
assert callable(get_player_attack_profile)
print("[PASS] get_equipped_slot runtime contract")
