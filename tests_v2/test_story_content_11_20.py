import unittest
from rom_v2.content.story_start_path_11_20 import STORY_START_PATH_11_20,validate_story_start_path_11_20
class TestStory1120(unittest.TestCase):
 def test_manifest(self): validate_story_start_path_11_20();self.assertEqual([q.number for q in STORY_START_PATH_11_20],list(range(11,21)))
 def test_bridge_chain(self):
  self.assertEqual(STORY_START_PATH_11_20[0].previous_quest_id,"start_path_010_investigation_begins")
  for a,b in zip(STORY_START_PATH_11_20,STORY_START_PATH_11_20[1:]):self.assertEqual(b.previous_quest_id,a.quest_id)
 def test_contract(self):
  for q in STORY_START_PATH_11_20:self.assertEqual((q.unlock_level,q.location_id,q.reward_exp,q.reward_gold),(2,"start_path",36,0.43))
 def test_text(self):
  for q in STORY_START_PATH_11_20:
   t=" ".join((q.title,q.description,q.objective_text,q.acceptance_text,q.completion_text));self.assertNotIn("start_path",t);self.assertNotIn("глава",t.lower())
 def test_turn_in_14(self): self.assertEqual(STORY_START_PATH_11_20[3].quest_type,"TURN_IN")
if __name__=="__main__":unittest.main()
