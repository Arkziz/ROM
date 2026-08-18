from __future__ import annotations
import inspect, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
import db_modules.equipment as equipment

class FakeSystem:
    def get_inventory_refined_display_name(self, inventory_id, name=None):
        return str(name or "Предмет") + " [+7]"

original = equipment._equipment_system
try:
    equipment._equipment_system = lambda: FakeSystem()
    assert equipment.get_inventory_refined_display_name(77, "Посох") == "Посох [+7]"
    assert equipment.get_inventory_refined_display_name(77, base_name="Кільце") == "Кільце [+7]"
finally:
    equipment._equipment_system = original

sig = inspect.signature(equipment.get_inventory_refined_display_name)
assert list(sig.parameters) == ["inventory_id", "base_name"]
assert sig.parameters["base_name"].default is None
print("[PASS] refined display name signature bridge")
