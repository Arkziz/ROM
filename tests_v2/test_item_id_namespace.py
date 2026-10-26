import unittest
from rom_v2.application.item_id_namespace_service import V2ItemIdNamespaceService
from rom_v2.domain.item_id_namespace import *
class TestItemIdNamespace(unittest.TestCase):
 def test_event_partition(self):
  blocks=[event_block(i,"e") for i in range(240)];self.assertEqual((blocks[0].start_id,blocks[-1].end_id),(4000,9999));self.assertTrue(all(x.end_id-x.start_id+1==25 for x in blocks))
 def test_event_retired_never_reused(self):
  s=V2ItemIdNamespaceService();a=s.allocate_event_block("a");self.assertEqual(a,s.allocate_event_block("a"));s.retire_event("a");b=s.allocate_event_block("b");self.assertNotEqual(a.ordinal,b.ordinal);c=s.allocate_event_block("a",additional=True);self.assertNotIn(c.ordinal,{a.ordinal,b.ordinal})
 def test_generated_never_reuse(self):
  s=V2ItemIdNamespaceService();a=s.allocate_generated_id();s.retire_generated_id(a);self.assertEqual(s.allocate_generated_id(),a+1)
 def test_preview_promotion_exact_once(self):
  s=V2ItemIdNamespaceService();p=s.allocate_preview_id();a=s.plan_preview_promotion(p);b=s.plan_preview_promotion(p);self.assertEqual((p,a.permanent_id),(10010000,10000));self.assertEqual(a,b);self.assertNotIn(p,s.state.allocated_preview_ids);self.assertEqual(len(s.state.allocated_generated_ids),1)
 def test_ranges_do_not_overlap(self):
  self.assertLess(EVENT_RANGE.end,GENERATED_RANGE.start);self.assertLess(GENERATED_RANGE.end,PREVIEW_RANGE.start)
 def test_static_gaps_reserved(self):
  s=V2ItemIdNamespaceService();self.assertTrue(s.static_id_is_assigned(201));self.assertFalse(s.static_id_is_assigned(205));
  with self.assertRaises(ValueError):classify_numeric_item_id(205)
 def test_story_key_has_no_numeric_identity(self):
  k=V2StoryQuestItemKey(1,"q","item");self.assertFalse(hasattr(k,"item_id"));self.assertFalse(hasattr(k,"inventory_id"))
if __name__=="__main__":unittest.main()
