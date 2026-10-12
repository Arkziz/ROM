#!/usr/bin/env python3
from __future__ import annotations
import ast,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from systems.timed_exp_bonus_system import calculate_premium_combat_gold

def fn(text,name):
 tree=ast.parse(text);nodes=[n for n in tree.body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)) and n.name==name]
 assert len(nodes)==1,(name,len(nodes));return ast.get_source_segment(text,nodes[0]) or ''
def main():
 inactive=calculate_premium_combat_gold(1.01,False);active=calculate_premium_combat_gold(1.01,True)
 assert inactive=={'active':False,'base_gold':1.01,'bonus_gold':0.0,'final_gold':1.01,'bonus_percent':0}
 assert active=={'active':True,'base_gold':1.01,'bonus_gold':0.25,'final_gold':1.26,'bonus_percent':25}
 assert calculate_premium_combat_gold(0.01,True)['final_gold']==0.01
 assert calculate_premium_combat_gold(10.0,True)['final_gold']==12.5
 reward=(ROOT/'systems/reward_system.py').read_text(encoding='utf-8-sig');body=fn(reward,'process_victory_reward')
 assert body.count('calculate_mob_kill_gold')==2
 assert body.count('calculate_gold_reward')==1
 assert body.count('add_gold(user_id, gold)')==1
 assert '"base_gold": float(gold_breakdown["base_gold"])' in body
 assert '"premium_gold_bonus": float(gold_breakdown["bonus_gold"])' in body
 assert 'process_enemy_drops(user_id, mob)' in body and 'premium_loot' not in body.lower()
 combat=(ROOT/'handlers/combat.py').read_text(encoding='utf-8-sig')
 assert 'Premium +25%: +' in combat
 assert 'premium_gold_bonus' in combat
 assert 'premium_gold_active' in combat
 assert 'base_gold' in combat
 sim=(ROOT/'systems/simulation/world_progression.py').read_text(encoding='utf-8-sig')
 assert 'premium_active: bool = False' in sim
 assert 'calculate_premium_combat_gold(base_gold, self.premium_active)' in sim
 assert '"premium_gold_bonus": premium_gold_bonus' in sim
 timed=(ROOT/'handlers/timed_exp_bonus.py').read_text(encoding='utf-8-sig')
 assert 'Додатково +25% золота за ці перемоги.' in timed
 print('[OK] Premium combat gold +25% - rounding, one reward application, UI, simulator, no loot modifier')
if __name__=='__main__':main()
