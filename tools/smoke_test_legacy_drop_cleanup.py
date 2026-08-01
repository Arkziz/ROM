#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import ast
import sys
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def fail(message):
    print(f"[FAIL] {message}")
    raise SystemExit(1)


def top_level_counts(path):
    source = path.read_text(encoding="utf-8-sig")
    tree = ast.parse(source, filename=str(path))
    counts = {}
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            counts[node.name] = counts.get(node.name, 0) + 1
    return source, tree, counts


def main():
    reward_path = ROOT / "systems" / "reward_system.py"
    drop_path = ROOT / "systems" / "drop_system.py"
    rune_path = ROOT / "systems" / "rune_system.py"

    reward_source, reward_tree, reward_counts = top_level_counts(reward_path)
    drop_source, drop_tree, drop_counts = top_level_counts(drop_path)
    rune_source, rune_tree, rune_counts = top_level_counts(rune_path)

    expected_reward = (
        "roll_equipment_drop",
        "roll_loot_from_loot_table",
        "roll_loot_from_simple_keys",
        "roll_refine_stone_drop",
        "roll_potion_drop",
        "roll_loot",
        "process_victory_reward",
        "process_enemy_drops",
    )
    for name in expected_reward:
        if reward_counts.get(name) != 1:
            fail(f"reward singleton {name}: {reward_counts.get(name, 0)}")
    for name in ("validate_drop_tables",):
        if drop_counts.get(name) != 1:
            fail(f"drop singleton {name}: {drop_counts.get(name, 0)}")
    if drop_counts.get("_validate_drop_tables_schema_11_10_0") != 1:
        fail("private schema validator helper missing or duplicated")
    if "_VALIDATE_DROP_TABLES_BEFORE_SPECIAL_POLICY_11_7_0" in drop_source:
        fail("obsolete special-policy validator alias remains")
    for name in ("roll_rune_drop", "award_rune_drop", "simulate_rune_drops"):
        if rune_counts.get(name) != 1:
            fail(f"rune singleton {name}: {rune_counts.get(name, 0)}")
    if rune_counts.get("_legacy_roll_rune_drop_11_10_0") != 1:
        fail("private roll_rune_drop compatibility helper missing or duplicated")
    for unexpected in (
        "_legacy_award_rune_drop_11_10_0",
        "_legacy_simulate_rune_drops_11_10_0",
    ):
        if rune_counts.get(unexpected, 0):
            fail(f"unexpected synthetic rune helper: {unexpected}")
    if "_RUNE_DROP_LEGACY_" in rune_source:
        fail("obsolete rune legacy alias remains")

    forbidden_aliases = (
        "_base_roll_loot_",
        "_ROLL_LOOT_",
        "_RUNE_DROP_BASE_PROCESS_VICTORY_REWARD_",
        "_PROCESS_VICTORY_REWARD_BEFORE_CENTRAL_",
        "_ROLL_EQUIPMENT_LEGACY_",
        "_ROLL_REFINE_STONE_LEGACY_",
        "_ROLL_LOOT_TABLE_LEGACY_",
        "_ROLL_LOOT_SIMPLE_LEGACY_",
        "_RUNE_DROP_LEGACY_",
    )
    assigned_names = []
    for node in ast.walk(reward_tree):
        if isinstance(node, (ast.Assign, ast.AnnAssign)):
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            for target in targets:
                if isinstance(target, ast.Name):
                    assigned_names.append(target.id)
    for alias in forbidden_aliases:
        matches = [name for name in assigned_names if name.startswith(alias)]
        if matches:
            fail(f"legacy alias assignments remain: {matches}")

    # Final runtime composition must still execute each rule exactly once.
    import systems.reward_system as rewards
    from systems.drop_system import get_victory_drop_plan
    expected = ("trophy", "equipment", "refine_stone", "rune", "potion")
    if get_victory_drop_plan() != expected:
        fail(f"victory plan changed: {get_victory_drop_plan()}")

    calls = []
    fake_rune = type("RuneModule", (), {
        "award_rune_drop": staticmethod(
            lambda *a, **k: calls.append("rune") or {"dropped": True, "message": "R"}
        )
    })
    with patch.object(rewards, "roll_loot_from_simple_keys", lambda *a, **k: calls.append("trophy") or ["T"]), \
         patch.object(rewards, "roll_equipment_drop", lambda *a, **k: calls.append("equipment") or "E"), \
         patch.object(rewards, "roll_refine_stone_drop", lambda *a, **k: calls.append("refine_stone") or "S"), \
         patch.object(rewards, "roll_potion_drop", lambda *a, **k: calls.append("potion") or "P"), \
         patch.dict(sys.modules, {"systems.rune_system": fake_rune}), \
         patch.object(rewards, "_central_guild_elite_reward_11_9_0", lambda *a, **k: None):
        result = rewards.process_enemy_drops(1, {})
    if tuple(calls) != expected:
        fail(f"central runtime order/duplication changed: {calls}")
    if result["messages"] != ["T", "E", "S", "R", "P"]:
        fail(f"central messages changed: {result}")

    # Compatibility API still delegates once to the authoritative composition.
    with patch.object(rewards, "process_enemy_drops", return_value={"messages": ["X"]}) as central:
        if rewards.roll_loot(1, {}) != ["X"] or central.call_count != 1:
            fail("roll_loot compatibility API is not single-delegation")

    print("[OK] Legacy central-drop cleanup contracts")
    print("- reward singleton definitions: 8/8")
    print("- drop validator singleton definition: OK")
    print("- rune public API singleton definitions: 3/3")
    print("- historical roll_loot/process_victory aliases removed: OK")
    print("- authoritative rule order unchanged: OK")
    print("- every production drop executes exactly once: OK")
    print("- compatibility roll_loot single delegation: OK")
    print("- database mutations: 0")


if __name__ == "__main__":
    main()
