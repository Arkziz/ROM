# -*- coding: utf-8 -*-
import ast
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from data.mobs import get_mobs_for_location
from systems.combat_system import build_mob, get_available_mobs

PRIMARY_FIELDS = tuple(
    f"{stat}_{bound}"
    for stat in ("str", "dex", "int", "wis", "sta")
    for bound in ("min", "max")
)

player_level = 7
location_id = "start_path"
available = get_available_mobs(player_level, location_id)
assert available, "canonical ordinary templates unavailable"
base = dict(available[0])
event = {
    "name": "🧪 Нестабільний слизень",
    "attack_type": "physical",
    "level_policy": "player_level",
    "primary_stat_profile": "normal_physical",
    "min_gold": 0,
    "max_gold": 0,
    "loot_chance": 0,
    "trash_items": [],
}
runtime = dict(base)
runtime.update({
    "name": event["name"],
    "attack_type": event["attack_type"],
    "level": player_level,
    "location_id": location_id,
})
assert all(field in runtime for field in PRIMARY_FIELDS), runtime
assert all(runtime[field] == base[field] for field in PRIMARY_FIELDS)
assert runtime["min_gold"] == base["min_gold"]
assert runtime["max_gold"] == base["max_gold"]
assert runtime["loot_chance"] == base["loot_chance"]
assert runtime["trash_items"] == base["trash_items"]

state = random.getstate()
try:
    random.seed(18294)
    mob = build_mob(runtime)
finally:
    random.setstate(state)
assert mob["name"] == "🧪 Нестабільний слизень", mob
assert mob["level"] == player_level, mob
assert mob["location_id"] == location_id, mob
assert mob["attack_type"] == "physical", mob
assert mob["hp"] > 0 and mob["attack"] > 0
assert mob["pdef"] > 0 and mob["mdef"] > 0

combat_source = (ROOT / "systems" / "combat_system.py").read_text(encoding="utf-8")
tree = ast.parse(combat_source)
factories = [node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef) and node.name == "_build_normal_mob"]
assert len(factories) == 1
factory_source = ast.get_source_segment(combat_source, factories[0]) or ""
assert "runtime_template = dict(base_template)" in factory_source
assert '"name": event_template["name"]' in factory_source
assert '"level": int(player_level)' in factory_source
assert '"location_id": location_id' in factory_source
assert "runtime_template.update(event_template)" not in factory_source
for field in PRIMARY_FIELDS:
    assert field not in event, field

# Shared canonical templates remain unchanged.
assert get_mobs_for_location(location_id)[0] != runtime or get_mobs_for_location(location_id)[0]["name"] != event["name"]
print("TEST_EVENT_MOB_PRIMARY_STAT_TEMPLATE_18_29_4L_OK")
