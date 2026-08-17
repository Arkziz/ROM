from __future__ import annotations
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from systems import dynamic_equipment_system as dynamic
required=("init_dynamic_equipment_system","get_dynamic_weapon_name","get_dynamic_armor_name","generate_dynamic_equipment_stats","apply_armor_type_defense_profile_to_stats","get_dynamic_sell_price")
assert all(callable(getattr(dynamic,n,None)) for n in required)
name=dynamic.get_dynamic_armor_name("ring","common");assert isinstance(name,str) and name
stats=dynamic.generate_dynamic_equipment_stats(slot_key="ring",item_level=8,rarity="common",weapon_hands=1,item_profile="")
assert isinstance(stats,dict) and all(k in stats for k in ("bonus_str","bonus_dex","bonus_int","bonus_wis","bonus_sta","pdef","mdef"))
price=dynamic.get_dynamic_sell_price(8,"common");assert float(price)>=0
print("[PASS] dynamic equipment generation API")
