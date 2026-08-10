from __future__ import annotations

import json
import random
from collections import Counter
from pathlib import Path

from systems.pvp_balance_simulator import CLASSES, LABELS, actor
from systems.pvp_models import PvpActionIntent, PvpActorState
from systems.pvp_round_engine import resolve_pvp_round
from systems.pvp_skill_adapter import load_production_pvp_skill_catalog

POLICIES = ("priority", "random_valid", "resource_aware", "target_aware")
NEGATIVE_KINDS = {"poison", "bleed", "dot", "pdef_down", "mdef_down", "debuff"}


def _projected_resource(value):
    return min(100, int(value.resource) + 20) if "energy" in value.resource_type else int(value.resource)


def _valid(value, skill):
    if int(value.cooldowns.get(skill["key"], 0) or 0) > 1:
        return False
    cost_type = str(skill.get("cost_type") or "")
    cost = int(skill.get("cost") or 0)
    projected = _projected_resource(value)
    if cost_type == "mana" and value.mp < cost:
        return False
    if cost_type == "rage" and value.resource < cost:
        return False
    if cost_type == "rage_all_min" and value.resource < int(skill.get("min_cost") or 0):
        return False
    if cost_type in {"combat_energy", "combat_energy_combo"} and projected < cost:
        return False
    if cost_type == "combat_energy_combo" and value.combo < int(skill.get("min_combo") or 1):
        return False
    return True


def _resource_valid(value, skill):
    cost_type = str(skill.get("cost_type") or "")
    cost = int(skill.get("cost") or 0)
    projected = _projected_resource(value)
    if cost_type == "mana":
        return value.mp >= cost
    if cost_type == "rage":
        return value.resource >= cost
    if cost_type == "rage_all_min":
        return value.resource >= int(skill.get("min_cost") or 0)
    if cost_type in {"combat_energy", "combat_energy_combo"}:
        if projected < cost:
            return False
        if cost_type == "combat_energy_combo":
            return value.combo >= int(skill.get("min_combo") or 1)
    return True


def _cooldown_ready(value, skill):
    return int(value.cooldowns.get(skill["key"], 0) or 0) <= 1


def _intent(value, key=None):
    return PvpActionIntent(value.user_id, "skill", key) if key else PvpActionIntent(value.user_id, "basic_attack")


def _remaining_effect(value, key):
    return int(dict(value.effects.get(key) or {}).get("duration", 0) or 0)


def _choose(value, opponent, policy, rng, catalog):
    valid = [skill for skill in catalog[value.class_key] if _valid(value, skill)]
    by_key = {skill["key"]: skill for skill in valid}

    if policy == "random_valid":
        choice = rng.choice([None] + valid)
        return _intent(value, choice["key"] if choice else None)

    if policy == "target_aware":
        cls = value.class_key
        if cls == "warrior":
            if "warrior_suppression" in by_key and _remaining_effect(opponent, "pdef_down") <= 1:
                return _intent(value, "warrior_suppression")
            if "warrior_subjugation_strike" in by_key and value.resource >= 70 and _remaining_effect(opponent, "pdef_down") > 0:
                return _intent(value, "warrior_subjugation_strike")
            if "warrior_cleave" in by_key:
                return _intent(value, "warrior_cleave")
        elif cls == "knight":
            shield = dict(value.effects.get("shield") or {})
            remaining = int(shield.get("remaining", 0) or 0)
            if "knight_holy_protection" in by_key and remaining <= 25:
                return _intent(value, "knight_holy_protection")
            if "knight_judgement" in by_key and value.resource >= 50:
                return _intent(value, "knight_judgement")
            if "knight_shield_bash" in by_key:
                return _intent(value, "knight_shield_bash")
        elif cls == "scout":
            if "scout_sting_arrow" in by_key and _remaining_effect(opponent, "poison") <= 1:
                return _intent(value, "scout_sting_arrow")
            if "scout_trap" in by_key and _remaining_effect(opponent, "pdef_down") <= 1:
                return _intent(value, "scout_trap")
            if "scout_aimed_shot" in by_key:
                return _intent(value, "scout_aimed_shot")
        elif cls == "rogue":
            if value.combo >= 3 and "rogue_eviscerate" in by_key:
                return _intent(value, "rogue_eviscerate")
            if "rogue_bleeding_follow" in by_key and _remaining_effect(opponent, "bleed") <= 1:
                return _intent(value, "rogue_bleeding_follow")
            if "rogue_sneak_strike" in by_key:
                return _intent(value, "rogue_sneak_strike")
        elif cls == "mage":
            offensive = [key for key in ("mage_thunder_spell", "mage_fireball") if key in by_key]
            if offensive:
                return _intent(value, offensive[0])
            if "mage_arcane_flow" in by_key and value.mp <= 125:
                return _intent(value, "mage_arcane_flow")
        elif cls == "priest":
            hot_left = _remaining_effect(value, "hot")
            hp_pct = value.hp / max(1, value.max_hp)
            has_debuff = any(dict(effect).get("kind") in NEGATIVE_KINDS for effect in value.effects.values())
            if "priest_purify_faith" in by_key and (has_debuff or value.mp < 120):
                return _intent(value, "priest_purify_faith")
            if "priest_healing_blessing" in by_key and hp_pct <= 0.65 and hot_left <= 1:
                return _intent(value, "priest_healing_blessing")
            if "priest_holy_ray" in by_key:
                return _intent(value, "priest_holy_ray")
        if valid:
            return _intent(value, valid[-1]["key"])
        return _intent(value)

    if policy == "resource_aware":
        cls = value.class_key
        if cls == "warrior":
            if "warrior_suppression" in by_key and "pdef_down" not in value.effects:
                return _intent(value, "warrior_suppression")
            if "warrior_subjugation_strike" in by_key and value.resource >= 70:
                return _intent(value, "warrior_subjugation_strike")
            if "warrior_cleave" in by_key:
                return _intent(value, "warrior_cleave")
        if cls == "knight":
            remaining = int(dict(value.effects.get("shield") or {}).get("remaining", 0) or 0)
            if "knight_holy_protection" in by_key and remaining < 100:
                return _intent(value, "knight_holy_protection")
        if cls == "scout":
            for key in ("scout_sting_arrow", "scout_trap", "scout_aimed_shot"):
                if key in by_key:
                    return _intent(value, key)
        if cls == "rogue":
            if value.combo >= 3 and "rogue_eviscerate" in by_key:
                return _intent(value, "rogue_eviscerate")
            for key in ("rogue_bleeding_follow", "rogue_sneak_strike"):
                if key in by_key:
                    return _intent(value, key)
        if cls == "mage":
            if value.mp <= 125 and "mage_arcane_flow" in by_key:
                return _intent(value, "mage_arcane_flow")
            for key in ("mage_thunder_spell", "mage_fireball"):
                if key in by_key:
                    return _intent(value, key)
        if cls == "priest":
            hot = dict(value.effects.get("hot") or {})
            hp_pct = value.hp / max(1, value.max_hp)
            if "priest_healing_blessing" in by_key and hp_pct < 0.75 and int(hot.get("duration", 0) or 0) <= 1:
                return _intent(value, "priest_healing_blessing")
            if "priest_purify_faith" in by_key and (value.mp < 150 or any(dict(x).get("kind") in NEGATIVE_KINDS for x in value.effects.values())):
                return _intent(value, "priest_purify_faith")
            if "priest_holy_ray" in by_key:
                return _intent(value, "priest_holy_ray")
        if valid:
            return _intent(value, valid[-1]["key"])
        return _intent(value)

    if valid:
        return _intent(value, valid[-1]["key"])
    return _intent(value)


def _blank():
    return {
        "actions": Counter(), "skill_success": Counter(), "damage_dealt": 0,
        "healing_done": 0, "healing_received": 0, "overheal": 0,
        "shield_casts": 0, "shield_absorbed": 0, "shield_uptime_rounds": 0,
        "dot_applications": 0, "dot_refreshes": 0, "dot_ticks_dealt": 0,
        "dot_damage_dealt": 0, "dot_ticks_received": 0, "dot_damage_received": 0,
        "dot_uptime_rounds": 0, "hot_casts": 0, "hot_refreshes": 0,
        "hot_ticks": 0, "hot_uptime_rounds": 0, "debuff_applications": 0,
        "debuff_refreshes": 0, "debuff_uptime_rounds": 0, "cleanse_casts": 0,
        "debuffs_removed": 0, "stuns_applied": 0, "stunned_rounds_inflicted": 0,
        "stunned_rounds_received": 0, "resource_spent": 0,
        "resource_gained_attack": 0, "resource_gained_damage_taken": 0,
        "resource_gained_skill": 0, "resource_gained_round_regen": 0,
        "resource_restored_skill": 0, "resource_wasted_at_cap": 0, "resource_starved_rounds": 0,
 "no_valid_skill_rounds": 0, "cooldown_blocked_rounds": 0,
 "policy_basic_attack_rounds": 0, "combo_gained": 0, "combo_spent": 0,
        "eviscerate_1_combo": 0, "eviscerate_2_combo": 0, "eviscerate_3_combo": 0,
        "rounds": 0, "wins": 0, "losses": 0, "draws": 0,
    }


def _effect_uptime(values, metrics):
    by_id = {value.user_id: value for value in values}
    for owner in values:
        for effect in owner.effects.values():
            effect = dict(effect)
            source_id = int(effect.get("source_id") or owner.user_id)
            source = metrics.get(source_id)
            received = metrics.get(owner.user_id)
            kind = str(effect.get("kind") or "")
            if kind in {"poison", "bleed", "dot"}:
                if source: source["dot_uptime_rounds"] += 1
            elif kind in {"hot", "heal_over_time"}:
                if source: source["hot_uptime_rounds"] += 1
            elif kind in {"pdef_down", "mdef_down", "debuff"}:
                if source: source["debuff_uptime_rounds"] += 1
            elif kind == "shield" and received:
                received["shield_uptime_rounds"] += 1


def _merge(dst, src):
    for key, value in src.items():
        if isinstance(value, Counter):
            dst[key].update(value)
        else:
            dst[key] += value


def simulate_duel(class_a, class_b, policy, seed):
    catalog = load_production_pvp_skill_catalog()
    left, right = actor(1, class_a), actor(2, class_b)
    rng = random.Random(seed)
    metrics = {1: _blank(), 2: _blank()}
    pending_stun_source = {}
    result = None
    for round_number in range(1, 51):
        before = {1: left.clone(), 2: right.clone()}
        _effect_uptime((left, right), metrics)
        left_intent = _choose(left, right, policy, rng, catalog)
        right_intent = _choose(right, left, policy, rng, catalog)
        metrics[1]["actions"][left_intent.skill_key or left_intent.action_type] += 1
        metrics[2]["actions"][right_intent.skill_key or right_intent.action_type] += 1
        for uid, value, intent in ((1, left, left_intent), (2, right, right_intent)):
            if value.resource_type in {"combat_energy", "combat_energy_combo"}:
                metrics[uid]["resource_wasted_at_cap"] += max(0, 20 - (min(100, value.resource + 20) - value.resource))
            if intent.action_type == "basic_attack":
                skills = list(catalog[value.class_key])
                valid_skills = [skill for skill in skills if _valid(value, skill)]
                resource_ready = [skill for skill in skills if _resource_valid(value, skill)]
                if valid_skills:
                    metrics[uid]["policy_basic_attack_rounds"] += 1
                else:
                    metrics[uid]["no_valid_skill_rounds"] += 1
                    if not resource_ready:
                        metrics[uid]["resource_starved_rounds"] += 1
                    elif not any(_cooldown_ready(value, skill) for skill in resource_ready):
                        metrics[uid]["cooldown_blocked_rounds"] += 1
        result = resolve_pvp_round(round_number, round_number, left, right, left_intent, right_intent, seed=seed * 1000 + round_number, catalog=catalog)
        after = {1: PvpActorState.from_dict(result.actor_a), 2: PvpActorState.from_dict(result.actor_b)}

        for outcome in result.outcomes:
            uid = int(outcome.user_id)
            metric = metrics[uid]
            metric["damage_dealt"] += int(outcome.damage or 0)
            metric["resource_spent"] += int(outcome.resource_spent or 0)
            # Engine events are the canonical Rage/Energy source. outcome.resource_gained
            # is an aggregate and must not be added again.
            metric["combo_spent"] += int(outcome.combo_spent or 0)
            if before[uid].resource_type == "mana" and outcome.valid:
                restored = max(0, int(after[uid].mp) - int(before[uid].mp) + int(outcome.resource_spent or 0))
                metric["resource_restored_skill"] += restored
            metric["combo_gained"] += int(outcome.combo_gained or 0)
            if outcome.valid:
                metric["skill_success"][outcome.skill_key or outcome.action_type] += 1
            if outcome.action_type == "stunned_skip":
                metric["stunned_rounds_received"] += 1
                source_id = int(pending_stun_source.pop(uid, 0) or 0)
                if source_id in metrics:
                    metrics[source_id]["stunned_rounds_inflicted"] += 1
            if outcome.skill_key == "rogue_eviscerate":
                spent = int(outcome.combo_spent or 0)
                if spent in (1, 2, 3): metric[f"eviscerate_{spent}_combo"] += 1
            if outcome.skill_key == "priest_purify_faith" and outcome.valid:
                metric["cleanse_casts"] += 1
                old_debuffs = sum(1 for effect in before[uid].effects.values() if dict(effect).get("kind") in NEGATIVE_KINDS)
                new_debuffs = sum(1 for effect in after[uid].effects.values() if dict(effect).get("kind") in NEGATIVE_KINDS)
                metric["debuffs_removed"] += max(0, old_debuffs - new_debuffs)
            for applied in outcome.applied_effects:
                applied = dict(applied)
                key = str(applied.get("effect_key") or "")
                target_id = int(applied.get("target_id") or uid)
                existed = key in before[target_id].effects if target_id in before else False
                if key in {"poison", "bleed"}:
                    metric["dot_refreshes" if existed else "dot_applications"] += 1
                elif key == "hot":
                    metric["hot_refreshes" if existed else "hot_casts"] += 1
                elif key == "shield":
                    metric["shield_casts"] += 1
                elif key in {"pdef_down", "mdef_down"}:
                    metric["debuff_refreshes" if existed else "debuff_applications"] += 1
                elif key == "stun_next":
                    metric["stuns_applied"] += 1
                    pending_stun_source[target_id] = uid
                elif key == "mana_restore":
                    # Counted once through MP state delta.
                    pass

        for event in result.events:
            kind = str(event.get("type") or "")
            uid = int(event.get("user_id") or 0)
            if kind == "combat_energy_regen" and uid in metrics:
                metrics[uid]["resource_gained_round_regen"] += int(event.get("value") or 0)
            elif kind == "rage_gain_attack" and uid in metrics:
                metrics[uid]["resource_gained_attack"] += int(event.get("value") or 0)
            elif kind == "rage_gain_damage_taken" and uid in metrics:
                metrics[uid]["resource_gained_damage_taken"] += int(event.get("value") or 0)
            elif kind == "rage_gain_skill" and uid in metrics:
                metrics[uid]["resource_gained_skill"] += int(event.get("value") or 0)
            elif kind == "hot_tick" and uid in metrics:
                source_id = int(dict(before[uid].effects.get(str(event.get("effect") or "hot")) or {}).get("source_id") or uid)
                value = int(event.get("value") or 0)
                metrics[uid]["healing_received"] += value
                if source_id in metrics: metrics[source_id]["healing_done"] += value; metrics[source_id]["hot_ticks"] += 1; metrics[source_id]["overheal"] += max(0, int(event.get("nominal_value") or 0) - value)
            elif kind == "dot_tick" and uid in metrics:
                key = str(event.get("effect") or "")
                source_id = int(dict(before[uid].effects.get(key) or {}).get("source_id") or 0)
                value = int(event.get("value") or 0)
                metrics[uid]["dot_ticks_received"] += 1; metrics[uid]["dot_damage_received"] += value
                if source_id in metrics: metrics[source_id]["dot_ticks_dealt"] += 1; metrics[source_id]["dot_damage_dealt"] += value
            elif kind == "shield_absorb" and uid in metrics:
                metrics[uid]["shield_absorbed"] += int(event.get("value") or 0)

        left, right = after[1], after[2]
        metrics[1]["rounds"] = round_number; metrics[2]["rounds"] = round_number
        if result.terminal:
            break
    if result.winner_id == 1:
        metrics[1]["wins"] += 1; metrics[2]["losses"] += 1
    elif result.winner_id == 2:
        metrics[2]["wins"] += 1; metrics[1]["losses"] += 1
    else:
        metrics[1]["draws"] += 1; metrics[2]["draws"] += 1
    return result, metrics


def audit_policy(policy, trials=25, seed=1461):
    if policy not in POLICIES:
        raise ValueError("unknown policy")
    trials = max(1, min(300, int(trials)))
    classes = {key: _blank() for key in CLASSES}
    matchups = []
    for i, class_a in enumerate(CLASSES):
        for j, class_b in enumerate(CLASSES):
            wins_a = wins_b = draws = rounds = 0
            for trial in range(trials):
                result, duel_metrics = simulate_duel(class_a, class_b, policy, seed + i * 100000 + j * 1000 + trial)
                _merge(classes[class_a], duel_metrics[1]); _merge(classes[class_b], duel_metrics[2])
                rounds += result.round_number
                if result.winner_id == 1: wins_a += 1
                elif result.winner_id == 2: wins_b += 1
                else: draws += 1
            matchups.append({"class_a": class_a, "class_b": class_b, "wins_a": wins_a, "wins_b": wins_b, "draws": draws, "trials": trials, "avg_rounds": round(rounds / trials, 2)})
    summary = {}
    for cls, metric in classes.items():
        games = metric["wins"] + metric["losses"] + metric["draws"]
        non_mirror = [row for row in matchups if row["class_a"] == cls and row["class_b"] != cls]
        non_mirror_wins = sum(row["wins_a"] for row in non_mirror)
        non_mirror_games = sum(row["trials"] for row in non_mirror)
        row = {key: (dict(value) if isinstance(value, Counter) else value) for key, value in metric.items()}
        row.update({"games": games, "win_rate": round(100 * metric["wins"] / max(1, games), 2), "non_mirror_win_rate": round(100 * non_mirror_wins / max(1, non_mirror_games), 2), "avg_rounds": round(metric["rounds"] / max(1, games), 2)})
        row["resource_gained_total"] = sum(row[key] for key in ("resource_gained_attack", "resource_gained_damage_taken", "resource_gained_skill", "resource_gained_round_regen", "resource_restored_skill"))
        summary[cls] = row
    return {"policy": policy, "trials_per_matchup": trials, "class_summary": summary, "matchups": matchups}


def audit_all_policies(trials=25):
    return {"version": "14.6.1a", "policies": {policy: audit_policy(policy, trials) for policy in POLICIES}, "balance_changes_applied": False, "synthetic_equalized_actors": True, "metrics_attribution": "source_and_target_v2"}


def save_report(data, path):
    value = Path(path); value.parent.mkdir(parents=True, exist_ok=True)
    value.write_text(json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return value


def format_summary(data):
    first = next(iter(data["policies"].values()))
    lines = ["🔬 <b>PvP policy audit 14.6.1a</b>", f"\nСимуляцій на matchup: {first['trials_per_matchup']}"]
    for policy, report in data["policies"].items():
        lines.append(f"\n<b>{policy}</b>")
        for cls, row in sorted(report["class_summary"].items(), key=lambda item: item[1]["non_mirror_win_rate"], reverse=True):
            lines.append(f"{LABELS[cls]}: non-mirror {row['non_mirror_win_rate']}%, overall {row['win_rate']}%")
    return "\n".join(lines)
