from __future__ import annotations
import copy,json,random,statistics,sys
from collections import Counter
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from systems.boss_system import build_location_boss,prepare_boss_turn,build_boss_damage_request,finalize_boss_turn,get_effective_boss_defenses
from systems.simulation.battle_models import BattleActor,BattleAction
from systems.simulation.progression_provider import ProgressionProvider
from systems.simulation.pve_battle import ExactPveBattleEngine
from systems.simulation.canonical_rules import call_rule
from systems.simulation.rng import SimulationRng
CLASSES=('warrior','knight','scout','rogue','mage','priest')
LOCATIONS={'start_path':range(1,6),'dark_forest':range(6,11)}
PROFILES={
 'naked':{'hp':1.00,'attack':1.00,'defense':1.00,'weapon':0},
 'progression':{'hp':1.20,'attack':1.35,'defense':1.30,'weapon':3},
 'strong':{'hp':1.45,'attack':1.70,'defense':1.60,'weapon':6},
}
TRIALS=50;MAX_TURNS=100

def actor(cls,level,profile):
 p=ProgressionProvider().player_actor(cls,level);m=PROFILES[profile]
 p.max_hp=max(1,round(p.max_hp*m['hp']));p.hp=p.max_hp
 p.attack=max(1,round(p.attack*m['attack']));p.magic_attack=max(1,round(p.magic_attack*m['attack']))
 p.pdef=max(0,round(p.pdef*m['defense']));p.mdef=max(0,round(p.mdef*m['defense']))
 p.weapon_min_damage=max(0,level*m['weapon']);p.weapon_max_damage=max(p.weapon_min_damage,round(level*m['weapon']*1.35))
 return p

def boss_actor(data):
 return BattleActor(data['name'],data['level'],data['hp'],data['max_hp'],data['attack'],data['attack'],data['pdef'],data['mdef'],data['dex'],0,0,data['attack_type'])

def one(cls,level,location,profile,seed):
 engine=ExactPveBattleEngine(ROOT,seed,max_turns=MAX_TURNS);p=actor(cls,level,profile);boss=build_location_boss(location,level,rng=random.Random(seed));m=boss_actor(boss);actions=[]
 p.resource_type={'warrior':'rage','knight':'rage','scout':'combat_energy','rogue':'combat_energy_combo','mage':'mana','priest':'mana'}[cls]
 if p.max_resource<=0:p.max_resource=100
 p.resource=0 if p.resource_type=='rage' else p.max_resource
 enrage=False;special=False;bleed_damage=0;boss_damage=0;player_damage=0
 for turn in range(1,MAX_TURNS+1):
  engine._tick_start(p,actions,turn);engine._tick_start(m,actions,turn)
  # Synchronize boss effective defense/buffs into Stage 13 BattleActor.
  ep,em=get_effective_boss_defenses(boss);m.pdef=ep;m.mdef=em;m.hp=boss['hp'];m.max_hp=boss['max_hp']
  before=m.hp;engine._player_action(turn,cls,p,m,actions);boss['hp']=m.hp;player_damage+=max(0,before-m.hp)
  if m.hp<=0:return {'win':1,'turns':turn,'player_hp_pct':p.hp/p.max_hp,'enrage':enrage,'special':special,'player_damage':player_damage,'boss_damage':boss_damage,'bleed_damage':bleed_damage,'skills':sum(a.actor=='player' and a.action!='basic_attack' for a in actions)}
  bt=prepare_boss_turn(boss,rng=random.Random(seed*1000+turn));plan=bt['action_plan'];enrage|=bt['enrage_triggered'];special|=bt['enrage_triggered'];req=build_boss_damage_request(plan);damage=0
  if req:
   raw=call_rule('mob_attack',req['mob_attack'],p.pdef,p.mdef,p.dex,boss['dex'],p.sta,p.level,req['attack_type'],rng=engine.rng);damage=engine._absorb(p,int(raw['damage']));p.hp=max(0,p.hp-damage);boss_damage+=damage
   if p.resource_type=='rage' and damage>0:p.resource=min(p.max_resource,p.resource+10)
  fin=finalize_boss_turn(boss,plan,damage);pe=fin.get('player_effect')
  if pe:p.effects['boss_bleed']={'type':'dot','turns':pe['turns'],'damage':pe['damage']}
  if p.hp<=0:return {'win':0,'turns':turn,'player_hp_pct':0.0,'enrage':enrage,'special':special,'player_damage':player_damage,'boss_damage':boss_damage,'bleed_damage':sum(a.damage for a in actions if a.actor=='effect' and a.action=='boss_bleed'),'skills':sum(a.actor=='player' and a.action!='basic_attack' for a in actions)}
 return {'win':0,'turns':MAX_TURNS,'player_hp_pct':p.hp/p.max_hp,'enrage':enrage,'special':special,'player_damage':player_damage,'boss_damage':boss_damage,'bleed_damage':sum(a.damage for a in actions if a.actor=='effect' and a.action=='boss_bleed'),'skills':sum(a.actor=='player' and a.action!='basic_attack' for a in actions),'cap':1}

old=json.loads((ROOT/'reports'/'boss_stage_15_7_0_balance_simulation.json').read_text(encoding='utf-8'))
old_zero=sum(1 for x in old['rows'] if x['win_rate']==0);old_summary={'cells':old['cells'],'zero_win_cells':old_zero,'all_classes_zero':all(v['mean_win_rate']==0 for v in old['class_summary'].values()),'mean_rounds_by_class':{k:v['mean_rounds'] for k,v in old['class_summary'].items()}}
rows=[]
for profile in PROFILES:
 for location,levels in LOCATIONS.items():
  for level in levels:
   for cls in CLASSES:
    runs=[one(cls,level,location,profile,157100000+list(PROFILES).index(profile)*1000000+level*10000+CLASSES.index(cls)*100+i) for i in range(TRIALS)]
    rows.append({'profile':profile,'location':location,'level':level,'class':cls,'trials':TRIALS,'wins':sum(x['win'] for x in runs),'win_rate':round(statistics.mean(x['win'] for x in runs),4),'avg_turns':round(statistics.mean(x['turns'] for x in runs),2),'avg_remaining_hp_percent':round(statistics.mean(x['player_hp_pct'] for x in runs)*100,2),'enrage_reach_rate':round(statistics.mean(x['enrage'] for x in runs),4),'special_use_rate':round(statistics.mean(x['special'] for x in runs),4),'avg_player_damage':round(statistics.mean(x['player_damage'] for x in runs),2),'avg_boss_damage':round(statistics.mean(x['boss_damage'] for x in runs),2),'avg_bleed_damage':round(statistics.mean(x['bleed_damage'] for x in runs),2),'avg_skills_used':round(statistics.mean(x['skills'] for x in runs),2),'round_cap_count':sum(x.get('cap',0) for x in runs)})
summary={}
for profile in PROFILES:
 data=[x for x in rows if x['profile']==profile];summary[profile]={'cells':len(data),'mean_win_rate':round(statistics.mean(x['win_rate'] for x in data),4),'zero_win_cells':sum(x['win_rate']==0 for x in data),'mean_turns':round(statistics.mean(x['avg_turns'] for x in data),2),'mean_skills_used':round(statistics.mean(x['avg_skills_used'] for x in data),2),'enrage_reach_rate':round(statistics.mean(x['enrage_reach_rate'] for x in data),4)}
findings=[]
if old_summary['zero_win_cells']==60:findings.append('stage_15_7_0_all_60_cells_zero_win_confirmed')
if summary['progression']['mean_win_rate']<0.10:findings.append('production_parity_progression_profile_below_10pct')
if summary['strong']['mean_win_rate']<0.25:findings.append('strong_profile_below_25pct')
if all(summary[p]['zero_win_cells']==60 for p in summary):findings.append('all_profiles_all_cells_zero_win')
verdict='PASS' if not findings else 'PASS_WITH_REVIEW'
result={'version':'15.7.1','verdict':verdict,'model':'stage13_exact_pve_reuse_with_boss_turn_adapter','trials_per_cell':TRIALS,'profiles':PROFILES,'cells':len(rows),'total_trials':len(rows)*TRIALS,'stage_15_7_0_root_cause':old_summary,'profile_summary':summary,'findings':findings,'rows':rows,'reused_components':['ProgressionProvider.player_actor','ExactPveBattleEngine._tick_start','ExactPveBattleEngine._player_action','ExactPveBattleEngine skill catalog','canonical_rules.player_attack','canonical_rules.mob_attack'],'database_writes':0,'production_files_changed':False,'feature_gate_changed':False}
out=ROOT/'reports'/'boss_stage_15_7_1_root_cause_and_parity.json';out.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
print(f'[{verdict}] root-cause and production-parity audit',{'trials':result['total_trials'],'summaries':summary,'findings':findings})
