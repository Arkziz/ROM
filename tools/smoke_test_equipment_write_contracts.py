from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import db

USER_ID = 243129101

slots = db.conn.execute(
    "SELECT slot_key, inventory_id FROM equipment_slots WHERE user_id=? ORDER BY slot_key",
    (USER_ID,),
).fetchall()

if len(slots) != 10:
    raise AssertionError(f"Expected 10 equipment slots, got {len(slots)}")

for slot_key, inventory_id in slots:
    if inventory_id is None:
        continue
    owner = db.conn.execute(
        "SELECT user_id FROM inventory WHERE id=?", (int(inventory_id),)
    ).fetchone()
    if not owner or int(owner[0]) != USER_ID:
        raise AssertionError(f"Invalid equipped inventory ownership: {slot_key}={inventory_id}")

from systems import equipment_system as equipment

for name in (
    "equip_inventory_item",
    "unequip_inventory_item",
    "unequip_incompatible_items_after_class_change",
):
    func = getattr(equipment, name, None)
    if not callable(func):
        raise AssertionError(f"Missing callable: {name}")

print("[OK] equipment write runtime contracts")
print("- equipment slots:", len(slots))
print("- equipped:", sum(1 for _, value in slots if value is not None))
print("- direct write functions: available")
