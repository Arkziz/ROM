from __future__ import annotations

import ast
import json
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from data.bosses import (
    BOSS_CORE_STAT_MULTIPLIER,
    BOSS_DEFINITIONS,
    BOSS_ENCOUNTER_CHANCE_PERCENT,
    BOSS_ENCOUNTERS_ENABLED,
)
from systems.boss_system import build_location_boss
from systems.combat_system import (
    ELITE_ATTACK_MULTIPLIER,
    ELITE_CHANCE_PERCENT,
    ELITE_CORE_STAT_MULTIPLIER,
    ELITE_EXP_MULTIPLIER,
    ELITE_GOLD_MULTIPLIER,
    ELITE_HP_MULTIPLIER,
)

APPROVED = {
    "elite": {
        "core_multiplier": 1.8,
        "bonus_percent": 80,
        "exp_multiplier": 3.0,
        "gold_multiplier": 3.0,
    },
    "boss": {
        "core_multiplier": 2.0,
        "bonus_percent": 100,
        "exp_multiplier": 5.0,
        "gold_multiplier": 5.0,
        "enrage_hp_fraction": 0.25,
        "enrage_attack_percent": 20,
    },
    "pack_leader": {
        "ferocious_bite": 1.0,
        "fang_rend": 1.4,
        "fang_rend_bleed_turns": 2,
        "fang_rend_bleed_fraction": 0.20,
        "spectral_roar": 1.3,
        "enraged_rend": 1.7,
    },
    "goblin_king": {
        "chieftain_axe": 1.0,
        "skull_splitter": 1.3,
        "battle_cry_percent": 15,
        "battle_cry_turns": 3,
        "defense_command_percent": 30,
        "defense_command_turns": 2,
        "tyrant_strike": 1.6,
    },
}

findings = []
metrics = {}


def require(condition, label, actual=None, expected=None):
    if not condition:
        findings.append({"label": label, "actual": actual, "expected": expected})


require(ELITE_CORE_STAT_MULTIPLIER == 1.8, "elite core multiplier", ELITE_CORE_STAT_MULTIPLIER, 1.8)
require(ELITE_HP_MULTIPLIER == 1.8, "elite HP multiplier", ELITE_HP_MULTIPLIER, 1.8)
require(ELITE_ATTACK_MULTIPLIER == 1.8, "elite ATK multiplier", ELITE_ATTACK_MULTIPLIER, 1.8)
require(ELITE_EXP_MULTIPLIER == 3.0, "elite EXP multiplier", ELITE_EXP_MULTIPLIER, 3.0)
require(ELITE_GOLD_MULTIPLIER == 3.0, "elite Gold multiplier", ELITE_GOLD_MULTIPLIER, 3.0)

pack = BOSS_DEFINITIONS["pack_leader"]
king = BOSS_DEFINITIONS["goblin_king"]
require(BOSS_CORE_STAT_MULTIPLIER == 2.0, "boss core multiplier", BOSS_CORE_STAT_MULTIPLIER, 2.0)
for boss_key, definition in (("pack_leader", pack), ("goblin_king", king)):
    require(definition["enrage"]["hp_threshold_fraction"] == 0.25, f"{boss_key} enrage threshold", definition["enrage"]["hp_threshold_fraction"], 0.25)
    require(definition["enrage"]["permanent_attack_buff_percent"] == 20, f"{boss_key} enrage ATK", definition["enrage"]["permanent_attack_buff_percent"], 20)
    require(definition["enrage"]["special_replaces_regular_action"] is True, f"{boss_key} special replaces regular action")

require(pack["skills"]["ferocious_bite"]["damage_multiplier"] == 1.0, "ferocious_bite", pack["skills"]["ferocious_bite"]["damage_multiplier"], 1.0)
require(pack["skills"]["fang_rend"]["damage_multiplier"] == 1.4, "fang_rend", pack["skills"]["fang_rend"]["damage_multiplier"], 1.4)
require(pack["skills"]["fang_rend"]["bleed_turns"] == 2, "fang_rend bleed turns", pack["skills"]["fang_rend"]["bleed_turns"], 2)
require(pack["skills"]["fang_rend"]["bleed_damage_fraction"] == 0.20, "fang_rend bleed fraction", pack["skills"]["fang_rend"]["bleed_damage_fraction"], 0.20)
require(pack["skills"]["spectral_roar"]["damage_multiplier"] == 1.3, "spectral_roar", pack["skills"]["spectral_roar"]["damage_multiplier"], 1.3)
require(pack["skills"]["enraged_rend"]["damage_multiplier"] == 1.7, "enraged_rend", pack["skills"]["enraged_rend"]["damage_multiplier"], 1.7)
require(king["skills"]["chieftain_axe"]["damage_multiplier"] == 1.0, "chieftain_axe", king["skills"]["chieftain_axe"]["damage_multiplier"], 1.0)
require(king["skills"]["skull_splitter"]["damage_multiplier"] == 1.3, "skull_splitter", king["skills"]["skull_splitter"]["damage_multiplier"], 1.3)
require(king["skills"]["battle_cry"]["attack_buff_percent"] == 15, "battle_cry percent", king["skills"]["battle_cry"]["attack_buff_percent"], 15)
require(king["skills"]["battle_cry"]["duration_turns"] == 3, "battle_cry turns", king["skills"]["battle_cry"]["duration_turns"], 3)
require(king["skills"]["defense_command"]["pdef_buff_percent"] == 30, "defense_command PDEF", king["skills"]["defense_command"]["pdef_buff_percent"], 30)
require(king["skills"]["defense_command"]["mdef_buff_percent"] == 30, "defense_command MDEF", king["skills"]["defense_command"]["mdef_buff_percent"], 30)
require(king["skills"]["defense_command"]["duration_turns"] == 2, "defense_command turns", king["skills"]["defense_command"]["duration_turns"], 2)
require(king["skills"]["tyrant_strike"]["damage_multiplier"] == 1.6, "tyrant_strike", king["skills"]["tyrant_strike"]["damage_multiplier"], 1.6)

boss_samples = []
for location_id, level in (("start_path", 1), ("start_path", 5), ("dark_forest", 6), ("dark_forest", 10)):
    boss = build_location_boss(location_id, level, rng=random.Random(15710 + level))
    boss_samples.append({
        "location_id": location_id,
        "level": level,
        "boss_key": boss["boss_key"],
        "is_boss": boss["is_boss"],
        "is_elite": boss["is_elite"],
        "enemy_type": boss["enemy_type"],
        "exp_multiplier": boss["elite_exp_multiplier"],
        "gold_multiplier": boss["elite_gold_multiplier"],
    })
    require(boss["level"] == level, f"{location_id} level parity", boss["level"], level)
    require(boss["is_boss"] is True and boss["is_elite"] is False, f"{location_id} classification")
    require(boss["enemy_type"] == "boss" and boss["mob_type"] == "boss", f"{location_id} type fields")
    require(boss["elite_exp_multiplier"] == 5.0, f"{location_id} EXP multiplier", boss["elite_exp_multiplier"], 5.0)
    require(boss["elite_gold_multiplier"] == 5.0, f"{location_id} Gold multiplier", boss["elite_gold_multiplier"], 5.0)

combat_path = ROOT / "handlers" / "combat.py"
combat_text = combat_path.read_text(encoding="utf-8")
ast.parse(combat_text, filename=str(combat_path))
for token, label, expected_count in (
    ("👑 БОС ЛОКАЦІЇ!", "boss encounter banner", 1),
    ("🏆👑 ВИ ПЕРЕМОГЛИ БОСА!", "boss victory title", 1),
    ("💥 ОСТАННІ ПОДІЇ БОЮ", "lethal event header", 1),
):
    require(combat_text.count(token) == expected_count, label, combat_text.count(token), expected_count)
require(combat_text.count("build_lethal_combat_log(") == 4, "lethal helper definition plus three calls", combat_text.count("build_lethal_combat_log("), 4)
require('if mob.get("is_boss"):' in combat_text and 'elif mob.get("is_elite"):' in combat_text, "boss UI priority before elite")

combat_system_path = ROOT / "systems" / "combat_system.py"
combat_system_text = combat_system_path.read_text(encoding="utf-8")
ast.parse(combat_system_text, filename=str(combat_system_path))
require("apply_elite_modifier" in combat_system_text, "elite modifier exists")

boss_system_path = ROOT / "systems" / "boss_system.py"
boss_system_text = boss_system_path.read_text(encoding="utf-8")
ast.parse(boss_system_text, filename=str(boss_system_path))
require("def generate_hunt_encounter(" in boss_system_text, "boss encounter bridge exists")
require("roll_boss_encounter(" in boss_system_text, "boss encounter roll is wired")
require("build_location_boss(" in boss_system_text, "boss builder is wired")

metrics.update({
    "approved": APPROVED,
    "elite_chance_percent": ELITE_CHANCE_PERCENT,
    "boss_encounters_enabled": bool(BOSS_ENCOUNTERS_ENABLED),
    "boss_encounter_chance_percent": float(BOSS_ENCOUNTER_CHANCE_PERCENT),
    "boss_samples": boss_samples,
    "combat_simulations": 0,
    "database_writes": 0,
})

result = {
    "version": "15.7.10.1",
    "verdict": "PASS" if not findings else "FAIL",
    "metrics": metrics,
    "findings": findings,
}
print(json.dumps(result, ensure_ascii=False))
if findings:
    raise SystemExit(1)
