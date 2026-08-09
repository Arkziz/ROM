from __future__ import annotations

import random
from typing import Any, Mapping

from systems.pvp_config import (
    PVP_COMBAT_ENERGY_MAX, PVP_CONSECUTIVE_AFK_LIMIT, PVP_DAMAGE_MULTIPLIER,
    PVP_DEBUFF_MULTIPLIER, PVP_HEALING_MULTIPLIER, PVP_MAX_ROUNDS,
    PVP_RAGE_GAIN_ON_ATTACK, PVP_RAGE_GAIN_ON_DAMAGE_TAKEN,
    PVP_SHIELD_MULTIPLIER,
)
from systems.pvp_models import PvpActionIntent, PvpActionOutcome, PvpActorState, PvpRoundResult
from systems.pvp_skill_adapter import get_production_pvp_skill, load_production_pvp_skill_catalog


class PvpRoundError(RuntimeError):
    pass


def _clamp(value: int, low: int, high: int) -> int:
    return max(low, min(high, int(value)))


def _effect_value(effect: Mapping[str, Any], key: str, default: float = 0.0) -> float:
    try:
        return float(effect.get(key, default))
    except (TypeError, ValueError):
        return default


def _effective_defense(actor: PvpActorState, attack_type: str) -> float:
    base = actor.magical_defense if attack_type == "magical" else actor.physical_defense
    down_key = "mdef_down" if attack_type == "magical" else "pdef_down"
    buff_key = "mdef_buff" if attack_type == "magical" else "pdef_buff"
    down = _effect_value(actor.effects.get(down_key, {}), "percent")
    buff = _effect_value(actor.effects.get(buff_key, {}), "percent")
    return max(0.0, base * (1.0 - down / 100.0) * (1.0 + buff / 100.0))


def _tick_start(actor: PvpActorState, events: list[dict[str, Any]]) -> None:
    # PvE parity: Scout and Rogue restore 20 combat energy at the start of every round,
    # before action cost validation. Energy is duel-local and capped at 100.
    if actor.resource_type in {"combat_energy", "combat_energy_combo"}:
        before_energy = int(actor.resource or 0)
        actor.resource = min(PVP_COMBAT_ENERGY_MAX, before_energy + 20)
        restored = actor.resource - before_energy
        if restored > 0:
            events.append({
                "type": "combat_energy_regen",
                "user_id": actor.user_id,
                "value": restored,
                "before": before_energy,
                "after": actor.resource,
                "maximum": PVP_COMBAT_ENERGY_MAX,
            })
    for key, effect in list(actor.effects.items()):
        kind = effect.get("kind", key)
        if kind in {"poison", "bleed", "dot"}:
            damage = max(0, int(round(_effect_value(effect, "power"))))
            actor.hp = max(0, actor.hp - damage)
            events.append({"type": "dot_tick", "user_id": actor.user_id, "effect": key, "value": damage})
        elif kind in {"hot", "heal_over_time"}:
            healing = max(0, int(round(_effect_value(effect, "power") * PVP_HEALING_MULTIPLIER)))
            before = actor.hp
            actor.hp = min(actor.max_hp, actor.hp + healing)
            events.append({
                "type": "hot_tick", "user_id": actor.user_id, "effect": key,
                "value": actor.hp - before, "nominal_value": healing,
                "hp_before": before, "hp_after": actor.hp, "max_hp": actor.max_hp,
            })
        remaining = int(effect.get("duration", 1)) - 1
        if remaining <= 0:
            del actor.effects[key]
            events.append({"type": "effect_expired", "user_id": actor.user_id, "effect": key})
        else:
            effect["duration"] = remaining
    for key in list(actor.cooldowns):
        actor.cooldowns[key] = max(0, int(actor.cooldowns[key]) - 1)
        if actor.cooldowns[key] == 0:
            del actor.cooldowns[key]


def _terminal(a: PvpActorState, b: PvpActorState, reason: str) -> tuple[bool, int | None, str | None]:
    if a.hp <= 0 and b.hp <= 0:
        return True, None, "draw_" + reason
    if a.hp <= 0:
        return True, b.user_id, reason
    if b.hp <= 0:
        return True, a.user_id, reason
    return False, None, None


def _base_damage(attacker: PvpActorState, defender: PvpActorState, attack_type: str, rng: random.Random) -> tuple[int, bool, bool]:
    dodge = rng.random() * 100 < max(0.0, min(100.0, defender.dodge_chance))
    if dodge:
        return 0, False, True
    if attack_type == "magical":
        weapon = rng.uniform(attacker.weapon_magical_min, attacker.weapon_magical_max)
        attack = attacker.magical_attack
        crit_chance = attacker.magical_crit_chance
    else:
        weapon = rng.uniform(attacker.weapon_physical_min, attacker.weapon_physical_max)
        attack = attacker.physical_attack
        crit_chance = attacker.physical_crit_chance
    damage = max(1.0, weapon + attack - _effective_defense(defender, attack_type) * 0.5)
    critical = rng.random() * 100 < max(0.0, min(100.0, crit_chance))
    if critical:
        damage *= 1.5
    return max(1, int(round(damage * PVP_DAMAGE_MULTIPLIER))), critical, False


def _pay(actor: PvpActorState, skill: Mapping[str, Any]) -> tuple[bool, str, int, int]:
    cost_type = str(skill.get("cost_type") or "")
    cost = max(0, int(skill.get("cost") or 0))
    combo_spent = 0
    if cost_type == "mana":
        if actor.mp < cost: return False, "not_enough_mana", 0, 0
        actor.mp -= cost
    elif cost_type == "rage":
        if actor.resource < cost: return False, "not_enough_rage", 0, 0
        actor.resource -= cost
    elif cost_type in {"combat_energy", "combat_energy_combo"}:
        if actor.resource < cost: return False, "not_enough_combat_energy", 0, 0
        minimum_combo = int(skill.get("min_combo") or (1 if cost_type == "combat_energy_combo" else 0))
        if actor.combo < minimum_combo: return False, "not_enough_combo", 0, 0
        actor.resource -= cost
        if cost_type == "combat_energy_combo":
            combo_spent = actor.combo
            actor.combo = 0
    elif cost_type == "rage_all_min":
        minimum = int(skill.get("min_cost") or 0)
        if actor.resource < minimum: return False, "not_enough_rage", 0, 0
        cost = actor.resource
        actor.resource = 0
    return True, "ok", cost, combo_spent


def _replace_effect(target: PvpActorState, key: str, kind: str, power: float, duration: int, source_id: int) -> dict[str, Any]:
    effect = {"kind": kind, "power": power, "duration": max(1, duration), "source_id": source_id}
    target.effects[key] = effect
    return {"target_id": target.user_id, "effect_key": key, **effect}


def _special(actor: PvpActorState, target: PvpActorState, skill: Mapping[str, Any], direct_damage: int, rng: random.Random) -> tuple[list[dict[str, Any]], int, int]:
    applied: list[dict[str, Any]] = []
    resource_gain = int(skill.get("extra_rage") or skill.get("resource_gain") or 0)
    combo_gain = int(skill.get("combo_gain") or 0)
    effect = str(skill.get("effect") or "")
    duration = int(skill.get("duration") or 0)
    if effect in {"enemy_poison", "enemy_bleed"}:
        kind = "poison" if effect == "enemy_poison" else "bleed"
        applied.append(_replace_effect(target, kind, kind, max(2, round(direct_damage * 0.30)), duration or 3, actor.user_id))
    elif effect in {"enemy_pdef_down", "enemy_pdef_trap"}:
        percent = 30 if effect == "enemy_pdef_down" else 50
        percent *= PVP_DEBUFF_MULTIPLIER
        applied.append(_replace_effect(target, "pdef_down", "pdef_down", percent, duration or (3 if effect == "enemy_pdef_down" else 2), actor.user_id))
        target.effects["pdef_down"]["percent"] = percent
    elif effect == "player_shield":
        amount = max(15, round(actor.physical_defense * 2 + actor.level * 3))
        amount = round(amount * PVP_SHIELD_MULTIPLIER)
        applied.append(_replace_effect(actor, "shield", "shield", amount, duration or 3, actor.user_id))
        actor.effects["shield"]["remaining"] = amount
    elif effect == "player_hot":
        amount = max(5, round(actor.max_hp * 0.10))
        applied.append(_replace_effect(actor, "hot", "hot", amount, duration or 4, actor.user_id))
    elif effect == "restore_mana_percent":
        amount = max(1, round(actor.max_mp * 0.25))
        actor.mp = min(actor.max_mp, actor.mp + amount)
        applied.append({"target_id": actor.user_id, "effect_key": "mana_restore", "power": amount})
    elif effect == "player_cleanse_mdef_buff":
        for key in list(actor.effects):
            if actor.effects[key].get("kind") in {"poison", "bleed", "dot", "pdef_down", "mdef_down", "debuff"}:
                del actor.effects[key]
        applied.append(_replace_effect(actor, "mdef_buff", "mdef_buff", 30, duration or 3, actor.user_id))
        actor.effects["mdef_buff"]["percent"] = 30
        amount = max(1, round(actor.max_mp * 0.15))
        actor.mp = min(actor.max_mp, actor.mp + amount)
    stun_chance = float(skill.get("stun_chance") or 0)
    if stun_chance and rng.random() * 100 < stun_chance:
        target.stunned_next = True
        applied.append({"target_id": target.user_id, "effect_key": "stun_next", "duration": 1})
    return applied, resource_gain, combo_gain


def _shield_absorb(target: PvpActorState, incoming: int, events: list[dict[str, Any]]) -> int:
    shield = target.effects.get("shield")
    if not shield or incoming <= 0:
        return incoming
    remaining = max(0, int(shield.get("remaining", shield.get("power", 0))))
    absorbed = min(remaining, incoming)
    remaining -= absorbed
    if remaining <= 0:
        target.effects.pop("shield", None)
    else:
        shield["remaining"] = remaining
    events.append({"type": "shield_absorb", "user_id": target.user_id, "value": absorbed})
    return incoming - absorbed


def resolve_pvp_round(round_number: int, revision: int, actor_a: PvpActorState, actor_b: PvpActorState, action_a: PvpActionIntent, action_b: PvpActionIntent, seed: int | None = None, catalog: Mapping[str, tuple[dict[str, Any], ...]] | None = None) -> PvpRoundResult:
    if {action_a.user_id, action_b.user_id} != {actor_a.user_id, actor_b.user_id}:
        raise PvpRoundError("action actor mismatch")
    rng = random.Random(seed)
    skills = catalog or load_production_pvp_skill_catalog()
    a, b = actor_a.clone(), actor_b.clone()
    events: list[dict[str, Any]] = []
    _tick_start(a, events); _tick_start(b, events)
    terminal, winner, reason = _terminal(a, b, "periodic")
    no = PvpActionOutcome(a.user_id, "none", None, False, "terminal_before_actions")
    if terminal:
        return PvpRoundResult(round_number, revision, a.to_dict(), b.to_dict(), (no, PvpActionOutcome(b.user_id, "none", None, False, "terminal_before_actions")), tuple(events), True, winner, reason)

    forced: dict[int, str] = {}
    for actor in (a, b):
        if actor.stunned_next:
            forced[actor.user_id] = "stunned_skip"
            actor.stunned_next = False

    prepared: dict[int, dict[str, Any]] = {}
    outcomes: dict[int, PvpActionOutcome] = {}
    pairs = ((a, b, action_a if action_a.user_id == a.user_id else action_b), (b, a, action_b if action_b.user_id == b.user_id else action_a))
    for actor, target, intent in pairs:
        action_type = forced.get(actor.user_id, intent.action_type)
        if action_type in {"afk_skip", "stunned_skip"}:
            if action_type == "afk_skip": actor.consecutive_afk += 1
            else: actor.consecutive_afk = 0
            outcomes[actor.user_id] = PvpActionOutcome(actor.user_id, action_type, None, True, action_type)
            continue
        actor.consecutive_afk = 0
        if action_type == "basic_attack":
            prepared[actor.user_id] = {"actor": actor, "target": target, "intent": intent, "skill": None, "cost": 0, "combo_spent": 0}
            continue
        if action_type != "skill" or not intent.skill_key:
            outcomes[actor.user_id] = PvpActionOutcome(actor.user_id, action_type, intent.skill_key, False, "invalid_action")
            continue
        skill = get_production_pvp_skill(actor.class_key, intent.skill_key, skills)
        if not skill:
            outcomes[actor.user_id] = PvpActionOutcome(actor.user_id, action_type, intent.skill_key, False, "unknown_skill")
            continue
        if actor.cooldowns.get(intent.skill_key, 0) > 0:
            outcomes[actor.user_id] = PvpActionOutcome(actor.user_id, action_type, intent.skill_key, False, "skill_on_cooldown")
            continue
        paid, pay_reason, cost, combo_spent = _pay(actor, skill)
        if not paid:
            outcomes[actor.user_id] = PvpActionOutcome(actor.user_id, action_type, intent.skill_key, False, pay_reason)
            continue
        cooldown = int(skill.get("cooldown") or 0)
        if cooldown > 0: actor.cooldowns[intent.skill_key] = cooldown
        prepared[actor.user_id] = {"actor": actor, "target": target, "intent": intent, "skill": skill, "cost": cost, "combo_spent": combo_spent}

    # Utility and defensive effects are prepared before both damage packets.
    for item in prepared.values():
        skill = item["skill"]
        if skill and (skill.get("no_damage") or float(skill.get("damage_multiplier") or 0) == 0):
            applied, gained, combo_gain = _special(item["actor"], item["target"], skill, 0, rng)
            item["actor"].resource = _clamp(item["actor"].resource + gained, 0, PVP_COMBAT_ENERGY_MAX if "energy" in item["actor"].resource_type else 100)
            item["actor"].combo = _clamp(item["actor"].combo + combo_gain, 0, 3)
            outcomes[item["actor"].user_id] = PvpActionOutcome(item["actor"].user_id, "skill", item["intent"].skill_key, True, "ok", resource_spent=item["cost"], combo_spent=item["combo_spent"], resource_gained=gained, combo_gained=combo_gain, applied_effects=tuple(applied))

    damage_packets: list[tuple[PvpActorState, PvpActorState, int, bool, bool, dict[str, Any]]] = []
    for item in prepared.values():
        actor, target, skill = item["actor"], item["target"], item["skill"]
        if skill and (skill.get("no_damage") or float(skill.get("damage_multiplier") or 0) == 0):
            continue
        attack_type = str((skill or {}).get("attack_type") or ("magical" if actor.class_key in {"mage", "priest"} else "physical"))
        damage, critical, dodged = _base_damage(actor, target, attack_type, rng)
        multiplier = float((skill or {}).get("damage_multiplier") or 1.0)
        damage = 0 if dodged else max(1, round(damage * multiplier))
        # Production flags use the same PvE definitions; no PvP-specific constants are introduced.
        if skill and skill.get("scales_with_spent_rage"):
            damage = max(1, round(damage * (1.0 + item["cost"] / 100.0)))
        if skill and skill.get("scales_with_combo"):
            damage = max(1, round(damage * (1.0 + item["combo_spent"] * 0.35)))
        if skill and skill.get("scales_with_player_pdef"):
            damage = max(1, round(damage + actor.physical_defense * 1.4))
        # PvE parity for rage classes:
        # every executed damaging action grants +15 Rage, then the skill-specific
        # extra_rage is added. This applies to basic attacks and damaging skills.
        attack_rage_gain = PVP_RAGE_GAIN_ON_ATTACK if actor.resource_type == "rage" else 0
        rage_before_attack = int(actor.resource or 0)
        if attack_rage_gain > 0:
            actor.resource = _clamp(actor.resource + attack_rage_gain, 0, 100)
            attack_rage_gain = actor.resource - rage_before_attack
            if attack_rage_gain > 0:
                events.append({
                    "type": "rage_gain_attack",
                    "user_id": actor.user_id,
                    "value": attack_rage_gain,
                    "before": rage_before_attack,
                    "after": actor.resource,
                    "maximum": 100,
                })
        applied, gained, combo_gain = _special(actor, target, skill or {}, damage, rng)
        rage_before_extra = int(actor.resource or 0)
        actor.resource = _clamp(actor.resource + gained, 0, PVP_COMBAT_ENERGY_MAX if "energy" in actor.resource_type else 100)
        actual_extra_gain = actor.resource - rage_before_extra
        item["attack_rage_gain"] = attack_rage_gain
        item["actual_extra_gain"] = actual_extra_gain
        if actual_extra_gain > 0 and actor.resource_type == "rage":
            events.append({
                "type": "rage_gain_skill",
                "user_id": actor.user_id,
                "value": actual_extra_gain,
                "before": rage_before_extra,
                "after": actor.resource,
                "maximum": 100,
            })
        # Production rogue finisher consumes every accumulated combo point.
        # Keep this explicit after special-effect processing so no later gain can resurrect spent combo.
        if item["combo_spent"] > 0:
            actor.combo = 0
        else:
            actor.combo = _clamp(actor.combo + combo_gain, 0, 3)
        damage_packets.append((actor, target, damage, critical, dodged, {"applied": applied, "gained": gained, "combo_gain": combo_gain, "item": item}))

    for actor, target, damage, critical, dodged, meta in damage_packets:
        final_damage = _shield_absorb(target, damage, events)
        target.hp = max(0, target.hp - final_damage)
        # PvE parity: a rage-based defender gains +10 Rage only when positive
        # damage remains after dodge and shield absorption.
        if target.resource_type == "rage" and final_damage > 0:
            rage_before_damage = int(target.resource or 0)
            target.resource = _clamp(target.resource + PVP_RAGE_GAIN_ON_DAMAGE_TAKEN, 0, 100)
            damage_rage_gain = target.resource - rage_before_damage
            if damage_rage_gain > 0:
                events.append({
                    "type": "rage_gain_damage_taken",
                    "user_id": target.user_id,
                    "value": damage_rage_gain,
                    "before": rage_before_damage,
                    "after": target.resource,
                    "maximum": 100,
                    "damage": final_damage,
                })
        item = meta["item"]
        action_resource_gain = int(item.get("actual_extra_gain", meta["gained"]) or 0)
        if actor.resource_type == "rage":
            action_resource_gain += int(item.get("attack_rage_gain", 0) or 0)
        outcomes[actor.user_id] = PvpActionOutcome(actor.user_id, item["intent"].action_type, item["intent"].skill_key, True, "ok", damage=final_damage, critical=critical, dodged=dodged, resource_spent=item["cost"], combo_spent=item["combo_spent"], resource_gained=action_resource_gain, combo_gained=meta["combo_gain"], applied_effects=tuple(meta["applied"]))
        events.append({"type": "damage", "actor_id": actor.user_id, "target_id": target.user_id, "value": final_damage, "critical": critical, "dodged": dodged})

    if a.consecutive_afk >= PVP_CONSECUTIVE_AFK_LIMIT and b.consecutive_afk >= PVP_CONSECUTIVE_AFK_LIMIT:
        terminal, winner, reason = True, None, "technical_draw_both_afk"
    elif a.consecutive_afk >= PVP_CONSECUTIVE_AFK_LIMIT:
        terminal, winner, reason = True, b.user_id, "afk_defeat"
    elif b.consecutive_afk >= PVP_CONSECUTIVE_AFK_LIMIT:
        terminal, winner, reason = True, a.user_id, "afk_defeat"
    else:
        terminal, winner, reason = _terminal(a, b, "simultaneous")
    if not terminal and round_number >= PVP_MAX_ROUNDS:
        a_pct = a.hp / max(1, a.max_hp); b_pct = b.hp / max(1, b.max_hp)
        terminal = True
        winner = a.user_id if a_pct > b_pct else b.user_id if b_pct > a_pct else None
        reason = "round_limit_hp_percent" if winner is not None else "draw_round_limit_equal_hp_percent"
    return PvpRoundResult(round_number, revision, a.to_dict(), b.to_dict(), (outcomes[a.user_id], outcomes[b.user_id]), tuple(events), terminal, winner, reason)
