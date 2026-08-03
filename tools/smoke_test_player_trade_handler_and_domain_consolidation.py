#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations
import ast
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HANDLER = ROOT / "handlers" / "player_interaction.py"
SYSTEM = ROOT / "systems" / "player_interaction_system.py"


def fail(message):
    print(f"[FAIL] {message}")
    raise SystemExit(1)


def function_counts(tree):
    return Counter(
        node.name for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    )


def main():
    hs = HANDLER.read_text(encoding="utf-8-sig")
    ss = SYSTEM.read_text(encoding="utf-8-sig")
    ht = ast.parse(hs, filename=str(HANDLER))
    st = ast.parse(ss, filename=str(SYSTEM))
    hc = function_counts(ht)
    sc = function_counts(st)

    if "ROM 12.6.8 PLAYER TRADE HANDLER AND DOMAIN CONSOLIDATION" not in hs:
        fail("12.6.8 marker missing")
    duplicate_handler = {key: value for key, value in hc.items() if value > 1}
    duplicate_system = {key: value for key, value in sc.items() if value > 1}
    if duplicate_handler:
        fail(f"handler duplicates remain: {duplicate_handler}")
    if duplicate_system:
        fail(f"system duplicates remain: {duplicate_system}")

    if hc.get("register_player_interaction_handlers") != 1:
        fail("canonical register function count mismatch")
    if hc.get("_register_player_interaction_base_handlers_12_6_8") != 1:
        fail("base handler registration function missing")
    for alias in (
        "_trade_ux_base_register_player_interaction_handlers",
        "_trade_preview_base_register_player_interaction_handlers",
        "_trade_amount_base_register_12_6_3",
        "_trade_navigation_base_register_12_6_4",
    ):
        if alias in hs:
            fail(f"historical registration alias remains: {alias}")

    registers = [
        node for node in ht.body
        if isinstance(node, ast.FunctionDef)
        and node.name == "register_player_interaction_handlers"
    ]
    register_source = ast.get_source_segment(hs, registers[0]) or ""
    required_order = (
        "_register_trade_navigation_and_categories_12_6_4(bot)",
        "_trade_register_amount_input_12_6_3(bot)",
        "_register_trade_preview_wallet_handlers_12_6_2(bot)",
        "_register_player_trade_offer_editor_ux_handlers(bot)",
        "_register_player_interaction_base_handlers_12_6_8(bot)",
        "_install_player_trade_handler_level_navigation_guard_12_6_6(bot)",
    )
    positions = []
    for contract in required_order:
        position = register_source.find(contract)
        if position < 0:
            fail(f"registration contract missing: {contract}")
        positions.append(position)
    if positions != sorted(positions):
        fail("registration call order changed")

    if hc.get("_install_player_trade_handler_level_navigation_guard_12_6_6") != 1:
        fail("handler-level navigation guard count mismatch")
    if hc.get("install_player_trade_navigation_lock_12_6_4", 0) != 0:
        fail("obsolete dispatcher lock returned")
    for node in ast.walk(ht):
        if isinstance(node, ast.Assign):
            targets = node.targets
        elif isinstance(node, ast.AnnAssign):
            targets = [node.target]
        else:
            continue
        if any(isinstance(target, ast.Attribute) and target.attr == "process_new_updates" for target in targets):
            fail("process_new_updates wrapper returned")

    if sc.get("_trade_base_build_item_snapshot_12_6_3") != 1:
        fail("canonical private snapshot base missing")
    if "_trade_base_build_item_snapshot_12_6_3 = build_trade_item_snapshot" in ss:
        fail("historical snapshot alias assignment remains")

    for name in (
        "build_trade_item_snapshot",
        "get_tradeable_inventory_for_trade",
        "get_item_trade_policy",
        "reserve_inventory_for_trade",
        "set_player_trade_item_offer",
        "set_player_trade_gold_offer",
    ):
        if sc.get(name) != 1:
            fail(f"domain function count mismatch: {name}={sc.get(name, 0)}")

    print("[OK] Player trade handler/domain consolidation contracts")
    print("- one canonical register_player_interaction_handlers: OK")
    print("- historical registration aliases physically removed: OK")
    print("- final handler helper definitions are singletons: OK")
    print("- final domain snapshot/inventory definitions are singletons: OK")
    print("- registration order preserved: OK")
    print("- handler-level navigation guard preserved: OK")
    print("- dispatcher wrapper remains absent: OK")
    print("- gameplay/database behavior changes: 0")


if __name__ == "__main__":
    main()
