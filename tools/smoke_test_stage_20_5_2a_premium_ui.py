#!/usr/bin/env python3
import ast
from pathlib import Path
R=Path(__file__).resolve().parents[1]
def main():
 shop=(R/'handlers/crystal_shop.py').read_text(encoding='utf-8-sig');premium=(R/'handlers/timed_exp_bonus.py').read_text(encoding='utf-8-sig');city=(R/'handlers/city.py').read_text(encoding='utf-8-sig');combat=(R/'handlers/combat.py').read_text(encoding='utf-8-sig')
 for n,t in [('shop',shop),('premium',premium),('city',city),('combat',combat)]:ast.parse(t,filename=n)
 assert shop.count('💎 Premium: +25% досвіду та золота')==1
 assert premium.count("BUTTON='💎 Premium: +25% досвіду та золота'")==1
 assert premium.count('💎 Premium-бонус')==3
 for token in ('• +25% досвіду;','• +25% золота.','Premium не збільшує нагороди за квести'):assert token in premium
 assert 'Бонус досвіду +25%' not in shop+premium
 assert city.count('💎 Premium: +25% досвіду та золота за перемогу над мобами')==2
 assert 'Бонус за вбивство мобів: +25% EXP' not in city
 assert combat.count('Premium +25% досвіду:')==1
 assert combat.count('Premium +25%: +')==1
 assert 'Premium +25%: +{premium_gold:.2f}' in combat
 print('[OK] Premium UI unified: досвід and gold together; gold breakdown preserved')
if __name__=='__main__':main()
