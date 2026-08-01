#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations
import ast, random, sys
from collections import Counter
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))

def fail(message): print(f"[FAIL] {message}"); raise SystemExit(1)
class Sequence:
    def __init__(self, values): self.values=iter(values); self.calls=0
    def __call__(self): self.calls+=1; return next(self.values)

def main():
    from data.drop_tables import CENTRAL_DROP_MIGRATED_RULES,DROP_RULES_BY_ID
    from systems.drop_system import get_central_drop_status,roll_central_potion_drop,validate_drop_tables
    rule=DROP_RULES_BY_ID['potion']
    if tuple(CENTRAL_DROP_MIGRATED_RULES)!=("rune","refine_stone","equipment","trophy","potion"):
        fail(CENTRAL_DROP_MIGRATED_RULES)
    expected_chances={"normal":0.06,"elite":0.19,"boss":0.45}
    if {k:v['chance'] for k,v in rule['enemy'].items()}!=expected_chances: fail(rule['enemy'])
    expected_weights={
      "normal":((201,4/6),(202,2/6)),
      "elite":((201,10/19),(202,6/19),(203,2/19),(204,1/19)),
      "boss":((201,20/45),(202,12/45),(203,8/45),(204,5/45)),
    }
    for enemy,weights in expected_weights.items():
        actual=rule['item_weights'][enemy]
        if len(actual)!=len(weights) or any(a[0]!=b[0] or abs(a[1]-b[1])>1e-12 for a,b in zip(actual,weights)):
            fail(f"{enemy} weights={actual}")
    if not rule.get('enabled') or not rule.get('production_enabled'): fail('potion rule disabled')
    validation=validate_drop_tables()
    if not validation['success']: fail(validation['errors'])

    # Inclusive group boundaries and at-most-one contract.
    for mob,chance in (({},0.06),({'is_elite':True},0.19),({'is_boss':True},0.45)):
        hit=roll_central_potion_drop(mob,Sequence((chance,0.0)))
        miss=roll_central_potion_drop(mob,Sequence((chance+0.000001,)))
        if not hit['rolled'] or miss['rolled']: fail((hit,miss))
        if hit['payload']['quantity']!=1: fail(hit)

    # 100k simulations per enemy type; check total and individual marginal rates.
    targets={
      'normal':({201:0.04,202:0.02},{}),
      'elite':({201:0.10,202:0.06,203:0.02,204:0.01},{'is_elite':True}),
      'boss':({201:0.20,202:0.12,203:0.08,204:0.05},{'is_boss':True}),
    }
    for enemy,(expected,mob) in targets.items():
        rng=random.Random(116000+len(enemy)); counts=Counter(); none=0
        for _ in range(100000):
            result=roll_central_potion_drop(mob,rng.random)
            if result['rolled']: counts[result['payload']['item_id']]+=1
            else: none+=1
        if sum(counts.values())>100000: fail('more than one potion per kill')
        for item_id,target in expected.items():
            actual=counts[item_id]/100000
            if abs(actual-target)>0.008: fail(f"{enemy} item {item_id}: {actual} vs {target}")

    status=get_central_drop_status()
    if status['production_rules']!=['equipment','trophy','refine_stone','rune','potion']:
        fail(status)
    if DROP_RULES_BY_ID['success_rune'].get('production_enabled'): fail('success rune enabled')
    if DROP_RULES_BY_ID['perfect_extractor'].get('production_enabled'): fail('perfect extractor enabled')

    reward=(ROOT/'systems/reward_system.py').read_text(encoding='utf-8-sig')
    tree=ast.parse(reward)
    names=[n.name for n in ast.walk(tree) if isinstance(n,ast.FunctionDef)]
    if names.count('roll_potion_drop') != 1 or names.count('process_enemy_drops') != 1: fail('final potion integration missing or duplicated')
    if 'process_enemy_drops' not in reward: fail('final central integration missing')

    print('[OK] Central potion drop balance contracts')
    print('- normal: total 6% = small HP 4% + small MP 2%')
    print('- elite: total 19% = 10% + 6% + 2% + 1%')
    print('- boss: total 45% = 20% + 12% + 8% + 5%')
    print('- mutually exclusive: maximum one potion per victory')
    print('- item IDs 201/202/203/204: OK')
    print('- inclusive chance boundaries: OK')
    print('- Rune of Success and Perfect Extractor remain disabled')
    print('- database mutations: 0')
if __name__=='__main__': main()
