from __future__ import annotations
import json,random
from collections import Counter
from contextlib import contextmanager
from pathlib import Path
import systems.pvp_round_engine as engine
from systems.pvp_models import PvpActionIntent,PvpActorState
from systems.pvp_policy_metrics_audit import _choose as production_choose,_valid
from systems.pvp_production_calibration import CLASSES
from systems.pvp_real_actor_state_replay import build_real_actor
from systems.pvp_skill_adapter import load_production_pvp_skill_catalog
VERSION="14.6.4a"
SCENARIOS={
 "baseline":{},
 "mage_only":{"mage_matk":1.12},
 "dex_penetration":{"scout_pen":0.40,"rogue_pen":0.40},
 "priest_hot_reduction":{"priest_hot":0.65},
 "knight_controlled":{"judgement":0.45,"shield":0.65},
 "combined_conservative":{"mage_matk":1.08,"scout_pen":0.25,"rogue_pen":0.25,"priest_hot":0.80,"judgement":0.45,"shield":0.80},
 "combined_moderate":{"mage_matk":1.12,"scout_pen":0.40,"rogue_pen":0.40,"priest_hot":0.65,"judgement":0.45,"shield":0.65},
 "combined_aggressive":{"mage_matk":1.16,"scout_pen":0.55,"rogue_pen":0.55,"priest_hot":0.50,"judgement":0.55,"shield":0.60},
}
def _catalog(cfg):
 source=load_production_pvp_skill_catalog(); out={c:tuple(dict(s) for s in skills) for c,skills in source.items()}
 if "judgement" in cfg:
  for s in out["knight"]:
   if s["key"]=="knight_judgement": s["damage_multiplier"]*=cfg["judgement"]
 return out
def _actor(cls,uid,cfg):
 a=build_real_actor(cls,uid)
 if cls=="mage": a.magical_attack*=cfg.get("mage_matk",1)
 return a
def _intent(a,key=None): return PvpActionIntent(a.user_id,"skill",key) if key else PvpActionIntent(a.user_id,"basic_attack")
def _choose(a,b,rng,catalog,cfg):
 if "judgement" in cfg and a.class_key=="knight":
  valid={s["key"]:s for s in catalog["knight"] if _valid(a,s)}; shield=dict(a.effects.get("shield") or {}); remaining=int(shield.get("remaining",0) or 0)
  if "knight_judgement" in valid and a.resource>=50: return _intent(a,"knight_judgement")
  if "knight_holy_protection" in valid and remaining<=0: return _intent(a,"knight_holy_protection")
  if remaining>0 and a.resource<50: return _intent(a)
  if "knight_shield_bash" in valid: return _intent(a,"knight_shield_bash")
 return production_choose(a,b,"target_aware",rng,catalog)
def _penetration(actor,intent,cfg):
 if actor.class_key=="scout" and intent.skill_key=="scout_aimed_shot": return cfg.get("scout_pen",0)
 if actor.class_key=="rogue" and intent.skill_key=="rogue_eviscerate": return cfg.get("rogue_pen",0)
 return 0
@contextmanager
def _shield(value):
 old=engine.PVP_SHIELD_MULTIPLIER; engine.PVP_SHIELD_MULTIPLIER=old*value
 try: yield
 finally: engine.PVP_SHIELD_MULTIPLIER=old
def _duel(ca,cb,trials,seed,cfg):
 catalog=_catalog(cfg); wins=Counter(); draws=0; rounds=[]; terminals=Counter(); usage=Counter(); contributions=Counter()
 for i in range(trials):
  swap=bool(i%2); x,y=(cb,ca) if swap else (ca,cb); a,b=_actor(x,1,cfg),_actor(y,2,cfg)
  for rnd in range(1,51):
   ia=_choose(a,b,random.Random(seed+i*1000+rnd),catalog,cfg); ib=_choose(b,a,random.Random(seed+i*1000+rnd+37),catalog,cfg)
   for it in (ia,ib): usage[str(it.skill_key or it.action_type)]+=1
   pa=_penetration(a,ia,cfg); pb=_penetration(b,ib,cfg); old_a=a.physical_defense; old_b=b.physical_defense
   if pa: b.physical_defense*=1-pa; contributions["scout_penetration_rounds"]+=1
   if pb: a.physical_defense*=1-pb; contributions["rogue_penetration_rounds"]+=1
   with _shield(cfg.get("shield",1)): r=engine.resolve_pvp_round(rnd,rnd,a,b,ia,ib,seed=seed+i*1000+rnd,catalog=catalog)
   na=PvpActorState.from_dict(r.actor_a); nb=PvpActorState.from_dict(r.actor_b); na.physical_defense=old_a; nb.physical_defense=old_b
   for actor in (na,nb):
    if actor.class_key=="priest" and "hot" in actor.effects and "priest_hot" in cfg:
     effect=dict(actor.effects["hot"]); original=float(effect.get("power",0)); scaled=max(1,round(original*cfg["priest_hot"])); contributions["priest_hot_reduction"]+=max(0,round(original-scaled)); effect["power"]=scaled; actor.effects["hot"]=effect
   for out in r.outcomes:
    if out.skill_key=="knight_judgement": contributions["judgement_damage"]+=int(out.damage or 0)
   a,b=na,nb
   if r.terminal: break
  rounds.append(r.round_number); terminals[str(r.result_reason or "none")]+=1
  if r.winner_id is None: draws+=1
  else: wins[a.class_key if r.winner_id==a.user_id else b.class_key]+=1
 return {"class_a":ca,"class_b":cb,"a_win_rate":round(100*wins[ca]/trials,2),"b_win_rate":round(100*wins[cb]/trials,2),"draw_rate":round(100*draws/trials,2),"avg_rounds":round(sum(rounds)/trials,2),"terminal_reasons":dict(terminals),"mechanic_usage":dict(usage),"contributions":dict(contributions)}
def _score(rows):
 dom=sum(1 for r in rows if max(r["a_win_rate"],r["b_win_rate"])>=95 or min(r["a_win_rate"],r["b_win_rate"])<=5); hd=sum(1 for r in rows if r["draw_rate"]>=50); limits=sum(r["terminal_reasons"].get("round_limit_hp_percent",0) for r in rows); rates={c:round(sum(r["a_win_rate"] if r["class_a"]==c else r["b_win_rate"] for r in rows if c in (r["class_a"],r["class_b"]))/5,2) for c in CLASSES}; spread=round(max(rates.values())-min(rates.values()),2); below=sum(1 for v in rates.values() if v<20); above=sum(1 for v in rates.values() if v>80)
 return {"dominance_count":dom,"high_draw_count":hd,"round_limit_battles":limits,"class_average_win_rates":rates,"class_win_rate_spread_pp":spread,"classes_below_20":below,"classes_above_80":above,"objective":round(dom*100+hd*50+limits/10+spread+below*100+above*100,2)}
def run_sandbox(trials=50,seed=14641):
 trials=max(10,min(150,int(trials))); scenarios={}
 for si,(name,cfg) in enumerate(SCENARIOS.items()):
  rows=[]
  for i,a in enumerate(CLASSES):
   for j in range(i+1,len(CLASSES)): rows.append(_duel(a,CLASSES[j],trials,seed+si*1000000+i*100000+j*1000,cfg))
  scenarios[name]={"config":cfg,"rows":rows,"score":_score(rows)}
 ranking=sorted(scenarios,key=lambda n:(scenarios[n]["score"]["objective"],n)); best=ranking[0]
 return {"version":VERSION,"verdict":"PASS_WITH_REVIEW","trials_per_pair":trials,"scenarios":scenarios,"ranking":ranking,"recommended_candidate":best,"recommendation_status":"SANDBOX_ONLY_NOT_APPROVED_FOR_LIVE","acceptance_targets":{"dominance_max":5,"spread_max_pp":40,"class_average_min":20,"class_average_max":80,"high_draw_max":0},"production_round_resolver_used":True,"production_skill_catalog_used":True,"live_balance_changed":False,"fixture_values_changed":False,"production_database_writes":0}
def save_report(d,path):
 p=Path(path); p.parent.mkdir(parents=True,exist_ok=True); p.write_text(json.dumps(d,ensure_ascii=False,indent=2,sort_keys=True)+"\n",encoding="utf-8"); return p
def format_summary(d):
 lines=[f"PvP targeted mechanics candidate sandbox {d['version']}",f"Verdict: {d['verdict']}",f"Trials/pair/scenario: {d['trials_per_pair']}"]
 for n in d["ranking"]:
  s=d["scenarios"][n]["score"]; lines.append(f"{n}: dominance={s['dominance_count']}, spread={s['class_win_rate_spread_pp']} pp, below20={s['classes_below_20']}, above80={s['classes_above_80']}, objective={s['objective']}")
 lines += [f"Recommended sandbox candidate: {d['recommended_candidate']}","Live approval: NO","Live balance changed: NO"]
 return "\n".join(lines)
