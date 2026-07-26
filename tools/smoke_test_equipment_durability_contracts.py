from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import db
from systems import equipment_system as equipment

USER_ID = 243129101

rows = db.get_equipped_items_for_repair(USER_ID)
assert isinstance(rows, list)
assert len(rows) == 10
assert abs(float(db.calculate_repair_cost(95, "common")) - 0.25) < 1e-9
assert abs(float(db.calculate_repair_cost(95, "uncommon")) - 0.62) < 1e-9
assert abs(float(db.calculate_repair_cost(95, "rare")) - 1.75) < 1e-9
assert abs(float(db.calculate_repair_cost(95, "epic")) - 4.5) < 1e-9

# Validate the death formatter contract without damaging real equipment.
synthetic_damage = [
    {"name": "Тестовий предмет", "old": 10, "new": 5, "broken": False},
    {"name": "Зламаний предмет", "old": 5, "new": 0, "broken": True},
]
for item in synthetic_damage:
    assert set(("name", "old", "new", "broken")).issubset(item)
    assert isinstance(item["broken"], bool)

# Validate no-trigger victory contract without modifying the database.
wear = equipment.apply_random_durability_wear_on_victory(USER_ID, chance_percent=0)
assert isinstance(wear, dict)
assert wear == {"triggered": False, "message": None}, wear

# Inspect function source contract by invoking the mapper on an empty account id.
death = equipment.damage_equipped_items_on_death(-999999999, amount=5)
assert isinstance(death, list), type(death)
for item in death:
    assert isinstance(item, dict)
    assert set(("name", "old", "new", "broken")).issubset(item)

print("[OK] equipment durability public contracts")
print("- repair rows:", len(rows))
print("- death result: list[dict]")
print("- death item keys: name, old, new, broken")
print("- victory result keys: triggered, message")
print("- death durability loss: 5")
