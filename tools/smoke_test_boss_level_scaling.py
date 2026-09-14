#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Maintained boss level-scaling smoke test for canonical no-weaker floors."""
from pathlib import Path
import random
import sys
ROOT=Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from data.bosses import BOSS_DEFINITIONS
from systems.boss_system import build_location_boss, scale_boss_stat_ranges
for key,definition in BOSS_DEFINITIONS.items():
    floors=definition.get("no_weaker_floor_by_level") or {}
    expected=set(range(int(definition["level_min"]),int(definition["level_max"])+1))
    assert set(floors)==expected
    for level in sorted(expected):
        ranges=scale_boss_stat_ranges(definition,level)
        floor=floors[level]
        for stat in ("hp","attack","pdef","mdef"):
            assert ranges[f"{stat}_min"]==int(floor[stat])
            assert ranges[f"{stat}_max"]==int(floor[stat])
        for seed in range(25):
            boss=build_location_boss(definition["location_id"],level,random.Random(182760000+level*100+seed))
            assert boss["hp"]==boss["max_hp"]
            for stat in ("hp","attack","pdef","mdef"):
                assert int(boss[stat])>=int(floor[stat])
print("BOSS_CANONICAL_FLOOR_OK")
