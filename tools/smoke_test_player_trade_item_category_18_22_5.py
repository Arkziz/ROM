from __future__ import annotations
import ast
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

SOURCE_PATH = ROOT / "systems/player_interaction_system.py"
source = SOURCE_PATH.read_text(encoding="utf-8-sig")
tree = ast.parse(source, filename=str(SOURCE_PATH))
required = {"_trade_offer_is_equipment_snapshot", "_player_trade_item_category_12_6_4"}
functions = {
    node.name: node
    for node in ast.walk(tree)
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name in required
}
assert set(functions) == required
namespace = {}
for name in ("_trade_offer_is_equipment_snapshot", "_player_trade_item_category_12_6_4"):
    module = ast.Module(body=[functions[name]], type_ignores=[])
    ast.fix_missing_locations(module)
    exec(compile(module, str(SOURCE_PATH), "exec"), namespace)

equipment = namespace["_trade_offer_is_equipment_snapshot"]
category = namespace["_player_trade_item_category_12_6_4"]

def item(item_id, canonical_category, **extra):
    snapshot = {
        "item_id": item_id,
        "category": canonical_category,
        # Reproduce the production defect: compatibility defaults exist on
        # stack items even though they are not equipment.
        "durability": 100,
        "max_durability": 100,
    }
    snapshot.update(extra)
    return {"snapshot": snapshot, "is_equipment": equipment(snapshot)}

fixtures = [
    (item(701, "rune"), "rune"),
    (item(601, "material"), "material"),
    (item(101, "potion"), "potion"),
    (item(504, "consumable"), "consumable"),
    (item(9001, "weapon", slot_key="main_hand"), "equipment"),
    (item(9002, "armor", slot_key="boots"), "equipment"),
    (item(9003, "jewelry", slot_key="ring"), "equipment"),
    ({"snapshot": {"item_id": 9004, "category": "", "slot_key": "off_hand", "durability": None, "max_durability": None}, "is_equipment": False}, "equipment"),
]
actual = [category(value) for value, _ in fixtures]
expected = [expected for _, expected in fixtures]
assert actual == expected, (actual, expected)
assert equipment(item(701, "rune")["snapshot"]) is False
assert equipment(item(601, "material")["snapshot"]) is False
assert equipment(item(101, "potion")["snapshot"]) is False
assert equipment(item(504, "consumable")["snapshot"]) is False

counts = {name: actual.count(name) for name in ("equipment", "potion", "material", "rune", "consumable")}
assert counts == {"equipment": 4, "potion": 1, "material": 1, "rune": 1, "consumable": 1}
print(json_line := '{"status":"PASS","fixtures":8,"exclusive_categories":5,"durability_default_regression":"PASS"}')
