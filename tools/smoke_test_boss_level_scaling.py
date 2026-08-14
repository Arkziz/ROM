from __future__ import annotations
import random,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from data.bosses import get_location_boss_definition
from systems.boss_system import build_location_boss,scale_boss_stat_ranges
cases=(("start_path",1,5),("dark_forest",6,10))
for location,level_min,level_max in cases:
 definition=get_location_boss_definition(location)
 prior=None
 for level in range(level_min,level_max+1):
  ranges=scale_boss_stat_ranges(definition,level)
  assert ranges["hp_min"]<=ranges["hp_max"]
  assert ranges["attack_min"]<=ranges["attack_max"]
  if prior:
   assert ranges["hp_min"]>=prior["hp_min"]
   assert ranges["attack_min"]>=prior["attack_min"]
  boss=build_location_boss(location,level,rng=random.Random(151000+level))
  assert boss["level"]==level and boss["is_boss"] is True and boss["is_elite"] is False
  assert boss["enemy_type"]==boss["mob_type"]=="boss"
  assert boss["boss_state"]["enrage_used"] is False
  prior=ranges
 assert scale_boss_stat_ranges(definition,level_max)==definition["reference_stats"]
try:
 build_location_boss("start_path",6,rng=random.Random(1))
 raise AssertionError("out-of-range level accepted")
except ValueError:
 pass
print("[PASS] boss level scaling and runtime state")
