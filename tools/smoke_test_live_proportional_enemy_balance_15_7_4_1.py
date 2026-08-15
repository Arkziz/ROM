from __future__ import annotations
import random
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from systems.combat_system import build_mob,apply_elite_modifier,get_available_mobs,ELITE_CORE_STAT_MULTIPLIER
from systems.boss_system import build_location_boss,_templates_for_level,_average_range
from data.bosses import BOSS_CORE_STAT_MULTIPLIER,BOSS_ENCOUNTERS_ENABLED
assert ELITE_CORE_STAT_MULTIPLIER==1.5
assert BOSS_CORE_STAT_MULTIPLIER==2.0
for location,levels in (("start_path",(1,3,5)),("dark_forest",(6,8,10))):
 for level in levels:
  templates=_templates_for_level(location,level); assert templates
  boss=build_location_boss(location,level,rng=random.Random(157400+level))
  assert boss["level"]==level and boss["is_boss"] and not boss["is_elite"]
  for stat in ("hp","attack","pdef","mdef","dex"):
   lo,hi=_average_range(templates,f"{stat}_min",f"{stat}_max")
   assert round(lo*2.0)<=boss[stat]<=round(hi*2.0),(location,level,stat,boss[stat],lo,hi)
  base=build_mob(templates[0]); original={k:base[k] for k in ("hp","attack","pdef","mdef","dex")}
  elite=apply_elite_modifier(base)
  for stat,value in original.items():
   expected=max(1,int(value*1.5)) if stat in ("hp","attack") else max(1,int(round(value*1.5)))
   assert elite[stat]==expected,(stat,value,elite[stat],expected)
assert BOSS_ENCOUNTERS_ENABLED is False
print("[PASS] live proportional elite/boss stat contract",{"elite":1.5,"boss":2.0,"boss_gate":False})
