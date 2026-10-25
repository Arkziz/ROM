import unittest
from rom_v2.content.story_dark_forest_81_90 import STORY_DARK_FOREST_81_90
from rom_v2.content.story_dark_forest_91_100 import STORY_DARK_FOREST_91_100,validate_story_dark_forest_91_100
class TestStory91100(unittest.TestCase):
 def test_manifest(self): validate_story_dark_forest_91_100();self.assertEqual([q.number for q in STORY_DARK_FOREST_91_100],list(range(91,101)))
 def test_bridge_chain(self):
  self.assertEqual(STORY_DARK_FOREST_91_100[0].previous_quest_id,STORY_DARK_FOREST_81_90[-1].quest_id)
  for a,b in zip(STORY_DARK_FOREST_91_100,STORY_DARK_FOREST_91_100[1:]):self.assertEqual(b.previous_quest_id,a.quest_id)
 def test_contract(self):
  for q in STORY_DARK_FOREST_91_100:self.assertEqual((q.unlock_level,q.location_id),(10,"dark_forest"))
 def test_rewards_are_canonical_non_negative(self):
  for q in STORY_DARK_FOREST_91_100:self.assertGreaterEqual(q.reward_exp,0);self.assertGreaterEqual(q.reward_gold,0)
 def test_text(self):
  for q in STORY_DARK_FOREST_91_100:
   t=" ".join((q.title,q.description,q.objective_text,q.acceptance_text,q.completion_text));self.assertNotIn("dark_forest",t);self.assertNotIn("глава",t.lower())
 def test_story_terminal(self): self.assertEqual(STORY_DARK_FOREST_91_100[-1].number,100)
if __name__=="__main__":unittest.main()
