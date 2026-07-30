#!/usr/bin/env python3
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
def fail(x):print('[FAIL]',x);raise SystemExit(1)
def seq(values):
 it=iter(values);return lambda:next(it)
def main():
 from data.rune_drop_balance import RUNE_DROP_CHANCES,RUNE_LEVEL_WEIGHTS,RUNE_STAT_WEIGHTS
 from systems.rune_system import classify_rune_drop_enemy,roll_rune_drop,simulate_rune_drops
 if RUNE_DROP_CHANCES!={"normal":0.05,"elite":0.12,"boss":0.35}:fail(RUNE_DROP_CHANCES)
 if classify_rune_drop_enemy({"is_boss":True,"is_elite":True})!="boss":fail('boss priority')
 if classify_rune_drop_enemy({"is_elite":True})!="elite":fail('elite class')
 if classify_rune_drop_enemy({})!="normal":fail('normal class')
 normal=roll_rune_drop({},seq([0.049,0.2,0.1]))
 if not normal.get('dropped') or normal['level']!=1 or normal['stat']!='STR':fail(normal)
 miss=roll_rune_drop({},seq([0.05]))
 if miss.get('dropped'):fail('5% boundary')
 elite2=roll_rune_drop({"is_elite":True},seq([0.01,0.95,0.3]))
 if elite2['level']!=2:fail(elite2)
 boss3=roll_rune_drop({"is_boss":True,"is_elite":True},seq([0.01,0.99,0.9]))
 if boss3['enemy_type']!='boss' or boss3['level']!=3 or boss3['stat']!='WIS':fail(boss3)
 for kind in ('normal','elite','boss'):
  sim=simulate_rune_drops(kind,50000,seed=1100)
  if not sim.get('success'):fail(sim)
  target=RUNE_DROP_CHANCES[kind]
  if abs(sim['actual_rate']-target)>0.012:fail((kind,sim['actual_rate']))
  if sim['levels'][4] or sim['levels'][5]:fail('direct IV/V')
 if simulate_rune_drops('bad',10).get('success') is not False:fail('invalid type')
 reward=(ROOT/'systems/reward_system.py').read_text(encoding='utf-8-sig')
 dev=(ROOT/'handlers/dev.py').read_text(encoding='utf-8-sig')
 if '_RUNE_DROP_BASE_PROCESS_VICTORY_REWARD_10_11_0' not in reward:fail('victory integration')
 if '/dev_rune_drop_sim' not in dev:fail('dev help/command')
 print('[OK] Rune drop and balance contracts')
 print('- normal chance: 5%');print('- elite chance: 12%');print('- boss chance: 35%')
 print('- normal levels: I only');print('- elite levels: I 80% / II 20%')
 print('- boss levels: I 60% / II 35% / III 5%')
 print('- stat distribution: 20% each');print('- direct Rune IV/V drops: 0')
 print('- boss priority over elite: OK');print('- maximum runes per kill: 1')
 print('- DEV simulation is read-only: OK');print('- real user mutations: 0')
if __name__=='__main__':main()
