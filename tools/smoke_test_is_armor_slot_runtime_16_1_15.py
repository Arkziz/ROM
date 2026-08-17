from __future__ import annotations
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from systems.equipment_system import is_armor_slot
for slot in ("helmet","shoulders","chest","gloves","legs","boots"):assert is_armor_slot(slot) is True,slot
for slot in ("main_hand","off_hand","necklace","ring","",None,"invalid"):assert is_armor_slot(slot) is False,slot
from db_modules.shop import create_common_equipment_shop_preview
assert callable(create_common_equipment_shop_preview)
print("[PASS] is_armor_slot runtime contract")
