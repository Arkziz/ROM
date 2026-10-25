import unittest
from types import SimpleNamespace
from rom_v2.application.story_navigation_service import StoryNavigationService
from rom_v2.domain.story_navigation import StoryQuestState,StoryQuestStatus,ensure_safe_ui_text
from rom_v2.presentation.story_navigation import *
def quests():
 return [SimpleNamespace(number=n,quest_id=f"q{n}",title=f"Квест {n}",quest_type="KILL",target_quantity=1,objective_text=f"Ціль {n}") for n in range(1,101)]
class TestStoryNavigation(unittest.TestCase):
 def setUp(self):self.s=StoryNavigationService(quests())
 def test_hierarchy(self):
  tree=self.s.build({},10);self.assertEqual([x.display_name for x in tree],["Початок Шляху","Темний Бір"]);self.assertEqual([len(x.sections) for x in tree],[5,5]);self.assertEqual(sum(len(s.quests) for x in tree for s in x.sections),100)
 def test_status_derivation(self):
  states={1:StoryQuestState(1,StoryQuestStatus.COMPLETED),2:StoryQuestState(2,StoryQuestStatus.ACTIVE,0,2)};tree=self.s.build(states,1);q=[q for x in tree for s in x.sections for q in s.quests];self.assertEqual(q[0].status,StoryQuestStatus.COMPLETED);self.assertEqual(q[1].status,StoryQuestStatus.ACTIVE);self.assertEqual(q[2].status,StoryQuestStatus.LOCKED)
 def test_skipped_opens_chain(self):self.assertEqual(self.s.derive_status(2,{1:StoryQuestState(1,StoryQuestStatus.SKIPPED)},1),StoryQuestStatus.AVAILABLE)
 def test_active_target(self):self.assertEqual(self.s.active_target({1:StoryQuestState(1,StoryQuestStatus.ACTIVE,1,2)})["progress"],1)
 def test_routes(self):
  for route in (StoryRoute("index"),StoryRoute("loc","start_path"),StoryRoute("sec","start_path_01"),StoryRoute("q",1),StoryRoute("profile")):self.assertEqual(decode_route(encode_route(route)),route)
  self.assertEqual(parent_route(StoryRoute("q",1),{1:"start_path_01"},{}),StoryRoute("sec","start_path_01"));self.assertEqual(parent_route(StoryRoute("index")),StoryRoute("profile"))
 def test_forbidden_ui(self):
  for text in ("глава 1","start_path","dark_forest"):
   with self.assertRaises(ValueError):ensure_safe_ui_text(text)
if __name__=="__main__":unittest.main()
