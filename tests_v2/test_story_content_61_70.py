import unittest
from rom_v2.content.story_dark_forest_51_60 import STORY_DARK_FOREST_51_60
from rom_v2.content.story_dark_forest_61_70 import STORY_DARK_FOREST_61_70,validate_story_dark_forest_61_70
class TestStory6170(unittest.TestCase):
 def test_manifest(self): validate_story_dark_forest_61_70();self.assertEqual([q.number for q in STORY_DARK_FOREST_61_70],list(range(61,71)))
 def test_bridge_chain(self):
  self.assertEqual(STORY_DARK_FOREST_61_70[0].previous_quest_id,STORY_DARK_FOREST_51_60[-1].quest_id)
  for a,b in zip(STORY_DARK_FOREST_61_70,STORY_DARK_FOREST_61_70[1:]):self.assertEqual(b.previous_quest_id,a.quest_id)
 def test_contract(self):
  for q in STORY_DARK_FOREST_61_70:self.assertEqual((q.unlock_level,q.location_id),(7,"dark_forest"))
 def test_rewards_are_canonical_non_negative(self):
  for q in STORY_DARK_FOREST_61_70:self.assertGreaterEqual(q.reward_exp,0);self.assertGreaterEqual(q.reward_gold,0)
 def test_text(self):
  for q in STORY_DARK_FOREST_61_70:
   t=" ".join((q.title,q.description,q.objective_text,q.acceptance_text,q.completion_text));self.assertNotIn("dark_forest",t);self.assertNotIn("глава",t.lower())
if __name__=="__main__":unittest.main()
