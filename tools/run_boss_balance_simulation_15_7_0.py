from __future__ import annotations
import json,math,random,statistics,sys
from collections import Counter,defaultdict
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from systems.boss_system import build_location_boss,prepare_boss_turn,build_boss_damage_request,finalize_boss_turn,get_effective_boss_defenses
from systems.combat_system import calculate_mob_attack
CLASSES=('warrior','knight','scout','rogue','mage','priest')
LEVELS={'start_path':range(1,6),'dark_forest':range(6,11)}
TRIALS_PER_CELL=200
MAX_ROUNDS=80
# Read-only standardized baseline. It intentionally uses the canonical level-up
# stat rule and class-role coefficients; no users or DB fixtures are created.
ROLE={
 'warrior':{'hp':1.12,'atk':1.12,'pdef':1.15,'mdef':0.90,'dodge':0.95},
 'knight': {'hp':1.22,'atk':0.92,'pdef':1.35,'mdef':1.00,'dodge':0.85},
 'scout':  {'hp':0.94,'atk':1.18,'pdef':0.90,'mdef':0.92,'dodge':1.25},
 'rogue':  {'hp':0.92,'atk':1.20,'pdef':0.88,'mdef':0.90,'dodge':1.30},
 'mage':   {'hp':0.86,'atk':1.28,'pdef':0.78,'mdef':1.18,'dodge':1.00},
 'priest': {'hp':0.98,'atk':0.96,'pdef':0.86,'mdef':1.30,'dodge':0.95},
}
def actor(cls,level):
 base=10+level-1; r=ROLE[cls]
 hp=round((100+level*20+base*5)*r['hp'])
 atk=round(base*r['atk']+level*3)
 pdef=round((base*.2+level*2)*r['pdef']);mdef=round((base+level)*r['mdef'])
 dex=round(base*r['dodge']);wis=base;sta=base
 return {'class':cls,'level':level,'hp':hp,'max_hp':hp,'attack':atk,'pdef':pdef,'mdef':mdef,'dex':dex,'wis':wis,'sta':sta,'attack_type':'magical' if cls in {'mage','priest'} else 'physical'}
def player_hit(a,boss,rng):
 pdef,mdef=get_effective_boss_defenses(boss); defense=mdef if a['attack_type']=='magical' else pdef
 spread=rng.uniform(.88,1.12); raw=max(1,a['attack']*spread-defense*.5)
 crit=rng.random()<.08; return max(1,round(raw*(1.5 if crit else 1)))
def one(cls,level,location,seed):
 rng=random.Random(seed);a=actor(cls,level);b=build_location_boss(location,level,rng=rng)
 enrage=False;special=False;bleed_total=0;buff_rounds=Counter();actions=Counter()
 for rnd in range(1,MAX_ROUNDS+1):
  b['hp']-=player_hit(a,b,rng)
  if b['hp']<=0:return {'win':1,'rounds':rnd,'hp_pct':max(0,a['hp'])/a['max_hp'],'enrage':enrage,'special':special,'bleed':bleed_total,'actions':actions,'buff_rounds':buff_rounds}
  turn=prepare_boss_turn(b,rng=rng);plan=turn['action_plan'];actions[plan['skill_key']]+=1
  enrage|=bool(turn.get('enrage_triggered'));special|=bool(turn.get('enrage_triggered'))
  req=build_boss_damage_request(plan);damage=0
  if req:
   # Use production mob attack calculation with deterministic global random state.
   state=random.getstate();random.seed(seed*100+rnd)
   try:res=calculate_mob_attack(req['mob_attack'],a['pdef'],a['mdef'],a['dex'],b['dex'],a['sta'],level,req['attack_type'])
   finally:random.setstate(state)
   damage=int(res['damage'])
  result=finalize_boss_turn(b,plan,damage)
  pe=result.get('player_effect')
  if pe: b.setdefault('_sim_bleed',{})['effect']=dict(pe)
  if b['boss_state'].get('attack_buff_turns',0)>0:buff_rounds['attack']+=1
  if b['boss_state'].get('defense_buff_turns',0)>0:buff_rounds['defense']+=1
  a['hp']-=damage
  effect=(b.get('_sim_bleed') or {}).get('effect')
  if effect and a['hp']>0:
   tick=min(a['hp'],int(effect['damage']));a['hp']-=tick;bleed_total+=tick;effect['turns']-=1
   if effect['turns']<=0:b.pop('_sim_bleed',None)
  if a['hp']<=0:return {'win':0,'rounds':rnd,'hp_pct':0.0,'enrage':enrage,'special':special,'bleed':bleed_total,'actions':actions,'buff_rounds':buff_rounds}
 return {'win':0,'rounds':MAX_ROUNDS,'hp_pct':max(0,a['hp'])/a['max_hp'],'enrage':enrage,'special':special,'bleed':bleed_total,'actions':actions,'buff_rounds':buff_rounds,'round_cap':1}
rows=[];totals=[]
for location,levels in LEVELS.items():
 for level in levels:
  for cls in CLASSES:
   runs=[one(cls,level,location,157000+level*100000+CLASSES.index(cls)*1000+i) for i in range(TRIALS_PER_CELL)]
   wins=sum(x['win'] for x in runs);actions=Counter();buffs=Counter()
   for x in runs:actions.update(x['actions']);buffs.update(x['buff_rounds'])
   row={'location':location,'level':level,'class':cls,'trials':len(runs),'wins':wins,'win_rate':round(wins/len(runs),4),'death_rate':round(1-wins/len(runs),4),'avg_rounds':round(statistics.mean(x['rounds'] for x in runs),2),'avg_remaining_hp_percent':round(statistics.mean(x['hp_pct'] for x in runs)*100,2),'enrage_reach_rate':round(sum(x['enrage'] for x in runs)/len(runs),4),'special_use_rate':round(sum(x['special'] for x in runs)/len(runs),4),'avg_bleed_damage':round(statistics.mean(x['bleed'] for x in runs),2),'round_cap_count':sum(x.get('round_cap',0) for x in runs),'actions':dict(actions),'buff_rounds':dict(buffs)}
   rows.append(row)
class_summary={}
for cls in CLASSES:
 data=[x for x in rows if x['class']==cls];class_summary[cls]={'cells':len(data),'mean_win_rate':round(statistics.mean(x['win_rate'] for x in data),4),'min_win_rate':min(x['win_rate'] for x in data),'max_win_rate':max(x['win_rate'] for x in data),'mean_rounds':round(statistics.mean(x['avg_rounds'] for x in data),2)}
all_rates=[x['win_rate'] for x in rows];spread=max(v['mean_win_rate'] for v in class_summary.values())-min(v['mean_win_rate'] for v in class_summary.values())
findings=[]
if any(x['round_cap_count'] for x in rows):findings.append('round_cap_reached')
if spread>0.35:findings.append('class_win_rate_spread_over_35pp')
if min(all_rates)<0.10:findings.append('one_or_more_cells_below_10pct_win_rate')
if max(all_rates)>0.95:findings.append('one_or_more_cells_above_95pct_win_rate')
verdict='PASS' if not findings else 'PASS_WITH_REVIEW'
result={'version':'15.7.0','verdict':verdict,'model':'standardized_read_only_baseline','trials_per_cell':TRIALS_PER_CELL,'total_trials':len(rows)*TRIALS_PER_CELL,'cells':len(rows),'classes':list(CLASSES),'levels':{'start_path':[1,2,3,4,5],'dark_forest':[6,7,8,9,10]},'class_summary':class_summary,'class_mean_win_rate_spread':round(spread,4),'findings':findings,'rows':rows,'database_writes':0,'live_balance_changed':False,'feature_gate_changed':False}
out=ROOT/'reports'/'boss_stage_15_7_0_balance_simulation.json';out.parent.mkdir(exist_ok=True);out.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
print(f"[{verdict}] boss balance simulation",{'cells':len(rows),'trials':result['total_trials'],'spread':result['class_mean_win_rate_spread'],'findings':findings})
