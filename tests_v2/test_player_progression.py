import unittest
from rom_v2.domain.player_progression import *

class PlayerProgressionTests(unittest.TestCase):
 def test_tables_cover_1_to_50(self):
  self.assertEqual((min(BASE_EXP_BY_LEVEL),max(BASE_EXP_BY_LEVEL),len(BASE_EXP_BY_LEVEL)),(1,50,50))
  self.assertEqual(len(CONDITIONAL_MOBS_TO_NEXT_BY_LEVEL),50)
 def test_known_thresholds(self):
  self.assertEqual(get_player_exp_to_next_level(1),500)
  self.assertEqual(get_player_base_exp_for_level(15),120)
  self.assertEqual(get_player_base_exp_for_level(30),600)
 def test_below_threshold(self):
  result=apply_player_exp_award(1,0,499,30);self.assertEqual((result.level,result.exp,result.level_ups,result.unapplied_exp),(1,499,0,0))
 def test_exact_threshold_and_residual(self):
  result=apply_player_exp_award(1,0,505,30);self.assertEqual((result.level,result.exp,result.level_ups),(2,5,1))
 def test_multi_level(self):
  amount=get_player_exp_to_next_level(1)+get_player_exp_to_next_level(2)+7
  result=apply_player_exp_award(1,0,amount,30);self.assertEqual((result.level,result.exp,result.level_ups,result.reached_levels),(3,7,2,(2,3)))
  self.assertEqual(result.attribute_points_awarded,10)
 def test_cap_returns_unapplied(self):
  result=apply_player_exp_award(30,4,500,30);self.assertEqual((result.level,result.exp,result.unapplied_exp),(30,4,500))
 def test_zero_and_negative_match_v1(self):
  for amount in (0,-5):
   result=apply_player_exp_award(2,9,amount,30);self.assertEqual((result.level,result.exp,result.level_ups,result.unapplied_exp),(2,9,0,amount))
 def test_configuration_is_immutable(self):
  with self.assertRaises(TypeError):BASE_EXP_BY_LEVEL[1]=999

if __name__=="__main__":unittest.main()
