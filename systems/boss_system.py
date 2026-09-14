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
    BOSS_CORE_STAT_MULTIPLIER,
    BOSS_DEFINITIONS,
    BOSS_HP_MULTIPLIER,
    BOSS_SCHEMA_VERSION,
    BOSS_ENCOUNTERS_ENABLED,
    BOSS_ENCOUNTER_CHANCE_PERCENT,
    get_location_boss_definition,
)
from data.mobs import get_mobs_for_location

STAT_RANGE_KEYS = (
    "hp_min", "hp_max", "attack_min", "attack_max",
    "pdef_min", "pdef_max", "mdef_min", "mdef_max",
    "dex_min", "dex_max",
    "str_min", "str_max", "int_min", "int_max",
    "wis_min", "wis_max", "sta_min", "sta_max",
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
    str_min, str_max = _average_range(templates, "str_min", "str_max")
    int_min, int_max = _average_range(templates, "int_min", "int_max")
    wis_min, wis_max = _average_range(templates, "wis_min", "wis_max")
    sta_min, sta_max = _average_range(templates, "sta_min", "sta_max")
    return {
        "hp_min": max(1, round(hp_min * BOSS_HP_MULTIPLIER)),
        "hp_max": max(1, round(hp_max * BOSS_HP_MULTIPLIER)),
        "attack_min": max(1, round(atk_min * BOSS_ATTACK_MULTIPLIER)),
        "attack_max": max(1, round(atk_max * BOSS_ATTACK_MULTIPLIER)),
        "pdef_min": pdef_min, "pdef_max": pdef_max,
        "mdef_min": mdef_min, "mdef_max": mdef_max,
        "dex_min": dex_min, "dex_max": dex_max,
        "str_min": str_min, "str_max": str_max,
        "int_min": int_min, "int_max": int_max,
        "wis_min": wis_min, "wis_max": wis_max,
        "sta_min": sta_min, "sta_max": sta_max,
    }


def scale_boss_stat_ranges(definition: Mapping[str, Any], player_level: int) -> dict[str, int]:
    """Build primary ranges and canonical derived compatibility floor."""
    level_min = _int(definition["level_min"], 1)
    level_max = _int(definition["level_max"], level_min)
    level = max(level_min, min(level_max, _int(player_level, level_min)))
    templates = _templates_for_level(str(definition["location_id"]), level)
    if not templates:
        raise ValueError(f"No normal mob templates for boss reference: {definition['location_id']} level {level}")
    scaled = {}
    for prefix in ("dex", "str", "int", "wis", "sta"):
        lo, hi = _average_range(templates, f"{prefix}_min", f"{prefix}_max")
        scaled[f"{prefix}_min"] = max(1, round(lo * BOSS_CORE_STAT_MULTIPLIER))
        scaled[f"{prefix}_max"] = max(scaled[f"{prefix}_min"], round(hi * BOSS_CORE_STAT_MULTIPLIER))
    floors = definition.get("no_weaker_floor_by_level") or {}
    floor = floors.get(level)
    if not isinstance(floor, Mapping):
        raise ValueError(f"Canonical boss floor missing: {definition['boss_key']} level {level}")
    for stat in ("hp", "attack", "pdef", "mdef"):
        value = _int(floor.get(stat), 0)
        if value < 1:
            raise ValueError(f"Invalid canonical boss floor: {definition['boss_key']} level {level} {stat}")
        scaled[f"{stat}_min"] = value
        scaled[f"{stat}_max"] = value
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
    # Build one boss snapshot from primary stats with one no-weaker floor.
    import math

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
    primary_stats = {
        stat: rng.randint(ranges[f"{stat}_min"], ranges[f"{stat}_max"])
        for stat in ("str", "dex", "int", "wis", "sta")
    }
    attack_type = definition.get("attack_type", "physical")
    candidate_hp = max(1, int(math.ceil((level * 10) + (primary_stats["sta"] * 5))))
    if attack_type == "physical":
        candidate_attack = max(1, int(math.ceil((level * 2) + primary_stats["str"])))
    else:
        candidate_attack = max(1, int(math.ceil(
            (level * 2) + primary_stats["int"] + (primary_stats["wis"] * 0.25)
        )))
    candidate_pdef = max(1, int(math.ceil(primary_stats["sta"] * 0.5)))
    candidate_mdef = max(1, int(math.ceil(primary_stats["wis"] * 0.75)))

    # One compatibility layer: a boss can become stronger, never weaker than
    # the current scaled minimum for the same level.
    hp = max(candidate_hp, int(ranges["hp_min"]))
    attack = max(candidate_attack, int(ranges["attack_min"]))
    pdef = max(candidate_pdef, int(ranges["pdef_min"]))
    mdef = max(candidate_mdef, int(ranges["mdef_min"]))

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
        "def": pdef if attack_type == "physical" else mdef,
        "str": primary_stats["str"],
        "dex": primary_stats["dex"],
        "int": primary_stats["int"],
        "wis": primary_stats["wis"],
        "sta": primary_stats["sta"],
        "attack_type": attack_type,
        "is_boss": True,
        "is_elite": False,
        "enemy_type": "boss",
        "mob_type": "boss",
        "elite_exp_multiplier": 5.0,
        "elite_gold_multiplier": 5.0,
        "boss_exp_multiplier": 5.0,
        "boss_gold_multiplier": 5.0,
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


def roll_boss_encounter(rng=None, chance_percent=None, enabled=None) -> bool:
    """Return whether the mutually exclusive hunt result is a boss.

    The production default is controlled by BOSS_ENCOUNTERS_ENABLED. Tests and
    future simulations can pass enabled=True explicitly without changing live
    behavior. A single random() roll is used for deterministic distribution.
    """
    if enabled is None:
        enabled = BOSS_ENCOUNTERS_ENABLED
    if not enabled:
        return False
    if chance_percent is None:
        chance_percent = BOSS_ENCOUNTER_CHANCE_PERCENT
    chance = max(0.0, min(100.0, float(chance_percent)))
    rng = rng or random
    return float(rng.random()) < chance / 100.0


def generate_hunt_encounter(
    player_level: int,
    location_id: str,
    normal_mob_factory,
    elite_modifier,
    elite_roll,
    rng=None,
    boss_enabled=None,
    boss_chance_percent=None,
) -> dict[str, Any]:
    """Resolve one exclusive hunt encounter using boss > elite > normal.

    Boss is checked first. If no boss is selected, the existing production
    normal factory and elite roll are called unchanged. The boss never receives
    an elite modifier and always has player_level.
    """
    rng = rng or random
    if roll_boss_encounter(
        rng=rng,
        chance_percent=boss_chance_percent,
        enabled=boss_enabled,
    ):
        mob = build_location_boss(location_id, player_level, rng=rng)
        return {"enemy_type": "boss", "mob": mob}

    mob = normal_mob_factory()
    if elite_roll():
        mob = elite_modifier(mob)
        mob["enemy_type"] = "elite"
        mob["mob_type"] = "elite"
        mob["is_boss"] = False
        return {"enemy_type": "elite", "mob": mob}

    mob["enemy_type"] = "normal"
    mob["mob_type"] = "normal"
    mob["is_boss"] = False
    mob["is_elite"] = False
    return {"enemy_type": "normal", "mob": mob}

# ============================================================================
# Stage 15.3.0: boss combat actions, player bleed and temporary self-buffs
# ============================================================================

PLAYER_BOSS_BLEED_EFFECT_KEY = "boss_bleed"


def _boss_state(boss: dict[str, Any]) -> dict[str, Any]:
    state = boss.get("boss_state")
    if not isinstance(state, dict):
        state = create_boss_state()
        boss["boss_state"] = state
    defaults = create_boss_state()
    for key, value in defaults.items():
        state.setdefault(key, value)
    return state


def get_effective_boss_attack(boss: Mapping[str, Any]) -> int:
    """Return boss ATK after permanent enrage and temporary ATK buffs.

    Different ATK buffs are additive. The same temporary buff never stacks;
    applying it again only refreshes the duration in apply_boss_action_effects().
    """
    state = boss.get("boss_state") or {}
    permanent = float(state.get("permanent_attack_buff_percent", 0.0) or 0.0)
    temporary = 0.0
    if int(state.get("attack_buff_turns", 0) or 0) > 0:
        temporary = float(state.get("attack_buff_percent", 0.0) or 0.0)
    multiplier = 1.0 + (permanent + temporary) / 100.0
    return max(1, int(round(float(boss.get("attack", 1) or 1) * multiplier)))


def get_effective_boss_defenses(boss: Mapping[str, Any]) -> tuple[int, int]:
    state = boss.get("boss_state") or {}
    pdef_percent = 0.0
    mdef_percent = 0.0
    if int(state.get("defense_buff_turns", 0) or 0) > 0:
        pdef_percent = float(state.get("physical_defense_buff_percent", 0.0) or 0.0)
        mdef_percent = float(state.get("magical_defense_buff_percent", 0.0) or 0.0)
    pdef = max(0, int(round(float(boss.get("pdef", boss.get("def", 0)) or 0) * (1.0 + pdef_percent / 100.0))))
    mdef = max(0, int(round(float(boss.get("mdef", boss.get("def", 0)) or 0) * (1.0 + mdef_percent / 100.0))))
    return pdef, mdef


def build_boss_action_plan(boss: dict[str, Any], rng=None, forced_skill_key=None) -> dict[str, Any]:
    """Create a pure action plan without rolling dodge, crit or final damage."""
    definition = boss.get("boss_definition") or {}
    skills = definition.get("skills") or {}
    if forced_skill_key is None:
        selected = choose_boss_action(boss, rng=rng)
        skill_key = selected["skill_key"]
        skill = dict(selected["skill"])
        phase = selected["phase"]
    else:
        skill_key = str(forced_skill_key)
        skill = dict(skills.get(skill_key) or {})
        if not skill:
            raise ValueError(f"Unknown boss skill: {skill_key}")
        phase = "forced"
    no_damage = bool(skill.get("no_damage"))
    return {
        "boss_key": boss.get("boss_key"),
        "skill_key": skill_key,
        "skill_name": skill.get("name", skill_key),
        "phase": phase,
        "no_damage": no_damage,
        "attack_type": None if no_damage else skill.get("attack_type", boss.get("attack_type", "physical")),
        "damage_multiplier": 0.0 if no_damage else float(skill.get("damage_multiplier", 1.0) or 0.0),
        "effective_attack": 0 if no_damage else get_effective_boss_attack(boss),
        "skill": skill,
    }


def calculate_boss_bleed_damage(actual_damage: int, skill: Mapping[str, Any]) -> int:
    """Bleed is based on actual post-defense damage and never crits."""
    fraction = float(skill.get("bleed_damage_fraction", 0.0) or 0.0)
    minimum = max(0, int(skill.get("bleed_min_damage", 1) or 1))
    if fraction <= 0 or int(actual_damage or 0) <= 0:
        return 0
    return max(minimum, int(round(int(actual_damage) * fraction)))


def apply_boss_action_effects(
    boss: dict[str, Any],
    action_plan: Mapping[str, Any],
    actual_damage: int = 0,
) -> dict[str, Any]:
    """Apply boss self-buffs and return a player-effect instruction.

    The returned player_effect is intentionally data-only. The production
    handler integration in the next stage will insert it into player_effects.
    """
    state = _boss_state(boss)
    skill = dict(action_plan.get("skill") or {})
    skill_key = str(action_plan.get("skill_key") or "")
    events = []
    player_effect = None

    if "attack_buff_percent" in skill:
        state["attack_buff_percent"] = float(skill.get("attack_buff_percent", 0) or 0)
        state["attack_buff_turns"] = max(0, int(skill.get("duration_turns", 0) or 0))
        events.append({
            "type": "boss_attack_buff",
            "percent": state["attack_buff_percent"],
            "turns": state["attack_buff_turns"],
            "refresh_policy": skill.get("refresh_policy", "replace"),
        })

    if "pdef_buff_percent" in skill or "mdef_buff_percent" in skill:
        state["physical_defense_buff_percent"] = float(skill.get("pdef_buff_percent", 0) or 0)
        state["magical_defense_buff_percent"] = float(skill.get("mdef_buff_percent", 0) or 0)
        state["defense_buff_turns"] = max(0, int(skill.get("duration_turns", 0) or 0))
        events.append({
            "type": "boss_defense_buff",
            "pdef_percent": state["physical_defense_buff_percent"],
            "mdef_percent": state["magical_defense_buff_percent"],
            "turns": state["defense_buff_turns"],
            "refresh_policy": skill.get("refresh_policy", "replace"),
        })

    bleed_damage = calculate_boss_bleed_damage(actual_damage, skill)
    if bleed_damage > 0:
        player_effect = {
            "key": PLAYER_BOSS_BLEED_EFFECT_KEY,
            "name": "🩸 Кровотеча",
            "icon": "🩸",
            "type": "dot",
            "source": "boss",
            "source_boss_key": boss.get("boss_key"),
            "source_skill_key": skill_key,
            "turns": max(1, int(skill.get("bleed_turns", 1) or 1)),
            "damage": bleed_damage,
            "can_crit": False,
            "refresh_policy": skill.get("bleed_refresh_policy", "replace"),
        }
        events.append({
            "type": "player_bleed_applied",
            "damage": bleed_damage,
            "turns": player_effect["turns"],
            "refresh_policy": player_effect["refresh_policy"],
        })

    state["last_action_key"] = skill_key
    return {
        "boss_state": copy.deepcopy(state),
        "events": events,
        "player_effect": player_effect,
    }


def apply_player_effect_instruction(mob: dict[str, Any], effect_instruction: Mapping[str, Any] | None) -> dict[str, Any] | None:
    """Insert/refresh the boss bleed instruction in combat player_effects."""
    if not effect_instruction:
        return None
    effect = dict(effect_instruction)
    key = str(effect.pop("key", PLAYER_BOSS_BLEED_EFFECT_KEY))
    effects = mob.setdefault("player_effects", {})
    effects[key] = effect
    return effect


def process_boss_player_dots(mob: dict[str, Any], current_hp: int) -> dict[str, Any]:
    """Tick only boss-origin player DoTs at player-turn start.

    This helper does not write game.db. It mutates the in-memory combat object
    and returns the new HP so the handler can use its existing HP persistence.
    """
    hp = max(0, int(current_hp or 0))
    effects = mob.setdefault("player_effects", {})
    total_damage = 0
    events = []
    expired = []
    for key, effect in list(effects.items()):
        if effect.get("type") != "dot" or effect.get("source") != "boss":
            continue
        damage = max(0, int(effect.get("damage", 0) or 0))
        applied = min(hp, damage)
        hp -= applied
        total_damage += applied
        turns = int(effect.get("turns", 0) or 0) - 1
        effect["turns"] = turns
        events.append({"type": "boss_dot_tick", "key": key, "damage": applied, "turns_left": max(0, turns)})
        if turns <= 0:
            expired.append(key)
    for key in expired:
        effects.pop(key, None)
    return {"current_hp": hp, "damage": total_damage, "events": events, "expired": expired}


def tick_boss_temporary_buffs(boss: dict[str, Any]) -> dict[str, Any]:
    """Decrement temporary boss buffs after a completed boss action."""
    state = _boss_state(boss)
    expired = []
    if int(state.get("attack_buff_turns", 0) or 0) > 0:
        state["attack_buff_turns"] = int(state["attack_buff_turns"]) - 1
        if state["attack_buff_turns"] <= 0:
            state["attack_buff_turns"] = 0
            state["attack_buff_percent"] = 0.0
            expired.append("attack_buff")
    if int(state.get("defense_buff_turns", 0) or 0) > 0:
        state["defense_buff_turns"] = int(state["defense_buff_turns"]) - 1
        if state["defense_buff_turns"] <= 0:
            state["defense_buff_turns"] = 0
            state["physical_defense_buff_percent"] = 0.0
            state["magical_defense_buff_percent"] = 0.0
            expired.append("defense_buff")
    return {"boss_state": copy.deepcopy(state), "expired": expired}


def resolve_boss_combat_action(
    boss: dict[str, Any],
    rng=None,
    forced_skill_key=None,
    actual_damage: int | None = None,
) -> dict[str, Any]:
    """Resolve action selection and effects around the existing damage engine.

    If actual_damage is None, the caller must calculate final damage through the
    existing production calculate_mob_attack() and call apply_boss_action_effects
    afterwards. Tests may pass actual_damage to verify bleed semantics.
    """
    plan = build_boss_action_plan(boss, rng=rng, forced_skill_key=forced_skill_key)
    effects = None
    if actual_damage is not None or plan["no_damage"]:
        effects = apply_boss_action_effects(boss, plan, actual_damage=int(actual_damage or 0))
    return {"plan": plan, "effects": effects}

# ============================================================================
# Stage 15.4.0: one-time enrage transition and production combat bridge
# ============================================================================

def get_boss_enrage_threshold_hp(boss: Mapping[str, Any]) -> int:
    definition=boss.get("boss_definition") or {}
    enrage=definition.get("enrage") or {}
    fraction=float(enrage.get("hp_threshold_fraction",0.25) or 0.25)
    return max(1,int(float(boss.get("max_hp",1) or 1)*fraction))


def should_trigger_boss_enrage(boss: Mapping[str, Any]) -> bool:
    if not boss.get("is_boss") or int(boss.get("hp",0) or 0)<=0:
        return False
    state=boss.get("boss_state") or {}
    if state.get("enrage_used"):
        return False
    return int(boss.get("hp",0) or 0)<=get_boss_enrage_threshold_hp(boss)


def trigger_boss_enrage(boss: dict[str, Any]) -> dict[str, Any]:
    """Atomically mark enrage and return the automatic special action plan."""
    state=_boss_state(boss)
    if not should_trigger_boss_enrage(boss):
        return {"triggered":False,"reason":"not_eligible","action_plan":None,"events":[]}
    definition=boss.get("boss_definition") or {}
    enrage=definition.get("enrage") or {}
    special=str(enrage.get("special_skill_key") or "")
    state["enrage_used"]=True
    state["special_attack_used"]=True
    state["permanent_attack_buff_percent"]=float(enrage.get("permanent_attack_buff_percent",0) or 0)
    plan=build_boss_action_plan(boss,forced_skill_key=special)
    state["last_action_key"]=special
    return {
        "triggered":True,
        "reason":"hp_threshold",
        "action_plan":plan,
        "special_replaces_regular_action":bool(enrage.get("special_replaces_regular_action",True)),
        "events":[
            {"type":"boss_enrage","attack_buff_percent":state["permanent_attack_buff_percent"]},
            {"type":"boss_enrage_special","skill_key":special},
        ],
    }


def prepare_boss_turn(boss: dict[str, Any], rng=None) -> dict[str, Any]:
    """Select exactly one boss action for the current enemy turn.

    Enrage special has priority and replaces the normal weighted action. Once
    used, all future turns use the after-enrage AI table.
    """
    if not boss.get("is_boss"):
        return {"is_boss":False,"enrage_triggered":False,"action_plan":None}
    enrage=trigger_boss_enrage(boss)
    if enrage["triggered"]:
        return {"is_boss":True,"enrage_triggered":True,"action_plan":enrage["action_plan"],"events":enrage["events"]}
    return {"is_boss":True,"enrage_triggered":False,"action_plan":build_boss_action_plan(boss,rng=rng),"events":[]}


def build_boss_damage_request(action_plan: Mapping[str, Any]) -> dict[str, Any] | None:
    """Translate a boss plan to arguments for production calculate_mob_attack()."""
    if not action_plan or action_plan.get("no_damage"):
        return None
    return {
        "mob_attack":max(1,int(round(float(action_plan.get("effective_attack",1) or 1)*float(action_plan.get("damage_multiplier",1.0) or 1.0)))),
        "attack_type":str(action_plan.get("attack_type") or "physical"),
    }


def finalize_boss_turn(boss: dict[str, Any], action_plan: Mapping[str, Any], actual_damage: int=0) -> dict[str, Any]:
    """Apply effects, then decrement buffs that existed before this action.

    Newly applied Battle Cry/Defense Command must retain their full advertised
    duration. Therefore existing timers are captured before effect application.
    """
    state=_boss_state(boss)
    old_attack_turns=int(state.get("attack_buff_turns",0) or 0)
    old_defense_turns=int(state.get("defense_buff_turns",0) or 0)
    effects=apply_boss_action_effects(boss,action_plan,actual_damage=actual_damage)
    skill=action_plan.get("skill") or {}
    if "attack_buff_percent" not in skill and old_attack_turns>0:
        state["attack_buff_turns"]=old_attack_turns-1
        if state["attack_buff_turns"]<=0:
            state["attack_buff_turns"]=0; state["attack_buff_percent"]=0.0
    if not ("pdef_buff_percent" in skill or "mdef_buff_percent" in skill) and old_defense_turns>0:
        state["defense_buff_turns"]=old_defense_turns-1
        if state["defense_buff_turns"]<=0:
            state["defense_buff_turns"]=0
            state["physical_defense_buff_percent"]=0.0
            state["magical_defense_buff_percent"]=0.0
    player_effect=effects.get("player_effect")
    if player_effect:
        apply_player_effect_instruction(boss,player_effect)
    return {"effects":effects,"boss_state":copy.deepcopy(state),"player_effect":player_effect}


def render_boss_action_text(boss: Mapping[str, Any], turn: Mapping[str, Any], actual_damage: int=0, dodged: bool=False) -> str:
    plan=turn.get("action_plan") or {}
    lines=[]
    if turn.get("enrage_triggered"):
        percent=int((boss.get("boss_state") or {}).get("permanent_attack_buff_percent",0) or 0)
        lines.append(f"🌕 {boss.get('name','Бос')} входить у Лють! ATK +{percent}% до кінця бою.")
    name=plan.get("skill_name") or "Атака боса"
    if plan.get("no_damage"):
        skill=plan.get("skill") or {}
        if "attack_buff_percent" in skill:
            lines.append(f"{name}: ATK +{int(skill['attack_buff_percent'])}% на {int(skill.get('duration_turns',0))} ходи.")
        else:
            lines.append(f"{name}: PDEF і MDEF +30% на {int(skill.get('duration_turns',0))} ходи.")
    elif dodged:
        lines.append(f"💨 {name}: гравець ухилився.")
    else:
        lines.append(f"{name}: завдано {int(actual_damage)} шкоди.")
    return "\n".join(lines)
