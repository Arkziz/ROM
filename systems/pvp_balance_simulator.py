from __future__ import annotations
import json
from pathlib import Path
from systems.pvp_models import PvpActionIntent,PvpActorState
from systems.pvp_round_engine import resolve_pvp_round
from systems.pvp_skill_adapter import load_production_pvp_skill_catalog
CLASSES=("warrior","knight","scout","rogue","mage","priest")
LABELS={"warrior":"Воїн","knight":"Лицар","scout":"Скаут","rogue":"Розбійник","mage":"Маг","priest":"Жрець"}
RESOURCE={"warrior":"rage","knight":"rage","scout":"combat_energy","rogue":"combat_energy_combo","mage":"mana","priest":"mana"}

def actor(uid,cls):
 return PvpActorState(user_id=uid,class_key=cls,character_name=LABELS[cls],max_hp=1000,hp=1000,max_mp=500,mp=500,resource_type=RESOURCE[cls],resource=0 if RESOURCE[cls]=="rage" else 100,combo=0,physical_attack=75,magical_attack=75,physical_defense=35,magical_defense=35,weapon_physical_min=20,weapon_physical_max=20,weapon_magical_min=20,weapon_magical_max=20,physical_crit_chance=5,magical_crit_chance=5,dodge_chance=5,level=20)

def choose(a,catalog):
 skills=catalog[a.class_key]
 for s in reversed(skills):
  if a.cooldowns.get(s["key"],0)>1: continue
  t=s.get("cost_type"); cost=int(s.get("cost") or 0)
  if t=="mana" and a.mp<cost: continue
  if t=="rage" and a.resource<cost: continue
  if t=="rage_all_min" and a.resource<int(s.get("min_cost") or 0): continue
  projected=min(100,a.resource+20) if "energy" in a.resource_type else a.resource
  if t in {"combat_energy","combat_energy_combo"} and projected<cost: continue
  if t=="combat_energy_combo" and a.combo<int(s.get("min_combo") or 1): continue
  return PvpActionIntent(a.user_id,"skill",s["key"])
 return PvpActionIntent(a.user_id,"basic_attack")

def simulate_duel(class_a,class_b,seed=1,max_rounds=50):
 if class_a not in CLASSES or class_b not in CLASSES: raise ValueError("unknown class")
 catalog=load_production_pvp_skill_catalog(); a=actor(1,class_a); b=actor(2,class_b)
 damage={1:0,2:0}; healing={1:0,2:0}; shields={1:0,2:0}; stuns={1:0,2:0}
 result=None
 for rnd in range(1,max_rounds+1):
  result=resolve_pvp_round(rnd,rnd,a,b,choose(a,catalog),choose(b,catalog),seed=seed*1000+rnd,catalog=catalog)
  for o in result.outcomes: damage[o.user_id]+=o.damage; healing[o.user_id]+=o.healing
  for e in result.events:
   if e.get("type")=="hot_tick": healing[int(e["user_id"])]+=int(e.get("value") or 0)
   if e.get("type")=="shield_absorb": shields[int(e["user_id"])]+=int(e.get("value") or 0)
  for o in result.outcomes:
   stuns[o.user_id]+=sum(1 for x in o.applied_effects if x.get("effect_key")=="stun_next")
  a=PvpActorState.from_dict(result.actor_a); b=PvpActorState.from_dict(result.actor_b)
  if result.terminal: break
 return {"class_a":class_a,"class_b":class_b,"winner":"a" if result.winner_id==1 else "b" if result.winner_id==2 else "draw","rounds":result.round_number,"hp_a":a.hp,"hp_b":b.hp,"damage_a":damage[1],"damage_b":damage[2],"healing_a":healing[1],"healing_b":healing[2],"shield_a":shields[1],"shield_b":shields[2],"stuns_a":stuns[1],"stuns_b":stuns[2],"reason":result.result_reason}

def simulate_matchup(class_a,class_b,trials=100,seed=1460):
 trials=max(1,min(5000,int(trials))); rows=[]
 # Swap user-side assignment every trial to expose first/second actor bias.
 for i in range(trials):
  if i%2==0: rows.append(simulate_duel(class_a,class_b,seed+i))
  else:
   x=simulate_duel(class_b,class_a,seed+i); x={**x,"class_a":class_a,"class_b":class_b,"winner":"a" if x["winner"]=="b" else "b" if x["winner"]=="a" else "draw","hp_a":x["hp_b"],"hp_b":x["hp_a"],"damage_a":x["damage_b"],"damage_b":x["damage_a"],"healing_a":x["healing_b"],"healing_b":x["healing_a"],"shield_a":x["shield_b"],"shield_b":x["shield_a"],"stuns_a":x["stuns_b"],"stuns_b":x["stuns_a"]}; rows.append(x)
 return {"class_a":class_a,"class_b":class_b,"trials":trials,"wins_a":sum(x["winner"]=="a" for x in rows),"wins_b":sum(x["winner"]=="b" for x in rows),"draws":sum(x["winner"]=="draw" for x in rows),"win_rate_a":round(100*sum(x["winner"]=="a" for x in rows)/trials,2),"win_rate_b":round(100*sum(x["winner"]=="b" for x in rows)/trials,2),"avg_rounds":round(sum(x["rounds"] for x in rows)/trials,2),"avg_hp_a":round(sum(x["hp_a"] for x in rows)/trials,2),"avg_hp_b":round(sum(x["hp_b"] for x in rows)/trials,2),"avg_damage_a":round(sum(x["damage_a"] for x in rows)/trials,2),"avg_damage_b":round(sum(x["damage_b"] for x in rows)/trials,2),"avg_healing_a":round(sum(x["healing_a"] for x in rows)/trials,2),"avg_healing_b":round(sum(x["healing_b"] for x in rows)/trials,2),"avg_shield_a":round(sum(x["shield_a"] for x in rows)/trials,2),"avg_shield_b":round(sum(x["shield_b"] for x in rows)/trials,2)}

def simulate_matrix(trials=100,seed=1460):
 rows=[simulate_matchup(a,b,trials,seed+i*10000+j*100) for i,a in enumerate(CLASSES) for j,b in enumerate(CLASSES)]
 summary={c:{"wins":0,"losses":0,"draws":0,"games":0} for c in CLASSES}
 for r in rows:
  summary[r["class_a"]]["wins"]+=r["wins_a"]; summary[r["class_a"]]["losses"]+=r["wins_b"]; summary[r["class_a"]]["draws"]+=r["draws"]; summary[r["class_a"]]["games"]+=r["trials"]
 for c,v in summary.items(): v["win_rate"]=round(100*v["wins"]/max(1,v["games"]),2)
 return {"version":"14.6.0","trials_per_matchup":trials,"matchups":rows,"class_summary":summary,"synthetic_equalized_actors":True,"balance_changes_applied":False}

def save_report(data,path):
 p=Path(path); p.parent.mkdir(parents=True,exist_ok=True); p.write_text(json.dumps(data,ensure_ascii=False,indent=2,sort_keys=True)+"\n",encoding="utf-8"); return p

def format_matchup(r): return f"⚔️ {LABELS[r['class_a']]} проти {LABELS[r['class_b']]}\n\nСимуляцій: {r['trials']}\nПеремоги: {r['wins_a']} / {r['wins_b']}\nНічиї: {r['draws']}\nWin rate: {r['win_rate_a']}% / {r['win_rate_b']}%\nСередня тривалість: {r['avg_rounds']} раунд(и)\nСереднє HP: {r['avg_hp_a']} / {r['avg_hp_b']}"
