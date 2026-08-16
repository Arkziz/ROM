from __future__ import annotations
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))
from db import (
    is_inventory_item_equipped, find_equipped_slot_by_inventory_id,
    get_item_required_level_by_inventory_id, get_item_classification_by_inventory_id,
    is_class_reset_sphere_inventory_item, use_class_reset_sphere_from_inventory,
    ARMOR_ALLOWED_BY_CLASS, MAIN_HAND_ALLOWED_BY_CLASS, OFF_HAND_ALLOWED_BY_CLASS,
)
for function in (is_inventory_item_equipped,find_equipped_slot_by_inventory_id,get_item_required_level_by_inventory_id,get_item_classification_by_inventory_id,is_class_reset_sphere_inventory_item,use_class_reset_sphere_from_inventory):
    assert callable(function),function
assert ARMOR_ALLOWED_BY_CLASS["mage"]=="cloth"
assert "staff_2h" in MAIN_HAND_ALLOWED_BY_CLASS["mage"]
assert "shield" in OFF_HAND_ALLOWED_BY_CLASS["knight"]
print("[PASS] inventory handler DB API restored")
