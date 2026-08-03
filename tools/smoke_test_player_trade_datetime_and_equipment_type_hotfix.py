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
    datetime_imported = False
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module == "datetime":
            if any(alias.name == "datetime" for alias in node.names):
                datetime_imported = True
                break
    if not datetime_imported:
        fail("datetime class import is missing")
    required = (
        "ROM 12.6.3a PLAYER TRADE DATETIME AND EQUIPMENT TYPE HOTFIX",
        "def _trade_add_list_display_name_12_6_3a(",
        "_TRADE_ARMOR_SLOT_KEYS_12_6_3A",
        "typed_suffix = f\"[{armor_label}]\"",
        "callback_data=f\"pi:tep:view:",
        "datetime.now().timestamp()",
    )
    for contract in required:
        if contract not in source:
            fail(f"missing contract: {contract}")
    namespace = {"ARMOR_TYPE_LABELS": {"cloth": "Тканина"}}
    module = ast.parse(source, filename=str(HANDLER))
    wanted = []
    for node in module.body:
        if isinstance(node, (ast.Assign, ast.AnnAssign)):
            text = ast.get_source_segment(source, node) or ""
            if "_TRADE_ARMOR_SLOT_KEYS_12_6_3A" in text:
                wanted.append(node)
        elif isinstance(node, ast.FunctionDef) and node.name == "_trade_add_list_display_name_12_6_3a":
            wanted.append(node)
    exec(compile(ast.Module(body=wanted, type_ignores=[]), str(HANDLER), "exec"), namespace)
    build = namespace["_trade_add_list_display_name_12_6_3a"]
    armor = build({
        "item_name": "⚪️ Наплічники 8 рівня",
        "slot_key": "shoulders", "armor_type": "cloth", "item_level": 8,
    })
    if armor != "⚪️ Наплічники [Тканина] 8 рівня":
        fail(f"wrong armor display: {armor}")
    duplicate = build({
        "item_name": "⚪️ Наплічники [Тканина] 8 рівня",
        "slot_key": "shoulders", "armor_type": "cloth", "item_level": 8,
    })
    if duplicate.count("[Тканина]") != 1:
        fail(f"duplicated armor type: {duplicate}")
    weapon = build({
        "item_name": "🔵 Дворучний посох 8 рівня",
        "slot_key": "main_hand", "armor_type": "", "item_level": 8,
    })
    if weapon != "🔵 Дворучний посох 8 рівня":
        fail(f"weapon name changed unexpectedly: {weapon}")
    print("[OK] Player trade datetime and equipment type hotfix contracts")
    print("- datetime import for manual gold/item input: OK")
    print("- armor type in square brackets in add list: OK")
    print("- duplicate armor type prevention: OK")
    print("- preview callback routing preserved: OK")
    print("- isolated static/runtime helper checks; real user mutations: 0")


if __name__ == "__main__":
    main()
