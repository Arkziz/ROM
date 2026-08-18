from __future__ import annotations
import inspect, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
import db_modules.equipment as equipment

class FakeSystem:
    def __init__(self):
        self.calls = []
    def buy_item_for_gold(self, user_id, item_id, price, quantity=1):
        self.calls.append((user_id, item_id, price, quantity))
        return {"success": True, "message": "ok"}

fake = FakeSystem()
original = equipment._equipment_system
try:
    equipment._equipment_system = lambda: fake
    result = equipment.buy_item_for_gold(11, 22, price=33.5, quantity=1)
    assert result["success"] is True
    assert fake.calls == [(11, 22, 33.5, 1)]
finally:
    equipment._equipment_system = original

sig = inspect.signature(equipment.buy_item_for_gold)
assert list(sig.parameters) == ["user_id", "item_id", "price", "quantity"]
assert sig.parameters["quantity"].default == 1
print("[PASS] buy_item_for_gold signature bridge")
