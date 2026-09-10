#!/usr/bin/env python3
import ast,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R))
from systems.level_up_reward_system import build_level_up_reward_message
s=build_level_up_reward_message({"new_ledger_levels":[6],"rows":[{"reached_level":6}],"gold_awarded_now":0,"item_result":{},"attribute_points_awarded":5,"free_attribute_points":8})
assert "⭐ Отримано очок характеристик: 5" in s
assert "📌 Вільних очок загалом: 8" in s
assert "Розподілити очки можна у профілі: «Характеристики»." in s
m=build_level_up_reward_message({"new_ledger_levels":[6,7],"rows":[{"reached_level":6},{"reached_level":7}],"gold_awarded_now":0,"item_result":{},"attribute_points_awarded":10,"free_attribute_points":13})
assert "⭐ Отримано очок характеристик: 10" in m
assert build_level_up_reward_message({"new_ledger_levels":[]})==""
p=(R/"systems/player_system.py").read_text(encoding="utf-8-sig");a=ast.parse(p);d=[n for n in a.body if isinstance(n,ast.FunctionDef) and n.name=="add_exp"];assert len(d)==1
seg=ast.get_source_segment(p,d[0]) or ""
assert seg.count('reward_result["attribute_points_awarded"] = attribute_points_awarded')==1
assert seg.count('reward_result["free_attribute_points"] = free_attribute_points')==1
assert seg.count('build_level_up_reward_message(reward_result)')==1
print("[PASS] Stage 18.16.6 level-up attribute point message contract")
