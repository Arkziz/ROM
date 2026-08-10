from __future__ import annotations
import json
from pathlib import Path
from systems.pvp_production_calibration import ARMOR,CLASSES,LABELS,RARITIES,SLOTS,SLOT_WEIGHTS,SLOT_WEIGHT_TOTAL,_stats,build_standard_actor,duel
from systems.pvp_skill_adapter import load_production_pvp_skill_catalog

EXPECTED_SKILLS_PER_CLASS=3
PRIMARY=("str","dex","int","wis","sta")

def _actor_snapshot(class_key,level,rarity):
 actor=build_standard_actor(class_key,level,rarity); equipment={slot:_stats(class_key,slot,level,rarity) for slot in SLOTS}; equipment_primary={key:sum(int(item.get(key,0) or 0) for item in equipment.values()) for key in PRIMARY}; base={key:10+level-1 for key in PRIMARY}; final={key:base[key]+equipment_primary[key] for key in PRIMARY}
 return {"class_key":class_key,"label":LABELS[class_key],"level":actor.level,"rarity":rarity,"armor_profile":ARMOR[class_key],"base_primary_stats":base,"equipment_primary_stats":equipment_primary,"final_primary_stats":final,"equipment_breakdown":equipment,"max_hp":actor.max_hp,"max_mp":actor.max_mp,"physical_attack":actor.physical_attack,"magical_attack":actor.magical_attack,"physical_defense":actor.physical_defense,"magical_defense":actor.magical_defense,"weapon_physical_min":actor.weapon_physical_min,"weapon_physical_max":actor.weapon_physical_max,"weapon_magical_min":actor.weapon_magical_min,"weapon_magical_max":actor.weapon_magical_max,"resource_type":actor.resource_type,"resource":actor.resource,"equipment_slots":list(SLOTS)}

def _skill_audit():
 catalog=load_production_pvp_skill_catalog(); rows={}; keys=[]; failures=[]
 for class_key in CLASSES:
  skills=list(catalog.get(class_key) or []); class_keys=[str(skill.get("key") or "") for skill in skills]; keys.extend(class_keys)
  if len(skills)!=EXPECTED_SKILLS_PER_CLASS: failures.append(f"{class_key}: expected 3 skills, got {len(skills)}")
  if any(not key for key in class_keys): failures.append(f"{class_key}: empty skill key")
  rows[class_key]={"count":len(skills),"keys":class_keys,"cost_types":[x.get("cost_type") for x in skills],"cooldowns":[x.get("cooldown") for x in skills]}
 if len(keys)!=len(set(keys)): failures.append("duplicate skill keys")
 return {"classes_checked":len(rows),"skills_checked":len(keys),"expected_skills":18,"by_class":rows,"failures":failures,"pass":not failures}

def _matrix_integrity(trials,level,rarity,seed):
 rows=[]; failures=[]; deltas=[]
 for i,class_a in enumerate(CLASSES):
  mirror=duel(class_a,class_a,trials,level,rarity,seed+i*10000); total=mirror["wins_a"]+mirror["wins_b"]+mirror["draws"]; ok=total==trials
  if not ok: failures.append(f"mirror {class_a}: {total} != {trials}")
  rows.append({"kind":"mirror","class_a":class_a,"class_b":class_a,"wins_a":mirror["wins_a"],"wins_b":mirror["wins_b"],"draws":mirror["draws"],"total":total,"trials":trials,"pass":ok})
 for i,class_a in enumerate(CLASSES):
  for j in range(i+1,len(CLASSES)):
   class_b=CLASSES[j]; pair_seed=seed+i*100000+j*1000; ab=duel(class_a,class_b,trials,level,rarity,pair_seed); ba=duel(class_b,class_a,trials,level,rarity,pair_seed); total_ab=ab["wins_a"]+ab["wins_b"]+ab["draws"]; total_ba=ba["wins_a"]+ba["wins_b"]+ba["draws"]; delta=round(abs(ab["win_rate_a"]-ba["win_rate_b"]),2); deltas.append(delta); ok=total_ab==trials and total_ba==trials
   if not ok: failures.append(f"pair {class_a}/{class_b}: invalid totals")
   rows.append({"kind":"side_pair","class_a":class_a,"class_b":class_b,"a_win_rate_when_first":ab["win_rate_a"],"a_win_rate_when_second":ba["win_rate_b"],"side_delta_pp":delta,"ab_total":total_ab,"ba_total":total_ba,"trials_each_direction":trials,"pass":ok})
 return {"rows":rows,"failures":failures,"pass":not failures,"max_side_delta_pp":max(deltas,default=0),"avg_side_delta_pp":round(sum(deltas)/max(1,len(deltas)),2),"side_delta_review":max(deltas,default=0)>10}

def _combat_signature(row):
 keys=("wins_a","wins_b","draws","avg_rounds","avg_damage_a","avg_damage_b","avg_healing_a","avg_healing_b","avg_shield_a","avg_shield_b","avg_dot_a","avg_dot_b")
 return {key:row.get(key) for key in keys}

def _sensitivity(trials,level,rarity,seed):
 configs=(("healing",("priest","knight"),{"healing":1.0},{"healing":0.4}),("warrior_damage",("warrior","knight"),{"class_damage":{"warrior":1.0}},{"class_damage":{"warrior":1.3}}),("scout_damage",("scout","rogue"),{"class_damage":{"scout":1.0}},{"class_damage":{"scout":1.3}})); checks=[]
 for index,(name,pair,base_kwargs,var_kwargs) in enumerate(configs):
  baseline=duel(pair[0],pair[1],trials,level,rarity,seed+index,**base_kwargs); variant=duel(pair[0],pair[1],trials,level,rarity,seed+index,**var_kwargs); a=_combat_signature(baseline); b=_combat_signature(variant); changed={key:{"baseline":a[key],"variant":b[key]} for key in a if a[key]!=b[key]}; checks.append({"parameter":name,"baseline_config":base_kwargs,"variant_config":var_kwargs,"combat_baseline":a,"combat_variant":b,"changed_combat_metrics":changed,"observable_change":bool(changed)})
 return {"checks":checks,"all_observable":all(row["observable_change"] for row in checks),"criterion":"combat_metrics_only_v2"}

def _slot_weighted_fixture_parity():
 weights={slot:float(SLOT_WEIGHTS[slot]) for slot in SLOTS if slot in SLOT_WEIGHTS}; failures=[]
 if set(SLOTS)!=set(SLOT_WEIGHTS): failures.append("slot set mismatch")
 total=round(sum(weights.values()),6)
 if total!=float(SLOT_WEIGHT_TOTAL): failures.append(f"weight total {total} != {SLOT_WEIGHT_TOTAL}")
 if weights.get("chest",0)<=weights.get("gloves",0): failures.append("chest weight must exceed gloves weight")
 if weights.get("main_hand",0)!=max(weights.values(),default=0): failures.append("main_hand must have the largest fixture weight")
 samples={class_key:{slot:{"weight":weights.get(slot),"stats":_stats(class_key,slot,10,"rare")} for slot in SLOTS} for class_key in CLASSES}
 return {"weights":weights,"weight_total":total,"expected_total":float(SLOT_WEIGHT_TOTAL),"slots_checked":len(weights),"samples_level_10_rare":samples,"failures":failures,"pass":not failures}


def _fixture_warnings(actors):
 hp=[x["max_hp"] for x in actors.values()]; attacks=[max(x["physical_attack"],x["magical_attack"]) for x in actors.values()]; hp_ratio=round(max(hp)/max(1,min(hp)),2); attack_ratio=round(max(attacks)/max(1,min(attacks)),2); warnings=[]
 if hp_ratio>1.6: warnings.append(f"HP max/min ratio {hp_ratio} > 1.60")
 if attack_ratio>1.6: warnings.append(f"Attack max/min ratio {attack_ratio} > 1.60")
 return {"hp_max_min_ratio":hp_ratio,"attack_max_min_ratio":attack_ratio,"warnings":warnings,"review":bool(warnings)}

def run_audit(trials=10,level=10,rarity="rare",seed=14622):
 trials=max(2,min(100,int(trials))); level=max(1,min(100,int(level)))
 if rarity not in RARITIES: raise ValueError("rarity must be common, uncommon or rare")
 actors={key:_actor_snapshot(key,level,rarity) for key in CLASSES}; skills=_skill_audit(); integrity=_matrix_integrity(trials,level,rarity,seed); sensitivity=_sensitivity(trials,level,rarity,seed+900000); fixtures=_fixture_warnings(actors); parity=_slot_weighted_fixture_parity(); verdict="PASS" if skills["pass"] and integrity["pass"] and parity["pass"] else "FAIL"
 return {"version":"14.6.2d","verdict":verdict,"trials":trials,"level":level,"rarity":rarity,"actors":actors,"skills":skills,"matrix_integrity":integrity,"modifier_sensitivity":sensitivity,"fixture_warnings":fixtures,"fixture_slot_parity":parity,"all_classes_checked":len(actors)==6,"all_skills_checked":skills["skills_checked"]==18,"live_balance_changed":False,"production_database_writes":0,"corrections_applied":False}

def save_report(data,path):
 value=Path(path); value.parent.mkdir(parents=True,exist_ok=True); value.write_text(json.dumps(data,ensure_ascii=False,indent=2,sort_keys=True)+"\n",encoding="utf-8"); return value

def format_summary(data):
    integrity = dict(data.get("matrix_integrity") or {})
    slot_parity = dict(data.get("fixture_slot_parity") or {})
    spread = dict(data.get("fixture_warnings") or {})
    sensitivity = dict(data.get("modifier_sensitivity") or {})
    trials = int(data.get("trials") or 0)
    side_review = bool(integrity.get("side_delta_review"))
    statistical_label = "REVIEW" if trials < 100 else ("REVIEW" if side_review else "PASS")
    lines = [
        f"🔎 <b>PvP production fixture audit {data.get('version', '14.6.2d')}</b>",
        "",
        f"Verdict: <b>{data.get('verdict', 'FAIL')}</b>",
        f"Класів перевірено: {len(data.get('actors') or {})}/6",
        f"Навичок перевірено: {dict(data.get('skills') or {}).get('skills_checked', 0)}/18",
        f"Mirror/matrix integrity: {'PASS' if integrity.get('pass') else 'FAIL'}",
        f"Max side delta: {integrity.get('max_side_delta_pp', 0)} п.п.",
        f"Modifier sensitivity: {'PASS' if sensitivity.get('all_observable') else 'REVIEW'}",
        f"Slot-weighted fixture parity: {'PASS' if slot_parity.get('pass') else 'FAIL'}",
        f"Fixture balance spread: {'REVIEW' if spread.get('review') else 'PASS'}",
        f"Statistical confidence: {statistical_label} ({trials} trials/direction)",
    ]
    if trials < 100:
        lines.append("Рекомендація: повторити audit зі 100 trials для статистичного review.")
    if side_review:
        lines.append("Side-order sensitivity: REVIEW.")
    lines.extend(["", "Live-баланс не змінено."])
    return "\n".join(lines)
