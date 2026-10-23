import unittest
from copy import deepcopy
from rom_v2.application.potion_trading import *
class Catalog:
 def __init__(self):self.prices={("small_hp",TradeDirection.BUY):5,("small_hp",TradeDirection.SELL):1}
 def get_unit_price(self,k,d):return self.prices.get((k,d))
class Inventory:
 def __init__(self,q=4,reserved=1):self.q=q;self.reserved=reserved;self.applied=[]
 def get_quantity(self,u,k):return self.q
 def get_reserved_quantity(self,u,k):return self.reserved
 def build_stack_plan(self,u,k,d):return StackPlan(k,self.q,d,self.q+d)
 def apply_stack_plan(self,u,p):self.q=p.quantity_after;self.applied.append(p)
class Wallet:
 def __init__(self,b=20):self.b=b
 def get_balance(self,u):return self.b
 def debit(self,u,a):
  if self.b<a:raise PotionTradingContractError("insufficient_gold")
  self.b-=a;return self.b
 def credit(self,u,a):self.b+=a;return self.b
class Receipts:
 def __init__(self):self.rows={}
 def get_receipt(self,k):return self.rows.get(k)
 def save_receipt(self,r):self.rows[r.operation_key]=r
class Uow:
 def __init__(self,b=20,q=4,reserved=1,fail=False):self.catalog=Catalog();self.inventory=Inventory(q,reserved);self.wallet=Wallet(b);self.receipts=Receipts();self.fail=fail;self.commits=0;self.rollbacks=0;self.snap=None
 def begin(self):self.snap=deepcopy((self.catalog,self.inventory,self.wallet,self.receipts))
 def commit(self):
  if self.fail:raise RuntimeError("commit_failure")
  self.commits+=1;self.snap=None
 def rollback(self):
  self.rollbacks+=1
  if self.snap:self.catalog,self.inventory,self.wallet,self.receipts=self.snap;self.snap=None
def cmd(k="op",d=TradeDirection.BUY,q=2,p=5):return PotionTradeCommand(k,1,"small_hp",d,q,p)
def execute(u,c):u.begin();return PotionTradingService().execute(c,u)
class Tests(unittest.TestCase):
 def test_buy(self):
  u=Uow();r=execute(u,cmd());self.assertEqual(r.receipt.gold_delta,-10);self.assertEqual(u.wallet.b,10);self.assertEqual(u.inventory.q,6);self.assertEqual(u.commits,1)
 def test_sell_reservation_aware(self):
  u=Uow();r=execute(u,cmd(d=TradeDirection.SELL,q=3,p=1));self.assertEqual(r.receipt.gold_delta,3);self.assertEqual(u.inventory.q,1)
 def test_reserved_quantity_blocks_sell(self):
  u=Uow()
  with self.assertRaisesRegex(PotionTradingContractError,"insufficient_available_quantity"):execute(u,cmd(d=TradeDirection.SELL,q=4,p=1))
  self.assertEqual(u.inventory.q,4);self.assertEqual(u.wallet.b,20)
 def test_stale_price_fails_closed(self):
  u=Uow()
  with self.assertRaisesRegex(PotionTradingContractError,"stale_price"):execute(u,cmd(p=6))
  self.assertFalse(u.inventory.applied);self.assertEqual(u.wallet.b,20)
 def test_insufficient_gold_fails_closed(self):
  u=Uow(b=9)
  with self.assertRaisesRegex(PotionTradingContractError,"insufficient_gold"):execute(u,cmd())
  self.assertFalse(u.inventory.applied)
 def test_replay_and_conflict(self):
  u=Uow();first=execute(u,cmd());u.begin();again=PotionTradingService().execute(cmd(),u);self.assertTrue(again.replayed);self.assertEqual(first.receipt,again.receipt);u.begin()
  with self.assertRaises(PotionTradingConflictError):PotionTradingService().execute(cmd(q=1),u)
 def test_commit_failure_rolls_back_all(self):
  u=Uow(fail=True)
  with self.assertRaisesRegex(RuntimeError,"commit_failure"):execute(u,cmd())
  self.assertEqual(u.wallet.b,20);self.assertEqual(u.inventory.q,4);self.assertFalse(u.receipts.rows)
 def test_invalid_quantity(self):
  for q in (0,-1,True,1.5):
   with self.subTest(q=q),self.assertRaises(PotionTradingContractError):PotionTradingService().execute(cmd(q=q),Uow())
 def test_restart_replay(self):
  first=Uow();original=execute(first,cmd());second=deepcopy(first);second.begin();replay=PotionTradingService().execute(cmd(),second);self.assertTrue(replay.replayed);self.assertEqual(replay.receipt,original.receipt)
if __name__=="__main__":unittest.main()
