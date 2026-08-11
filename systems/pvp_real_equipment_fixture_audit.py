from __future__ import annotations

import json
from pathlib import Path

from systems.pvp_production_calibration import CLASSES, LABELS, duel

VERSION = "14.6.3"
REFERENCE_LEVEL = 8
REFERENCE_RARITY = "common"
DEFAULT_TRIALS = 100
DOMINANCE_REVIEW_WIN_RATE = 95.0
DRAW_REVIEW_RATE = 50.0

# Manually verified production characters at level 8 in basic common shop gear.
# Mage max HP was supplied separately and is intentionally fixed at 415.
PRODUCTION_REFERENCE = {
    "warrior": {"hp":425,"str":48,"dex":18,"int":17,"wis":23,"sta":33,"physical_attack":48,"magical_attack":17,"pdef":56,"mdef":49,"weapon_type":"physical","weapon_min":9,"weapon_max":13,"active_slots":9,"off_hand":"empty"},
    "knight": {"hp":435,"str":47,"dex":17,"int":24,"wis":23,"sta":35,"physical_attack":47,"magical_attack":24,"pdef":78,"mdef":41,"weapon_type":"physical","weapon_min":6,"weapon_max":10,"active_slots":10,"off_hand":"shield"},
    "scout": {"hp":395,"str":19,"dex":53,"int":17,"wis":23,"sta":27,"physical_attack":19,"magical_attack":17,"pdef":38,"mdef":61,"weapon_type":"physical","weapon_min":9,"weapon_max":13,"active_slots":9,"off_hand":"empty"},
    "rogue": {"hp":395,"str":26,"dex":48,"int":24,"wis":23,"sta":27,"physical_attack":26,"magical_attack":24,"pdef":38,"mdef":61,"weapon_type":"physical","weapon_min":6,"weapon_max":10,"active_slots":10,"off_hand":"dagger"},
    "mage": {"hp":415,"str":24,"dex":17,"int":36,"wis":28,"sta":31,"physical_attack":24,"magical_attack":36,"pdef":25,"mdef":81,"weapon_type":"magical","weapon_min":9,"weapon_max":13,"active_slots":9,"off_hand":"empty"},
    "priest": {"hp":380,"str":17,"dex":17,"int":45,"wis":36,"sta":24,"physical_attack":17,"magical_attack":45,"pdef":23,"mdef":86,"weapon_type":"magical","weapon_min":9,"weapon_max":13,"active_slots":9,"off_hand":"empty"},
}


def _expected_basic_damage(attacker, defender):
    a = PRODUCTION_REFERENCE[attacker]
    d = PRODUCTION_REFERENCE[defender]
    attack = a["magical_attack"] if a["weapon_type"] == "magical" else a["physical_attack"]
    defense = d["mdef"] if a["weapon_type"] == "magical" else d["pdef"]
    average_weapon = (a["weapon_min"] + a["weapon_max"]) / 2.0
    return round(max(1.0, average_weapon + attack - defense * 0.5), 2)


def _reference_analysis():
    rows = []
    for attacker in CLASSES:
        for defender in CLASSES:
            if attacker == defender:
                continue
            rows.append({"attacker":attacker,"defender":defender,"attack_type":PRODUCTION_REFERENCE[attacker]["weapon_type"],"expected_basic_damage":_expected_basic_damage(attacker,defender)})
    by_class = {}
    for key, row in PRODUCTION_REFERENCE.items():
        correct_defense_shape = (row["mdef"] > row["pdef"] if key in ("mage","priest") else row["pdef"] > row["mdef"] if key in ("warrior","knight") else True)
        dex_attack_gap = row["dex"] - row["physical_attack"] if key in ("scout","rogue") else 0
        by_class[key] = {**row,"defense_profile_expected":correct_defense_shape,"dex_minus_physical_attack":dex_attack_gap}
    return {"level":REFERENCE_LEVEL,"rarity":REFERENCE_RARITY,"classes":by_class,"expected_basic_damage_matrix":rows,"all_defense_profiles_expected":all(x["defense_profile_expected"] for x in by_class.values()),"dex_class_attack_review":any(by_class[x]["dex_minus_physical_attack"] >= 20 for x in ("scout","rogue"))}


def _matchup_audit(trials, level, rarity, seed):
    rows=[]; dominance=[]; side_reviews=[]
    for i, a in enumerate(CLASSES):
        for j in range(i+1,len(CLASSES)):
            b=CLASSES[j]; pair_seed=seed+i*100000+j*1000
            ab=duel(a,b,trials,level,rarity,pair_seed); ba=duel(b,a,trials,level,rarity,pair_seed)
            a_when_first=float(ab["win_rate_a"]); a_when_second=float(ba["win_rate_b"])
            a_rate=round((a_when_first+a_when_second)/2,2); b_rate=round((float(ab["win_rate_b"])+float(ba["win_rate_a"]))/2,2)
            draw_rate=round((float(ab["draws"])+float(ba["draws"]))/(2*trials)*100,2)
            side_delta=round(abs(a_when_first-a_when_second),2)
            dominant=max(a_rate,b_rate); dominated=min(a_rate,b_rate)
            flags=[]
            if dominant>=DOMINANCE_REVIEW_WIN_RATE or dominated<=100-DOMINANCE_REVIEW_WIN_RATE: flags.append("dominance")
            if draw_rate>=DRAW_REVIEW_RATE: flags.append("high_draw")
            if side_delta>10: flags.append("side_order")
            row={"class_a":a,"class_b":b,"a_win_rate":a_rate,"b_win_rate":b_rate,"draw_rate":draw_rate,"a_first":a_when_first,"a_second":a_when_second,"side_delta_pp":side_delta,"flags":flags}
            rows.append(row)
            if "dominance" in flags: dominance.append(row)
            if "side_order" in flags: side_reviews.append(row)
    return {"rows":rows,"dominance_rows":dominance,"side_order_rows":side_reviews,"max_side_delta_pp":max((x["side_delta_pp"] for x in rows),default=0),"dominance_count":len(dominance),"side_order_review_count":len(side_reviews)}


def run_audit(trials=DEFAULT_TRIALS, level=10, rarity="rare", seed=14630):
    trials=max(10,min(500,int(trials))); level=max(1,min(100,int(level)))
    reference=_reference_analysis(); matchups=_matchup_audit(trials,level,rarity,seed)
    findings=[]
    if not reference["all_defense_profiles_expected"]: findings.append("production defense profile mismatch")
    if reference["dex_class_attack_review"]: findings.append("DEX classes have a large DEX versus physical_attack gap")
    if matchups["dominance_count"]: findings.append(f"{matchups['dominance_count']} matchup rows meet dominance review threshold")
    verdict="PASS_WITH_REVIEW" if findings else "PASS"
    return {"version":VERSION,"verdict":verdict,"trials":trials,"level":level,"rarity":rarity,"production_reference":reference,"matchup_dominance":matchups,"findings":findings,"live_balance_changed":False,"fixture_values_changed":False,"production_database_writes":0}


def save_report(data,path):
    out=Path(path); out.parent.mkdir(parents=True,exist_ok=True); out.write_text(json.dumps(data,ensure_ascii=False,indent=2,sort_keys=True)+"\n",encoding="utf-8"); return out


def format_summary(data):
    ref=data["production_reference"]; matrix=data["matchup_dominance"]
    return "\n".join([
        f"PvP real-equipment dominance audit {data['version']}",
        f"Verdict: {data['verdict']}",
        f"Reference: level {ref['level']} {ref['rarity']}, 6 production characters",
        f"Defense profile parity: {'PASS' if ref['all_defense_profiles_expected'] else 'FAIL'}",
        f"DEX-class attack mapping: {'REVIEW' if ref['dex_class_attack_review'] else 'PASS'}",
        f"Matchups checked: {len(matrix['rows'])}",
        f"Dominance rows: {matrix['dominance_count']}",
        f"Max side delta: {matrix['max_side_delta_pp']} pp",
        "Live balance changed: NO",
    ])
