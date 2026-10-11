#!/usr/bin/env python3
from __future__ import annotations
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from systems.level_up_reward_system import build_level_up_reward_message,calculate_level_rewards

def message(old,new):
 result=calculate_level_rewards(old,new);result['new_ledger_levels']=result['reached_levels'];result['gold_awarded_now']=result['gold'];result['item_result']={};return build_level_up_reward_message(result)
def main():
 cases={(1,2):'• Золото: 0.45',(2,3):'• Золото: 1.43',(4,5):'• Золото: 11.98',(9,10):'• Золото: 479.19',(10,11):'• Золото: 881.25'}
 for levels,expected in cases.items():
  text=message(*levels);assert expected in text,(levels,text);assert '• Золото: 0\n' not in text
 multi=message(1,3);assert '• Золото: 1.88' in multi,multi
 assert build_level_up_reward_message({'new_ledger_levels':[]})==''
 print('[OK] Level-up gold presentation - exactly two decimals for single and multi-level rewards')
 return 0
if __name__=='__main__':raise SystemExit(main())
