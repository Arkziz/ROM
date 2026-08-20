#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import ast
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TARGETS = {
    "db_modules/inventory.py": {"sell_all_trash"},
    "handlers/auction_house.py": {
        "auction_stack_items_kb_v2", "build_auction_stack_price_prompt_v2",
        "build_auction_stack_confirm_text_v2", "auction_buy_lots_kb",
        "auction_sell_items_inline_kb_v1", "auction_buy_lots_inline_kb_v1",
        "auction_my_lots_inline_kb_v1", "auction_unclaimed_items_inline_kb_v1",
    },
    "handlers/city.py": {"build_sell_equipment_confirm_text"},
    "handlers/combat.py": {"build_combat_potion_kb"},
    "handlers/dev.py": {"give_class_reset_sphere"},
    "handlers/inventory.py": {"build_item_button_label"},
    "handlers/player_interaction.py": {
        "_trade_item_kb", "_trade_ux_stack_kb", "_trade_preview_stack_kb_12_6_2",
    },
    "systems/auction_house_system.py": {"create_stack_auction_lot"},
}
LEGACY = re.compile(r"[xX](?=\{[^{}]*(?:quantity|qty|count|amount|added)[^{}]*\})", re.I)
CANONICAL = re.compile(r"×(?=\{[^{}]*(?:quantity|qty|count|amount|added)[^{}]*\})", re.I)

legacy = []
canonical = 0
for rel, names in TARGETS.items():
    source = (ROOT / rel).read_text(encoding="utf-8")
    tree = ast.parse(source)
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name in names:
            text = ast.get_source_segment(source, node) or ""
            if LEGACY.search(text):
                legacy.append((rel, node.name))
            canonical += len(CANONICAL.findall(text))
assert not legacy, legacy
assert canonical >= 20, canonical

# Explicitly preserve out-of-scope formats and existing canonical rune behavior.
daily_compat = (ROOT / "db_modules/daily_compat.py").read_text(encoding="utf-8")
assert "Мале зілля здоров’я x3" in daily_compat
inventory = (ROOT / "handlers/inventory.py").read_text(encoding="utf-8")
assert "hide redundant ×1" in inventory
runes = (ROOT / "handlers/runes.py").read_text(encoding="utf-8")
assert "×3" in runes and "×1" in runes
print(f"[PASS] Stage 17.10.1 item quantity display format; canonical={canonical}")
