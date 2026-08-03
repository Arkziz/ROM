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


def final_function_source(source, tree, name):
    functions = [
        node for node in tree.body
        if isinstance(node, ast.FunctionDef) and node.name == name
    ]
    if not functions:
        fail(f"missing function: {name}")
    return ast.get_source_segment(source, functions[-1]) or ""


def main():
    source = HANDLER.read_text(encoding="utf-8-sig")
    tree = ast.parse(source, filename=str(HANDLER))
    if "ROM 12.6.4c PLAYER TRADE CONTEXTUAL NAVIGATION CLEANUP" not in source:
        fail("hotfix marker is missing")

    category_source = final_function_source(
        source, tree, "_trade_category_list_kb_12_6_4")
    if "✏️ Моя пропозиція" in category_source:
        fail("My Offer button remains in category item list")
    for required in (
        "⬅️ Попередні", "➡️ Наступні", "🔙 До категорій", "🔙 До обміну",
        "pi:tec:view:", "pi:tec:list:",
    ):
        if required not in category_source:
            fail(f"category navigation regression: {required}")

    mine_source = final_function_source(source, tree, "_trade_ux_mine_kb")
    if "➕ Додати предмет" in mine_source:
        fail("Add Item button remains in empty My Offer keyboard")
    for required in (
        "pi:teux:gold:", "pi:teux:edit:", "🔙 До обміну",
    ):
        if required not in mine_source:
            fail(f"My Offer navigation regression: {required}")

    print("[OK] Player trade contextual navigation cleanup contracts")
    print("- My Offer removed from category item lists: OK")
    print("- pagination and category/back navigation preserved: OK")
    print("- empty My Offer has no Add Item shortcut: OK")
    print("- existing item and gold edit buttons preserved: OK")
    print("- isolated static checks; real user mutations: 0")


if __name__ == "__main__":
    main()
