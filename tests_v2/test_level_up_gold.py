import unittest
from rom_v2.domain.level_up_gold import *

class LevelUpGoldTests(unittest.TestCase):
 def test_exact_matrix(self):
  self.assertEqual(dict(LEVEL_UP_GOLD_BY_REACHED_LEVEL),{2:0.45,3:1.43,4:4.30,5:11.98,6:34.40,7:69.58,8:130.73,9:255.74,10:479.19,11:881.25})
 def test_range_contiguous(self):self.assertEqual((CONFIGURED_MIN_REACHED_LEVEL,CONFIGURED_MAX_REACHED_LEVEL,len(LEVEL_UP_GOLD_BY_REACHED_LEVEL)),(2,11,10))
 def test_single_non_milestone_shape(self):
  row=calculate_v2_level_up_reward(2);self.assertEqual(row,{"reached_level":2,"gold":0.45,"small_health_potions":3,"small_mana_potions":1,"refine_stones":2,"medium_health_potions":0,"medium_mana_potions":0,"crystals":0,"milestone":False})
 def test_single_milestone_shape(self):
  row=calculate_v2_level_up_reward(5);self.assertTrue(row["milestone"]);self.assertEqual((row["refine_stones"],row["medium_health_potions"],row["medium_mana_potions"]),(4,2,1))
 def test_unconfigured_fails_closed(self):
  for level in (1,12,50):
   with self.assertRaises(ValueError):calculate_v2_level_up_reward(level)
 def test_multi_level_ascending_and_exact_gold(self):
  result=calculate_v2_level_up_rewards(1,5);self.assertEqual(result["reached_levels"],[2,3,4,5]);self.assertEqual(result["milestone_levels"],[5]);self.assertAlmostEqual(result["gold"],18.16,places=9)
 def test_reverse_and_equal_are_empty(self):
  for old,new in ((5,5),(5,4)):
   result=calculate_v2_level_up_rewards(old,new);self.assertEqual(result["rows"],[]);self.assertEqual(result["gold"],0)
 def test_matrix_immutable(self):
  with self.assertRaises(TypeError):LEVEL_UP_GOLD_BY_REACHED_LEVEL[2]=999
if __name__=="__main__":unittest.main()
