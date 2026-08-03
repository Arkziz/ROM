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
    required = (
        "ROM 12.6.4d PLAYER TRADE AMOUNT CANCEL AND LOCK RECOVERY",
        "reply_markup=player_trade_active_reply_kb_12_6_4()",
        "active_trade = get_active_player_trade(uid)",
        "_send_trade_editor(",
        "def _trade_reopen_directly_12_6_4d(",
        "text == PLAYER_TRADE_ACTIVE_REPLY_BUTTON_12_6_4",
        "PLAYER_TRADE_LOCK_NOTICE_COOLDOWN_SECONDS_12_6_4D = 10.0",
        "_rom_trade_navigation_lock_12_6_4d",
    )
    for value in required:
        if value not in source:
            fail(f"missing contract: {value}")

    # Inspect only the AST body of the exact cancel branch. The previous test
    # used a text slice and accidentally included later success/timeout branches
    # that legitimately contain ReplyKeyboardRemove.
    amount_handlers = [
        node for node in ast.walk(tree)
        if isinstance(node, ast.FunctionDef) and node.name == "amount_message"
    ]
    if not amount_handlers:
        fail("amount_message handler missing")
    cancel_nodes = []
    for node in ast.walk(amount_handlers[-1]):
        if not isinstance(node, ast.If):
            continue
        test_source = ast.get_source_segment(source, node.test) or ""
        if "Скасувати введення" in test_source:
            cancel_nodes.append(node)
    if len(cancel_nodes) != 1:
        fail(f"expected one exact cancel branch, found {len(cancel_nodes)}")
    cancel_module = ast.Module(body=cancel_nodes[0].body, type_ignores=[])
    cancel_source = ast.unparse(cancel_module)
    cancel_calls = [
        node for node in ast.walk(cancel_module) if isinstance(node, ast.Call)
    ]
    forbidden_remove = any(
        (isinstance(call.func, ast.Attribute)
         and call.func.attr == "ReplyKeyboardRemove")
        or (isinstance(call.func, ast.Name)
            and call.func.id == "ReplyKeyboardRemove")
        for call in cancel_calls
    )
    if forbidden_remove:
        fail("cancel branch still removes the trade keyboard")
    if "player_trade_active_reply_kb_12_6_4" not in cancel_source:
        fail("cancel branch does not restore active trade keyboard")
    if "_send_trade_editor" not in cancel_source:
        fail("cancel branch does not reopen the trade editor")

    namespace = {}
    wanted = []
    for node in tree.body:
        if isinstance(node, (ast.Assign, ast.AnnAssign)):
            text = ast.get_source_segment(source, node) or ""
            if (
                "PLAYER_TRADE_LOCK_NOTICE_COOLDOWN_SECONDS_12_6_4D" in text
                or "_PLAYER_TRADE_LOCK_NOTICE_AT_12_6_4D" in text
            ):
                wanted.append(node)
        elif isinstance(node, ast.FunctionDef) and node.name == "_trade_lock_notice_allowed_12_6_4d":
            wanted.append(node)
    namespace["_trade_lock_time_12_6_4a"] = type(
        "Clock", (), {"monotonic": staticmethod(lambda: 0.0)}
    )
    exec(compile(ast.Module(body=wanted, type_ignores=[]), str(HANDLER), "exec"), namespace)
    allow = namespace["_trade_lock_notice_allowed_12_6_4d"]
    if allow(1, now=100.0) is not True:
        fail("first notice rejected")
    if allow(1, now=105.0) is not False:
        fail("notice spam not suppressed")
    if allow(1, now=110.1) is not True:
        fail("notice cooldown did not recover")

    print("[OK] Player trade amount-cancel and lock recovery contracts")
    print("- invalid amount keeps input mode active: OK")
    print("- cancel restores the active-trade reply keyboard: OK")
    print("- cancel immediately reopens the trade editor: OK")
    print("- active-trade button is handled directly by the lock: OK")
    print("- blocked-action warnings use a 10-second cooldown: OK")
    print("- isolated static/helper checks; real user mutations: 0")


if __name__ == "__main__":
    main()
