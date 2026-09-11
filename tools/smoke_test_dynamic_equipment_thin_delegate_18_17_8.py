#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import ast
import inspect
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import db_modules.generated_equipment as canonical
from systems import dynamic_equipment_system as compatibility

EXPECTED_ALL = [
    "init_dynamic_equipment_system",
    "get_dynamic_weapon_name",
    "get_dynamic_armor_name",
    "generate_dynamic_equipment_stats",
    "apply_armor_type_defense_profile_to_stats",
    "get_dynamic_sell_price",
]
DELEGATES = (
    "add_primary_stat_to_stats",
    "add_stat_value",
    "apply_armor_type_defense_profile_to_stats",
    "apply_armor_type_primary_stat_profile_to_stats",
    "clear_primary_stat_bonuses",
    "generate_dynamic_equipment_stats",
    "get_dynamic_armor_name",
    "get_dynamic_sell_price",
    "get_dynamic_stat_value",
    "get_dynamic_weapon_name",
    "get_existing_primary_stat_budget",
    "get_profile_for_generated_item",
    "get_random_main_hand_profile",
    "get_random_off_hand_profile",
    "init_dynamic_equipment_system",
    "normalize_equipment_restriction_value",
    "pick_weighted_stat",
)

assert compatibility.__all__ == EXPECTED_ALL
for name in DELEGATES:
    left = getattr(canonical, name)
    right = getattr(compatibility, name)
    assert callable(right)
    assert inspect.signature(left) == inspect.signature(right), (name, inspect.signature(left), inspect.signature(right))

source = (ROOT / "systems/dynamic_equipment_system.py").read_text(encoding="utf-8-sig")
tree = ast.parse(source)
function_names = {node.name for node in tree.body if isinstance(node, ast.FunctionDef)}
assert set(DELEGATES) <= function_names
assert "_canonical" in function_names
assert len([node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "_canonical"]) == 1

for forbidden in (
    "sqlite3", "cursor", "conn", "INSERT ", "UPDATE ", "DELETE ",
    "CREATE TABLE", "ALTER TABLE", "random.", "ARMOR_PRIMARY_STAT_PROFILES =",
    "ARMOR_DEFENSE_DISTRIBUTION_PROFILES =", "DYNAMIC_STAT_MULTIPLIERS =",
    "create_generated_equipment_item", "allocate_generated_item_id",
):
    assert forbidden not in source, forbidden

# Every compatibility function except the lazy loader must contain a canonical call.
for node in tree.body:
    if isinstance(node, ast.FunctionDef) and node.name in DELEGATES:
        calls = [item for item in ast.walk(node) if isinstance(item, ast.Call)]
        assert any(isinstance(call.func, ast.Name) and call.func.id == "_canonical" for call in calls), node.name

# The generator must not import the compatibility module, preventing a cycle.
generator_source = (ROOT / "db_modules/generated_equipment.py").read_text(encoding="utf-8-sig")
assert "systems.dynamic_equipment_system" not in generator_source
assert "from systems import dynamic_equipment_system" not in generator_source

print("[PASS] Stage 18.17.8 dynamic equipment thin compatibility delegate")
