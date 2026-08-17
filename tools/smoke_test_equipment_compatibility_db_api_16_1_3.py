from __future__ import annotations
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))
from db import check_armor_compatibility_for_class as armor,check_main_hand_compatibility_for_class as main,check_off_hand_compatibility_for_class as off,check_two_handed_conflict_for_equip as two
staff={"category":"equipment","slot_key":"main_hand","item_subtype":"staff_2h","weapon_hands":2}
assert main("priest",staff)["success"] is True
assert main("mage",staff)["success"] is True
assert main("warrior",staff)["success"] is False
assert armor("priest",{"slot_key":"chest","armor_type":"cloth"})["success"] is True
assert armor("priest",{"slot_key":"chest","armor_type":"plate"})["success"] is False
assert off("priest",{"slot_key":"off_hand","item_subtype":"talisman"})["success"] is True
assert off("priest",{"slot_key":"off_hand","item_subtype":"shield"})["success"] is False
assert two(1,staff)["success"] is True
print("[PASS] equipment compatibility DB API restored")
