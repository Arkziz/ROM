#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
inventory = (ROOT / "handlers/inventory.py").read_text(encoding="utf-8")
runes = (ROOT / "handlers/runes.py").read_text(encoding="utf-8")
ast.parse(inventory)
ast.parse(runes)

expected_inventory = (
    "Оберіть потрібний розділ вашого інвентаря:",
    "Оберіть предмет для перегляду або виконання доступної дії:",
    "Оберіть предмет для ознайомлення:",
)
expected_runes = (
    "Оберіть предмет спорядження для роботи з рунними слотами:",
    "Оберіть руну, яку потрібно вставити у вибраний слот:",
    "Оберіть доступний рецепт для переробки рун:",
    "Оберіть знятий предмет спорядження зі вставленими рунами:",
)
for value in expected_inventory:
    assert value in inventory, value
for value in expected_runes:
    assert value in runes, value

assert inventory.count("ROM 17.6.1 INVENTORY MOBILE MESSAGE WIDTH") == 1
assert runes.count("ROM 17.6.1 RUNE MOBILE MESSAGE WIDTH") == 1
assert 'f"Оберіть розділ інвентаря:"' not in inventory
assert 'text += "Оберіть предмет:"' not in inventory
assert '        "Оберіть предмет спорядження:"' not in runes
assert '        "Оберіть руну:"' not in runes
assert '        "Оберіть рецепт:"' not in runes
assert "_short_name(" in runes
print("[PASS] Stage 17.6.1 inventory/rune mobile message width")
