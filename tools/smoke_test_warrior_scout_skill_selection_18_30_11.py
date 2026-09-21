from __future__ import annotations
import sys
from collections import Counter
from pathlib import Path
R=Path(__file__).resolve().parents[1]
if str(R) not in sys.path:sys.path.insert(0,str(R))
from systems.simulation.battle_models import BattleActor
from systems.simulation.pve_battle import ExactPveBattleEngine
def actor(resource_type,resource):return BattleActor('player',5,100000,100000,45,45,20,20,20,20,20,'physical',5,9,resource_type,resource,100)
def mob(hp=100000):return BattleActor('mob',5,hp,hp,1,1,20,20,1,1,1,'physical')
def dynamic(cls,turns=30):
 e=ExactPveBattleEngine(R,3);p=actor('rage' if cls=='warrior' else 'combat_energy',0 if cls=='warrior' else 100);m=mob();actions=[]
 for turn in range(1,turns+1):
  e._tick_start(p,actions,turn);e._tick_start(m,actions,turn);e._player_action(turn,cls,p,m,actions)
  if m.alive:e._mob_action(turn,p,m,actions)
 return p,m,[a for a in actions if a.actor=='player']
e=ExactPveBattleEngine(R,3)
# Warrior: suppression remains an opener at 20 rage, but the finisher wins whenever 30+ rage is available.
p=actor('rage',20);assert e._choose('warrior',p,mob())['key']=='warrior_suppression'
p=actor('rage',30);assert e._choose('warrior',p,mob())['key']=='warrior_subjugation_strike'
p=actor('rage',100);assert e._choose('warrior',p,mob())['key']=='warrior_subjugation_strike'
wp,wm,wa=dynamic('warrior');wc=Counter(a.action for a in wa);assert wc['warrior_cleave']>0 and wc['warrior_suppression']>0 and wc['warrior_subjugation_strike']>0;assert wp.resource<100
# Scout: trap opens, poison follows while the target has enough HP, then aimed shot fills the direct-damage turns.
p=actor('combat_energy',100);m=mob();assert e._choose('scout',p,m)['key']=='scout_trap';m.effects['scout_pdef']={'turns':2,'pdef_percent':-50};assert e._choose('scout',p,m)['key']=='scout_sting_arrow';m.effects['enemy_poison']={'type':'dot','turns':3,'damage':5};assert e._choose('scout',p,m)['key']=='scout_aimed_shot'
sp,sm,sa=dynamic('scout');sc=Counter(a.action for a in sa);assert sc['scout_trap']>0 and sc['scout_sting_arrow']>0 and sc['scout_aimed_shot']>0
# Do not spend 35 energy on poison when a target is already near death.
p=actor('combat_energy',100);m=mob(100);m.hp=30;m.effects['scout_pdef']={'turns':2,'pdef_percent':-50};assert e._choose('scout',p,m)['key']=='scout_aimed_shot'
print('[PASS] warrior finisher, scout poison, debuff, and near-death selection regression')
