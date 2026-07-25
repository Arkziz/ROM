from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import db

USER_ID = 243129101
items = db.get_all_equipped_items(USER_ID)
assert isinstance(items, list), type(items)
assert len(items) == 10, f"expected 10 equipment slots, got {len(items)}"
for entry in items:
    assert isinstance(entry, dict), type(entry)
    for key in ("slot_key", "slot_name", "inventory_id", "item"):
        assert key in entry, (key, entry)
    if entry["inventory_id"] is not None:
        assert isinstance(entry["item"], tuple), type(entry["item"])
        assert len(entry["item"]) == 19, len(entry["item"])

repair_rows = db.get_equipped_items_for_repair(USER_ID)
assert isinstance(repair_rows, list), type(repair_rows)
assert len(repair_rows) == 10, f"expected 10 repair rows, got {len(repair_rows)}"
for row in repair_rows:
    assert isinstance(row, dict), type(row)
    for key in ("slot", "slot_key", "inventory_id", "name", "durability", "repair_cost", "is_broken"):
        assert key in row, (key, row)

print("[OK] equipment full legacy contract")
print("- equipment slots:", len(items))
print("- repair rows:", len(repair_rows))
print("- repairable:", sum(1 for row in repair_rows if row.get("repair_cost", 0) > 0))
