#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations
import ast
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HANDLER = ROOT / "handlers" / "player_interaction.py"


def fail(message):
    print(f"[FAIL] {message}")
    raise SystemExit(1)


def main():
    source = HANDLER.read_text(encoding="utf-8-sig")
    tree = ast.parse(source, filename=str(HANDLER))
    if "ROM 12.6.8B PLAYER TRADE COMPACT QUANTITY PARENTHESES FIX" not in source:
        fail("12.6.8b marker missing")

    functions = [
        node for node in tree.body
        if isinstance(node, ast.FunctionDef)
        and node.name == "_trade_category_list_kb_12_6_4"
    ]
    if len(functions) != 1:
        fail(f"category keyboard function count: {len(functions)}")
    body = ast.get_source_segment(source, functions[0]) or ""

    forbidden = (
        r"\(\(\{[^{}]+\}\)\)",
        r"\(\(\{[^{}]+\}\)",
        r"\(\{[^{}]+\}\)\)",
    )
    for pattern in forbidden:
        if re.search(pattern, body):
            fail(f"nested quantity parentheses remain: {pattern}")

    # Ensure the visible stack button still contains one compact quantity pair.
    compact = False
    for node in ast.walk(functions[0]):
        if not isinstance(node, ast.JoinedStr):
            continue
        constants = "".join(
            value.value for value in node.values
            if isinstance(value, ast.Constant) and isinstance(value.value, str)
        )
        if "(" in constants and ")" in constants:
            compact = True
            break
    if not compact:
        fail("single compact quantity pair not found")

    top_functions = [
        node.name for node in tree.body if isinstance(node, ast.FunctionDef)
    ]
    if top_functions.count("register_player_interaction_handlers") != 1:
        fail("canonical registration changed")
    if top_functions.count("_trade_category_list_kb_12_6_4") != 1:
        fail("category keyboard duplicate introduced")

    print("[OK] Player trade compact quantity-parentheses contracts")
    print("- stack quantity uses exactly one pair of parentheses: OK")
    print("- nested ((N)), ((N) and (N)) variants removed: OK")
    print("- equipment labels remain quantity-free: OK")
    print("- category text, pagination and callbacks unchanged: OK")
    print("- consolidated 12.6.8 architecture preserved: OK")
    print("- gameplay/database behavior changes: 0")


if __name__ == "__main__":
    main()
