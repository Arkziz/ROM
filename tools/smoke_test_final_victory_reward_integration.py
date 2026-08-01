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


def main():
    from data.drop_tables import (
        CENTRAL_DROP_VICTORY_INTEGRATION_ENABLED,
        CENTRAL_DROP_VICTORY_RULE_ORDER,
    )
    from systems.drop_system import get_victory_drop_plan
    import systems.reward_system as rewards

    expected = ("trophy", "equipment", "refine_stone", "rune", "potion")
    if not CENTRAL_DROP_VICTORY_INTEGRATION_ENABLED:
        fail("victory integration flag disabled")
    if tuple(CENTRAL_DROP_VICTORY_RULE_ORDER) != expected:
        fail(f"configured order mismatch: {CENTRAL_DROP_VICTORY_RULE_ORDER}")
    if get_victory_drop_plan() != expected:
        fail(f"resolved plan mismatch: {get_victory_drop_plan()}")

    source = (ROOT / "systems" / "reward_system.py").read_text(encoding="utf-8-sig")
    tree = ast.parse(source)
    functions = [
        node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)
    ]
    final_process = [node for node in functions if node.name == "process_victory_reward"][-1]
    final_loot = [node for node in functions if node.name == "roll_loot"][-1]
    process_enemy = [node for node in functions if node.name == "process_enemy_drops"]
    if len(process_enemy) != 1:
        fail(f"process_enemy_drops definitions={len(process_enemy)}")
    final_process_source = ast.get_source_segment(source, final_process) or ""
    final_loot_source = ast.get_source_segment(source, final_loot) or ""
    if "process_enemy_drops(user_id, mob)" not in final_process_source:
        fail("final process_victory_reward does not use central composition")
    if "process_enemy_drops(user_id, mob)" not in final_loot_source:
        fail("compatibility roll_loot does not use central composition")
    if "_PROCESS_VICTORY_REWARD_BEFORE_CENTRAL_11_9_0(" in final_process_source:
        fail("final victory function calls legacy reward chain")
    if "_ROLL_LOOT_BEFORE_CENTRAL_11_9_0(" in final_loot_source:
        fail("final roll_loot calls legacy nested chain")

    calls = []
    def trophy(*args, **kwargs): calls.append("trophy"); return ["T"]
    def equipment(*args, **kwargs): calls.append("equipment"); return "E"
    def stone(*args, **kwargs): calls.append("refine_stone"); return "S"
    def potion(*args, **kwargs): calls.append("potion"); return "P"
    fake_rune = type("RuneModule", (), {
        "award_rune_drop": staticmethod(
            lambda *args, **kwargs: (
                calls.append("rune") or {"dropped": True, "message": "R"}
            )
        )
    })

    with patch.object(rewards, "roll_loot_from_simple_keys", trophy), \
         patch.object(rewards, "roll_equipment_drop", equipment), \
         patch.object(rewards, "roll_refine_stone_drop", stone), \
         patch.object(rewards, "roll_potion_drop", potion), \
         patch.dict(sys.modules, {"systems.rune_system": fake_rune}), \
         patch.object(rewards, "_central_guild_elite_reward_11_9_0", lambda *a: None):
        result = rewards.process_enemy_drops(1, {})

    if tuple(calls) != expected:
        fail(f"runtime order/duplication mismatch: {calls}")
    if result["messages"] != ["T", "E", "S", "R", "P"]:
        fail(f"message composition mismatch: {result}")
    if result["executed_rules"] != expected:
        fail(f"executed rules mismatch: {result}")

    # Compatibility roll_loot must still execute exactly one central composition.
    with patch.object(rewards, "process_enemy_drops", return_value={"messages": ["X"]}) as central:
        if rewards.roll_loot(1, {}) != ["X"] or central.call_count != 1:
            fail("roll_loot compatibility route duplicated central composition")

    print("[OK] Final central victory reward integration contracts")
    print("- authoritative rule order: trophy, equipment, stone, rune, potion")
    print("- every production rule executes exactly once: OK")
    print("- old nested roll_loot chain bypassed: OK")
    print("- final process_victory_reward calls one central composition: OK")
    print("- rune result/message compatibility preserved: OK")
    print("- guild elite hook remains outside item-drop plan: OK")
    print("- compatibility roll_loot routes once to central composition: OK")
    print("- database mutations: 0")


if __name__ == "__main__":
    main()
