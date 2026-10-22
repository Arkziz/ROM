import copy
import unittest
from dataclasses import replace
from rom_v2.application.reward_settlement import (
 RewardLootCommand, RewardLootOutcome, RewardPlayerProgressState,
 RewardObjectiveProgressCommand, RewardSettlementCommand,
 RewardSettlementInProgressError, RewardSettlementService,
 RewardSettlementUnitOfWork, RewardSettlementValidationError,
)

class FakeUow:
 def __init__(self, fail_at=None):
  self.fail_at=fail_at;self.commit_count=0;self.rollback_count=0;self.events=[]
  self.claims=self.Claims(self);self.progression=self.Progress(self);self.wallet=self.Wallet(self);self.loot=self.Loot(self);self.objective_progress=self.Quests(self);self.history=self.History(self)
  self._stable=self.snapshot()
 def snapshot(self):
  return copy.deepcopy({"claim_rows":getattr(self,"claim_rows",{}),"state":getattr(self,"state",RewardPlayerProgressState(1,0,11)),"credits":getattr(self,"credits",[]),"loot_rows":getattr(self,"loot_rows",[]),"quest_rows":getattr(self,"quest_rows",[]),"history_rows":getattr(self,"history_rows",[])})
 def restore(self,s):
  self.claim_rows=s["claim_rows"];self.state=s["state"];self.credits=s["credits"];self.loot_rows=s["loot_rows"];self.quest_rows=s["quest_rows"];self.history_rows=s["history_rows"]
 def trip(self,name):
  self.events.append(name)
  if self.fail_at==name:raise RuntimeError(name)
 def commit(self):self.trip("commit");self.commit_count+=1;self._stable=self.snapshot()
 def rollback(self):self.rollback_count+=1;self.events.append("rollback");self.restore(self._stable)
 class Claims:
  def __init__(self,u):self.u=u;u.claim_rows={}
  def claim(self,key):
   self.u.trip("claim");row=self.u.claim_rows.get(key)
   if row and row[0]=="completed":return "completed"
   if row:return "processing"
   self.u.claim_rows[key]=("processing",None);return "claimed"
  def completed_result(self,key):return self.u.claim_rows[key][1]
  def complete(self,key,result):self.u.trip("complete");self.u.claim_rows[key]=("completed",result)
 class Progress:
  def __init__(self,u):self.u=u;u.state=RewardPlayerProgressState(1,0,11)
  def get_state(self,actor):self.u.trip("get_state");return self.u.state
  def apply(self,actor,result):self.u.trip("progression");self.u.state=RewardPlayerProgressState(result.level,result.exp,11)
 class Wallet:
  def __init__(self,u):self.u=u;u.credits=[]
  def credit(self,actor,amount,source):self.u.trip("wallet_"+source);self.u.credits.append((amount,source))
 class Loot:
  def __init__(self,u):self.u=u;u.loot_rows=[]
  def apply(self,actor,commands):self.u.trip("loot");self.u.loot_rows.extend(commands);return RewardLootOutcome("applied",tuple(commands))
 class Quests:
  def __init__(self,u):self.u=u;u.quest_rows=[]
  def apply(self,actor,commands):self.u.trip("quest");self.u.quest_rows.extend(commands);return tuple(commands)
 class History:
  def __init__(self,u):self.u=u;u.history_rows=[]
  def append(self,key,actor,summary):self.u.trip("history");self.u.history_rows.append((key,summary));return "history-1"

def command(key="op-1",source="pve"):
 return RewardSettlementCommand(key,source,7,"enc-9",500,10.0,2.5,(RewardLootCommand("item-a",1),),(RewardObjectiveProgressCommand("kill-a",1),))

class RewardSettlementIntegrationTests(unittest.TestCase):
 def test_exact_once_duplicate_returns_prior_result(self):
  u=FakeUow();service=RewardSettlementService();first=service.settle(command(),u);second=service.settle(command(),u)
  self.assertFalse(first.duplicate);self.assertTrue(second.duplicate);self.assertEqual(u.commit_count,1);self.assertEqual(len(u.credits),2);self.assertEqual(len(u.history_rows),1)
 def test_one_commit_and_order(self):
  u=FakeUow();result=RewardSettlementService().settle(command(),u)
  self.assertEqual(u.commit_count,1);self.assertEqual(u.rollback_count,0);self.assertEqual(result.progression.level,2)
  self.assertEqual(u.events,["claim","get_state","progression","wallet_level_up_gold","wallet_combat_gold","loot","quest","history","complete","commit"])
 def test_premium_applies_only_to_combat_gold(self):
  u=FakeUow();result=RewardSettlementService().settle(command(),u)
  self.assertEqual(result.combat_gold,12.5);self.assertEqual(u.credits,[(0.45,"level_up_gold"),(12.5,"combat_gold")])
 def test_processing_duplicate_fails_closed(self):
  u=FakeUow();u.claim_rows["op-1"]=("processing",None)
  with self.assertRaises(RewardSettlementInProgressError):RewardSettlementService().settle(command(),u)
  self.assertEqual(u.commit_count,0);self.assertEqual(u.rollback_count,1)
 def test_rollback_at_every_mutation_boundary(self):
  for boundary in ("progression","wallet_level_up_gold","wallet_combat_gold","loot","quest","history","complete","commit"):
   with self.subTest(boundary=boundary):
    u=FakeUow(boundary);initial=u.snapshot()
    with self.assertRaises(RuntimeError):RewardSettlementService().settle(command(),u)
    self.assertEqual(u.snapshot(),initial);self.assertEqual(u.commit_count,0);self.assertEqual(u.rollback_count,1)
 def test_pending_loot_is_explicit_success_outcome(self):
  u=FakeUow()
  def pending(actor,commands):u.trip("loot");return RewardLootOutcome("pending",pending=tuple(commands))
  u.loot.apply=pending;result=RewardSettlementService().settle(command(),u);self.assertEqual(result.loot_outcome.status,"pending");self.assertEqual(u.commit_count,1)
 def test_pvp_and_invalid_input_rejected_before_mutation(self):
  for bad in (command(source="pvp"),replace(command(),operation_key=""),replace(command(),exp_award=-1)):
   u=FakeUow()
   with self.assertRaises(RewardSettlementValidationError):RewardSettlementService().settle(bad,u)
   self.assertEqual(u.events,[]);self.assertEqual(u.rollback_count,0)
 def test_service_has_no_presentation_port(self):
  self.assertFalse(any("message" in name or "send" in name for name in RewardSettlementUnitOfWork.__annotations__))

if __name__=="__main__":unittest.main()
