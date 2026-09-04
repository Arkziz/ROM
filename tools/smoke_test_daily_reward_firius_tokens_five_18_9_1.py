#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from pathlib import Path
import ast
ROOT = Path(__file__).resolve().parents[1]
def read(name):
    text=(ROOT/name).read_text(encoding="utf-8-sig")
    ast.parse(text, filename=name)
    return text
runes=read("data/runes.py")
daily=read("handlers/daily.py")
inv=read("handlers/inventory.py")
rune_system=read("systems/rune_system.py")
meta=read("systems/simulation/meta_progression.py")
world=read("systems/simulation/world_progression.py")
assert runes.count("FIRIUS_TOKENS_PER_DAILY_REWARD = 5") == 1
assert "FIRIUS_TOKENS_PER_DAILY_REWARD = 10" not in runes
assert "🪙 Жетон Фіріуса ×5\\n" in daily and "🪙 Жетон Фіріуса ×10\\n" not in daily
assert "• 5 жетонів можна отримати за виконання щоденного завдання." in inv
assert "• 10 жетонів можна отримати за виконання щоденного завдання." not in inv
assert "plus 5 cumulative Firius Tokens" in rune_system
assert "DAILY_FIRIUS_TOKENS=5" in meta and "DAILY_FIRIUS_TOKENS=10" not in meta
assert "items_awarded += 8" in world
assert '{"potions": 3, "firius_tokens": 5}' in world
assert "DAILY_QUEST_REWARD_QUANTITY = 3" in read("data/balance.py")
assert "FIRIUS_TOKEN_ITEM_ID = 726" in runes
assert "FIRIUS_TOKEN_ITEM_ID)==5" in read("tools/smoke_test_simulation_meta_progression.py")
print("PASS: daily reward = item 401 x3 + item 726 x5; production and simulation parity")
