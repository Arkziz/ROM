import unittest
from rom_v2.domain.npc_dialogue_model import *
from rom_v2.application.npc_dialogue_service import *
class NpcDialogueModelTest(unittest.TestCase):
 def service(self):
  npc=V2NpcDefinition("npc_a","Локалізоване ім'я","loc_a",(10,));port=InMemoryV2QuestNpcPort({10:(True,2,"Прийняти квест")});return V2NpcDialogueService(InMemoryV2NpcRegistry((npc,)),port),port
 def test_unknown_and_wrong_location(self):
  s,_=self.service();self.assertEqual(s.view("missing","loc_a").reason,"unknown_npc");self.assertEqual(s.view("npc_a","loc_b").reason,"wrong_location")
 def test_localized_view_and_action(self):
  s,_=self.service();v=s.view("npc_a","loc_a").view;self.assertEqual(v.display_name,"Локалізоване ім'я");self.assertEqual(v.actions[0].action_key,"story_quest:10")
 def test_accept_delegates(self):
  s,p=self.service();self.assertTrue(s.accept(V2NpcAcceptCommand(1,"npc_a",10,2),"loc_a").ok);self.assertEqual(p.accepted,[(1,10,2)])
 def test_unlinked_and_stale(self):
  s,_=self.service();self.assertEqual(s.accept(V2NpcAcceptCommand(1,"npc_a",11,2),"loc_a").reason,"quest_not_linked");self.assertEqual(s.accept(V2NpcAcceptCommand(1,"npc_a",10,1),"loc_a").reason,"stale_revision")
 def test_duplicate_registry(self):
  n=V2NpcDefinition("x","X","l");self.assertRaises(ValueError,InMemoryV2NpcRegistry,(n,n))
if __name__=="__main__":unittest.main()
