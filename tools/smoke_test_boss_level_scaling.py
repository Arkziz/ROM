#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Maintained Rule A smoke test for dynamic boss scaling."""
from pathlib import Path
import random,sys
ROOT=Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from data.bosses import BOSS_DEFINITIONS
from systems.boss_system import build_location_boss,scale_boss_stat_ranges
for key,d in BOSS_DEFINITIONS.items():
    assert "no_weaker_floor_by_level" not in d
    for level in range(int(d["level_min"]),int(d["level_max"])+1):
        ranges=scale_boss_stat_ranges(d,level)
        seen=set()
        for seed in range(100):
            b=build_location_boss(d["location_id"],level,random.Random(182760000+level*1000+seed))
            assert b["hp"]>=ranges["elite_hp_ceiling"]+1
            assert b["attack"]>=ranges["elite_attack_ceiling"]+1
            assert b["hp"]==b["max_hp"]
            assert b["def"]==(b["pdef"] if b["attack_type"]=="physical" else b["mdef"])
            seen.add((b["str"],b["dex"],b["int"],b["wis"],b["sta"],b["hp"],b["attack"],b["pdef"],b["mdef"]))
        assert len(seen)>1
print("DYNAMIC_BOSS_RULE_A_OK")
