import unittest
from rom_v2.content.story_start_path_1_10 import STORY_START_PATH_1_10,validate_story_start_path_1_10
class StoryContentOneToTenTest(unittest.TestCase):
 def test_manifest(self):
  validate_story_start_path_1_10();self.assertEqual([q.number for q in STORY_START_PATH_1_10],list(range(1,11)))
 def test_level_and_chain(self):
  self.assertTrue(all(q.unlock_level==1 for q in STORY_START_PATH_1_10));self.assertIsNone(STORY_START_PATH_1_10[0].previous_quest_id)
  for previous,current in zip(STORY_START_PATH_1_10,STORY_START_PATH_1_10[1:]):self.assertEqual(current.previous_quest_id,previous.quest_id)
 def test_location_and_rewards(self):
  for q in STORY_START_PATH_1_10:
   self.assertEqual(q.location_id,"start_path");self.assertEqual(q.reward_exp,30);self.assertAlmostEqual(q.reward_gold,0.27)
 def test_localized_text(self):
  for q in STORY_START_PATH_1_10:
   visible=" ".join((q.title,q.description,q.objective_text,q.acceptance_text,q.completion_text));self.assertNotIn("start_path",visible);self.assertNotIn("глава",visible.lower())
 def test_types(self):self.assertEqual(STORY_START_PATH_1_10[7].quest_type,"TURN_IN")
if __name__=="__main__":unittest.main()
