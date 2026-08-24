#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations
import ast
import sys
from pathlib import Path

R = Path(__file__).resolve().parents[1]
if str(R) not in sys.path:
    sys.path.insert(0, str(R))

MARKER = "ROM 17.19.1 MANA POTION PRICE BALANCE"
for rel in ("systems/potion_system.py", "db_modules/connection.py"):
    source = (R / rel).read_text(encoding="utf-8")
    ast.parse(source)
    assert source.count(MARKER) == 1, (rel, source.count(MARKER))

from systems.potion_system import POTIONS
assert float(POTIONS[202]["buy_price"]) == 4.00
assert float(POTIONS[202]["sell_price"]) == 0.80
assert float(POTIONS[204]["buy_price"]) == 12.50
assert float(POTIONS[204]["sell_price"]) == 2.50
assert int(POTIONS[202]["restore"]) == 40
assert int(POTIONS[204]["restore"]) == 100
assert float(POTIONS[201]["buy_price"]) == 5.00
assert float(POTIONS[203]["buy_price"]) == 15.00

source = (R / "db_modules/connection.py").read_text(encoding="utf-8")
tree = ast.parse(source)
fn = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "seed_items")
rows = {}
for node in fn.body:
    if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "items" for t in node.targets):
        for row in node.value.elts:
            values = ast.literal_eval(row)
            rows[int(values[0])] = values
assert float(rows[202][8]) == 0.80
assert float(rows[204][8]) == 2.50
assert float(rows[201][8]) == 1.00
assert float(rows[203][8]) == 3.00
print("[PASS] Stage 17.19.1 mana potion price balance contract")
