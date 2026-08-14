from __future__ import annotations
import random,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from data.bosses import BOSS_ENCOUNTERS_ENABLED,BOSS_ENCOUNTER_CHANCE_PERCENT
from systems.boss_system import generate_hunt_encounter,roll_boss_encounter

assert BOSS_ENCOUNTERS_ENABLED is False
assert BOSS_ENCOUNTER_CHANCE_PERCENT==1.0
assert not roll_boss_encounter(random.Random(1))

normal_calls={"build":0,"elite":0}
def factory():
 normal_calls["build"]+=1
 return {"name":"normal","level":3,"is_elite":False}
def elite(mob):
 mob=dict(mob); mob["is_elite"]=True; mob["name"]="elite"; return mob
def never_elite(): normal_calls["elite"]+=1; return False

# Live safety gate: boss is disabled and existing normal flow remains active.
r=generate_hunt_encounter(3,"start_path",factory,elite,never_elite,rng=random.Random(1))
assert r["enemy_type"]=="normal" and normal_calls=={"build":1,"elite":1}

# Forced boss: boss is exclusive and normal/elite callbacks are never called.
normal_calls={"build":0,"elite":0}
r=generate_hunt_encounter(3,"start_path",factory,elite,never_elite,rng=random.Random(1),boss_enabled=True,boss_chance_percent=100)
assert r["enemy_type"]=="boss"
assert r["mob"]["is_boss"] is True and r["mob"]["is_elite"] is False
assert r["mob"]["level"]==3 and r["mob"]["location_id"]=="start_path"
assert normal_calls=={"build":0,"elite":0}

# Forced elite when boss misses.
normal_calls={"build":0,"elite":0}
def yes_elite(): normal_calls["elite"]+=1; return True
r=generate_hunt_encounter(3,"start_path",factory,elite,yes_elite,rng=random.Random(1),boss_enabled=True,boss_chance_percent=0)
assert r["enemy_type"]=="elite"
assert r["mob"]["is_elite"] is True and r["mob"]["is_boss"] is False
assert normal_calls=={"build":1,"elite":1}

# Forced normal when both boss and elite miss.
normal_calls={"build":0,"elite":0}
r=generate_hunt_encounter(3,"start_path",factory,elite,never_elite,rng=random.Random(1),boss_enabled=True,boss_chance_percent=0)
assert r["enemy_type"]=="normal"
assert r["mob"]["is_elite"] is False and r["mob"]["is_boss"] is False
print("[PASS] boss > elite > normal encounter exclusivity and safety gate")
