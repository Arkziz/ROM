import unittest
from rom_v2.content.story_dark_forest_51_60 import STORY_DARK_FOREST_51_60,validate_story_dark_forest_51_60
class TestStory5160(unittest.TestCase):
 def test_manifest(self): validate_story_dark_forest_51_60();self.assertEqual([q.number for q in STORY_DARK_FOREST_51_60],list(range(51,61)))
 def test_bridge_chain(self):
  self.assertEqual(STORY_DARK_FOREST_51_60[0].previous_quest_id,"start_path_050_road_ahead")
  for a,b in zip(STORY_DARK_FOREST_51_60,STORY_DARK_FOREST_51_60[1:]):self.assertEqual(b.previous_quest_id,a.quest_id)
 def test_contract(self):
  for q in STORY_DARK_FOREST_51_60:self.assertEqual((q.unlock_level,q.location_id,q.reward_exp,q.reward_gold),(6,"dark_forest",66,1.84))
 def test_text(self):
  for q in STORY_DARK_FOREST_51_60:
   t=" ".join((q.title,q.description,q.objective_text,q.acceptance_text,q.completion_text));self.assertNotIn("dark_forest",t);self.assertNotIn("глава",t.lower())
if __name__=="__main__":unittest.main()
