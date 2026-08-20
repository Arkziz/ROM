#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PREVIOUS = "⬅️ Назад"
NEXT = "➡️ Далі"
FILES = (
    "handlers/auction_house.py",
    "handlers/player_interaction.py",
    "handlers/runes.py",
    "handlers/guild.py",
)
PREFIXES = (
    "ah_sell_page:", "ah_buy_page:", "ah_my_page:", "ah_uncl_page:",
    "ah_sale_page:", "ah_buy2_page:", "ah_search_page:", "ah_hist:",
    "pi:list:", "pi:te:list:", "pi:teux:list:", "pi:tec:list:",
    "rm:home:", "rf:home:",
)

def call_name(node):
    if isinstance(node.func, ast.Attribute): return node.func.attr
    if isinstance(node.func, ast.Name): return node.func.id
    return ""

def arg(call, keyword, position):
    for item in call.keywords:
        if item.arg == keyword: return item.value
    return call.args[position] if len(call.args) > position else None

def literal(node):
    return node.value if isinstance(node, ast.Constant) and isinstance(node.value, str) else None

previous_count = 0
next_count = 0
for rel in FILES:
    source = (ROOT / rel).read_text(encoding="utf-8")
    tree = ast.parse(source)
    if rel != "handlers/guild.py":
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call) or call_name(node) != "InlineKeyboardButton":
                continue
            text_node = arg(node, "text", 0)
            callback_node = arg(node, "callback_data", 1)
            callback = ast.get_source_segment(source, callback_node) or ""
            if not any(prefix in callback for prefix in PREFIXES):
                continue
            label = literal(text_node)
            compact = callback.replace(" ", "")
            if "-1" in compact:
                assert label == PREVIOUS, (rel, node.lineno, label, callback)
                previous_count += 1
            elif "+1" in compact:
                assert label == NEXT, (rel, node.lineno, label, callback)
                next_count += 1

assert previous_count >= 10, previous_count
assert next_count >= 10, next_count

guild = (ROOT / "handlers/guild.py").read_text(encoding="utf-8")
for forbidden in (
    "⬅️ Попередні гільдії", "➡️ Наступні гільдії",
    "⬅️ Попередні записи", "➡️ Наступні записи",
):
    assert forbidden not in guild, forbidden
assert guild.count(PREVIOUS) >= 2
assert guild.count(NEXT) >= 2

# Menu/context labels explicitly remain intact.
auction = (ROOT / "handlers/auction_house.py").read_text(encoding="utf-8")
assert "🔙 Торговий дім" in auction
assert "🔙 Категорії виставлення" in auction
player = (ROOT / "handlers/player_interaction.py").read_text(encoding="utf-8")
assert "🔙 До обміну" in player
runes = (ROOT / "handlers/runes.py").read_text(encoding="utf-8")
assert "⬅️ До спорядження" in runes or "⬅️ До списку спорядження" in runes
print(f"[PASS] Stage 17.9.1 canonical pagination labels: previous={previous_count}, next={next_count}")
