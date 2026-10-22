import unittest
from rom_v2.application.post_combat_hooks import *

class Consumer:
 def __init__(self,key,log,fail=False):self.consumer_key=key;self.log=log;self.fail=fail
 def consume(self,event):
  self.log.append(self.consumer_key)
  if self.fail:raise RuntimeError("consumer_failure")
class Uow:
 def __init__(self,complete=()):self.complete=set(complete);self.marked=[];self.commits=0;self.rollbacks=0
 def is_consumer_complete(self,o,k):return (o,k) in self.complete
 def mark_consumer_complete(self,o,k):self.marked.append((o,k));self.complete.add((o,k))
 def commit(self):self.commits+=1
 def rollback(self):self.rollbacks+=1

def event(status="committed",enemy_class="normal"):
 return SettledVictoryEvent("op-1","battle-1",7,"mob",enemy_class,3,"start_path",status,10,"2.50",("item",))

class PostCombatHookCoordinatorTests(unittest.TestCase):
 def test_canonical_order_and_single_commit(self):
  log=[];u=Uow();cs=[Consumer("durability",log),Consumer("story_region_kill",log),Consumer("guild_contract",log)]
  out=PostCombatHookCoordinator().dispatch(event=event(),consumers=cs,unit_of_work=u)
  self.assertEqual(log,["story_region_kill","guild_contract","durability"]);self.assertEqual(u.commits,1);self.assertEqual(out.commit_count,1)
 def test_completed_consumer_is_skipped(self):
  log=[];u=Uow({("op-1","story_region_kill")});out=PostCombatHookCoordinator().dispatch(event=event(),consumers=[Consumer("story_region_kill",log),Consumer("daily_quest",log)],unit_of_work=u)
  self.assertEqual(log,["daily_quest"]);self.assertEqual([x.status for x in out.consumer_results],["already_complete","applied"])
 def test_failure_rolls_back_hook_uow_without_commit(self):
  log=[];u=Uow()
  with self.assertRaises(RuntimeError):PostCombatHookCoordinator().dispatch(event=event(),consumers=[Consumer("story_region_kill",log),Consumer("daily_quest",log,True)],unit_of_work=u)
  self.assertEqual(u.commits,0);self.assertEqual(u.rollbacks,1)
 def test_uncommitted_settlement_fails_before_consumer(self):
  log=[];u=Uow()
  with self.assertRaises(PostCombatHookContractError):PostCombatHookCoordinator().dispatch(event=event("processing"),consumers=[Consumer("story_region_kill",log)],unit_of_work=u)
  self.assertFalse(log);self.assertEqual(u.commits,0)
 def test_normal_elite_boss_share_event_contract(self):
  for kind in ("normal","elite","boss"):
   u=Uow();PostCombatHookCoordinator().dispatch(event=event(enemy_class=kind),consumers=[],unit_of_work=u);self.assertEqual(u.commits,1)
 def test_duplicate_and_unknown_consumers_rejected(self):
  for consumers in ([Consumer("daily_quest",[]),Consumer("daily_quest",[])],[Consumer("shadow",[])]):
   with self.assertRaises(PostCombatHookContractError):PostCombatHookCoordinator().dispatch(event=event(),consumers=consumers,unit_of_work=Uow())
 def test_event_has_summary_not_reward_commands(self):
  fields=SettledVictoryEvent.__dataclass_fields__
  for forbidden in ("exp_command","gold_command","loot_command","quest_reward_command"):self.assertNotIn(forbidden,fields)

if __name__=="__main__":unittest.main()
