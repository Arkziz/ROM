#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations
import ast,random,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1]
if str(R) not in sys.path:sys.path.insert(0,str(R))
from data.equipment_stat_policy import PRIMARY_STATS,get_allowed_equipment_stats,redistribute_primary_stat_budget

def choose(profile):return random.choices([x[0] for x in profile],weights=[x[1] for x in profile],k=1)[0]
def check(cls,kind,subtype=""):
 base={"bonus_str":7,"bonus_dex":5,"bonus_int":3,"bonus_wis":0,"bonus_sta":2,"pdef":9,"mdef":4}
 random.seed(181702);out=redistribute_primary_stat_budget(base,cls,kind,item_subtype=subtype,chooser=choose)
 assert sum(out["bonus_"+s] for s in PRIMARY_STATS)==17
 assert all(out["bonus_"+s]==0 for s in set(PRIMARY_STATS)-set(get_allowed_equipment_stats(cls,kind,item_subtype=subtype)))
 assert out["pdef"]==9 and out["mdef"]==4
for cls in ("warrior","knight","scout","rogue","mage","priest"):
 for kind in ("weapon","armor","jewelry"):check(cls,kind)
check("knight","off_hand","shield")
random.seed(1);shield=redistribute_primary_stat_budget({"bonus_wis":8,"bonus_sta":4},"knight","off_hand",item_subtype="shield",chooser=choose)
assert shield.get("bonus_wis",0)==0 and shield.get("bonus_dex",0)==0 and shield.get("bonus_int",0)==0
assert shield.get("bonus_sta",0)+shield.get("bonus_str",0)==12
# Structural integration contracts.
gen=(R/"db_modules/generated_equipment.py").read_text(encoding="utf-8-sig")
shop=(R/"db_modules/shop.py").read_text(encoding="utf-8-sig")
assert gen.count("redistribute_primary_stat_budget(")==2
assert "if is_class_aware:" in gen and "target_class = get_character_class(user_id)" in gen
assert shop.count("redistribute_primary_stat_budget(")==1
assert "target_class = get_character_class(user_id)" in shop
assert "class-aware" in gen.lower() and "class-aware" in shop.lower()
ast.parse(gen);ast.parse(shop)
print("[PASS] Stage 18.17.2 class-aware drop and base-shop integration")
