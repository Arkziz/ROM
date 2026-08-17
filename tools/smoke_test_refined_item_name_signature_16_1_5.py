from __future__ import annotations
import inspect,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))
import db_modules.equipment as equipment
class FakeSystem:
    def format_refined_item_name(self,name,refine_level):
        return name if int(refine_level or 0)<=0 else f"{name} [+{int(refine_level)}]"
original=equipment._equipment_system
try:
    equipment._equipment_system=lambda:FakeSystem()
    assert equipment.format_refined_item_name("Зілля",0)=="Зілля"
    assert equipment.format_refined_item_name(base_name="Посох",refine_level=5)=="Посох [+5]"
finally:
    equipment._equipment_system=original
sig=inspect.signature(equipment.format_refined_item_name)
assert list(sig.parameters)==["base_name","refine_level"]
print("[PASS] refined item name signature bridge")
