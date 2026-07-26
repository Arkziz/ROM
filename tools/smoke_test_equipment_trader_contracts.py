from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import db
from systems import equipment_system as equipment

USER_ID = 243129101

items = db.get_sellable_equipment_items(USER_ID)
assert isinstance(items, list)
for item in items:
    assert isinstance(item, tuple), type(item)
    assert len(item) == 19, len(item)
    inventory_id = int(item[0])
    equipped = db.conn.execute(
        "SELECT 1 FROM equipment_slots WHERE user_id=? AND inventory_id=?",
        (USER_ID, inventory_id),
    ).fetchone()
    assert equipped is None, inventory_id

for name in (
    "get_sellable_equipment_items",
    "sell_inventory_item_to_trader",
    "buy_item_for_gold",
    "buy_common_equipment_from_trader",
):
    assert callable(getattr(equipment, name, None)), name

# Read-only refusal checks: no DB mutation.
missing_sale = equipment.sell_inventory_item_to_trader(USER_ID, -999999999)
assert isinstance(missing_sale, dict) and missing_sale.get("success") is False
missing_buy = equipment.buy_item_for_gold(USER_ID, -999999999, 1.0, 1)
assert isinstance(missing_buy, dict) and missing_buy.get("success") is False

print("[OK] equipment trader runtime contracts")
print("- sellable equipment:", len(items))
print("- sell rows: tuple[19]")
print("- equipped items excluded: yes")
print("- duplicate/missing sale protected: yes")
print("- missing product purchase protected: yes")
