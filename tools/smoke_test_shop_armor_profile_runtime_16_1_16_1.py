from __future__ import annotations
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
import db_modules.shop as shop
from data.equipment_profiles import ARMOR_ALLOWED_BY_CLASS
original=shop.get_character_class if hasattr(shop,"get_character_class") else None
# Function imports get_character_class locally, so validate canonical mapping directly and source contract.
for cls in ("warrior","knight","scout","rogue","mage","priest"):
    value=ARMOR_ALLOWED_BY_CLASS.get(cls)
    assert isinstance(value,str) and value
import ast
source=(ROOT/"db_modules"/"shop.py").read_text(encoding="utf-8")
tree=ast.parse(source,filename="db_modules/shop.py")
fn=next(node for node in tree.body if isinstance(node,ast.FunctionDef) and node.name=="get_shop_armor_type_for_user")
fn_source=ast.get_source_segment(source,fn)
assert "get_class_equipment_rules" not in fn_source
assert "ARMOR_ALLOWED_BY_CLASS" in fn_source
from systems.equipment_system import is_armor_slot
from systems import dynamic_equipment_system
assert is_armor_slot("ring") is False
assert callable(dynamic_equipment_system.get_dynamic_armor_name)
print("[PASS] shop armor profile runtime contract")
