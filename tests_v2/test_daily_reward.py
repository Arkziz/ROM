import unittest
from copy import deepcopy
from rom_v2.application.daily_reward import *
class Quest:
 def __init__(self,exists=True,complete=True,claimed=False):self.e=exists;self.c=complete;self.claimed=claimed
 def exists(self,u,p):return self.e
 def is_complete(self,u,p):return self.c
 def is_claimed(self,u,p):return self.claimed
 def mark_claimed(self,u,p):self.claimed=True
class Period:
 def __init__(self,p="2026-10-23"):self.p=p
 def current_period_key(self):return self.p
class Inventory:
 def __init__(self,q=2,capacity=True):self.q=q;self.capacity=capacity;self.plans=[]
 def quantity(self,u,k):return self.q
 def build_add_plan(self,u,k,q):return DailyRewardStackPlan(k,self.q,q,self.q+q)
 def validate_capacity(self,u,p):
  if not self.capacity:raise DailyRewardContractError("inventory_full")
 def apply_plan(self,u,p):self.q=p.quantity_after;self.plans.append(p)
class Tokens:
 def __init__(self,q=4):self.q=q
 def credit(self,u,k,q):self.q+=q;return self.q
class Receipts:
 def __init__(self):self.rows={};self.period={}
 def get_receipt(self,k):return self.rows.get(k)
 def get_period_receipt(self,u,p):return self.period.get((u,p))
 def save_receipt(self,r):self.rows[r.operation_key]=r;self.period[(r.user_id,r.period_key)]=r
class Uow:
 def __init__(self,complete=True,claimed=False,capacity=True,fail=False):self.quest=Quest(complete=complete,claimed=claimed);self.period=Period();self.inventory=Inventory(capacity=capacity);self.tokens=Tokens();self.receipts=Receipts();self.fail=fail;self.commits=0;self.rollbacks=0;self.snap=None
 def begin(self):self.snap=deepcopy((self.quest,self.period,self.inventory,self.tokens,self.receipts))
 def commit(self):
  if self.fail:raise RuntimeError("commit_failure")
  self.commits+=1;self.snap=None
 def rollback(self):
  self.rollbacks+=1
  if self.snap:self.quest,self.period,self.inventory,self.tokens,self.receipts=self.snap;self.snap=None
def cmd(k="op",p="2026-10-23",r=REWARD_KEY):return DailyRewardClaimCommand(k,1,p,r)
def execute(u,c=cmd()):u.begin();return DailyRewardService().claim(c,u)
class Tests(unittest.TestCase):
 def test_exact_three_plus_three(self):
  u=Uow();r=execute(u);self.assertEqual(r.receipt.small_hp_potions_granted,3);self.assertEqual(r.receipt.phirius_tokens_granted,3);self.assertEqual(u.inventory.q,5);self.assertEqual(u.tokens.q,7);self.assertTrue(u.quest.claimed);self.assertEqual(u.commits,1)
 def test_incomplete_rejected(self):
  u=Uow(complete=False)
  with self.assertRaisesRegex(DailyRewardContractError,"daily_quest_incomplete"):execute(u)
  self.assertEqual(u.inventory.q,2);self.assertEqual(u.tokens.q,4)
 def test_stale_period_rejected(self):
  u=Uow()
  with self.assertRaisesRegex(DailyRewardContractError,"stale_period"):execute(u,cmd(p="2026-10-22"))
 def test_inventory_full_rolls_nothing(self):
  u=Uow(capacity=False)
  with self.assertRaisesRegex(DailyRewardContractError,"inventory_full"):execute(u)
  self.assertEqual(u.inventory.q,2);self.assertEqual(u.tokens.q,4);self.assertFalse(u.quest.claimed)
 def test_already_claimed_rejected(self):
  u=Uow(claimed=True)
  with self.assertRaisesRegex(DailyRewardContractError,"already_claimed"):execute(u)
 def test_replay_and_conflict(self):
  u=Uow();first=execute(u);u.begin();again=DailyRewardService().claim(cmd(),u);self.assertTrue(again.replayed);self.assertEqual(first.receipt,again.receipt);self.assertEqual(u.inventory.q,5);self.assertEqual(u.tokens.q,7);u.begin()
  with self.assertRaises(DailyRewardConflictError):DailyRewardService().claim(DailyRewardClaimCommand("op",2,"2026-10-23",REWARD_KEY),u)
 def test_wrong_reward_key_forbidden(self):
  with self.assertRaisesRegex(DailyRewardContractError,"invalid_reward_key"):DailyRewardService().claim(cmd(r="legacy_five_tokens"),Uow())
 def test_commit_failure_rolls_back_all(self):
  u=Uow(fail=True)
  with self.assertRaisesRegex(RuntimeError,"commit_failure"):execute(u)
  self.assertEqual(u.inventory.q,2);self.assertEqual(u.tokens.q,4);self.assertFalse(u.quest.claimed);self.assertFalse(u.receipts.rows)
 def test_restart_replay(self):
  first=Uow();original=execute(first);second=deepcopy(first);second.begin();replay=DailyRewardService().claim(cmd(),second);self.assertTrue(replay.replayed);self.assertEqual(replay.receipt,original.receipt);self.assertEqual(second.inventory.q,5);self.assertEqual(second.tokens.q,7)
if __name__=="__main__":unittest.main()
