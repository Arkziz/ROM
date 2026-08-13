from __future__ import annotations

import json
import math
import random
import time
from collections import Counter
from contextlib import contextmanager
from copy import deepcopy
from pathlib import Path

import systems.pvp_round_engine as engine
from systems.pvp_models import PvpActorState
from systems.pvp_policy_metrics_audit import _choose as choose_action
from systems.pvp_production_calibration import CLASSES
from systems.pvp_real_actor_state_replay import PRODUCTION_REFERENCE, build_real_actor
from systems.pvp_skill_adapter import load_production_pvp_skill_catalog

VERSION = "14.6.4d5"
ROUND_CAP = 18
PARAMETERS = {
    "damage": (0.90, 1.20, 1.00, 0.04),
    "healing": (0.55, 1.00, 1.00, 0.08),
    "shield": (0.45, 1.00, 1.00, 0.08),
    "debuff": (0.80, 1.20, 1.00, 0.05),
    "scout_dex_patk": (0.45, 0.85, 0.75, 0.05),
    "rogue_dex_patk": (0.40, 0.75, 0.60, 0.05),
    "mage_matk": (1.00, 1.50, 1.12, 0.06),
    "knight_pdef": (0.55, 1.00, 0.80, 0.06),
    "priest_hot": (0.55, 1.00, 0.85, 0.07),
    "scout_skill": (0.85, 1.25, 1.00, 0.05),
    "rogue_skill": (0.80, 1.15, 0.95, 0.05),
    "mage_skill": (0.90, 1.30, 1.05, 0.05),
    "priest_damage": (0.75, 1.05, 0.95, 0.05),
    "shield_bash_stun": (5.0, 25.0, 15.0, 3.0),
    "warrior_pdef": (0.65, 1.00, 0.88, 0.05),
    "priest_mdef": (0.60, 1.00, 0.85, 0.05),
    "scout_physical_pen": (0.00, 0.45, 0.18, 0.05),
    "rogue_physical_pen": (0.00, 0.45, 0.18, 0.05),
    "mage_magical_pen": (0.00, 0.45, 0.20, 0.05),
    "warrior_skill": (0.75, 1.10, 0.95, 0.05),
    "knight_skill": (0.65, 1.00, 0.85, 0.05),
    "rogue_heavy_pen": (0.00, 0.50, 0.18, 0.05),
    "warrior_magic_received": (0.70, 1.05, 0.88, 0.04),
    "priest_physical_received": (0.65, 1.05, 0.82, 0.04),
    "knight_vs_priest_damage": (0.90, 1.40, 1.15, 0.06),
}
BASELINE = {key: spec[2] for key, spec in PARAMETERS.items()}
PRODUCTION_BASELINE = {
    "damage": 1.0, "healing": 1.0, "shield": 1.0, "debuff": 1.0,
    "scout_dex_patk": 0.0, "rogue_dex_patk": 0.0,
    "mage_matk": 1.0,
    "knight_pdef": 1.0, "priest_hot": 1.0,
    "scout_skill": 1.0, "rogue_skill": 1.0, "mage_skill": 1.0,
    "priest_damage": 1.0, "shield_bash_stun": 25.0,
    "warrior_pdef": 1.0, "priest_mdef": 1.0, "scout_physical_pen": 0.0,
    "rogue_physical_pen": 0.0, "mage_magical_pen": 0.0, "warrior_skill": 1.0, "knight_skill": 1.0,
    "rogue_heavy_pen": 0.0, "warrior_magic_received": 1.0, "priest_physical_received": 1.0, "knight_vs_priest_damage": 1.0,
}


def _clamp(name, value):
    low, high, _, _ = PARAMETERS[name]
    return round(max(low, min(high, float(value))), 4)


def _catalog(params):
    source = load_production_pvp_skill_catalog()
    catalog = {class_key: tuple(dict(skill) for skill in skills) for class_key, skills in source.items()}
    for class_key, skills in catalog.items():
        for skill in skills:
            key = str(skill.get("key") or "")
            if class_key == "warrior" and float(skill.get("damage_multiplier") or 0) > 0:
                skill["damage_multiplier"] = float(skill["damage_multiplier"]) * params["warrior_skill"]
            elif class_key == "knight" and float(skill.get("damage_multiplier") or 0) > 0:
                skill["damage_multiplier"] = float(skill["damage_multiplier"]) * params["knight_skill"]
            elif class_key == "scout" and float(skill.get("damage_multiplier") or 0) > 0:
                skill["damage_multiplier"] = float(skill["damage_multiplier"]) * params["scout_skill"]
            elif class_key == "rogue" and float(skill.get("damage_multiplier") or 0) > 0:
                skill["damage_multiplier"] = float(skill["damage_multiplier"]) * params["rogue_skill"]
            elif class_key == "mage" and float(skill.get("damage_multiplier") or 0) > 0:
                skill["damage_multiplier"] = float(skill["damage_multiplier"]) * params["mage_skill"]
            elif class_key == "priest" and key == "priest_holy_ray":
                skill["damage_multiplier"] = float(skill["damage_multiplier"]) * params["priest_damage"]
            if key == "knight_shield_bash":
                skill["stun_chance"] = params["shield_bash_stun"]
    return catalog


def _actor(class_key, user_id, params):
    actor = build_real_actor(class_key, user_id)
    reference = PRODUCTION_REFERENCE[class_key]
    if class_key == "warrior":
        actor.physical_defense *= params["warrior_pdef"]
    elif class_key == "scout":
        actor.physical_attack = max(float(reference["str"]), float(reference["dex"]) * params["scout_dex_patk"])
    elif class_key == "rogue":
        actor.physical_attack = max(float(reference["str"]), float(reference["dex"]) * params["rogue_dex_patk"])
    elif class_key == "mage":
        actor.magical_attack *= params["mage_matk"]
    elif class_key == "knight":
        actor.physical_defense *= params["knight_pdef"]
    elif class_key == "priest":
        actor.magical_defense *= params["priest_mdef"]
    return actor


@contextmanager
def _engine_parameters(params):
    old = (
        engine.PVP_DAMAGE_MULTIPLIER,
        engine.PVP_HEALING_MULTIPLIER,
        engine.PVP_SHIELD_MULTIPLIER,
        engine.PVP_DEBUFF_MULTIPLIER,
    )
    old_base_damage = engine._base_damage
    def candidate_base_damage(attacker, defender, attack_type, rng):
        physical_before = defender.physical_defense
        magical_before = defender.magical_defense
        try:
            if attack_type == "physical" and attacker.class_key == "scout":
                defender.physical_defense *= 1.0 - params["scout_physical_pen"]
            elif attack_type == "physical" and attacker.class_key == "rogue":
                penetration = params["rogue_physical_pen"]
                if defender.class_key in {"warrior", "knight"}:
                    penetration = 1.0 - (1.0 - penetration) * (1.0 - params["rogue_heavy_pen"])
                defender.physical_defense *= 1.0 - penetration
            elif attack_type == "magical" and attacker.class_key == "mage":
                defender.magical_defense *= 1.0 - params["mage_magical_pen"]
            damage, critical, dodged = old_base_damage(attacker, defender, attack_type, rng)
            if attack_type == "magical" and defender.class_key == "warrior" and damage > 0:
                damage = max(1, round(damage * params["warrior_magic_received"]))
            if attack_type == "physical" and defender.class_key == "priest" and damage > 0:
                damage = max(1, round(damage * params["priest_physical_received"]))
            if attacker.class_key == "knight" and defender.class_key == "priest" and damage > 0:
                damage = max(1, round(damage * params["knight_vs_priest_damage"]))
            return damage, critical, dodged
        finally:
            defender.physical_defense = physical_before
            defender.magical_defense = magical_before
    engine.PVP_DAMAGE_MULTIPLIER = old[0] * params["damage"]
    engine.PVP_HEALING_MULTIPLIER = old[1] * params["healing"]
    engine.PVP_SHIELD_MULTIPLIER = old[2] * params["shield"]
    engine.PVP_DEBUFF_MULTIPLIER = old[3] * params["debuff"]
    engine._base_damage = candidate_base_damage
    try:
        yield
    finally:
        engine._base_damage = old_base_damage
        (
            engine.PVP_DAMAGE_MULTIPLIER,
            engine.PVP_HEALING_MULTIPLIER,
            engine.PVP_SHIELD_MULTIPLIER,
            engine.PVP_DEBUFF_MULTIPLIER,
        ) = old


def _scale_priest_hot(actor, params, seen_hot):
    if actor.class_key != "priest" or "hot" not in actor.effects:
        return
    hot = actor.effects["hot"]
    marker = (actor.user_id, int(hot.get("source_id", actor.user_id)), int(hot.get("duration", 0)), float(hot.get("power", 0)))
    if marker in seen_hot:
        return
    original = float(hot.get("power", 0) or 0)
    hot["power"] = max(1, round(original * params["priest_hot"]))
    seen_hot.add((actor.user_id, int(hot.get("source_id", actor.user_id)), int(hot.get("duration", 0)), float(hot.get("power", 0))))


def _cap_winner(actor_a, actor_b):
    left = actor_a.hp / max(1, actor_a.max_hp)
    right = actor_b.hp / max(1, actor_b.max_hp)
    if abs(left - right) < 1e-12:
        return None
    return actor_a.user_id if left > right else actor_b.user_id


def _pair(class_a, class_b, trials, seed, params):
    catalog = _catalog(params)
    wins = Counter()
    draws = 0
    rounds = []
    cap_count = 0
    for trial in range(trials):
        swapped = bool(trial % 2)
        left, right = (class_b, class_a) if swapped else (class_a, class_b)
        actor_a = _actor(left, 1, params)
        actor_b = _actor(right, 2, params)
        seen_hot = set()
        winner_id = None
        terminal = False
        for round_number in range(1, ROUND_CAP + 1):
            intent_a = choose_action(actor_a, actor_b, "target_aware", random.Random(seed + trial * 1000 + round_number), catalog)
            intent_b = choose_action(actor_b, actor_a, "target_aware", random.Random(seed + trial * 1000 + round_number + 37), catalog)
            with _engine_parameters(params):
                result = engine.resolve_pvp_round(round_number, round_number, actor_a, actor_b, intent_a, intent_b, seed=seed + trial * 1000 + round_number, catalog=catalog)
            actor_a = PvpActorState.from_dict(result.actor_a)
            actor_b = PvpActorState.from_dict(result.actor_b)
            _scale_priest_hot(actor_a, params, seen_hot)
            _scale_priest_hot(actor_b, params, seen_hot)
            if result.terminal:
                winner_id = result.winner_id
                terminal = True
                break
        rounds.append(round_number)
        if not terminal:
            cap_count += 1
            winner_id = _cap_winner(actor_a, actor_b)
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
        "avg_rounds": round(sum(rounds) / trials, 2),
        "cap_rate": round(100 * cap_count / trials, 2),
    }


def evaluate(params, trials, seed):
    rows = []
    for i, class_a in enumerate(CLASSES):
        for j in range(i + 1, len(CLASSES)):
            rows.append(_pair(class_a, CLASSES[j], trials, seed + i * 100000 + j * 1000, params))
    class_rates = {
        class_key: round(sum(row["a_win_rate"] if row["class_a"] == class_key else row["b_win_rate"] for row in rows if class_key in (row["class_a"], row["class_b"])) / 5, 2)
        for class_key in CLASSES
    }
    dominance = sum(1 for row in rows if max(row["a_win_rate"], row["b_win_rate"]) >= 90 or min(row["a_win_rate"], row["b_win_rate"]) <= 10)
    extreme = sum(1 for row in rows if max(row["a_win_rate"], row["b_win_rate"]) >= 98 or min(row["a_win_rate"], row["b_win_rate"]) <= 2)
    spread = max(class_rates.values()) - min(class_rates.values())
    avg_rounds = sum(row["avg_rounds"] for row in rows) / len(rows)
    cap_rate = sum(row["cap_rate"] for row in rows) / len(rows)
    too_fast = sum(1 for row in rows if row["avg_rounds"] < 8)
    too_long = sum(1 for row in rows if row["avg_rounds"] > 16)
    high_draw = sum(1 for row in rows if row["draw_rate"] > 25)
    outside = sum(max(0, 20 - value) + max(0, value - 80) for value in class_rates.values())
    matchup_error = sum(max(0, abs(row["a_win_rate"] - row["b_win_rate"]) - 40) for row in rows)
    regularization = 0.0
    for name, value in params.items():
        low, high, neutral, _ = PARAMETERS[name]
        regularization += abs(value - neutral) / max(1e-9, high - low)
    objective = (
        extreme * 260 + dominance * 110 + spread * 5 + outside * 14 + matchup_error * 2.5
        + cap_rate * 5 + sum(max(0, row["cap_rate"] - 25) * 1.5 for row in rows)
        + max(0, avg_rounds - 16) * 30 + max(0, 9 - avg_rounds) * 20
        + too_long * 35 + too_fast * 35 + high_draw * 30 + regularization * 6
    )
    return {
        "objective": round(objective, 3),
        "params": {key: round(value, 4) for key, value in params.items()},
        "rows": rows,
        "class_average_win_rates": class_rates,
        "dominance_count_90_10": dominance,
        "extreme_count_98_2": extreme,
        "class_spread_pp": round(spread, 2),
        "average_rounds": round(avg_rounds, 2),
        "cap_rate_pct": round(cap_rate, 2),
        "too_fast_pairs": too_fast,
        "too_long_pairs": too_long,
        "high_draw_pairs": high_draw,
    }


def _diagnose(result):
    rates=result["class_average_win_rates"]; weak=min(rates,key=rates.get); strong=max(rates,key=rates.get); actions=[]
    if weak=="scout": actions += [("scout_dex_patk",1),("scout_skill",1),("scout_physical_pen",1)]
    elif weak=="rogue": actions += [("rogue_dex_patk",1),("rogue_skill",1),("rogue_physical_pen",1)]
    elif weak=="mage": actions += [("mage_matk",1),("mage_skill",1),("mage_magical_pen",1)]
    elif weak=="priest": actions += [("priest_hot",1),("priest_damage",1),("healing",1),("priest_mdef",1)]
    if strong=="knight": actions += [("knight_pdef",-1),("knight_skill",-1),("shield",-1),("shield_bash_stun",-1)]
    elif strong=="warrior": actions += [("warrior_pdef",-1),("warrior_skill",-1)]
    elif strong=="priest": actions += [("priest_hot",-1),("healing",-1),("priest_mdef",-1)]
    for row in result.get("rows",[]):
        a,b=row["class_a"],row["class_b"]; aw,bw=row["a_win_rate"],row["b_win_rate"]
        if {a,b}=={"warrior","scout"} and min(aw,bw)<=10: actions += [("scout_physical_pen",1),("warrior_pdef",-1),("warrior_skill",-1)]
        if {a,b}=={"warrior","rogue"} and min(aw,bw)<=10: actions += [("rogue_physical_pen",1),("warrior_pdef",-1),("warrior_skill",-1)]
        if {a,b}=={"knight","scout"} and min(aw,bw)<=10: actions += [("scout_physical_pen",1),("knight_pdef",-1),("knight_skill",-1)]
        if {a,b}=={"knight","rogue"} and min(aw,bw)<=10: actions += [("rogue_physical_pen",1),("knight_pdef",-1),("knight_skill",-1)]
        if {a,b}=={"mage","priest"} and min(aw,bw)<=10: actions += [("mage_magical_pen",1),("priest_mdef",-1)]
        if row.get("cap_rate",0)>50: actions += [("damage",1),("healing",-1),("shield",-1)]
    if result["cap_rate_pct"]>20: actions += [("damage",1),("healing",-1),("shield",-1)]
    elif result["average_rounds"]<9: actions += [("damage",-1)]
    return actions

def _mutate(parent, rng, scale, guided=True):
    child = dict(parent["params"] if "params" in parent else parent)
    actions = _diagnose(parent) if guided and "class_average_win_rates" in parent else []
    if actions:
        rng.shuffle(actions)
        for name, direction in actions[: rng.randint(1, min(4, len(actions)))]:
            step = PARAMETERS[name][3] * scale * rng.uniform(0.6, 1.4)
            child[name] = _clamp(name, child[name] + direction * step)
    for _ in range(rng.randint(1, 4)):
        name = rng.choice(list(PARAMETERS))
        step = PARAMETERS[name][3] * scale * rng.gauss(0, 1)
        child[name] = _clamp(name, child[name] + step)
    return child


def _random_candidate(rng):
    candidate = {}
    for name, (low, high, neutral, _) in PARAMETERS.items():
        if rng.random() < 0.65:
            candidate[name] = _clamp(name, rng.gauss(neutral, (high - low) / 6))
        else:
            candidate[name] = _clamp(name, rng.uniform(low, high))
    return candidate


def _compact(result):
    return {key: value for key, value in result.items() if key != "rows"}


def run_optimizer(minutes=20, seed=14644, checkpoint_path=None, report_path=None, smoke=False):
    started=time.monotonic(); total_seconds=35.0 if smoke else max(0.05,float(minutes))*60; deadline=started+total_seconds*0.72
    rng=random.Random(int(seed)); checkpoint=Path(checkpoint_path) if checkpoint_path else None; history=[]; archive=[]; candidates_evaluated=0; generation=0
    fast_trials=2 if smoke else 10; promotion_trials=3 if smoke else 30; final_trials=5 if smoke else 120
    allowed=["rogue_heavy_pen","warrior_magic_received","priest_physical_received","knight_vs_priest_damage","priest_damage","priest_hot","healing"]
    frozen={"damage":1.1375,"debuff":0.9044,"shield":0.4566,"knight_pdef":0.5518,"knight_skill":0.7104,"shield_bash_stun":10.41,"warrior_pdef":0.9291,"warrior_skill":0.9462,"scout_dex_patk":0.7105,"scout_physical_pen":0.2641,"scout_skill":0.9654,"rogue_dex_patk":0.626,"rogue_physical_pen":0.4223,"rogue_skill":0.9921,"mage_matk":1.1376,"mage_skill":0.9277,"mage_magical_pen":0.2707,"priest_mdef":0.8172}
    seeds_fast=[seed+131,seed+262]; seeds_prom=[seed+13001,seed+26002]; seeds_final=[seed+730001,seed+840002,seed+950003]
    def score(r):
        rates=r["class_average_win_rates"]; value=float(r["objective"])
        value += sum(abs(rates[c]-50)*8 for c in CLASSES)
        for row in r["rows"]:
            gap=abs(row["a_win_rate"]-row["b_win_rate"]); value += max(0,gap-45)*14
            if min(row["a_win_rate"],row["b_win_rate"])<=5: value += 350
            if row["cap_rate"]>35: value += (row["cap_rate"]-35)*5
            if row["avg_rounds"]>16: value += (row["avg_rounds"]-16)*80
        return round(value,3)
    def aggregate(params,trials,seeds,phase):
        nonlocal candidates_evaluated
        rs=[evaluate(params,trials,s) for s in seeds]; candidates_evaluated+=1; objectives=[score(r) for r in rs]; avg=sum(objectives)/len(objectives); var=sum((x-avg)**2 for x in objectives)/len(objectives); worst=max(rs,key=score)
        rates={c:round(sum(r["class_average_win_rates"][c] for r in rs)/len(rs),2) for c in CLASSES}; mean=lambda k:sum(float(r[k]) for r in rs)/len(rs)
        out=dict(worst); out.update({"objective":round(avg+var**0.5*.35,3),"objective_mean":round(avg,3),"objective_variance":round(var,3),"base_objective_mean":round(mean("objective"),3),"class_average_win_rates":rates,"class_spread_pp":round(max(rates.values())-min(rates.values()),2),"dominance_count_90_10":max(r["dominance_count_90_10"] for r in rs),"extreme_count_98_2":max(r["extreme_count_98_2"] for r in rs),"average_rounds":round(mean("average_rounds"),2),"cap_rate_pct":round(mean("cap_rate_pct"),2),"phase":phase,"trials_per_pair_per_seed":trials,"seed_count":len(seeds),"params":{k:round(v,4) for k,v in params.items()}}); return out
    def compact(r): return {k:v for k,v in r.items() if k!="rows"}
    def record(r):
        nonlocal archive
        archive.append(compact(r)); archive.sort(key=lambda x:x["objective"]); archive=archive[:30]
        if not history or r["objective"]<history[-1]["best_objective"]: history.append({"candidate":candidates_evaluated,"generation":generation,"phase":r["phase"],"best_objective":r["objective"],"params":r["params"]})
    def mutate(parent,scale,guided):
        child=dict(parent["params"]); actions=[]
        if guided:
            for row in parent["rows"]:
                pair={row["class_a"],row["class_b"]}; a=row["a_win_rate"]; b=row["b_win_rate"]
                if pair=={"warrior","rogue"} or pair=={"knight","rogue"}:
                    rogue=a if row["class_a"]=="rogue" else b
                    if rogue<20: actions += [("rogue_heavy_pen",1)]
                    elif rogue>70: actions += [("rogue_heavy_pen",-1)]
                if pair=={"warrior","mage"}:
                    warrior=a if row["class_a"]=="warrior" else b
                    actions += [("warrior_magic_received",-1 if warrior<25 else 1)]
                if "priest" in pair:
                    priest=a if row["class_a"]=="priest" else b
                    opponent=(pair-{"priest"}).pop()
                    if opponent in {"scout","rogue"} and priest<20: actions += [("priest_physical_received",-1),("priest_hot",1)]
                    if opponent=="knight" and priest>75: actions += [("knight_vs_priest_damage",1)]
                    if row["cap_rate"]>50: actions += [("priest_damage",1),("priest_hot",-1),("healing",-1)]
        rng.shuffle(actions)
        for name,direction in actions[:min(4,len(actions))]: child[name]=_clamp(name,child[name]+direction*PARAMETERS[name][3]*scale*rng.uniform(.7,1.3))
        for _ in range(rng.randint(1,3)):
            name=rng.choice(allowed); child[name]=_clamp(name,child[name]+PARAMETERS[name][3]*scale*rng.gauss(0,1))
        child.update(frozen); return child
    base=dict(BASELINE); base.update(frozen); base.update({"healing":.9547,"priest_damage":.9785,"priest_hot":.9824,"rogue_heavy_pen":.18,"warrior_magic_received":.88,"priest_physical_received":.82,"knight_vs_priest_damage":1.15})
    incumbent=aggregate(base,fast_trials,seeds_fast,"extreme_seed"); record(incumbent); scale=1.0
    while time.monotonic()<deadline and (not smoke or generation<3):
        generation+=1; proposals=[dict(incumbent["params"]),mutate(incumbent,scale,True),mutate(incumbent,scale,False),mutate(incumbent,scale*1.4,True)]; fast=[]
        for p in proposals:
            if time.monotonic()>=deadline: break
            r=aggregate(p,fast_trials,seeds_fast,"extreme_fast"); record(r); fast.append(r)
        fast.sort(key=lambda x:x["objective"])
        if fast:
            promoted=aggregate(fast[0]["params"],promotion_trials,seeds_prom,"extreme_promotion"); record(promoted)
            if promoted["objective"]<incumbent["objective"]: incumbent=promoted; scale=max(.2,scale*.86)
            else: scale=max(.16,scale*.68)
        if checkpoint: checkpoint.write_text(json.dumps({"version":VERSION,"generation":generation,"candidates_evaluated":candidates_evaluated,"history":history,"archive":archive[:10],"incumbent":compact(incumbent)},ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    finalists=[]; sigs=set()
    for c in [incumbent]+archive:
        sig=tuple((k,round(c["params"][k],3)) for k in sorted(allowed))
        if sig not in sigs: sigs.add(sig); finalists.append(c)
        if len(finalists)>=3: break
    finals=[aggregate(c["params"],final_trials,seeds_final,"final_validation") for c in finalists]; finals.sort(key=lambda x:x["objective"]); best=finals[0]
    output={"version":VERSION,"verdict":"PASS_WITH_REVIEW","algorithm":"frozen_d4_extreme_matchup_and_priest_pacing_refinement","time_budget_minutes":float(minutes),"elapsed_seconds":round(time.monotonic()-started,2),"seed":int(seed),"round_cap":ROUND_CAP,"preferred_round_range":[10,16],"candidates_evaluated":candidates_evaluated,"generations":generation,"history":history,"best_candidate":best,"finalists":finals,"top_archive":archive[:10],"optimized_parameters":allowed,"frozen_parameters":frozen,"matchup_specific_parameters_are_sandbox_candidates":True,"visible_resource_changes_allowed":False,"excluded_visible_parameters":["hp","max_hp","mp","max_mp","level","equipment_stats"],"recommendation_status":"SANDBOX_ONLY_NOT_APPROVED_FOR_LIVE","live_balance_changed":False,"fixture_values_changed":False,"production_database_writes":0}
    if checkpoint: checkpoint.write_text(json.dumps({"version":VERSION,"completed":True,"generation":generation,"candidates_evaluated":candidates_evaluated,"history":history,"archive":archive[:10],"best_candidate":compact(best)},ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    if report_path: Path(report_path).write_text(json.dumps(output,ensure_ascii=False,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    return output

def format_summary(data):
    best = data["best_candidate"]
    rates = best["class_average_win_rates"]
    return "\n".join([
        f"PvP adaptive balance optimizer {data['version']}",
        f"Verdict: {data['verdict']}",
        f"Elapsed: {data['elapsed_seconds']} sec",
        f"Candidates evaluated: {data['candidates_evaluated']}",
        f"Generations: {data['generations']}",
        f"Best objective: {best['objective']}",
        f"Dominance 90/10: {best['dominance_count_90_10']}",
        f"Extreme 98/2: {best['extreme_count_98_2']}",
        f"Class spread: {best['class_spread_pp']} pp",
        f"Average rounds: {best['average_rounds']}",
        f"Cap rate: {best['cap_rate_pct']}%",
        "Class rates: " + ", ".join(f"{key}={value}%" for key, value in rates.items()),
        "Recommendation: SANDBOX ONLY",
        "Live balance changed: NO",
    ])
