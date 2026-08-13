from __future__ import annotations

import json
import random
from collections import Counter, defaultdict
from pathlib import Path

from systems.pvp_models import PvpActorState
from systems.pvp_policy_metrics_audit import _choose as choose_action
from systems.pvp_production_calibration import CLASSES
from systems.pvp_real_actor_state_replay import build_real_actor
from systems.pvp_round_engine import resolve_pvp_round
from systems.pvp_skill_adapter import load_production_pvp_skill_catalog

VERSION = "14.6.3b"
DOMINANCE_REVIEW_WIN_RATE = 95.0


def _empty_metrics():
    return {
        "actions": Counter(), "chosen_skills": Counter(), "outcome_reasons": Counter(),
        "invalid_actions": 0, "valid_actions": 0, "basic_attacks": 0, "skill_actions": 0,
        "damage": 0, "healing": 0, "critical_hits": 0, "dodges_caused": 0,
        "resource_spent": 0, "resource_gained": 0, "combo_spent": 0, "combo_gained": 0,
        "dot_damage": 0, "hot_healing": 0, "shield_absorbed": 0,
        "effects_applied": Counter(), "cooldown_blocked_rounds": 0,
        "resource_blocked_rounds": 0, "rounds": 0, "ending_resource": 0,
        "ending_combo": 0, "ending_hp": 0, "wins": 0,
        "damage_by_action": defaultdict(int), "uses_by_action": Counter(),
    }


def _serialise(metrics, trials):
    uses = dict(sorted(metrics["uses_by_action"].items()))
    damage_by = dict(sorted(metrics["damage_by_action"].items()))
    avg_damage_by_use = {key: round(damage_by.get(key, 0) / max(1, count), 2) for key, count in uses.items()}
    return {
        "actions": dict(sorted(metrics["actions"].items())),
        "chosen_skills": dict(sorted(metrics["chosen_skills"].items())),
        "outcome_reasons": dict(sorted(metrics["outcome_reasons"].items())),
        "invalid_actions": metrics["invalid_actions"], "valid_actions": metrics["valid_actions"],
        "basic_attacks": metrics["basic_attacks"], "skill_actions": metrics["skill_actions"],
        "total_damage": metrics["damage"], "avg_damage_per_trial": round(metrics["damage"] / trials, 2),
        "total_healing": metrics["healing"], "avg_healing_per_trial": round(metrics["healing"] / trials, 2),
        "critical_hits": metrics["critical_hits"], "dodges_caused": metrics["dodges_caused"],
        "resource_spent": metrics["resource_spent"], "resource_gained": metrics["resource_gained"],
        "combo_spent": metrics["combo_spent"], "combo_gained": metrics["combo_gained"],
        "dot_damage": metrics["dot_damage"], "hot_healing": metrics["hot_healing"],
        "shield_absorbed": metrics["shield_absorbed"],
        "effects_applied": dict(sorted(metrics["effects_applied"].items())),
        "cooldown_blocked_rounds": metrics["cooldown_blocked_rounds"],
        "resource_blocked_rounds": metrics["resource_blocked_rounds"],
        "avg_rounds": round(metrics["rounds"] / trials, 2),
        "avg_ending_resource": round(metrics["ending_resource"] / trials, 2),
        "avg_ending_combo": round(metrics["ending_combo"] / trials, 2),
        "avg_ending_hp": round(metrics["ending_hp"] / trials, 2),
        "wins": metrics["wins"], "win_rate": round(100 * metrics["wins"] / trials, 2),
        "uses_by_action": uses, "damage_by_action": damage_by,
        "avg_damage_by_action_use": avg_damage_by_use,
    }


def _availability(actor, catalog):
    skills = list(catalog.get(actor.class_key) or [])
    cooldown_blocked = 0; resource_blocked = 0
    projected = min(100, int(actor.resource or 0) + 20) if "energy" in actor.resource_type else int(actor.resource or 0)
    for skill in skills:
        if int(actor.cooldowns.get(skill["key"], 0) or 0) > 1:
            cooldown_blocked += 1
        cost_type = str(skill.get("cost_type") or ""); cost = int(skill.get("cost") or 0)
        blocked = (cost_type == "mana" and actor.mp < cost) or (cost_type == "rage" and actor.resource < cost) or (cost_type == "rage_all_min" and actor.resource < int(skill.get("min_cost") or 0)) or (cost_type in {"combat_energy", "combat_energy_combo"} and projected < cost) or (cost_type == "combat_energy_combo" and actor.combo < int(skill.get("min_combo") or 1))
        if blocked: resource_blocked += 1
    return cooldown_blocked, resource_blocked


def _run_pair_once(class_a, class_b, trials, seed):
    catalog = load_production_pvp_skill_catalog(); metrics = {class_a:_empty_metrics(), class_b:_empty_metrics()}
    wins = Counter(); draws = 0; terminal_reasons = Counter(); round_counts = []
    for i in range(int(trials)):
        swap = bool(i % 2); ca, cb = (class_b, class_a) if swap else (class_a, class_b)
        actor_a, actor_b = build_real_actor(ca, 1), build_real_actor(cb, 2); result = None
        for rnd in range(1, 51):
            actors = {1:actor_a, 2:actor_b}
            intent_a = choose_action(actor_a, actor_b, "target_aware", random.Random(seed+i*1000+rnd), catalog)
            intent_b = choose_action(actor_b, actor_a, "target_aware", random.Random(seed+i*1000+rnd+37), catalog)
            intents = {1:intent_a, 2:intent_b}
            for uid, actor in actors.items():
                m=metrics[actor.class_key]; intent=intents[uid]
                action_key = str(intent.skill_key or intent.action_type)
                m["actions"][str(intent.action_type)] += 1; m["uses_by_action"][action_key] += 1
                if intent.action_type == "basic_attack": m["basic_attacks"] += 1
                elif intent.action_type == "skill": m["skill_actions"] += 1; m["chosen_skills"][str(intent.skill_key)] += 1
                cd, res = _availability(actor, catalog); m["cooldown_blocked_rounds"] += cd; m["resource_blocked_rounds"] += res
            before = {1:actor_a.clone(), 2:actor_b.clone()}
            result = resolve_pvp_round(rnd, rnd, actor_a, actor_b, intent_a, intent_b, seed=seed+i*1000+rnd, catalog=catalog)
            for outcome in result.outcomes:
                uid=int(outcome.user_id); actor=before[uid]; m=metrics[actor.class_key]; action_key=str(outcome.skill_key or outcome.action_type)
                m["outcome_reasons"][str(outcome.reason)] += 1
                if outcome.valid: m["valid_actions"] += 1
                else: m["invalid_actions"] += 1
                m["damage"] += int(outcome.damage or 0); m["healing"] += int(outcome.healing or 0)
                m["damage_by_action"][action_key] += int(outcome.damage or 0)
                m["critical_hits"] += int(bool(outcome.critical)); m["dodges_caused"] += int(bool(outcome.dodged))
                m["resource_spent"] += int(outcome.resource_spent or 0); m["resource_gained"] += int(outcome.resource_gained or 0)
                m["combo_spent"] += int(outcome.combo_spent or 0); m["combo_gained"] += int(outcome.combo_gained or 0)
                for effect in outcome.applied_effects or ():
                    m["effects_applied"][str(effect.get("kind") or effect.get("key") or "unknown")] += 1
            for event in result.events:
                uid=int(event.get("user_id") or 0); kind=str(event.get("type") or ""); value=int(event.get("value") or 0)
                if uid not in before: continue
                if kind == "hot_tick": metrics[before[uid].class_key]["hot_healing"] += value
                elif kind == "shield_absorb": metrics[before[uid].class_key]["shield_absorbed"] += value
                elif kind == "dot_tick":
                    effect_key=str(event.get("effect") or ""); source_id=int(dict(before[uid].effects.get(effect_key) or {}).get("source_id") or 0)
                    if source_id in before: metrics[before[source_id].class_key]["dot_damage"] += value
            actor_a=PvpActorState.from_dict(result.actor_a); actor_b=PvpActorState.from_dict(result.actor_b)
            if result.terminal: break
        round_counts.append(int(result.round_number if result else 50)); terminal_reasons[str(result.result_reason if result else "round_limit")] += 1
        final_by_class={actor_a.class_key:actor_a, actor_b.class_key:actor_b}
        for cls, actor in final_by_class.items():
            m=metrics[cls]; m["rounds"] += int(result.round_number if result else 50); m["ending_resource"] += int(actor.resource or actor.mp or 0); m["ending_combo"] += int(actor.combo or 0); m["ending_hp"] += int(actor.hp or 0)
        if result and result.winner_id:
            winner = actor_a.class_key if int(result.winner_id)==actor_a.user_id else actor_b.class_key
            wins[winner] += 1; metrics[winner]["wins"] += 1
        else: draws += 1
    return {"class_a":class_a,"class_b":class_b,"trials":trials,"wins":dict(wins),"draws":draws,"draw_rate":round(100*draws/trials,2),"avg_rounds":round(sum(round_counts)/trials,2),"terminal_reasons":dict(sorted(terminal_reasons.items())),"class_metrics":{cls:_serialise(metrics[cls],trials) for cls in (class_a,class_b)}}


def _diagnose(row):
    a=row["class_a"]; b=row["class_b"]; ma=row["class_metrics"][a]; mb=row["class_metrics"][b]
    stronger=a if ma["win_rate"]>=mb["win_rate"] else b; weaker=b if stronger==a else a; strong=row["class_metrics"][stronger]; weak=row["class_metrics"][weaker]
    reasons=[]
    if weak["avg_damage_per_trial"] <= strong["avg_damage_per_trial"]*0.5: reasons.append("damage_output_gap")
    if strong["avg_healing_per_trial"] > weak["avg_healing_per_trial"]+20: reasons.append("healing_sustain_gap")
    if strong["shield_absorbed"] > weak["shield_absorbed"]+20*row["trials"]: reasons.append("shield_absorption_gap")
    if weak["invalid_actions"]: reasons.append("invalid_action_present")
    if weak["resource_blocked_rounds"] > strong["resource_blocked_rounds"]*1.5+row["trials"]: reasons.append("resource_availability_gap")
    if strong["dot_damage"] > weak["dot_damage"]+20*row["trials"]: reasons.append("periodic_damage_gap")
    return {"winner_profile":stronger,"loser_profile":weaker,"reason_signals":reasons,"winner_top_actions":sorted(strong["uses_by_action"].items(),key=lambda x:(-x[1],x[0]))[:4],"loser_top_actions":sorted(weak["uses_by_action"].items(),key=lambda x:(-x[1],x[0]))[:4]}


def run_audit(trials=100, seed=14632):
    trials=max(10,min(300,int(trials))); rows=[]
    for i,a in enumerate(CLASSES):
        for j in range(i+1,len(CLASSES)):
            b=CLASSES[j]; row=_run_pair_once(a,b,trials,seed+i*100000+j*1000); ma=row["class_metrics"][a]; mb=row["class_metrics"][b]
            dominant=max(ma["win_rate"],mb["win_rate"]); dominated=min(ma["win_rate"],mb["win_rate"])
            row["dominance_review"] = dominant>=DOMINANCE_REVIEW_WIN_RATE or dominated<=100-DOMINANCE_REVIEW_WIN_RATE
            row["diagnosis"]=_diagnose(row); rows.append(row)
    dominance=[x for x in rows if x["dominance_review"]]
    invalid=sum(x["class_metrics"][c]["invalid_actions"] for x in rows for c in (x["class_a"],x["class_b"]))
    skill_keys=set()
    for row in rows:
        for cls in (row["class_a"],row["class_b"]): skill_keys.update(row["class_metrics"][cls]["chosen_skills"])
    return {"version":VERSION,"verdict":"PASS_WITH_REVIEW" if dominance else "PASS","trials_per_pair":trials,"pairs_checked":len(rows),"rows":rows,"dominance_pairs":dominance,"dominance_count":len(dominance),"invalid_action_count":invalid,"distinct_skills_observed":len(skill_keys),"production_skill_catalog_used":True,"target_aware_policy_used":True,"production_round_resolver_used":True,"actor_source":"stage_14_6_3a_real_reference","live_balance_changed":False,"fixture_values_changed":False,"production_database_writes":0}


def save_report(data,path):
    value=Path(path); value.parent.mkdir(parents=True,exist_ok=True); value.write_text(json.dumps(data,ensure_ascii=False,indent=2,sort_keys=True)+"\n",encoding="utf-8"); return value


def format_summary(data):
    return "\n".join([f"PvP real actor root-cause audit {data['version']}",f"Verdict: {data['verdict']}",f"Trials/pair: {data['trials_per_pair']}",f"Pairs checked: {data['pairs_checked']}/15",f"Dominance pairs: {data['dominance_count']}",f"Distinct skills observed: {data['distinct_skills_observed']}/18",f"Invalid actions: {data['invalid_action_count']}","Production engine, skills and policy: YES","Live balance changed: NO"])
