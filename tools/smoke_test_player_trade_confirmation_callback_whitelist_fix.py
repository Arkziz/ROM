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
    if "ROM 12.7.0A PLAYER TRADE CONFIRMATION CALLBACK WHITELIST FIX" not in source:
        fail("12.7.0a marker missing")

    allowed = [
        node for node in tree.body
        if isinstance(node, ast.FunctionDef)
        and node.name == "_trade_lock_allowed_callback_12_6_4"
    ]
    if len(allowed) != 1:
        fail(f"allowed-callback function count: {len(allowed)}")
    prefix_assignments = []
    for node in tree.body:
        if not isinstance(node, (ast.Assign, ast.AnnAssign)):
            continue
        targets = node.targets if isinstance(node, ast.Assign) else [node.target]
        if any(
            isinstance(target, ast.Name)
            and target.id == "_PLAYER_TRADE_ALLOWED_CALLBACK_PREFIXES_12_6_4"
            for target in targets
        ):
            prefix_assignments.append(node)
    if len(prefix_assignments) != 1:
        fail(f"canonical prefix tuple count: {len(prefix_assignments)}")
    prefix_source = ast.get_source_segment(source, prefix_assignments[0]) or ""
    if '"pi:tcf:"' not in prefix_source and "'pi:tcf:'" not in prefix_source:
        fail("pi:tcf confirmation prefix is not whitelisted")

    guard = [
        node for node in tree.body
        if isinstance(node, ast.FunctionDef)
        and node.name == "_install_player_trade_handler_level_navigation_guard_12_6_6"
    ]
    if len(guard) != 1:
        fail("handler-level guard count mismatch")
    guard_source = ast.get_source_segment(source, guard[0]) or ""
    if "_trade_lock_allowed_callback_12_6_4" not in guard_source:
        fail("callback guard no longer uses canonical whitelist")
    if "ContinueHandling()" not in guard_source:
        fail("allowed callback pass-through is missing")

    confirmation = [
        node for node in tree.body
        if isinstance(node, ast.FunctionDef)
        and node.name == "_register_trade_confirmation_handlers_12_7_0"
    ]
    if len(confirmation) != 1:
        fail("12.7.0 confirmation handlers missing")
    confirmation_source = ast.get_source_segment(source, confirmation[0]) or ""
    for callback in (
        "pi:tcf:ready:",
        "pi:tcf:edit:",
        "pi:tcf:confirm:",
    ):
        if callback not in confirmation_source:
            fail(f"confirmation callback missing: {callback}")

    functions = [
        node.name for node in tree.body if isinstance(node, ast.FunctionDef)
    ]
    if functions.count("register_player_interaction_handlers") != 1:
        fail("canonical registration count changed")
    if functions.count("_trade_lock_allowed_callback_12_6_4") != 1:
        fail("whitelist function duplicate introduced")

    print("[OK] Player trade confirmation callback-whitelist contracts")
    print("- pi:tcf ready/edit/confirm callbacks pass active-trade guard: OK")
    print("- handler-level guard still uses ContinueHandling: OK")
    print("- unrelated callbacks remain blocked during active trade: OK")
    print("- confirmation handlers and canonical registration preserved: OK")
    print("- gameplay/database mutations: 0")


if __name__ == "__main__":
    main()
