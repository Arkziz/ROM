import unittest
from rom_v2.content.story_dark_forest_61_70 import STORY_DARK_FOREST_61_70
from rom_v2.content.story_dark_forest_71_80 import STORY_DARK_FOREST_71_80,validate_story_dark_forest_71_80
class TestStory7180(unittest.TestCase):
 def test_manifest(self): validate_story_dark_forest_71_80();self.assertEqual([q.number for q in STORY_DARK_FOREST_71_80],list(range(71,81)))
 def test_bridge_chain(self):
  self.assertEqual(STORY_DARK_FOREST_71_80[0].previous_quest_id,STORY_DARK_FOREST_61_70[-1].quest_id)
  for a,b in zip(STORY_DARK_FOREST_71_80,STORY_DARK_FOREST_71_80[1:]):self.assertEqual(b.previous_quest_id,a.quest_id)
 def test_contract(self):
  for q in STORY_DARK_FOREST_71_80:self.assertEqual((q.unlock_level,q.location_id),(8,"dark_forest"))
 def test_rewards_are_canonical_non_negative(self):
  for q in STORY_DARK_FOREST_71_80:self.assertGreaterEqual(q.reward_exp,0);self.assertGreaterEqual(q.reward_gold,0)
 def test_text(self):
  for q in STORY_DARK_FOREST_71_80:
   t=" ".join((q.title,q.description,q.objective_text,q.acceptance_text,q.completion_text));self.assertNotIn("dark_forest",t);self.assertNotIn("глава",t.lower())
if __name__=="__main__":unittest.main()
