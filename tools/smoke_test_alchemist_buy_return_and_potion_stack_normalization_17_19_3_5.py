#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import ast
import sys
from pathlib import Path
R = Path(__file__).resolve().parents[1]
if str(R) not in sys.path:
    sys.path.insert(0, str(R))
for rel in ("systems/potion_system.py", "handlers/city.py"):
    source = (R / rel).read_text(encoding="utf-8")
    ast.parse(source)
    assert source.count("ROM 17.19.3.5 ALCHEMIST BUY RETURN POTION STACK NORMALIZATION") == 1, rel
from systems.potion_system import build_potion_stack_plan_17_19_3_5
assert build_potion_stack_plan_17_19_3_5([(1,1,0),(2,8,0)],10) == [(1,9),(2,0)]
assert build_potion_stack_plan_17_19_3_5([(1,1,0),(2,10,0)],10) == [(1,10),(2,1)]
assert build_potion_stack_plan_17_19_3_5([(1,5,2),(2,6,0)],10) == [(1,10),(2,1)]
assert build_potion_stack_plan_17_19_3_5([(1,2,2),(2,7,0)],10) == [(1,9),(2,0)]
assert build_potion_stack_plan_17_19_3_5([(1,10,3),(2,10,0),(3,1,0)],10) == [(1,10),(2,10),(3,1)]
city = (R / "handlers/city.py").read_text(encoding="utf-8")
assert 'if result.get("success"):' in city
assert 'text,kb=build_alchemist_buy_list_17_19_3(user_id)' in city
assert 'text,kb=build_alchemist_buy_preview_17_19_3(user_id,int(parts[2]),int(parts[3]))' in city
potion = (R / "systems/potion_system.py").read_text(encoding="utf-8")
assert potion.count("normalize_potion_stacks_17_19_3_5(int(user_id), item_id, cursor)") == 2
print("[PASS] Stage 17.19.3.5 buy return and potion stack normalization contract")
