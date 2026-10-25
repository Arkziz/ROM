import unittest
from rom_v2.content.story_start_path_21_30 import STORY_START_PATH_21_30,validate_story_start_path_21_30
class TestStory2130(unittest.TestCase):
 def test_manifest(self): validate_story_start_path_21_30();self.assertEqual([q.number for q in STORY_START_PATH_21_30],list(range(21,31)))
 def test_bridge_chain(self):
  self.assertEqual(STORY_START_PATH_21_30[0].previous_quest_id,"start_path_020_patrol_knew")
  for a,b in zip(STORY_START_PATH_21_30,STORY_START_PATH_21_30[1:]):self.assertEqual(b.previous_quest_id,a.quest_id)
 def test_contract(self):
  rewards={(q.reward_exp,q.reward_gold) for q in STORY_START_PATH_21_30}
  self.assertEqual(len(rewards),1)
  for q in STORY_START_PATH_21_30:self.assertEqual((q.unlock_level,q.location_id),(3,"start_path"))
 def test_text(self):
  for q in STORY_START_PATH_21_30:
   t=" ".join((q.title,q.description,q.objective_text,q.acceptance_text,q.completion_text));self.assertNotIn("start_path",t);self.assertNotIn("глава",t.lower())
 def test_known_objective_contracts(self):
  self.assertEqual(STORY_START_PATH_21_30[3].quest_type,"TALK")
  self.assertEqual(STORY_START_PATH_21_30[-1].quest_type,"TURN_IN")
if __name__=="__main__":unittest.main()
