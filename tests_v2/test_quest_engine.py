import unittest
from rom_v2.application.quest_engine_service import *
class Strategy:
 def progress_delta(self,d,event,u):return 1 if event=="match" else 0
def definition(kind=V2QuestObjectiveType.TALK):return V2QuestDefinition(1,"loc",1,kind,target=1,reward=V2QuestReward(3,4))
class QuestEngineTest(unittest.TestCase):
 def service(self):
  u=InMemoryV2QuestEngineUow();return u,V2QuestEngineService(u,{x:Strategy() for x in V2QuestObjectiveType})
 def test_availability_accept(self):
  u,s=self.service();r=s.accept(10,definition(),1,"loc");self.assertTrue(r.changed);self.assertEqual(r.progress.state,V2QuestState.ACTIVE)
 def test_duplicate_event_and_revision(self):
  u,s=self.service();r=s.accept(10,definition(),1,"loc");a=s.apply_event(10,definition(),"match","evt",r.progress.revision);self.assertEqual(a.progress.state,V2QuestState.READY_TO_TURN_IN);self.assertEqual(s.apply_event(10,definition(),"match","evt",a.progress.revision).reason,"duplicate_event")
 def test_exact_once_turn_in(self):
  u,s=self.service();r=s.accept(10,definition(),1,"loc");r=s.apply_event(10,definition(),"match","evt",r.progress.revision);done=s.turn_in(10,definition(),r.progress.revision);self.assertTrue(done.reward_planned);self.assertEqual(s.turn_in(10,definition(),r.progress.revision).reason,"already_completed");self.assertEqual(len(u.reward_plans),1)
 def test_skip_no_reward(self):
  u,s=self.service();r=s.accept(10,definition(),1,"loc");out=s.skip(10,definition(),r.progress.revision);self.assertEqual(out.progress.state,V2QuestState.SKIPPED);self.assertFalse(u.reward_plans)
 def test_wrong_location(self):
  u,s=self.service();self.assertEqual(s.availability(10,definition(),1,"other").reason,"wrong_location")
if __name__=="__main__":unittest.main()
