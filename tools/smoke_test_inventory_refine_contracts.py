from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import db

USER_ID = 243129101


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def main():
    inventory = db.get_inventory_detailed(USER_ID)
    require(isinstance(inventory, list), "get_inventory_detailed must return list")

    print("[OK] inventory/refine read-only runtime contracts")
    print("- inventory rows:", len(inventory))

    if not inventory:
        print("- no inventory rows available for deeper contract checks")
        return 0

    row = inventory[0]
    require(isinstance(row, tuple), "inventory row must be tuple")
    require(len(row) == 17, f"inventory row must have 17 fields, got {len(row)}")

    inventory_id = row[0]
    item = db.get_item_by_inventory_id(inventory_id)
    full = db.get_item_by_inventory_id_full(inventory_id)
    entry = db.get_inventory_entry(USER_ID, inventory_id)

    require(isinstance(item, tuple) and len(item) == 17, "get_item_by_inventory_id contract mismatch")
    require(isinstance(full, tuple) and len(full) == 19, "get_item_by_inventory_id_full contract mismatch")
    require(isinstance(entry, tuple) and len(entry) == 6, "get_inventory_entry contract mismatch")

    refine_level = db.get_inventory_refine_level(inventory_id)
    display_name = db.get_inventory_refined_display_name(inventory_id)
    require(isinstance(refine_level, int), "refine level must be int")
    require(isinstance(display_name, str), "refined display name must be str")

    if refine_level > 0:
        require(f"[+{refine_level}]" in display_name, "refine suffix missing from display name")
        require(f"[+{refine_level}]" in str(item[2]), "refine suffix missing from item tuple")
        require(f"[+{refine_level}]" in str(full[2]), "refine suffix missing from full tuple")
        require(f"[+{refine_level}]" in str(entry[2]), "refine suffix missing from entry tuple")

    print("- sample inventory_id:", inventory_id)
    print("- sample name:", display_name)
    print("- refine level:", refine_level)
    print("- tuple lengths: detailed=17 item=17 full=19 entry=6")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
