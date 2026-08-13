from __future__ import annotations

import json
import random
from collections import Counter
from contextlib import contextmanager
from pathlib import Path

import systems.pvp_round_engine as engine
from systems.pvp_models import PvpActorState
from systems.pvp_policy_metrics_audit import _choose as choose_action
from systems.pvp_production_calibration import CLASSES
from systems.pvp_real_actor_state_replay import PRODUCTION_REFERENCE, build_real_actor
from systems.pvp_skill_adapter import load_production_pvp_skill_catalog

VERSION = "14.6.4c"
ROUND_CAP = 15
DEX_FACTOR = 0.75

PACING = {
    "none": {"mid_damage": 1.00, "mid_sustain": 1.00, "late_damage": 1.00, "late_sustain": 1.00},
    "soft": {"mid_damage": 1.10, "mid_sustain": 0.90, "late_damage": 1.25, "late_sustain": 0.75},
    "moderate": {"mid_damage": 1.15, "mid_sustain": 0.85, "late_damage": 1.35, "late_sustain": 0.65},
    "strong": {"mid_damage": 1.20, "mid_sustain": 0.80, "late_damage": 1.50, "late_sustain": 0.50},
}

SCENARIOS = {
    "baseline_50": {"round_cap": 50, "dex_scaling": False, "pacing": "none"},
    "dex_base_cap15": {"round_cap": 15, "dex_scaling": True, "pacing": "none"},
    "anti_stall_soft": {"round_cap": 15, "dex_scaling": True, "pacing": "soft"},
    "anti_stall_moderate": {"round_cap": 15, "dex_scaling": True, "pacing": "moderate"},
    "anti_stall_strong": {"round_cap": 15, "dex_scaling": True, "pacing": "strong"},
    "moderate_mage90": {"round_cap": 15, "dex_scaling": True, "pacing": "moderate", "mage_physical_received": 0.90},
    "moderate_mage85": {"round_cap": 15, "dex_scaling": True, "pacing": "moderate", "mage_physical_received": 0.85},
    "balanced_candidate": {"round_cap": 15, "dex_scaling": True, "pacing": "moderate", "mage_physical_received": 0.90, "knight_shield": 0.65, "shield_bash_stun": 15},
}


def _catalog(config):
    source = load_production_pvp_skill_catalog()
    catalog = {class_key: tuple(dict(skill) for skill in skills) for class_key, skills in source.items()}
    if "shield_bash_stun" in config:
        for skill in catalog["knight"]:
            if skill["key"] == "knight_shield_bash":
                skill["stun_chance"] = float(config["shield_bash_stun"])
    return catalog


def _actor(class_key, user_id, config):
    actor = build_real_actor(class_key, user_id)
    if config.get("dex_scaling") and class_key in {"scout", "rogue"}:
        reference = PRODUCTION_REFERENCE[class_key]
        actor.physical_attack = max(float(reference["str"]), float(reference["dex"]) * DEX_FACTOR)
    return actor


def _phase(round_number, pacing_name):
    pacing = PACING[pacing_name]
    if round_number <= 8:
        return "normal", 1.0, 1.0
    if round_number <= 11:
        return "mid", pacing["mid_damage"], pacing["mid_sustain"]
    return "late", pacing["late_damage"], pacing["late_sustain"]


def _scale_active_sustain(actor, sustain_multiplier):
    if sustain_multiplier >= 0.999:
        return 0, 0
    hot_reduced = 0
    shield_reduced = 0
    hot = actor.effects.get("hot")
    if hot:
        current = float(hot.get("power", 0) or 0)
        scaled = max(1, round(current * sustain_multiplier))
        hot_reduced = max(0, round(current - scaled))
        hot["power"] = scaled
    shield = actor.effects.get("shield")
    if shield:
        current = int(shield.get("remaining", shield.get("power", 0)) or 0)
        scaled = max(0, round(current * sustain_multiplier))
        shield_reduced = max(0, current - scaled)
        shield["remaining"] = scaled
        shield["power"] = min(float(shield.get("power", scaled) or scaled), scaled)
        if scaled <= 0:
            actor.effects.pop("shield", None)
    return hot_reduced, shield_reduced


@contextmanager
def _engine_candidate_context(damage_multiplier, shield_multiplier, mage_physical_received):
    old_damage_multiplier = engine.PVP_DAMAGE_MULTIPLIER
    old_shield_multiplier = engine.PVP_SHIELD_MULTIPLIER
    old_damage_function = engine._base_damage

    def candidate_damage(attacker, defender, attack_type, rng):
        damage, critical, dodged = old_damage_function(attacker, defender, attack_type, rng)
        if attack_type == "physical" and defender.class_key == "mage" and damage > 0:
            damage = max(1, round(damage * mage_physical_received))
        return damage, critical, dodged

    engine.PVP_DAMAGE_MULTIPLIER = old_damage_multiplier * damage_multiplier
    engine.PVP_SHIELD_MULTIPLIER = old_shield_multiplier * shield_multiplier
    engine._base_damage = candidate_damage
    try:
        yield
    finally:
        engine._base_damage = old_damage_function
        engine.PVP_SHIELD_MULTIPLIER = old_shield_multiplier
        engine.PVP_DAMAGE_MULTIPLIER = old_damage_multiplier


def _hp_percent(actor):
    return actor.hp / max(1, actor.max_hp)


def _cap_winner(actor_a, actor_b):
    left = _hp_percent(actor_a)
    right = _hp_percent(actor_b)
    if abs(left - right) < 1e-12:
        return None, "round_cap_equal_hp_percent"
    return (actor_a.user_id if left > right else actor_b.user_id), "round_cap_hp_percent"


def _duel(class_a, class_b, trials, seed, config):
    catalog = _catalog(config)
    wins = Counter()
    draws = 0
    rounds = []
    terminals = Counter()
    cap_decisions = Counter()
    pacing_rounds = Counter()
    total_hot_reduced = 0
    total_shield_reduced = 0
    damage_profiles = Counter()
    cap = int(config.get("round_cap", ROUND_CAP))
    pacing_name = str(config.get("pacing", "none"))
    for trial in range(int(trials)):
        swapped = bool(trial % 2)
        left, right = (class_b, class_a) if swapped else (class_a, class_b)
        actor_a = _actor(left, 1, config)
        actor_b = _actor(right, 2, config)
        winner_id = None
        reason = None
        resolved_round = 0
        for round_number in range(1, cap + 1):
            phase, damage_multiplier, sustain_multiplier = _phase(round_number, pacing_name)
            pacing_rounds[phase] += 1
            damage_profiles[f"{damage_multiplier:.2f}"] += 1
            for actor in (actor_a, actor_b):
                hot_reduced, shield_reduced = _scale_active_sustain(actor, sustain_multiplier)
                total_hot_reduced += hot_reduced
                total_shield_reduced += shield_reduced
            intent_a = choose_action(actor_a, actor_b, "target_aware", random.Random(seed + trial * 1000 + round_number), catalog)
            intent_b = choose_action(actor_b, actor_a, "target_aware", random.Random(seed + trial * 1000 + round_number + 37), catalog)
            with _engine_candidate_context(
                damage_multiplier,
                float(config.get("knight_shield", 1.0)) * sustain_multiplier,
                float(config.get("mage_physical_received", 1.0)),
            ):
                result = engine.resolve_pvp_round(
                    round_number,
                    round_number,
                    actor_a,
                    actor_b,
                    intent_a,
                    intent_b,
                    seed=seed + trial * 1000 + round_number,
                    catalog=catalog,
                )
            actor_a = PvpActorState.from_dict(result.actor_a)
            actor_b = PvpActorState.from_dict(result.actor_b)
            resolved_round = round_number
            if result.terminal:
                winner_id = result.winner_id
                reason = str(result.result_reason or "terminal")
                break
        if reason is None:
            winner_id, reason = _cap_winner(actor_a, actor_b)
            cap_decisions[reason] += 1
        terminals[reason] += 1
        rounds.append(resolved_round)
        if winner_id is None:
            draws += 1
        else:
            winner_class = actor_a.class_key if int(winner_id) == actor_a.user_id else actor_b.class_key
            wins[winner_class] += 1
    return {
        "class_a": class_a,
        "class_b": class_b,
        "a_win_rate": round(100 * wins[class_a] / trials, 2),
        "b_win_rate": round(100 * wins[class_b] / trials, 2),
        "draw_rate": round(100 * draws / trials, 2),
        "avg_rounds": round(sum(rounds) / len(rounds), 2),
        "max_rounds_observed": max(rounds),
        "round_cap": cap,
        "cap_decisions": dict(cap_decisions),
        "terminal_reasons": dict(terminals),
        "pacing_rounds": dict(pacing_rounds),
        "damage_multiplier_rounds": dict(damage_profiles),
        "hot_power_reduced_total": total_hot_reduced,
        "shield_remaining_reduced_total": total_shield_reduced,
    }


def _score(rows):
    dominance = sum(1 for row in rows if max(row["a_win_rate"], row["b_win_rate"]) >= 95 or min(row["a_win_rate"], row["b_win_rate"]) <= 5)
    high_draw = sum(1 for row in rows if row["draw_rate"] >= 50)
    class_rates = {
        class_key: round(sum(row["a_win_rate"] if row["class_a"] == class_key else row["b_win_rate"] for row in rows if class_key in (row["class_a"], row["class_b"])) / 5, 2)
        for class_key in CLASSES
    }
    spread = round(max(class_rates.values()) - min(class_rates.values()), 2)
    average_rounds = round(sum(row["avg_rounds"] for row in rows) / len(rows), 2)
    target_pairs = sum(1 for row in rows if 10 <= row["avg_rounds"] <= 15)
    below_10 = sum(1 for row in rows if row["avg_rounds"] < 10)
    cap_count = sum(sum(row["cap_decisions"].values()) for row in rows)
    battle_count = sum(sum(row["terminal_reasons"].values()) for row in rows)
    cap_rate = round(100 * cap_count / max(1, battle_count), 2)
    below_20 = sum(1 for value in class_rates.values() if value < 20)
    above_80 = sum(1 for value in class_rates.values() if value > 80)
    objective = round(
        dominance * 100 + high_draw * 50 + spread + below_20 * 100 + above_80 * 100 + below_10 * 10 + cap_rate * 2,
        2,
    )
    return {
        "dominance_count": dominance,
        "high_draw_count": high_draw,
        "class_average_win_rates": class_rates,
        "class_win_rate_spread_pp": spread,
        "average_rounds_all_pairs": average_rounds,
        "pairs_in_10_15_average_round_target": target_pairs,
        "pairs_below_10_average_rounds": below_10,
        "round_cap_decision_rate_pct": cap_rate,
        "classes_below_20": below_20,
        "classes_above_80": above_80,
        "objective": objective,
    }


def run_sandbox(trials=50, seed=14643):
    trials = max(10, min(150, int(trials)))
    scenarios = {}
    for scenario_index, (name, config) in enumerate(SCENARIOS.items()):
        rows = []
        for i, class_a in enumerate(CLASSES):
            for j in range(i + 1, len(CLASSES)):
                rows.append(_duel(class_a, CLASSES[j], trials, seed + scenario_index * 1000000 + i * 100000 + j * 1000, config))
        scenarios[name] = {"config": config, "rows": rows, "score": _score(rows)}
    ranking = sorted(scenarios, key=lambda name: (scenarios[name]["score"]["objective"], name))
    return {
        "version": VERSION,
        "verdict": "PASS_WITH_REVIEW",
        "trials_per_pair": trials,
        "target_round_range": [10, 15],
        "target_cap_decision_rate_max_pct": 15,
        "scenarios": scenarios,
        "ranking": ranking,
        "recommended_candidate": ranking[0],
        "recommendation_status": "SANDBOX_ONLY_NOT_APPROVED_FOR_LIVE",
        "siege_readiness_note": "Preferred candidate should naturally finish most battles by round 15; HP-percent tiebreak remains emergency fallback only.",
        "production_round_resolver_used": True,
        "production_skill_catalog_used": True,
        "production_policy_used": True,
        "live_balance_changed": False,
        "fixture_values_changed": False,
        "production_database_writes": 0,
    }


def save_report(data, path):
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return output


def format_summary(data):
    lines = [
        f"PvP anti-stall and survivability candidate sandbox {data['version']}",
        f"Verdict: {data['verdict']}",
        f"Trials/pair/scenario: {data['trials_per_pair']}",
        "Target: 10-15 rounds, cap decisions <=15%",
    ]
    for name in data["ranking"]:
        score = data["scenarios"][name]["score"]
        lines.append(
            f"{name}: dominance={score['dominance_count']}, spread={score['class_win_rate_spread_pp']} pp, "
            f"avg_rounds={score['average_rounds_all_pairs']}, target_pairs={score['pairs_in_10_15_average_round_target']}/15, "
            f"cap_rate={score['round_cap_decision_rate_pct']}%, objective={score['objective']}"
        )
    lines.extend([
        f"Recommended sandbox candidate: {data['recommended_candidate']}",
        "Live approval: NO",
        "Live balance changed: NO",
    ])
    return "\n".join(lines)
