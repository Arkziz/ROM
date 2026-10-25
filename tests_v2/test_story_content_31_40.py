import unittest
from rom_v2.content.story_start_path_21_30 import STORY_START_PATH_21_30
from rom_v2.content.story_start_path_31_40 import STORY_START_PATH_31_40,validate_story_start_path_31_40
class TestStory3140(unittest.TestCase):
 def test_manifest(self): validate_story_start_path_31_40();self.assertEqual([q.number for q in STORY_START_PATH_31_40],list(range(31,41)))
 def test_bridge_chain(self):
  self.assertEqual(STORY_START_PATH_31_40[0].previous_quest_id,STORY_START_PATH_21_30[-1].quest_id)
  for a,b in zip(STORY_START_PATH_31_40,STORY_START_PATH_31_40[1:]):self.assertEqual(b.previous_quest_id,a.quest_id)
 def test_contract(self):
  rewards={(q.reward_exp,q.reward_gold) for q in STORY_START_PATH_31_40}
  self.assertEqual(len(rewards),1)
  for q in STORY_START_PATH_31_40:self.assertEqual((q.unlock_level,q.location_id),(4,"start_path"))
 def test_text(self):
  for q in STORY_START_PATH_31_40:
   t=" ".join((q.title,q.description,q.objective_text,q.acceptance_text,q.completion_text));self.assertNotIn("start_path",t);self.assertNotIn("глава",t.lower())
if __name__=="__main__":unittest.main()
