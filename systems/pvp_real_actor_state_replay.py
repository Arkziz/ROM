from __future__ import annotations

import json
import random
from pathlib import Path

from systems.pvp_models import PvpActorState
from systems.pvp_policy_metrics_audit import _choose as choose_action
from systems.pvp_production_calibration import CLASSES, duel as synthetic_duel
from systems.pvp_real_equipment_fixture_audit import PRODUCTION_REFERENCE
from systems.pvp_round_engine import resolve_pvp_round
from systems.pvp_skill_adapter import load_production_pvp_skill_catalog

VERSION = "14.6.3a"
REFERENCE_LEVEL = 8
REFERENCE_RARITY = "common"
DOMINANCE_REVIEW_WIN_RATE = 95.0
DRAW_REVIEW_RATE = 50.0

# Values copied from the manually verified production character displays.
RUNTIME_PROFILE = {
    "warrior": {"max_mp":0,"resource_type":"rage","physical_crit":5.50,"magical_crit":5.81,"dodge":5.00},
    "knight": {"max_mp":0,"resource_type":"rage","physical_crit":5.44,"magical_crit":5.81,"dodge":5.00},
    "scout": {"max_mp":0,"resource_type":"combat_energy","physical_crit":7.69,"magical_crit":5.81,"dodge":5.00},
    "rogue": {"max_mp":0,"resource_type":"combat_energy_combo","physical_crit":7.38,"magical_crit":5.81,"dodge":5.00},
    "mage": {"max_mp":345,"resource_type":"mana","physical_crit":5.44,"magical_crit":6.31,"dodge":5.00},
    "priest": {"max_mp":345,"resource_type":"mana","physical_crit":5.44,"magical_crit":6.62,"dodge":5.00},
}


def build_real_actor(class_key, user_id=1):
    row = PRODUCTION_REFERENCE[class_key]
    runtime = RUNTIME_PROFILE[class_key]
    magical = row["weapon_type"] == "magical"
    max_mp = int(runtime["max_mp"])
    resource_type = runtime["resource_type"]
    return PvpActorState(
        user_id=int(user_id), class_key=class_key, character_name=class_key,
        max_hp=int(row["hp"]), hp=int(row["hp"]), max_mp=max_mp, mp=max_mp,
        resource_type=resource_type,
        resource=0 if resource_type == "rage" else (max_mp if magical else 100), combo=0,
        physical_attack=float(row["physical_attack"]), magical_attack=float(row["magical_attack"]),
        physical_defense=float(row["pdef"]), magical_defense=float(row["mdef"]),
        weapon_physical_min=0.0 if magical else float(row["weapon_min"]),
        weapon_physical_max=0.0 if magical else float(row["weapon_max"]),
        weapon_magical_min=float(row["weapon_min"]) if magical else 0.0,
        weapon_magical_max=float(row["weapon_max"]) if magical else 0.0,
        physical_crit_chance=float(runtime["physical_crit"]),
        magical_crit_chance=float(runtime["magical_crit"]),
        dodge_chance=float(runtime["dodge"]), level=REFERENCE_LEVEL,
    )


def real_duel(a_cls, b_cls, trials=100, seed=14631):
    catalog = load_production_pvp_skill_catalog()
    wins_a = wins_b = draws = 0
    rounds = []
    totals = {"damage_a":0,"damage_b":0,"healing_a":0,"healing_b":0,"shield_a":0,"shield_b":0,"dot_a":0,"dot_b":0}
    for i in range(int(trials)):
        swap = bool(i % 2)
        ca, cb = (b_cls, a_cls) if swap else (a_cls, b_cls)
        actor_a = build_real_actor(ca, 1)
        actor_b = build_real_actor(cb, 2)
        result = None
        local = {1:{"damage":0,"healing":0,"shield":0,"dot":0},2:{"damage":0,"healing":0,"shield":0,"dot":0}}
        for rnd in range(1, 51):
            intent_a = choose_action(actor_a, actor_b, "target_aware", random.Random(seed+i*1000+rnd), catalog)
            intent_b = choose_action(actor_b, actor_a, "target_aware", random.Random(seed+i*1000+rnd+37), catalog)
            before = {1:actor_a, 2:actor_b}
            result = resolve_pvp_round(rnd, rnd, actor_a, actor_b, intent_a, intent_b, seed=seed+i*1000+rnd, catalog=catalog)
            for outcome in result.outcomes:
                uid = int(outcome.user_id)
                local[uid]["damage"] += int(outcome.damage or 0)
                local[uid]["healing"] += int(outcome.healing or 0)
            for event in result.events:
                uid = int(event.get("user_id") or 0); kind = str(event.get("type") or ""); value = int(event.get("value") or 0)
                if uid in local and kind == "hot_tick": local[uid]["healing"] += value
                elif uid in local and kind == "shield_absorb": local[uid]["shield"] += value
                elif uid in local and kind == "dot_tick":
                    key = str(event.get("effect") or "")
                    source_id = int(dict(before[uid].effects.get(key) or {}).get("source_id") or 0)
                    if source_id in local: local[source_id]["dot"] += value
            actor_a = PvpActorState.from_dict(result.actor_a)
            actor_b = PvpActorState.from_dict(result.actor_b)
            if result.terminal: break
        original_a_uid = 2 if swap else 1
        original_b_uid = 1 if swap else 2
        if not result or not result.winner_id: draws += 1
        elif int(result.winner_id) == original_a_uid: wins_a += 1
        elif int(result.winner_id) == original_b_uid: wins_b += 1
        else: raise AssertionError(f"unexpected winner_id={result.winner_id}")
        for metric in ("damage","healing","shield","dot"):
            totals[f"{metric}_a"] += local[original_a_uid][metric]
            totals[f"{metric}_b"] += local[original_b_uid][metric]
        rounds.append(result.round_number if result else 50)
    if wins_a + wins_b + draws != int(trials): raise AssertionError("real duel invariant failed")
    answer = {"class_a":a_cls,"class_b":b_cls,"trials":int(trials),"level":8,"rarity":"common","wins_a":wins_a,"wins_b":wins_b,"draws":draws,"win_rate_a":round(100*wins_a/int(trials),2),"win_rate_b":round(100*wins_b/int(trials),2),"draw_rate":round(100*draws/int(trials),2),"avg_rounds":round(sum(rounds)/len(rounds),2)}
    for key, value in totals.items(): answer[f"avg_{key}"] = round(value/int(trials),2)
    return answer


def _matrix(duel_func, trials, seed, synthetic=False):
    rows=[]; dominance=[]; high_draw=[]; side_order=[]
    for i, class_a in enumerate(CLASSES):
        for j in range(i+1, len(CLASSES)):
            class_b=CLASSES[j]; pair_seed=seed+i*100000+j*1000
            if synthetic:
                ab=duel_func(class_a,class_b,trials,10,"rare",pair_seed)
                ba=duel_func(class_b,class_a,trials,10,"rare",pair_seed)
            else:
                ab=duel_func(class_a,class_b,trials,pair_seed)
                ba=duel_func(class_b,class_a,trials,pair_seed)
            a_first=float(ab["win_rate_a"]); a_second=float(ba["win_rate_b"])
            a_rate=round((a_first+a_second)/2,2)
            b_rate=round((float(ab["win_rate_b"])+float(ba["win_rate_a"]))/2,2)
            draw_rate=round((float(ab["draws"])+float(ba["draws"]))/(2*trials)*100,2)
            delta=round(abs(a_first-a_second),2); flags=[]
            if max(a_rate,b_rate)>=DOMINANCE_REVIEW_WIN_RATE or min(a_rate,b_rate)<=100-DOMINANCE_REVIEW_WIN_RATE: flags.append("dominance")
            if draw_rate>=DRAW_REVIEW_RATE: flags.append("high_draw")
            if delta>10: flags.append("side_order")
            row={"class_a":class_a,"class_b":class_b,"a_win_rate":a_rate,"b_win_rate":b_rate,"draw_rate":draw_rate,"a_first":a_first,"a_second":a_second,"side_delta_pp":delta,"flags":flags}
            rows.append(row)
            if "dominance" in flags: dominance.append(row)
            if "high_draw" in flags: high_draw.append(row)
            if "side_order" in flags: side_order.append(row)
    return {"rows":rows,"dominance_rows":dominance,"high_draw_rows":high_draw,"side_order_rows":side_order,"dominance_count":len(dominance),"high_draw_count":len(high_draw),"side_order_review_count":len(side_order),"max_side_delta_pp":max((x["side_delta_pp"] for x in rows),default=0)}


def run_replay(trials=100, seed=14631):
    trials=max(10,min(500,int(trials)))
    real=_matrix(real_duel,trials,seed,False)
    synthetic=_matrix(synthetic_duel,trials,seed,True)
    pairs={f"{x['class_a']}:{x['class_b']}":x for x in synthetic["rows"]}
    comparison=[]
    for row in real["rows"]:
        key=f"{row['class_a']}:{row['class_b']}"; old=pairs[key]
        comparison.append({"class_a":row["class_a"],"class_b":row["class_b"],"synthetic_a_win_rate":old["a_win_rate"],"real_a_win_rate":row["a_win_rate"],"synthetic_draw_rate":old["draw_rate"],"real_draw_rate":row["draw_rate"],"dominance_changed":(("dominance" in old["flags"]) != ("dominance" in row["flags"]))})
    findings=[]
    if real["dominance_count"]: findings.append(f"real actor replay: {real['dominance_count']} dominance rows")
    if real["high_draw_count"]: findings.append(f"real actor replay: {real['high_draw_count']} high-draw rows")
    return {"version":VERSION,"verdict":"PASS_WITH_REVIEW" if findings else "PASS","trials_per_direction":trials,"real_reference":{"level":8,"rarity":"common","actors":{key:build_real_actor(key).to_dict() for key in CLASSES}},"real_actor_matrix":real,"synthetic_level_10_rare_matrix":synthetic,"comparison":comparison,"findings":findings,"production_skill_catalog_used":True,"target_aware_policy_used":True,"live_balance_changed":False,"fixture_values_changed":False,"production_database_writes":0}


def save_report(data, path):
    value=Path(path); value.parent.mkdir(parents=True,exist_ok=True); value.write_text(json.dumps(data,ensure_ascii=False,indent=2,sort_keys=True)+"\n",encoding="utf-8"); return value


def format_summary(data):
    real=data["real_actor_matrix"]; synthetic=data["synthetic_level_10_rare_matrix"]
    return "\n".join([f"PvP real actor-state dominance replay {data['version']}",f"Verdict: {data['verdict']}",f"Trials/direction: {data['trials_per_direction']}","Real reference: level 8 common, 6 manually verified actors",f"Real dominance rows: {real['dominance_count']}",f"Real high-draw rows: {real['high_draw_count']}",f"Real max side delta: {real['max_side_delta_pp']} pp",f"Synthetic dominance rows: {synthetic['dominance_count']}",f"Synthetic high-draw rows: {synthetic['high_draw_count']}","Production skills/policy: YES","Live balance changed: NO"])
