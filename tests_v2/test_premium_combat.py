import unittest
from decimal import Decimal
from rom_v2.domain.premium_combat import *

class PremiumCombatModifierTests(unittest.TestCase):
 def test_active_exact_25_percent(self):
  out=PremiumCombatModifier().apply(base_combat_exp=101,base_combat_gold=Decimal("10.01"),premium_active_snapshot=PremiumCombatSnapshot(True))
  self.assertEqual((out.exp_base,out.exp_bonus,out.exp_final),(101,25,126))
  self.assertEqual((out.gold_base,out.gold_bonus,out.gold_final),(Decimal("10.01"),Decimal("2.50"),Decimal("12.51")))
  self.assertEqual(out.multiplier,Decimal("1.25"))
 def test_inactive_is_identity(self):
  out=PremiumCombatModifier().apply(base_combat_exp=101,base_combat_gold=Decimal("10.01"),premium_active_snapshot=PremiumCombatSnapshot(False))
  self.assertEqual((out.exp_bonus,out.exp_final),(0,101));self.assertEqual((out.gold_bonus,out.gold_final),(Decimal("0.00"),Decimal("10.01")))
 def test_exp_rounds_down(self):
  out=PremiumCombatModifier().apply(base_combat_exp=3,base_combat_gold=Decimal("0"),premium_active_snapshot=PremiumCombatSnapshot(True))
  self.assertEqual((out.exp_bonus,out.exp_final),(0,3))
 def test_gold_rounding_boundary(self):
  out=PremiumCombatModifier().apply(base_combat_exp=0,base_combat_gold=Decimal("0.02"),premium_active_snapshot=PremiumCombatSnapshot(True))
  self.assertEqual(out.gold_final,Decimal("0.02"));self.assertEqual(out.gold_bonus,Decimal("0.00"))
 def test_negative_inputs_clamp_to_zero(self):
  out=PremiumCombatModifier().apply(base_combat_exp=-9,base_combat_gold=Decimal("-2"),premium_active_snapshot=PremiumCombatSnapshot(True))
  self.assertEqual(out.exp_final,0);self.assertEqual(out.gold_final,Decimal("0.00"))
 def test_api_has_no_clock_loot_or_non_combat_inputs(self):
  names=PremiumCombatModifier.apply.__annotations__
  for forbidden in ("now","expires_at","loot","quest","level_up_gold"):self.assertNotIn(forbidden,names)
 def test_snapshot_is_explicit(self):
  with self.assertRaises(TypeError):PremiumCombatModifier().apply(base_combat_exp=1,base_combat_gold=Decimal("1"))

if __name__=="__main__":unittest.main()
