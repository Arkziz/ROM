from __future__ import annotations
import json,random
from collections import Counter,defaultdict
from pathlib import Path
from systems.pvp_balance_simulator import CLASSES,LABELS,actor
from systems.pvp_models import PvpActionIntent,PvpActorState
from systems.pvp_round_engine import resolve_pvp_round
from systems.pvp_skill_adapter import load_production_pvp_skill_catalog
POLICIES=("priority","random_valid","resource_aware")

def _projected_resource(a): return min(100,a.resource+20) if "energy" in a.resource_type else a.resource

def _valid(a,s):
 if a.cooldowns.get(s["key"],0)>1:return False
 t=s.get("cost_type"); c=int(s.get("cost") or 0); r=_projected_resource(a)
 if t=="mana" and a.mp<c:return False
 if t=="rage" and a.resource<c:return False
 if t=="rage_all_min" and a.resource<int(s.get("min_cost") or 0):return False
 if t in {"combat_energy","combat_energy_combo"} and r<c:return False
 if t=="combat_energy_combo" and a.combo<int(s.get("min_combo") or 1):return False
 return True

def _choose(a,policy,rng,catalog):
 valid=[s for s in catalog[a.class_key] if _valid(a,s)]
 if policy=="random_valid":
  choices=[None]+valid; choice=rng.choice(choices); return PvpActionIntent(a.user_id,"skill",choice["key"]) if choice else PvpActionIntent(a.user_id,"basic_attack")
 if policy=="resource_aware":
  by={s["key"]:s for s in valid}; cls=a.class_key
  if cls=="warrior":
   if "warrior_suppression" in by and "pdef_down" not in a.effects:return PvpActionIntent(a.user_id,"skill","warrior_suppression")
   if "warrior_subjugation_strike" in by and a.resource>=70:return PvpActionIntent(a.user_id,"skill","warrior_subjugation_strike")
   if "warrior_cleave" in by:return PvpActionIntent(a.user_id,"skill","warrior_cleave")
  if cls=="knight":
   sh=a.effects.get("shield",{}); rem=int(sh.get("remaining",0) or 0)
   if "knight_holy_protection" in by and rem<100:return PvpActionIntent(a.user_id,"skill","knight_holy_protection")
  if cls=="scout":
   if "scout_sting_arrow" in by:return PvpActionIntent(a.user_id,"skill","scout_sting_arrow")
   if "scout_trap" in by:return PvpActionIntent(a.user_id,"skill","scout_trap")
  if cls=="rogue":
   if a.combo>=3 and "rogue_eviscerate" in by:return PvpActionIntent(a.user_id,"skill","rogue_eviscerate")
   for k in ("rogue_bleeding_follow","rogue_sneak_strike"):
    if k in by:return PvpActionIntent(a.user_id,"skill",k)
  if cls=="mage":
   if a.mp<=125 and "mage_arcane_flow" in by:return PvpActionIntent(a.user_id,"skill","mage_arcane_flow")
   for k in ("mage_thunder_spell","mage_fireball"):
    if k in by:return PvpActionIntent(a.user_id,"skill",k)
  if cls=="priest":
   hot=a.effects.get("hot",{}); hp_pct=a.hp/max(1,a.max_hp)
   if "priest_healing_blessing" in by and hp_pct<0.75 and int(hot.get("duration",0) or 0)<=1:return PvpActionIntent(a.user_id,"skill","priest_healing_blessing")
   if "priest_purify_faith" in by and (a.mp<150 or any(x.get("kind") in {"poison","bleed","pdef_down","mdef_down"} for x in a.effects.values())):return PvpActionIntent(a.user_id,"skill","priest_purify_faith")
   if "priest_holy_ray" in by:return PvpActionIntent(a.user_id,"skill","priest_holy_ray")
  if valid:return PvpActionIntent(a.user_id,"skill",valid[-1]["key"])
  return PvpActionIntent(a.user_id,"basic_attack")
 if valid:return PvpActionIntent(a.user_id,"skill",valid[-1]["key"])
 return PvpActionIntent(a.user_id,"basic_attack")

def _blank():return {"actions":Counter(),"skill_success":Counter(),"damage":0,"healing":0,"overheal":0,"shield_absorbed":0,"dot_ticks":0,"hot_ticks":0,"stuns":0,"stunned_rounds":0,"resource_spent":0,"resource_gained":0,"combo_spent":0,"combo_gained":0,"rounds":0,"wins":0,"losses":0,"draws":0}

def simulate_duel(a_cls,b_cls,policy,seed):
 cat=load_production_pvp_skill_catalog(); a=actor(1,a_cls); b=actor(2,b_cls); rng=random.Random(seed); metrics={1:_blank(),2:_blank()}; result=None
 for rnd in range(1,51):
  ia=_choose(a,policy,rng,cat); ib=_choose(b,policy,rng,cat)
  metrics[1]["actions"][ia.skill_key or ia.action_type]+=1; metrics[2]["actions"][ib.skill_key or ib.action_type]+=1
  result=resolve_pvp_round(rnd,rnd,a,b,ia,ib,seed=seed*1000+rnd,catalog=cat)
  for o in result.outcomes:
   m=metrics[o.user_id]; m["damage"]+=o.damage; m["resource_spent"]+=o.resource_spent; m["resource_gained"]+=o.resource_gained; m["combo_spent"]+=o.combo_spent; m["combo_gained"]+=o.combo_gained
   if o.valid:m["skill_success"][o.skill_key or o.action_type]+=1
   if o.action_type=="stunned_skip":m["stunned_rounds"]+=1
   m["stuns"]+=sum(1 for x in o.applied_effects if x.get("effect_key")=="stun_next")
  for e in result.events:
   uid=int(e.get("user_id") or 0); m=metrics.get(uid)
   if not m:continue
   if e.get("type")=="hot_tick":m["healing"]+=int(e.get("value") or 0);m["overheal"]+=max(0,int(e.get("nominal_value") or 0)-int(e.get("value") or 0));m["hot_ticks"]+=1
   elif e.get("type")=="dot_tick":m["dot_ticks"]+=1
   elif e.get("type")=="shield_absorb":m["shield_absorbed"]+=int(e.get("value") or 0)
  a=PvpActorState.from_dict(result.actor_a);b=PvpActorState.from_dict(result.actor_b)
  metrics[1]["rounds"]=rnd;metrics[2]["rounds"]=rnd
  if result.terminal:break
 if result.winner_id==1:metrics[1]["wins"]+=1;metrics[2]["losses"]+=1
 elif result.winner_id==2:metrics[2]["wins"]+=1;metrics[1]["losses"]+=1
 else:metrics[1]["draws"]+=1;metrics[2]["draws"]+=1
 return result,metrics

def _merge(dst,src):
 for k,v in src.items():
  if isinstance(v,Counter):dst[k].update(v)
  else:dst[k]+=v

def audit_policy(policy,trials=25,seed=1461):
 if policy not in POLICIES:raise ValueError("unknown policy")
 trials=max(1,min(300,int(trials))); classes={c:_blank() for c in CLASSES}; matchups=[]
 for i,a in enumerate(CLASSES):
  for j,b in enumerate(CLASSES):
   wa=wb=dr=0;rs=0
   for n in range(trials):
    r,m=simulate_duel(a,b,policy,seed+i*100000+j*1000+n);_merge(classes[a],m[1]);_merge(classes[b],m[2]);rs+=r.round_number
    if r.winner_id==1:wa+=1
    elif r.winner_id==2:wb+=1
    else:dr+=1
   matchups.append({"class_a":a,"class_b":b,"wins_a":wa,"wins_b":wb,"draws":dr,"trials":trials,"avg_rounds":round(rs/trials,2)})
 summary={}
 for c,m in classes.items():
  games=m["wins"]+m["losses"]+m["draws"]; nonmirror=[x for x in matchups if x["class_a"]==c and x["class_b"]!=c]; nw=sum(x["wins_a"] for x in nonmirror);ng=sum(x["trials"] for x in nonmirror)
  summary[c]={**{k:(dict(v) if isinstance(v,Counter) else v) for k,v in m.items()},"games":games,"win_rate":round(100*m["wins"]/max(1,games),2),"non_mirror_win_rate":round(100*nw/max(1,ng),2),"avg_rounds":round(m["rounds"]/max(1,games),2)}
 return {"policy":policy,"trials_per_matchup":trials,"class_summary":summary,"matchups":matchups}

def audit_all_policies(trials=25):return {"version":"14.6.1","policies":{p:audit_policy(p,trials) for p in POLICIES},"balance_changes_applied":False,"synthetic_equalized_actors":True}
def save_report(data,path):p=Path(path);p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(data,ensure_ascii=False,indent=2,sort_keys=True)+"\n",encoding="utf-8");return p
def format_summary(data):
 lines=["🔬 <b>PvP policy audit</b>",f"\nСимуляцій на matchup: {next(iter(data['policies'].values()))['trials_per_matchup']}"]
 for p,r in data["policies"].items():
  lines.append(f"\n<b>{p}</b>")
  for c,x in sorted(r["class_summary"].items(),key=lambda z:z[1]["non_mirror_win_rate"],reverse=True):lines.append(f"{LABELS[c]}: non-mirror {x['non_mirror_win_rate']}%, overall {x['win_rate']}%")
 return "\n".join(lines)
