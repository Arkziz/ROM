import unittest
from copy import deepcopy
from rom_v2.application.bag_expansion import *
class Capacity:
 def __init__(self,c=60):self.c=c
 def get_capacity(self,u):return self.c
 def set_capacity(self,u,c):self.c=c
class Wallet:
 def __init__(self,b=300):self.b=b
 def get_balance(self,u):return self.b
 def debit(self,u,a):
  if self.b<a:raise BagExpansionContractError("insufficient_crystals")
  self.b-=a;return self.b
class Receipts:
 def __init__(self):self.rows={}
 def get_receipt(self,k):return self.rows.get(k)
 def save_receipt(self,r):self.rows[r.operation_key]=r
class Uow:
 def __init__(self,c=60,b=300,fail=False):self.capacity=Capacity(c);self.wallet=Wallet(b);self.receipts=Receipts();self.fail=fail;self.commits=0;self.rollbacks=0;self.snap=None
 def begin(self):self.snap=deepcopy((self.capacity,self.wallet,self.receipts))
 def commit(self):
  if self.fail:raise RuntimeError("commit_failure")
  self.commits+=1;self.snap=None
 def rollback(self):
  self.rollbacks+=1
  if self.snap:self.capacity,self.wallet,self.receipts=self.snap;self.snap=None
def first(k="op"):return BagExpansionCommand(k,1,"bag_60_to_80",60,80,75)
def second(k="op2"):return BagExpansionCommand(k,1,"bag_80_to_100",80,100,150)
def execute(u,c):u.begin();return BagExpansionService().purchase(c,u)
class Tests(unittest.TestCase):
 def test_first_expansion(self):
  u=Uow();r=execute(u,first());self.assertEqual(r.receipt.target_capacity,80);self.assertEqual(u.capacity.c,80);self.assertEqual(u.wallet.b,225);self.assertEqual(u.commits,1)
 def test_second_expansion(self):
  u=Uow(c=80);r=execute(u,second());self.assertEqual(r.receipt.target_capacity,100);self.assertEqual(u.capacity.c,100);self.assertEqual(u.wallet.b,150)
 def test_maximum_capacity_rejected(self):
  u=Uow(c=100)
  with self.assertRaisesRegex(BagExpansionContractError,"maximum_capacity"):execute(u,second())
  self.assertEqual(u.wallet.b,300)
 def test_skip_and_stale_rejected(self):
  u=Uow()
  with self.assertRaisesRegex(BagExpansionContractError,"stale_capacity"):execute(u,second())
  u=Uow(c=80)
  with self.assertRaisesRegex(BagExpansionContractError,"stale_capacity"):execute(u,first())
 def test_stale_price_rejected(self):
  u=Uow();bad=BagExpansionCommand("x",1,"bag_60_to_80",60,80,76)
  with self.assertRaisesRegex(BagExpansionContractError,"stale_price"):execute(u,bad)
  self.assertEqual(u.wallet.b,300);self.assertEqual(u.capacity.c,60)
 def test_insufficient_crystals(self):
  u=Uow(b=74)
  with self.assertRaisesRegex(BagExpansionContractError,"insufficient_crystals"):execute(u,first())
  self.assertEqual(u.capacity.c,60)
 def test_replay_and_conflict(self):
  u=Uow();original=execute(u,first());u.begin();replay=BagExpansionService().purchase(first(),u);self.assertTrue(replay.replayed);self.assertEqual(replay.receipt,original.receipt);self.assertEqual(u.wallet.b,225);u.begin()
  with self.assertRaises(BagExpansionConflictError):BagExpansionService().purchase(BagExpansionCommand("op",2,"bag_60_to_80",60,80,75),u)
 def test_commit_failure_rolls_back_all(self):
  u=Uow(fail=True)
  with self.assertRaisesRegex(RuntimeError,"commit_failure"):execute(u,first())
  self.assertEqual(u.capacity.c,60);self.assertEqual(u.wallet.b,300);self.assertFalse(u.receipts.rows)
 def test_restart_replay_and_reset_survival(self):
  first_uow=Uow();original=execute(first_uow,first());second_uow=deepcopy(first_uow);second_uow.begin();replay=BagExpansionService().purchase(first(),second_uow);self.assertTrue(replay.replayed);self.assertEqual(replay.receipt,original.receipt);self.assertEqual(second_uow.capacity.c,80)
if __name__=="__main__":unittest.main()
