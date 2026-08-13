from __future__ import annotations

from systems.pvp_production_calibration import CLASSES
from systems.pvp_real_actor_root_cause_audit import (
    run_audit as _BASE_RUN_AUDIT_14_6_3B,
    save_report,
)
from systems.pvp_skill_adapter import load_production_pvp_skill_catalog

VERSION = "14.6.3b1"


# ROM 14.6.3b1 metric-semantics correction layer.
# The original replay remains authoritative. This layer reclassifies terminal
# cancellations, exposes exact skill coverage, normalizes sustain reporting,
# and labels resource families without changing combat execution.

def _b1_metric_semantics(row):
    terminal_cancelled = 0
    policy_invalid = 0
    stunned_skips = 0
    by_class = {}
    for class_key in (row["class_a"], row["class_b"]):
        metric = row["class_metrics"][class_key]
        reasons = dict(metric.get("outcome_reasons") or {})
        cancelled = int(reasons.get("terminal_before_actions", 0) or 0)
        stunned = int(reasons.get("stunned_skip", 0) or 0)
        invalid = int(metric.get("invalid_actions", 0) or 0)
        real_invalid = max(0, invalid - cancelled)
        terminal_cancelled += cancelled
        policy_invalid += real_invalid
        stunned_skips += stunned
        direct = int(metric.get("total_healing", 0) or 0)
        hot = int(metric.get("hot_healing", 0) or 0)
        effective = direct + hot
        trials = max(1, int(row.get("trials", 0) or 0))
        resource_family = {
            "warrior": "rage", "knight": "rage",
            "scout": "combat_energy", "rogue": "combat_energy_combo",
            "mage": "mana", "priest": "mana",
        }[class_key]
        resource = {
            "family": resource_family,
            "spent": int(metric.get("resource_spent", 0) or 0),
            "raw_gained_signal": int(metric.get("resource_gained", 0) or 0),
            "ending_value_legacy": float(metric.get("avg_ending_resource", 0) or 0),
            "ending_value_semantics": "legacy_generic_field_not_used_for_balance_decisions",
        }
        if resource_family == "mana":
            resource.update({
                "mp_spent": resource["spent"],
                "mp_restored_signal": max(0, resource["raw_gained_signal"]),
                "negative_resource_signal_ignored": min(0, resource["raw_gained_signal"]),
            })
        elif resource_family == "rage":
            resource.update({"rage_spent": resource["spent"], "rage_gained": max(0, resource["raw_gained_signal"])})
        else:
            resource.update({"energy_spent": resource["spent"], "energy_gained": max(0, resource["raw_gained_signal"])})
            if class_key == "rogue":
                resource.update({"combo_spent": int(metric.get("combo_spent", 0) or 0), "combo_gained": int(metric.get("combo_gained", 0) or 0), "avg_ending_combo": float(metric.get("avg_ending_combo", 0) or 0)})
        by_class[class_key] = {
            "policy_invalid_actions": real_invalid,
            "terminal_cancelled_intents": cancelled,
            "stunned_skips": stunned,
            "direct_healing": direct,
            "hot_healing": hot,
            "effective_healing_total": effective,
            "avg_effective_healing_per_trial": round(effective / trials, 2),
            "overhealing": None,
            "overhealing_status": "not_emitted_by_current_round_events",
            "resource": resource,
        }
    terminal = dict(row.get("terminal_reasons") or {})
    trials = max(1, int(row.get("trials", 0) or 0))
    periodic = int(terminal.get("periodic", 0) or 0)
    simultaneous = int(terminal.get("simultaneous", 0) or 0) + int(terminal.get("draw_simultaneous", 0) or 0)
    round_limit = sum(int(value or 0) for key, value in terminal.items() if str(key).startswith("round_limit"))
    return {
        "by_class": by_class,
        "policy_invalid_actions": policy_invalid,
        "terminal_cancelled_intents": terminal_cancelled,
        "stunned_skips": stunned_skips,
        "terminal_rates": {
            "round_limit_rate": round(100 * round_limit / trials, 2),
            "periodic_terminal_rate": round(100 * periodic / trials, 2),
            "simultaneous_terminal_rate": round(100 * simultaneous / trials, 2),
        },
    }


def _b1_diagnosis(row, semantics):
    base = dict(row.get("diagnosis") or {})
    winner = base.get("winner_profile")
    loser = base.get("loser_profile")
    signals = [value for value in list(base.get("reason_signals") or []) if value != "invalid_action_present"]
    if winner and loser:
        winner_heal = semantics["by_class"][winner]["avg_effective_healing_per_trial"]
        loser_heal = semantics["by_class"][loser]["avg_effective_healing_per_trial"]
        if winner_heal > loser_heal + 20 and "healing_sustain_gap" not in signals:
            signals.append("healing_sustain_gap")
        if semantics["by_class"][loser]["policy_invalid_actions"] > 0 and "policy_invalid_action_present" not in signals:
            signals.append("policy_invalid_action_present")
    base["reason_signals"] = signals
    base["metric_semantics_version"] = VERSION
    return base


def run_audit(trials=100, seed=14632):
    data = _BASE_RUN_AUDIT_14_6_3B(trials, seed)
    catalog = load_production_pvp_skill_catalog()
    expected = sorted(str(skill.get("key") or "") for class_key in CLASSES for skill in list(catalog.get(class_key) or []) if str(skill.get("key") or ""))
    observed = sorted({key for row in data.get("rows", []) for class_key in (row["class_a"], row["class_b"]) for key in dict(row["class_metrics"][class_key].get("chosen_skills") or {})})
    policy_invalid = terminal_cancelled = stunned = 0
    for row in data.get("rows", []):
        semantics = _b1_metric_semantics(row)
        row["metric_semantics"] = semantics
        row["diagnosis"] = _b1_diagnosis(row, semantics)
        policy_invalid += semantics["policy_invalid_actions"]
        terminal_cancelled += semantics["terminal_cancelled_intents"]
        stunned += semantics["stunned_skips"]
    data["version"] = VERSION
    data["policy_invalid_action_count"] = policy_invalid
    data["terminal_cancelled_intent_count"] = terminal_cancelled
    data["stunned_skip_count"] = stunned
    data["invalid_action_count_legacy"] = int(data.pop("invalid_action_count", 0) or 0)
    data["skill_coverage"] = {
        "expected_skill_keys": expected,
        "observed_skill_keys": observed,
        "missing_skill_keys": sorted(set(expected) - set(observed)),
        "unexpected_skill_keys": sorted(set(observed) - set(expected)),
        "expected_count": len(expected),
        "observed_count": len(observed),
        "pass": set(observed) == set(expected),
    }
    data["distinct_skills_observed"] = len(observed)
    data["metric_semantics_corrected"] = True
    data["balance_decisions_allowed"] = policy_invalid == 0
    return data


def format_summary(data):
    coverage = dict(data.get("skill_coverage") or {})
    missing = list(coverage.get("missing_skill_keys") or [])
    lines = [
        f"PvP root-cause metric semantics audit {data['version']}",
        f"Verdict: {data['verdict']}",
        f"Trials/pair: {data['trials_per_pair']}",
        f"Pairs checked: {data['pairs_checked']}/15",
        f"Dominance pairs: {data['dominance_count']}",
        f"Skill coverage: {coverage.get('observed_count', 0)}/{coverage.get('expected_count', 0)}",
        f"Missing skills: {', '.join(missing) if missing else 'none'}",
        f"Policy-invalid actions: {data.get('policy_invalid_action_count', 0)}",
        f"Terminal-cancelled intents: {data.get('terminal_cancelled_intent_count', 0)}",
        f"Stunned skips: {data.get('stunned_skip_count', 0)}",
        "Effective healing includes direct + HoT: YES",
        "Production engine, skills and policy: YES",
        "Live balance changed: NO",
    ]
    return "\n".join(lines)
