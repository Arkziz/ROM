import unittest
from rom_v2.content.story_start_path_31_40 import STORY_START_PATH_31_40
from rom_v2.content.story_start_path_41_50 import STORY_START_PATH_41_50,validate_story_start_path_41_50
class TestStory4150(unittest.TestCase):
 def test_manifest(self): validate_story_start_path_41_50();self.assertEqual([q.number for q in STORY_START_PATH_41_50],list(range(41,51)))
 def test_bridge_chain(self):
  self.assertEqual(STORY_START_PATH_41_50[0].previous_quest_id,STORY_START_PATH_31_40[-1].quest_id)
  for a,b in zip(STORY_START_PATH_41_50,STORY_START_PATH_41_50[1:]):self.assertEqual(b.previous_quest_id,a.quest_id)
 def test_contract(self):
  rewards={(q.reward_exp,q.reward_gold) for q in STORY_START_PATH_41_50}
  self.assertGreaterEqual(len(rewards),1)
  for q in STORY_START_PATH_41_50:self.assertEqual((q.unlock_level,q.location_id),(5,"start_path"))
 def test_text(self):
  for q in STORY_START_PATH_41_50:
   t=" ".join((q.title,q.description,q.objective_text,q.acceptance_text,q.completion_text));self.assertNotIn("start_path",t);self.assertNotIn("глава",t.lower())
 def test_terminal_contracts(self):
  boss=STORY_START_PATH_41_50[8];terminal=STORY_START_PATH_41_50[9]
  self.assertEqual(boss.quest_type,"BOSS");self.assertEqual(boss.giver_npc_id,"mercenary_head");self.assertIsNone(boss.turn_in_npc_id)
  self.assertEqual(terminal.quest_type,"TURN_IN")
if __name__=="__main__":unittest.main()
