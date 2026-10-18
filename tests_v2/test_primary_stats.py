from __future__ import annotations
import unittest
from rom_v2.domain.primary_stats import AttributePointState,PrimaryStats,base_primary_value,earned_points_for_level,normalize_primary_key
class PrimaryStatsTest(unittest.TestCase):
 def test_exact_v1_constants(self):self.assertEqual(base_primary_value(1),10);self.assertEqual(base_primary_value(5),14);self.assertEqual(earned_points_for_level(3),10);self.assertEqual(normalize_primary_key("strength"),"str")
 def test_invariant_allocation_stale_and_respec(self):
  state=AttributePointState(PrimaryStats(),10,10);updated=state.allocate({"str":2,"dexterity":1,"wis":2},10);self.assertEqual((updated.free_points,updated.allocated.str,updated.allocated.dex,updated.allocated.wis,updated.total_earned),(5,2,1,2,10));self.assertEqual(updated.respec(),AttributePointState(PrimaryStats(),10,10))
  with self.assertRaisesRegex(ValueError,"attribute_state_stale"):state.allocate({"sta":1},9)
 def test_invalid_allocations(self):
  state=AttributePointState(PrimaryStats(),5,5)
  for value in ({},{"luck":1},{"str":-1},{"str":6},{"str":True}):
   with self.assertRaises(ValueError):state.allocate(value)
if __name__=="__main__":unittest.main()
