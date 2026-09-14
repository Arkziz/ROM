#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Maintained dynamic Rule A boss smoke after legacy configuration cleanup."""
from pathlib import Path
import random
import sys

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from data.bosses import (
    BOSS_DEFINITIONS,
    BOSS_PRIMARY_STAT_MULTIPLIER,
    BOSS_HP_OUTPUT_MULTIPLIER,
    BOSS_ELITE_HP_CEILING_MULTIPLIER,
    BOSS_ELITE_ATTACK_CEILING_MULTIPLIER,
)
from systems.boss_system import build_location_boss, scale_boss_stat_ranges

assert BOSS_PRIMARY_STAT_MULTIPLIER == 2.2
assert BOSS_HP_OUTPUT_MULTIPLIER == 1.35
assert BOSS_ELITE_HP_CEILING_MULTIPLIER == 1.8
assert BOSS_ELITE_ATTACK_CEILING_MULTIPLIER == 1.8

for boss_key, definition in BOSS_DEFINITIONS.items():
    assert "reference_stats" not in definition
    expected_levels = range(int(definition["level_min"]), int(definition["level_max"]) + 1)
    for level in expected_levels:
        ranges = scale_boss_stat_ranges(definition, level)
        snapshots = set()
        for seed in range(100):
            boss = build_location_boss(
                definition["location_id"], level, random.Random(182770000 + level * 1000 + seed)
            )
            assert "boss_scaled_ranges" not in boss
            assert boss["hp"] == boss["max_hp"]
            assert boss["hp"] >= ranges["elite_hp_ceiling"] + 1
            assert boss["attack"] >= ranges["elite_attack_ceiling"] + 1
            assert boss["def"] == (
                boss["pdef"] if boss["attack_type"] == "physical" else boss["mdef"]
            )
            assert boss["boss_definition"]["skills"] == definition["skills"]
            assert boss["boss_definition"]["enrage"] == definition["enrage"]
            snapshots.add(
                (
                    boss["str"], boss["dex"], boss["int"], boss["wis"], boss["sta"],
                    boss["hp"], boss["attack"], boss["pdef"], boss["mdef"],
                )
            )
        assert len(snapshots) > 1

print("BOSS_LEGACY_CONFIGURATION_CLEANUP_OK")
