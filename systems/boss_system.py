"""Pure location-boss foundation for ROM Stage 15.1.0.

Encounter selection and combat integration intentionally remain outside this
stage. Functions accept an RNG object where randomness is needed so tests and
simulations remain deterministic.
"""
from __future__ import annotations

import copy
import random
from typing import Any, Mapping

from data.bosses import (
    BOSS_ATTACK_MULTIPLIER,
    BOSS_DEFINITIONS,
    BOSS_HP_MULTIPLIER,
    BOSS_SCHEMA_VERSION,
    get_location_boss_definition,
)
from data.mobs import get_mobs_for_location

STAT_RANGE_KEYS = (
    "hp_min", "hp_max", "attack_min", "attack_max",
    "pdef_min", "pdef_max", "mdef_min", "mdef_max",
    "dex_min", "dex_max",
)


def _int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return int(default)


def _templates_for_level(location_id: str, level: int) -> list[Mapping[str, Any]]:
    templates = list(get_mobs_for_location(location_id) or ())
    exact = [row for row in templates if _int(row.get("level"), 1) == level]
    if exact:
        return exact
    if not templates:
        return []
    distance = min(abs(_int(row.get("level"), 1) - level) for row in templates)
    return [row for row in templates if abs(_int(row.get("level"), 1) - level) == distance]


def _average_range(templates, minimum_key, maximum_key, fallback=1):
    if not templates:
        return int(fallback), int(fallback)
    mins = [_int(row.get(minimum_key, fallback), fallback) for row in templates]
    maxs = [_int(row.get(maximum_key, fallback), fallback) for row in templates]
    return max(1, round(sum(mins) / len(mins))), max(1, round(sum(maxs) / len(maxs)))


def derive_lower_anchor(definition: Mapping[str, Any]) -> dict[str, int]:
    """Build the location-min-level anchor from production mob data."""
    location_id = str(definition["location_id"])
    level_min = _int(definition["level_min"], 1)
    templates = _templates_for_level(location_id, level_min)
    hp_min, hp_max = _average_range(templates, "hp_min", "hp_max")
    atk_min, atk_max = _average_range(templates, "attack_min", "attack_max")
    pdef_min, pdef_max = _average_range(templates, "pdef_min", "pdef_max")
    mdef_min, mdef_max = _average_range(templates, "mdef_min", "mdef_max")
    dex_min, dex_max = _average_range(templates, "dex_min", "dex_max")
    return {
        "hp_min": max(1, round(hp_min * BOSS_HP_MULTIPLIER)),
        "hp_max": max(1, round(hp_max * BOSS_HP_MULTIPLIER)),
        "attack_min": max(1, round(atk_min * BOSS_ATTACK_MULTIPLIER)),
        "attack_max": max(1, round(atk_max * BOSS_ATTACK_MULTIPLIER)),
        "pdef_min": pdef_min, "pdef_max": pdef_max,
        "mdef_min": mdef_min, "mdef_max": mdef_max,
        "dex_min": dex_min, "dex_max": dex_max,
    }


def scale_boss_stat_ranges(definition: Mapping[str, Any], player_level: int) -> dict[str, int]:
    """Interpolate boss ranges between production-derived and PDF reference anchors."""
    level_min = _int(definition["level_min"], 1)
    level_max = _int(definition["level_max"], level_min)
    level = max(level_min, min(level_max, _int(player_level, level_min)))
    progress = (level - level_min) / max(1, level_max - level_min)
    lower = derive_lower_anchor(definition)
    upper = dict(definition["reference_stats"])
    scaled = {}
    for key in STAT_RANGE_KEYS:
        start = _int(lower[key], 1)
        end = _int(upper[key], start)
        scaled[key] = max(1, round(start + (end - start) * progress))
    for prefix in ("hp", "attack", "pdef", "mdef", "dex"):
        lo, hi = f"{prefix}_min", f"{prefix}_max"
        if scaled[hi] < scaled[lo]:
            scaled[hi] = scaled[lo]
    return scaled


def create_boss_state() -> dict[str, Any]:
    return {
        "enrage_used": False,
        "special_attack_used": False,
        "permanent_attack_buff_percent": 0.0,
        "attack_buff_turns": 0,
        "attack_buff_percent": 0.0,
        "defense_buff_turns": 0,
        "physical_defense_buff_percent": 0.0,
        "magical_defense_buff_percent": 0.0,
        "last_action_key": None,
    }


def build_location_boss(location_id: str, player_level: int, rng=None) -> dict[str, Any]:
    definition = get_location_boss_definition(location_id)
    if not definition:
        raise ValueError(f"No boss definition for location: {location_id}")
    level_min = _int(definition["level_min"], 1)
    level_max = _int(definition["level_max"], level_min)
    level = _int(player_level, level_min)
    if not level_min <= level <= level_max:
        raise ValueError(
            f"Player level {level} is outside boss location range {level_min}-{level_max}"
        )
    ranges = scale_boss_stat_ranges(definition, level)
    rng = rng or random
    hp = rng.randint(ranges["hp_min"], ranges["hp_max"])
    attack = rng.randint(ranges["attack_min"], ranges["attack_max"])
    pdef = rng.randint(ranges["pdef_min"], ranges["pdef_max"])
    mdef = rng.randint(ranges["mdef_min"], ranges["mdef_max"])
    dex = rng.randint(ranges["dex_min"], ranges["dex_max"])
    return {
        "boss_schema_version": BOSS_SCHEMA_VERSION,
        "boss_key": definition["boss_key"],
        "name": definition["name"],
        "base_name": definition["name"],
        "level": level,
        "min_player_level": level,
        "location_id": definition["location_id"],
        "hp": hp, "max_hp": hp,
        "attack": attack,
        "pdef": pdef, "mdef": mdef,
        "def": pdef if definition.get("attack_type") == "physical" else mdef,
        "dex": dex,
        "attack_type": definition.get("attack_type", "physical"),
        "is_boss": True,
        "is_elite": False,
        "enemy_type": "boss",
        "mob_type": "boss",
        "elite_exp_multiplier": 1.0,
        "elite_gold_multiplier": 1.0,
        "enemy_effects": {},
        "boss_state": create_boss_state(),
        "boss_definition": copy.deepcopy(definition),
        "boss_scaled_ranges": ranges,
    }


def choose_boss_action(boss: Mapping[str, Any], rng=None) -> dict[str, Any]:
    definition = boss.get("boss_definition") or {}
    state = boss.get("boss_state") or {}
    phase_key = "ai_after_enrage" if state.get("enrage_used") else "ai_before_enrage"
    choices = tuple(definition.get(phase_key) or ())
    if not choices:
        raise ValueError(f"Boss AI has no choices for phase: {phase_key}")
    total = sum(float(weight) for _, weight in choices)
    if total <= 0:
        raise ValueError("Boss AI weights must be positive")
    rng = rng or random
    roll = rng.random() * total
    running = 0.0
    selected = choices[-1][0]
    for skill_key, weight in choices:
        running += float(weight)
        if roll <= running:
            selected = skill_key
            break
    skill = dict((definition.get("skills") or {}).get(selected) or {})
    if not skill:
        raise ValueError(f"Unknown boss skill: {selected}")
    return {"skill_key": selected, "skill": skill, "phase": phase_key}


def validate_boss_definitions() -> dict[str, Any]:
    findings = []
    locations = set()
    for boss_key, definition in BOSS_DEFINITIONS.items():
        if definition.get("boss_key") != boss_key:
            findings.append(f"{boss_key}: boss_key mismatch")
        location_id = str(definition.get("location_id") or "")
        if not location_id:
            findings.append(f"{boss_key}: location_id missing")
        elif location_id in locations:
            findings.append(f"{boss_key}: duplicate location_id {location_id}")
        locations.add(location_id)
        if _int(definition.get("level_min"), 0) > _int(definition.get("level_max"), 0):
            findings.append(f"{boss_key}: invalid level range")
        for phase in ("ai_before_enrage", "ai_after_enrage"):
            rows = tuple(definition.get(phase) or ())
            weight_sum = sum(float(weight) for _, weight in rows)
            if abs(weight_sum - 1.0) > 1e-9:
                findings.append(f"{boss_key}: {phase} weights={weight_sum}")
            for skill_key, _ in rows:
                if skill_key not in (definition.get("skills") or {}):
                    findings.append(f"{boss_key}: missing skill {skill_key}")
        enrage = definition.get("enrage") or {}
        special = enrage.get("special_skill_key")
        if special not in (definition.get("skills") or {}):
            findings.append(f"{boss_key}: missing enrage special {special}")
        if enrage.get("special_replaces_regular_action") is not True:
            findings.append(f"{boss_key}: enrage special must replace regular action")
    return {
        "version": BOSS_SCHEMA_VERSION,
        "verdict": "PASS" if not findings else "FAIL",
        "boss_count": len(BOSS_DEFINITIONS),
        "location_count": len(locations),
        "findings": findings,
    }
