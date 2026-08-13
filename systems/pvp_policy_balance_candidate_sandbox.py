from __future__ import annotations
import json,random
from collections import Counter
from pathlib import Path
from systems.pvp_models import PvpActionIntent,PvpActorState
from systems.pvp_policy_metrics_audit import _choose as production_choose,_valid
from systems.pvp_production_calibration import CLASSES
from systems.pvp_real_actor_state_replay import build_real_actor
from systems.pvp_round_engine import resolve_pvp_round
from systems.pvp_skill_adapter import load_production_pvp_skill_catalog
VERSION="14.6.4"
SCENARIOS={
 "baseline":{"policy_fix":False,"stats":{}},
 "policy_only":{"policy_fix":True,"stats":{}},
 "candidate_gentle":{"policy_fix":True,"stats":{"scout_patk":1.35,"rogue_patk":1.25,"mage_matk":1.12,"priest_matk":0.95,"knight_pdef":0.95}},
 "candidate_stronger":{"policy_fix":True,"stats":{"scout_patk":1.50,"rogue_patk":1.35,"mage_matk":1.20,"priest_matk":0.90,"knight_pdef":0.90}},
}
def _actor(cls,uid,cfg):
 a=build_real_actor(cls,uid); s=cfg.get("stats",{})
 if cls=="scout": a.physical_attack*=s.get("scout_patk",1)
 if cls=="rogue": a.physical_attack*=s.get("rogue_patk",1)
 if cls=="mage": a.magical_attack*=s.get("mage_matk",1)
 if cls=="priest": a.magical_attack*=s.get("priest_matk",1)
 if cls=="knight": a.physical_defense*=s.get("knight_pdef",1)
 return a
def _intent(actor,key=None): return PvpActionIntent(actor.user_id,"skill",key) if key else PvpActionIntent(actor.user_id,"basic_attack")
def _choose(actor,enemy,rng,catalog,cfg):
 if cfg.get("policy_fix") and actor.class_key=="knight":
  valid={s["key"]:s for s in catalog["knight"] if _valid(actor,s)}; shield=dict(actor.effects.get("shield") or {}); remaining=int(shield.get("remaining",0) or 0)
  if "knight_judgement" in valid and actor.resource>=50: return _intent(actor,"knight_judgement")
  if "knight_holy_protection" in valid and remaining<=0: return _intent(actor,"knight_holy_protection")
  if remaining>0 and actor.resource<50: return _intent(actor)
  if "knight_shield_bash" in valid: return _intent(actor,"knight_shield_bash")
 return production_choose(actor,enemy,"target_aware",rng,catalog)
def _duel(ca,cb,trials,seed,cfg):
 catalog=load_production_pvp_skill_catalog(); wins=Counter(); draws=0; rounds=[]; judgement=0; terminals=Counter()
 for i in range(trials):
  swap=bool(i%2); x,y=(cb,ca) if swap else (ca,cb); a,b=_actor(x,1,cfg),_actor(y,2,cfg)
  for rnd in range(1,51):
   ia=_choose(a,b,random.Random(seed+i*1000+rnd),catalog,cfg); ib=_choose(b,a,random.Random(seed+i*1000+rnd+37),catalog,cfg)
   judgement+=int(ia.skill_key=="knight_judgement")+int(ib.skill_key=="knight_judgement")
   r=resolve_pvp_round(rnd,rnd,a,b,ia,ib,seed=seed+i*1000+rnd,catalog=catalog); a=PvpActorState.from_dict(r.actor_a); b=PvpActorState.from_dict(r.actor_b)
   if r.terminal: break
  rounds.append(r.round_number); terminals[str(r.result_reason or "none")]+=1
  if r.winner_id is None: draws+=1
  else: wins[a.class_key if r.winner_id==a.user_id else b.class_key]+=1
 return {"class_a":ca,"class_b":cb,"a_win_rate":round(100*wins[ca]/trials,2),"b_win_rate":round(100*wins[cb]/trials,2),"draw_rate":round(100*draws/trials,2),"avg_rounds":round(sum(rounds)/trials,2),"judgement_uses":judgement,"terminal_reasons":dict(terminals)}
def _score(rows):
 dominance=sum(1 for r in rows if max(r["a_win_rate"],r["b_win_rate"])>=95 or min(r["a_win_rate"],r["b_win_rate"])<=5)
 high_draw=sum(1 for r in rows if r["draw_rate"]>=50); round_limit=sum(r["terminal_reasons"].get("round_limit_hp_percent",0) for r in rows)
 class_rates={c:round(sum((r["a_win_rate"] if r["class_a"]==c else r["b_win_rate"]) for r in rows if c in (r["class_a"],r["class_b"]))/5,2) for c in CLASSES}
 spread=round(max(class_rates.values())-min(class_rates.values()),2)
 return {"dominance_count":dominance,"high_draw_count":high_draw,"round_limit_battles":round_limit,"class_average_win_rates":class_rates,"class_win_rate_spread_pp":spread,"objective":round(dominance*100+high_draw*50+round_limit/10+spread,2)}
def run_sandbox(trials=50,seed=14640):
 trials=max(10,min(200,int(trials))); scenarios={}
 for si,(name,cfg) in enumerate(SCENARIOS.items()):
  rows=[]
  for i,a in enumerate(CLASSES):
   for j in range(i+1,len(CLASSES)): rows.append(_duel(a,CLASSES[j],trials,seed+si*1000000+i*100000+j*1000,cfg))
  scenarios[name]={"config":cfg,"rows":rows,"score":_score(rows),"judgement_uses":sum(r["judgement_uses"] for r in rows)}
 ranked=sorted(scenarios,key=lambda n:(scenarios[n]["score"]["objective"],n)); best=ranked[0]
 return {"version":VERSION,"verdict":"PASS_WITH_REVIEW","trials_per_pair":trials,"scenarios":scenarios,"ranking":ranked,"recommended_candidate":best,"recommendation_status":"SANDBOX_ONLY_NOT_APPROVED_FOR_LIVE","production_round_resolver_used":True,"production_skill_catalog_used":True,"live_balance_changed":False,"fixture_values_changed":False,"production_database_writes":0}
def save_report(data,path):
 p=Path(path); p.parent.mkdir(parents=True,exist_ok=True); p.write_text(json.dumps(data,ensure_ascii=False,indent=2,sort_keys=True)+"\n",encoding="utf-8"); return p
def format_summary(d):
 lines=[f"PvP policy and balance candidate sandbox {d['version']}",f"Verdict: {d['verdict']}",f"Trials/pair/scenario: {d['trials_per_pair']}"]
 for n in d["ranking"]:
  x=d["scenarios"][n]; s=x["score"]; lines.append(f"{n}: dominance={s['dominance_count']}, high_draw={s['high_draw_count']}, spread={s['class_win_rate_spread_pp']} pp, Judgement={x['judgement_uses']}, objective={s['objective']}")
 lines += [f"Recommended sandbox candidate: {d['recommended_candidate']}","Live approval: NO","Live balance changed: NO"]
 return "\n".join(lines)
