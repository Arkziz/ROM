import unittest
from rom_v2.domain.quest_item_store import *
from rom_v2.application.quest_item_store_service import *
class QuestItemStoreTest(unittest.TestCase):
 def setUp(self):self.u=InMemoryV2QuestItemStoreUow();self.s=V2QuestItemStoreService(self.u);self.k=V2QuestItemBalanceKey(1,10,"fang")
 def test_isolated_scope_and_total(self):
  self.s.collect(V2QuestItemCollection(self.k,"e1",2));other=V2QuestItemBalanceKey(1,11,"fang");self.s.collect(V2QuestItemCollection(other,"e2",3));self.assertEqual(self.s.quantity(self.k),2);self.assertEqual(self.s.total_quantity(1,"fang"),5)
 def test_duplicate_collection(self):
  c=V2QuestItemCollection(self.k,"event",1);self.assertTrue(self.s.collect(c).ok);self.assertEqual(self.s.collect(c).reason,"already_collected");self.assertEqual(self.s.quantity(self.k),1)
 def test_non_negative_and_revision(self):
  b=self.s.collect(V2QuestItemCollection(self.k,"e",2)).balance;self.assertEqual(self.s.consume(self.k,3,b.revision).reason,"insufficient_quantity");self.assertEqual(self.s.consume(self.k,1,0).reason,"stale_revision")
 def test_exact_consume_and_zero_row(self):
  b=self.s.collect(V2QuestItemCollection(self.k,"e",2)).balance;r=self.s.consume(self.k,2,b.revision);self.assertTrue(r.ok);self.assertEqual(self.s.quantity(self.k),0);self.assertNotIn(self.k,self.u.balances)
 def test_turn_in_replay_and_skip_preserves(self):
  b=self.s.collect(V2QuestItemCollection(self.k,"e",2)).balance;p=V2QuestItemTurnInPlan(self.k,2,b.revision,"1:10:1");r=self.s.plan_turn_in(p);self.assertTrue(r.ok);self.s.commit_turn_in(p);self.assertEqual(self.s.plan_turn_in(p).reason,"already_completed");self.assertEqual(self.s.skip(self.k).reason,"preserved_on_skip")
if __name__=="__main__":unittest.main()
