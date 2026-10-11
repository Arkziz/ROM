#!/usr/bin/env python3
"""Acceptance checks for Stage 20.4.2b combat-income level-up gold."""
from __future__ import annotations
import sys
from decimal import Decimal
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from systems.level_up_reward_system import LEVEL_UP_GOLD_BY_REACHED_LEVEL,calculate_level_reward,calculate_level_rewards
EXPECTED={2:Decimal('0.45'),3:Decimal('1.43'),4:Decimal('4.30'),5:Decimal('11.98'),6:Decimal('34.40'),7:Decimal('69.58'),8:Decimal('130.73'),9:Decimal('255.74'),10:Decimal('479.19'),11:Decimal('881.25')}
def main():
 assert set(LEVEL_UP_GOLD_BY_REACHED_LEVEL)==set(EXPECTED)
 for level,expected in EXPECTED.items():
  row=calculate_level_reward(level)
  assert Decimal(str(row['gold'])).quantize(Decimal('0.01'))==expected,(level,row)
  milestone=(level%5==0)
  assert row['milestone'] is milestone
  assert row['small_health_potions']==3 and row['small_mana_potions']==1
  assert row['refine_stones']==(4 if milestone else 2)
  assert row['medium_health_potions']==(2 if milestone else 0)
  assert row['medium_mana_potions']==(1 if milestone else 0)
  assert row['crystals']==0
 plan=calculate_level_rewards(1,11)
 assert plan['reached_levels']==list(range(2,12))
 assert Decimal(str(plan['gold'])).quantize(Decimal('0.01'))==Decimal('1869.05')
 assert plan['milestone_levels']==[5,10]
 single=calculate_level_rewards(9,10)
 assert Decimal(str(single['gold'])).quantize(Decimal('0.01'))==Decimal('479.19')
 for invalid in (1,12,30):
  try:calculate_level_reward(invalid)
  except ValueError as exc:assert 'not configured' in str(exc)
  else:raise AssertionError(f'level {invalid} did not fail closed')
 print('[OK] Level-up gold - approved reached levels 2-11, total 1869.05, no milestone gold multiplier, future levels fail closed')
 return 0
if __name__=='__main__':raise SystemExit(main())
