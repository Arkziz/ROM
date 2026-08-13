from __future__ import annotations

import json
import random
from collections import Counter
from pathlib import Path

from systems.pvp_models import PvpActorState
from systems.pvp_policy_metrics_audit import _choose as choose_action
from systems.pvp_production_calibration import CLASSES
from systems.pvp_real_actor_state_replay import PRODUCTION_REFERENCE, build_real_actor
from systems.pvp_round_engine import resolve_pvp_round
from systems.pvp_skill_adapter import load_production_pvp_skill_catalog

VERSION = "14.6.4b"
TARGET_ROUND_MIN = 10
TARGET_ROUND_MAX = 15
HARD_ROUND_CAP = 15

SCENARIOS = {
    "baseline_50": {"round_cap": 50},
    "cap15_only": {"round_cap": 15},
    "dex_add_035_cap15": {"round_cap": 15, "dex_model": "str_plus_dex", "dex_factor": 0.35},
    "dex_add_050_cap15": {"round_cap": 15, "dex_model": "str_plus_dex", "dex_factor": 0.50},
    "dex_floor_075_cap15": {"round_cap": 15, "dex_model": "max_str_dex", "dex_factor": 0.75},
    "dex_add_035_mage112_cap15": {"round_cap": 15, "dex_model": "str_plus_dex", "dex_factor": 0.35, "mage_matk": 1.12},
    "dex_add_050_mage112_cap15": {"round_cap": 15, "dex_model": "str_plus_dex", "dex_factor": 0.50, "mage_matk": 1.12},
    "dex_floor_075_mage112_cap15": {"round_cap": 15, "dex_model": "max_str_dex", "dex_factor": 0.75, "mage_matk": 1.12},
}


def _actor(class_key, user_id, config):
    actor = build_real_actor(class_key, user_id)
    reference = PRODUCTION_REFERENCE[class_key]
    if class_key in {"scout", "rogue"} and config.get("dex_model"):
        strength = float(reference["str"])
        dexterity = float(reference["dex"])
        factor = float(config["dex_factor"])
        if config["dex_model"] == "str_plus_dex":
            actor.physical_attack = strength + dexterity * factor
        elif config["dex_model"] == "max_str_dex":
            actor.physical_attack = max(strength, dexterity * factor)
        else:
            raise ValueError(f"unknown dex_model={config['dex_model']}")
    if class_key == "mage":
        actor.magical_attack *= float(config.get("mage_matk", 1.0))
    return actor


def _hp_percent(actor):
    return actor.hp / max(1, actor.max_hp)


def _cap_winner(actor_a, actor_b):
    pct_a = _hp_percent(actor_a)
    pct_b = _hp_percent(actor_b)
    if abs(pct_a - pct_b) < 1e-12:
        return None, "round_cap_equal_hp_percent"
    return (actor_a.user_id if pct_a > pct_b else actor_b.user_id), "round_cap_hp_percent"


def _duel(class_a, class_b, trials, seed, config):
    catalog = load_production_pvp_skill_catalog()
    wins = Counter()
    draws = 0
    rounds = []
    terminal_reasons = Counter()
    cap_decisions = Counter()
    initial_attacks = {}
    for class_key in (class_a, class_b):
        snapshot = _actor(class_key, 99, config)
        initial_attacks[class_key] = {
            "physical_attack": round(snapshot.physical_attack, 3),
            "magical_attack": round(snapshot.magical_attack, 3),
        }
    cap = int(config.get("round_cap", 50))
    for trial in range(int(trials)):
        swapped = bool(trial % 2)
        left, right = (class_b, class_a) if swapped else (class_a, class_b)
        actor_a = _actor(left, 1, config)
        actor_b = _actor(right, 2, config)
        winner_id = None
        reason = None
        resolved_round = 0
        for round_number in range(1, cap + 1):
            intent_a = choose_action(actor_a, actor_b, "target_aware", random.Random(seed + trial * 1000 + round_number), catalog)
            intent_b = choose_action(actor_b, actor_a, "target_aware", random.Random(seed + trial * 1000 + round_number + 37), catalog)
            result = resolve_pvp_round(round_number, round_number, actor_a, actor_b, intent_a, intent_b, seed=seed + trial * 1000 + round_number, catalog=catalog)
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
        terminal_reasons[reason] += 1
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
        "terminal_reasons": dict(terminal_reasons),
        "initial_attacks": initial_attacks,
    }


def _score(rows):
    dominance = sum(1 for row in rows if max(row["a_win_rate"], row["b_win_rate"]) >= 95 or min(row["a_win_rate"], row["b_win_rate"]) <= 5)
    high_draw = sum(1 for row in rows if row["draw_rate"] >= 50)
    class_rates = {
        class_key: round(sum(row["a_win_rate"] if row["class_a"] == class_key else row["b_win_rate"] for row in rows if class_key in (row["class_a"], row["class_b"])) / 5, 2)
        for class_key in CLASSES
    }
    spread = round(max(class_rates.values()) - min(class_rates.values()), 2)
    avg_rounds = round(sum(row["avg_rounds"] for row in rows) / len(rows), 2)
    over_15 = sum(1 for row in rows if row["max_rounds_observed"] > 15)
    under_10 = sum(1 for row in rows if row["avg_rounds"] < TARGET_ROUND_MIN)
    in_target = sum(1 for row in rows if TARGET_ROUND_MIN <= row["avg_rounds"] <= TARGET_ROUND_MAX)
    cap_rate = round(100 * sum(sum(row["cap_decisions"].values()) for row in rows) / max(1, sum(sum(row["terminal_reasons"].values()) for row in rows)), 2)
    below = sum(1 for value in class_rates.values() if value < 20)
    above = sum(1 for value in class_rates.values() if value > 80)
    objective = round(dominance * 100 + high_draw * 50 + spread + below * 100 + above * 100 + under_10 * 10 + cap_rate, 2)
    return {
        "dominance_count": dominance,
        "high_draw_count": high_draw,
        "class_average_win_rates": class_rates,
        "class_win_rate_spread_pp": spread,
        "average_rounds_all_pairs": avg_rounds,
        "pairs_in_10_15_average_round_target": in_target,
        "pairs_below_10_average_rounds": under_10,
        "pairs_above_15_observed_rounds": over_15,
        "round_cap_decision_rate_pct": cap_rate,
        "classes_below_20": below,
        "classes_above_80": above,
        "objective": objective,
    }


def run_sandbox(trials=50, seed=14642):
    trials = max(10, min(200, int(trials)))
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
        "target_round_range": [TARGET_ROUND_MIN, TARGET_ROUND_MAX],
        "scenarios": scenarios,
        "ranking": ranking,
        "recommended_candidate": ranking[0],
        "recommendation_status": "SANDBOX_ONLY_NOT_APPROVED_FOR_LIVE",
        "pacing_design_note": "15-round hard cap with HP-percent tiebreak is tested for future siege scalability; cap-decision rate must remain low enough to avoid replacing combat with timeout scoring.",
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
        f"PvP primary-stat scaling and combat-pacing sandbox {data['version']}",
        f"Verdict: {data['verdict']}",
        f"Trials/pair/scenario: {data['trials_per_pair']}",
        f"Target rounds: {data['target_round_range'][0]}-{data['target_round_range'][1]}",
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
