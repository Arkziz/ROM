#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations
import ast
import random as stdlib_random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import db_modules.shop as shop

source = (ROOT / "db_modules/shop.py").read_text(encoding="utf-8-sig")
tree = ast.parse(source)
imports_random = any(
    isinstance(node, ast.Import)
    and any(alias.name == "random" and alias.asname is None for alias in node.names)
    for node in tree.body
)
assert imports_random, "db_modules/shop.py must import random at module scope"
assert shop.random is stdlib_random
profile = (("sta", 65), ("str", 35))
stdlib_random.seed(181702)
selected = shop.random.choices(
    [stat for stat, _weight in profile],
    weights=[weight for _stat, weight in profile],
    k=1,
)[0]
assert selected in {"sta", "str"}
assert "redistribute_primary_stat_budget(" in source
assert "target_class = get_character_class(user_id)" in source
print("[PASS] Stage 18.17.2a shop random import recovery")
