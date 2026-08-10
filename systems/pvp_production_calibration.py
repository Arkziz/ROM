from __future__ import annotations
import itertools, json, random
from contextlib import contextmanager
from pathlib import Path
from systems.pvp_models import PvpActorState
from systems.pvp_round_engine import resolve_pvp_round
from systems.pvp_skill_adapter import load_production_pvp_skill_catalog
from systems.pvp_policy_metrics_audit import _choose as choose_action
from systems.simulation.combat_actor_stats import build_combat_stat_snapshot
from systems.simulation.models import SimulationInventory, SimulationInventoryItem, SimulationEquipment

CLASSES=("warrior","knight","scout","rogue","mage","priest")
LABELS={"warrior":"Воїн","knight":"Лицар","scout":"Скаут","rogue":"Розбійник","mage":"Маг","priest":"Жрець"}
RARITIES=("common","uncommon","rare")
RARITY_MULT={"common":1.0,"uncommon":1.35,"rare":1.85}
ARMOR={"warrior":"chain","knight":"plate","scout":"leather","rogue":"leather","mage":"cloth","priest":"cloth"}
WEAPON={"warrior":"sword_2h","knight":"sword_1h","scout":"bow_2h","rogue":"dagger_1h","mage":"staff_2h","priest":"staff_2h"}
SLOTS=("main_hand","helmet","shoulders","chest","gloves","legs","boots","necklace","ring")

SLOT_BASE_WEIGHTS = {
    "main_hand": 1.80, "off_hand": 1.00, "helmet": 0.80,
    "shoulders": 0.70, "chest": 1.40, "gloves": 0.70,
    "legs": 1.20, "boots": 0.80, "necklace": 0.80, "ring": 0.80,
}
_unknown_fixture_slots = sorted(set(SLOTS) - set(SLOT_BASE_WEIGHTS))
if _unknown_fixture_slots:
    raise RuntimeError(f"Unsupported production fixture slots: {_unknown_fixture_slots}")
_raw_slot_weight_total = sum(SLOT_BASE_WEIGHTS[slot] for slot in SLOTS)
_slot_weight_scale = len(SLOTS) / _raw_slot_weight_total
SLOT_WEIGHTS = {
    slot: round(SLOT_BASE_WEIGHTS[slot] * _slot_weight_scale, 8)
    for slot in SLOTS
}
SLOT_WEIGHT_TOTAL = float(len(SLOTS))
SLOT_WEIGHTED_FIELDS = frozenset({
    "str", "dex", "int", "wis", "sta", "pdef", "mdef",
    "physical_defense", "magical_defense", "physical_min", "physical_max",
    "magical_min", "magical_max", "weapon_physical_min",
    "weapon_physical_max", "weapon_magical_min", "weapon_magical_max",
})


def _weighted_fixture_value(value, weight):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return value
    scaled = int(float(value) * float(weight) + 0.5)
    return max(1, scaled) if value > 0 else scaled


def _apply_slot_weight(stats, slot):
    if slot not in SLOT_WEIGHTS:
        raise ValueError(f"Unknown production fixture slot: {slot}")
    result = dict(stats)
    for key in SLOT_WEIGHTED_FIELDS:
        if key in result:
            result[key] = _weighted_fixture_value(result[key], SLOT_WEIGHTS[slot])
    result["fixture_slot_weight"] = SLOT_WEIGHTS[slot]
    return result


def _stats_unweighted(cls,slot,level,rarity):
 m=RARITY_MULT[rarity]; v=max(1,round(level*m)); d={"str":0,"dex":0,"int":0,"wis":0,"sta":0,"pdef":0,"mdef":0}
 if cls in ("warrior","knight"): d["str"]+=v; d["sta"]+=max(1,v//2)
 elif cls in ("scout","rogue"): d["dex"]+=v; d["str"]+=max(1,v//2)
 else: d["int"]+=v; d["wis"]+=max(1,v//2)
 if slot in ("helmet","shoulders","chest","gloves","legs","boots"):
  total=max(1,round(level*m*1.25)); armor=ARMOR[cls]; shares={"cloth":(.30,.70),"leather":(.55,.45),"chain":(.75,.25),"plate":(.88,.12)}[armor]
  d["pdef"]+=round(total*shares[0]); d["mdef"]+=round(total*shares[1])
 if slot=="main_hand":
  magical=cls in ("mage","priest"); base=max(1,round(level*m*1.6)); d["weapon_min_magic_damage" if magical else "weapon_min_damage"]=base; d["weapon_max_magic_damage" if magical else "weapon_max_damage"]=base+max(1,level//2)
 return d


def _stats(class_key, slot, level, rarity):
    return _apply_slot_weight(_stats_unweighted(class_key, slot, level, rarity), slot)

def build_standard_actor(cls,level=10,rarity="rare",uid=1,class_damage=1.0):
 if cls not in CLASSES or rarity not in RARITIES: raise ValueError("unsupported class/rarity")
 inv=SimulationInventory(capacity=40); eq=SimulationEquipment(); n=1
 for slot in SLOTS:
  item=SimulationInventoryItem(simulation_item_id=n,item_id=100000+n,name=f"{LABELS[cls]} {slot}",category="equipment",slot_key=slot,rarity=rarity,quantity=1,durability=100,refine_level=0,stats=_stats(cls,slot,level,rarity))
  inv.items.append(item); eq.slots[slot]=item.simulation_item_id; n+=1
 s=build_combat_stat_snapshot(cls,level,inv,eq); mana=s.resource_type=="mana"
 atk=round(s.attack*class_damage); matk=round(s.magic_attack*class_damage); wmin=round(s.weapon_min_damage*class_damage); wmax=round(s.weapon_max_damage*class_damage)
 return PvpActorState(user_id=uid,class_key=cls,character_name=LABELS[cls],max_hp=s.max_hp,hp=s.max_hp,max_mp=s.max_mp,mp=s.max_mp,resource_type=s.resource_type,resource=0 if s.resource_type=="rage" else (s.max_mp if mana else 100),combo=0,physical_attack=atk,magical_attack=matk,physical_defense=s.pdef,magical_defense=s.mdef,weapon_physical_min=0 if mana else wmin,weapon_physical_max=0 if mana else wmax,weapon_magical_min=wmin if mana else 0,weapon_magical_max=wmax if mana else 0,physical_crit_chance=5,magical_crit_chance=5,dodge_chance=5,level=level)

@contextmanager
def healing_multiplier(value):
 import systems.pvp_round_engine as eng
 old=getattr(eng,"PVP_HEALING_MULTIPLIER",1.0); eng.PVP_HEALING_MULTIPLIER=float(value)
 try: yield
 finally: eng.PVP_HEALING_MULTIPLIER=old

def duel(a_cls,b_cls,trials=100,level=10,rarity="rare",seed=1462,healing=1.0,class_damage=None):
 class_damage=class_damage or {}; catalog=load_production_pvp_skill_catalog(); wins_a=wins_b=draws=0; rounds=[]; totals={"damage_a":0,"damage_b":0,"healing_a":0,"healing_b":0,"shield_a":0,"shield_b":0,"dot_a":0,"dot_b":0}
 with healing_multiplier(healing):
  for i in range(int(trials)):
   swap=bool(i%2); ca,cb=(b_cls,a_cls) if swap else (a_cls,b_cls); a=build_standard_actor(ca,level,rarity,1,class_damage.get(ca,1.0)); b=build_standard_actor(cb,level,rarity,2,class_damage.get(cb,1.0)); result=None; local={1:{"damage":0,"healing":0,"shield":0,"dot":0},2:{"damage":0,"healing":0,"shield":0,"dot":0}}
   for rnd in range(1,51):
    ia=choose_action(a,b,"target_aware",random.Random(seed+i*1000+rnd),catalog); ib=choose_action(b,a,"target_aware",random.Random(seed+i*1000+rnd+37),catalog)
    before={1:a,2:b}; result=resolve_pvp_round(rnd,rnd,a,b,ia,ib,seed=seed+i*1000+rnd,catalog=catalog)
    for outcome in result.outcomes:
     uid=int(outcome.user_id); local[uid]["damage"]+=int(outcome.damage or 0); local[uid]["healing"]+=int(outcome.healing or 0)
    for event in result.events:
     uid=int(event.get("user_id") or 0); kind=str(event.get("type") or ""); value=int(event.get("value") or 0)
     if uid in local and kind=="hot_tick": local[uid]["healing"]+=value
     elif uid in local and kind=="shield_absorb": local[uid]["shield"]+=value
     elif uid in local and kind=="dot_tick":
      key=str(event.get("effect") or ""); source_id=int(dict(before[uid].effects.get(key) or {}).get("source_id") or 0)
      if source_id in local: local[source_id]["dot"]+=value
    a=PvpActorState.from_dict(result.actor_a); b=PvpActorState.from_dict(result.actor_b)
    if result.terminal: break
   original_a_uid=2 if swap else 1; original_b_uid=1 if swap else 2
   if not result.winner_id: draws+=1
   elif int(result.winner_id)==original_a_uid: wins_a+=1
   elif int(result.winner_id)==original_b_uid: wins_b+=1
   else: raise AssertionError(f"unexpected winner_id={result.winner_id}")
   for metric in ("damage","healing","shield","dot"):
    totals[f"{metric}_a"]+=local[original_a_uid][metric]; totals[f"{metric}_b"]+=local[original_b_uid][metric]
   rounds.append(result.round_number)
 if wins_a+wins_b+draws!=int(trials): raise AssertionError(f"duel invariant failed: {wins_a}+{wins_b}+{draws}!={trials}")
 answer={"class_a":a_cls,"class_b":b_cls,"trials":int(trials),"level":level,"rarity":rarity,"healing_multiplier":healing,"class_damage":class_damage,"wins_a":wins_a,"wins_b":wins_b,"draws":draws,"win_rate_a":round(100*wins_a/int(trials),2),"win_rate_b":round(100*wins_b/int(trials),2),"avg_rounds":round(sum(rounds)/len(rounds),2)}
 for key,value in totals.items(): answer[f"avg_{key}"]=round(value/int(trials),2)
 return answer

def matrix(trials=50,level=10,rarity="rare",seed=1462,healing=1.0,class_damage=None):
 rows=[]
 for i,a in enumerate(CLASSES):
  for j,b in enumerate(CLASSES): rows.append(duel(a,b,trials,level,rarity,seed+i*10000+j*100,healing,class_damage))
 summary={c:{"wins":0,"losses":0,"draws":0,"games":0,"non_mirror_games":0,"non_mirror_wins":0} for c in CLASSES}
 for r in rows:
  s=summary[r["class_a"]]; s["wins"]+=r["wins_a"]; s["losses"]+=r["wins_b"]; s["draws"]+=r["draws"]; s["games"]+=r["trials"]
  if r["class_a"]!=r["class_b"]: s["non_mirror_games"]+=r["trials"]; s["non_mirror_wins"]+=r["wins_a"]
 for s in summary.values(): s["overall_win_rate"]=round(100*s["wins"]/max(1,s["games"]),2); s["non_mirror_win_rate"]=round(100*s["non_mirror_wins"]/max(1,s["non_mirror_games"]),2)
 return {"version":"14.6.2c","mode":"production_standardized","trials_per_matchup":trials,"level":level,"rarity":rarity,"healing_multiplier":healing,"class_damage":class_damage or {},"matchups":rows,"class_summary":summary,"production_database_writes":0,"live_balance_changed":False}

def score(report):
 vals=[v["non_mirror_win_rate"] for v in report["class_summary"].values()]; return round(sum(abs(v-50) for v in vals)/len(vals),3)

def calibrate(trials=20,level=10,rarity="rare",seed=1462):
 candidates=[]
 for healing in (.4,.55,.7,.85,1.0):
  for warrior in (1.0,1.15,1.3,1.45):
   for scout in (1.0,1.15,1.3):
    r=matrix(trials,level,rarity,seed,healing,{"warrior":warrior,"scout":scout}); candidates.append({"score":score(r),"healing":healing,"warrior_damage":warrior,"scout_damage":scout,"class_summary":r["class_summary"]})
 candidates.sort(key=lambda x:x["score"]); return {"version":"14.6.2c","trials":trials,"level":level,"rarity":rarity,"candidates_tested":len(candidates),"best":candidates[:10],"live_balance_changed":False}

def save_report(data,path):
 p=Path(path); p.parent.mkdir(parents=True,exist_ok=True); p.write_text(json.dumps(data,ensure_ascii=False,indent=2,sort_keys=True)+"\n",encoding="utf-8"); return p
