import unittest
from rom_v2.application.overlevel_policy_service import *
from rom_v2.presentation.overlevel_policy import build_overlevel_message
def defs():return [OverlevelQuestDefinition(f"q{n}",n,"start_path" if n<=50 else "dark_forest") for n in range(1,101)]
class OverlevelPolicyTest(unittest.TestCase):
 def service(self):u=InMemoryOverlevelUnitOfWork();return u,OverlevelPolicyService(u,defs())
 def test_exact_max_is_noop(self):
  u,s=self.service();r=s.reconcile(1,5);self.assertEqual(r.changed,0);self.assertEqual(r.locations,());self.assertEqual(u.rows.get(1,{}),{})
 def test_start_path_location_wide(self):
  u,s=self.service();u.rows[1]={"q1":OverlevelQuestRow("q1",1,"start_path",OverlevelQuestStatus.COMPLETED,1,1,True),"q4":OverlevelQuestRow("q4",4,"start_path",OverlevelQuestStatus.ACTIVE,0,1,False)};u.quest_items[1]={("q4","item"):2}
  r=s.reconcile(1,6);self.assertEqual(r.changed,49);self.assertEqual(len(u.rows[1]),50);self.assertEqual(u.rows[1]["q1"].status,OverlevelQuestStatus.COMPLETED);self.assertTrue(u.rows[1]["q1"].reward_claimed);self.assertTrue(all(x.status==OverlevelQuestStatus.SKIPPED and not x.reward_claimed for k,x in u.rows[1].items() if k!="q1"));self.assertEqual(u.quest_items[1],{});self.assertIn("Початок Шляху",build_overlevel_message(r))
 def test_idempotent(self):
  u,s=self.service();self.assertEqual(s.reconcile(1,6).changed,50);self.assertEqual(s.reconcile(1,6).changed,0)
 def test_level_11_reconciles_both(self):
  u,s=self.service();r=s.reconcile(1,11);self.assertEqual(r.changed,100);self.assertEqual(len(r.locations),2);self.assertEqual(len(u.rows[1]),100)
 def test_atomic_rollback(self):
  class Broken(dict):
   def __setitem__(self,k,v):
    if k=="q2":raise RuntimeError("fixture")
    super().__setitem__(k,v)
  u,s=self.service();u.rows[1]=Broken()
  with self.assertRaises(RuntimeError):s.reconcile(1,6)
  self.assertEqual(dict(u.rows[1]),{})
 def test_skipped_reward_guard(self):
  with self.assertRaises(ValueError):OverlevelQuestRow("q1",1,"start_path",OverlevelQuestStatus.SKIPPED,0,1,True)
if __name__=="__main__":unittest.main()
