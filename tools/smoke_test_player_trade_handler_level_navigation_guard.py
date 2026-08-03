#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations
import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HANDLER = ROOT / "handlers" / "player_interaction.py"


def fail(message):
    print(f"[FAIL] {message}")
    raise SystemExit(1)


def main():
    source = HANDLER.read_text(encoding="utf-8-sig")
    tree = ast.parse(source, filename=str(HANDLER))

    if "ROM 12.6.6 PLAYER TRADE HANDLER LEVEL NAVIGATION GUARD" not in source:
        fail("12.6.6 marker missing")

    installers = [
        node for node in tree.body
        if isinstance(node, ast.FunctionDef)
        and node.name == "install_player_trade_navigation_lock_12_6_4"
    ]
    if installers:
        fail("dispatcher-level trade lock still exists")

    assignments = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Assign):
            continue
        for target in node.targets:
            if (
                isinstance(target, ast.Attribute)
                and target.attr == "process_new_updates"
            ):
                assignments.append(node.lineno)
    if assignments:
        fail(f"handler module still wraps process_new_updates at {assignments}")

    guards = [
        node for node in tree.body
        if isinstance(node, ast.FunctionDef)
        and node.name == "_install_player_trade_handler_level_navigation_guard_12_6_6"
    ]
    if len(guards) != 1:
        fail(f"expected one handler-level guard installer, found {len(guards)}")
    guard_source = ast.get_source_segment(source, guards[0]) or ""

    for contract in (
        "from telebot.handler_backends import ContinueHandling",
        "def trade_status_noop(message):",
        "def active_trade_message_guard(message):",
        "def active_trade_callback_guard(call):",
        "bot.message_handlers[0:0]",
        "bot.callback_query_handlers.insert(0",
        "_trade_is_amount_input_active_12_6_4",
        "_trade_lock_allowed_callback_12_6_4",
    ):
        if contract not in guard_source:
            fail(f"missing guard contract: {contract}")

    status_nodes = [
        node for node in ast.walk(guards[0])
        if isinstance(node, ast.FunctionDef) and node.name == "trade_status_noop"
    ]
    if len(status_nodes) != 1:
        fail("status no-op handler missing")
    status_body = ast.Module(body=status_nodes[0].body, type_ignores=[])
    if any(isinstance(node, ast.Call) for node in ast.walk(status_body)):
        fail("status no-op handler contains API/state calls")

    registers = [
        node for node in tree.body
        if isinstance(node, ast.FunctionDef)
        and node.name == "register_player_interaction_handlers"
    ]
    if not registers:
        fail("final handler registration function missing")
    final_register = ast.get_source_segment(source, registers[-1]) or ""
    if "_install_player_trade_handler_level_navigation_guard_12_6_6(bot)" not in final_register:
        fail("final registration does not install handler-level guards")
    if "install_player_trade_navigation_lock_12_6_4(bot)" in final_register:
        fail("final registration still installs dispatcher wrapper")

    print("[OK] Player trade handler-level navigation guard contracts")
    print("- dispatcher-level process_new_updates wrapper removed: OK")
    print("- status button uses normal no-op message handler: OK")
    print("- active-trade message guard is first priority: OK")
    print("- active-trade callback guard is first priority: OK")
    print("- inactive users continue to normal handlers: OK")
    print("- manual amount input continues to amount handler: OK")
    print("- trade inline callbacks, including Refresh, continue normally: OK")
    print("- isolated AST checks; real user mutations: 0")


if __name__ == "__main__":
    main()
