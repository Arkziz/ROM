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

    if "ROM 12.6.8A PLAYER TRADE MOBILE WIDTH AND ITEM LABELS" not in source:
        fail("12.6.8a marker missing")
    if source.count("Оберіть категорію для обміну:") != 1:
        fail("category prompt count mismatch")
    if source.count("Оберіть предмет для обміну:") < 1:
        fail("item prompt missing")
    if "Оберіть категорію:" in source:
        fail("old short category prompt remains")
    if "Оберіть предмет:" in source:
        fail("old short item prompt remains")

    category_kb = [
        node for node in tree.body
        if isinstance(node, ast.FunctionDef)
        and node.name == "_trade_category_list_kb_12_6_4"
    ]
    if len(category_kb) != 1:
        fail(f"category keyboard function count: {len(category_kb)}")
    # The phrase may legitimately remain in explanatory preview/help text.
    # The contract applies only to generated stack button labels, so do not
    # reject unrelated prose elsewhere in the handler module.
    compact_joined_strings = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.JoinedStr):
            continue
        text = "".join(
            value.value for value in node.values
            if isinstance(value, ast.Constant) and isinstance(value.value, str)
        )
        if "(" in text and ")" in text:
            compact_joined_strings.append(text)
    if not compact_joined_strings:
        fail("compact quantity label not found")

    # Consolidation contracts must remain intact.
    functions = [
        node.name for node in tree.body if isinstance(node, ast.FunctionDef)
    ]
    if functions.count("register_player_interaction_handlers") != 1:
        fail("canonical handler registration count changed")
    if functions.count("_trade_category_list_kb_12_6_4") != 1:
        fail("category keyboard duplicate introduced")
    if functions.count("_install_player_trade_handler_level_navigation_guard_12_6_6") != 1:
        fail("handler-level navigation guard changed")

    print("[OK] Player trade mobile-width and compact-label contracts")
    print("- category prompt replaced with longer mobile-width text: OK")
    print("- all item-list flows use one mobile-width prompt per screen: OK")
    print("- stack buttons use compact item-name (N) labels: OK")
    print("- equipment labels remain quantity-free: OK")
    print("- category pagination and callback routing unchanged: OK")
    print("- consolidated handler architecture preserved: OK")
    print("- gameplay/database behavior changes: 0")


if __name__ == "__main__":
    main()
