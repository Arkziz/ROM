from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import db
from systems.refine_system import apply_weapon_refine_to_damage

USER_ID = 243129101


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def main():
    base_1h = db.calculate_weapon_damage_by_values(8, "common", 1)
    base_2h = db.calculate_weapon_damage_by_values(8, "common", 2)
    require(base_1h == (6, 10), f"unexpected 1H formula result: {base_1h}")
    require(base_2h == (9, 13), f"unexpected 2H formula result: {base_2h}")

    row = db.conn.execute(
        "SELECT es.inventory_id FROM equipment_slots es "
        "WHERE es.user_id=? AND es.slot_key='main_hand'",
        (USER_ID,),
    ).fetchone()
    if not row or row[0] is None:
        print("[OK] weapon damage formula contracts")
        print("- no equipped main-hand weapon for runtime item check")
        return 0

    inventory_id = int(row[0])
    result = db.get_weapon_damage_by_inventory_id(inventory_id)
    display = db.get_inventory_weapon_damage_display(inventory_id)
    refine_level = db.get_inventory_refine_level(inventory_id)

    require(isinstance(result, dict), type(result))
    required_keys = {
        "is_weapon", "attack_type", "physical_min", "physical_max",
        "magic_min", "magic_max", "text",
    }
    require(required_keys.issubset(result), f"missing keys: {required_keys - set(result)}")
    require(result["is_weapon"] is True, result)
    require(result["attack_type"] in {"physical", "magical"}, result)
    require(isinstance(display, str) and display == result["text"], (display, result))

    raw = db.conn.execute(
        "SELECT COALESCE(it.weapon_min_damage,0), COALESCE(it.weapon_max_damage,0), "
        "COALESCE(it.weapon_min_magic_damage,0), COALESCE(it.weapon_max_magic_damage,0), "
        "COALESCE(it.item_level,1), it.rarity, COALESCE(it.weapon_hands,1) "
        "FROM inventory inv JOIN items it ON it.id=inv.item_id WHERE inv.id=?",
        (inventory_id,),
    ).fetchone()

    if result["attack_type"] == "magical":
        base_min, base_max = int(raw[2] or 0), int(raw[3] or 0)
        actual = (result["magic_min"], result["magic_max"])
    else:
        base_min, base_max = int(raw[0] or 0), int(raw[1] or 0)
        actual = (result["physical_min"], result["physical_max"])
    if base_min <= 0 or base_max <= 0:
        base_min, base_max = db.calculate_weapon_damage_by_values(raw[4], raw[5], raw[6])
    expected = apply_weapon_refine_to_damage(base_min, base_max, refine_level)
    require(actual == expected, f"refine mismatch: actual={actual}, expected={expected}")

    print("[OK] weapon damage read-only runtime contracts")
    print("- inventory_id:", inventory_id)
    print("- attack_type:", result["attack_type"])
    print("- refine_level:", refine_level)
    print("- base damage:", (base_min, base_max))
    print("- final damage:", actual)
    print("- display:", display)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
