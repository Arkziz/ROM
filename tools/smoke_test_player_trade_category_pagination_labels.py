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
        "ROM 12.6.4b PLAYER TRADE CATEGORY PAGINATION LABELS",
        '"⬅️ Попередні"',
        '"➡️ Наступні"',
        'callback_data=f"pi:tec:list:{trade_id}:{category}:{page-1}"',
        'callback_data=f"pi:tec:list:{trade_id}:{category}:{page+1}"',
        '"🔙 До категорій"',
        '"✏️ Моя пропозиція"',
        '"🔙 До обміну"',
    )
    for value in required:
        if value not in source:
            fail(f"missing contract: {value}")

    formatters = [
        node for node in tree.body
        if isinstance(node, ast.FunctionDef)
        and node.name == "_trade_category_list_kb_12_6_4"
    ]
    if not formatters:
        fail("final category keyboard function is missing")
    final_source = ast.get_source_segment(source, formatters[-1]) or ""
    if 'InlineKeyboardButton("⬅️",' in final_source:
        fail("final keyboard still contains icon-only previous button")
    if 'InlineKeyboardButton("➡️",' in final_source:
        fail("final keyboard still contains icon-only next button")

    previous_index = final_source.find('"⬅️ Попередні"')
    next_index = final_source.find('"➡️ Наступні"')
    categories_index = final_source.find('"🔙 До категорій"')
    if not (0 <= previous_index < categories_index and 0 <= next_index < categories_index):
        fail("pagination buttons are not placed above category navigation")

    print("[OK] Player trade category pagination label contracts")
    print("- previous button uses ‘⬅️ Попередні’: OK")
    print("- next button uses ‘➡️ Наступні’: OK")
    print("- category and page callback context preserved: OK")
    print("- navigation buttons remain above category/back actions: OK")
    print("- isolated static checks; real user mutations: 0")


if __name__ == "__main__":
    main()
