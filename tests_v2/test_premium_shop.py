import unittest
from copy import deepcopy
from datetime import datetime,timezone,timedelta
from rom_v2.application.premium_shop import *
NOW=datetime(2026,1,1,tzinfo=timezone.utc)
class Account:
 def __init__(self,e=None):self.expiry=e
 def get_expiry(self,u):return self.expiry
 def set_expiry(self,u,e):self.expiry=e
class Wallet:
 def __init__(self,b=500):self.b=b
 def get_balance(self,u):return self.b
 def debit(self,u,a):
  if self.b<a:raise PremiumShopContractError("insufficient_crystals")
  self.b-=a;return self.b
class Receipts:
 def __init__(self):self.rows={}
 def get_receipt(self,k):return self.rows.get(k)
 def save_receipt(self,r):self.rows[r.operation_key]=r
class Clock:
 def __init__(self,n=NOW):self.n=n
 def now_utc(self):return self.n
class Uow:
 def __init__(self,b=500,e=None,fail=False):self.account=Account(e);self.wallet=Wallet(b);self.receipts=Receipts();self.clock=Clock();self.fail=fail;self.commits=0;self.rollbacks=0;self.snap=None
 def begin(self):self.snap=deepcopy((self.account,self.wallet,self.receipts,self.clock))
 def commit(self):
  if self.fail:raise RuntimeError("commit_failure")
  self.commits+=1;self.snap=None
 def rollback(self):
  self.rollbacks+=1
  if self.snap:self.account,self.wallet,self.receipts,self.clock=self.snap;self.snap=None
def cmd(k="op",plan="premium_15d",price=100):return PremiumPurchaseCommand(k,1,plan,price)
def execute(u,c):u.begin();return PremiumShopService().purchase(c,u)
class Tests(unittest.TestCase):
 def test_activate_15_day_plan(self):
  u=Uow();r=execute(u,cmd());self.assertEqual(r.receipt.new_expiry,NOW+timedelta(days=15));self.assertEqual(u.wallet.b,400);self.assertEqual(u.commits,1)
 def test_activate_30_day_plan(self):
  u=Uow();r=execute(u,cmd(plan="premium_30d",price=180));self.assertEqual(r.receipt.new_expiry,NOW+timedelta(days=30));self.assertEqual(u.wallet.b,320)
 def test_extend_from_active_expiry(self):
  old=NOW+timedelta(days=5);u=Uow(e=old);r=execute(u,cmd());self.assertEqual(r.receipt.base_expiry,old);self.assertEqual(r.receipt.new_expiry,old+timedelta(days=15))
 def test_expired_activates_from_now(self):
  old=NOW-timedelta(seconds=1);u=Uow(e=old);r=execute(u,cmd());self.assertEqual(r.receipt.base_expiry,NOW)
 def test_stale_price_and_unknown_plan_fail_closed(self):
  for c,reason in ((cmd(price=101),"stale_plan_price"),(cmd(plan="other"),"unknown_premium_plan")):
   u=Uow()
   with self.subTest(reason=reason),self.assertRaisesRegex(PremiumShopContractError,reason):execute(u,c)
   self.assertEqual(u.wallet.b,500);self.assertIsNone(u.account.expiry)
 def test_insufficient_crystals(self):
  u=Uow(b=99)
  with self.assertRaisesRegex(PremiumShopContractError,"insufficient_crystals"):execute(u,cmd())
  self.assertIsNone(u.account.expiry)
 def test_replay_and_conflict(self):
  u=Uow();first=execute(u,cmd());u.begin();again=PremiumShopService().purchase(cmd(),u);self.assertTrue(again.replayed);self.assertEqual(first.receipt,again.receipt);self.assertEqual(u.wallet.b,400);u.begin()
  with self.assertRaises(PremiumShopConflictError):PremiumShopService().purchase(cmd(plan="premium_30d",price=180),u)
 def test_commit_failure_rolls_back_all(self):
  u=Uow(fail=True)
  with self.assertRaisesRegex(RuntimeError,"commit_failure"):execute(u,cmd())
  self.assertEqual(u.wallet.b,500);self.assertIsNone(u.account.expiry);self.assertFalse(u.receipts.rows)
 def test_restart_replay(self):
  first=Uow();original=execute(first,cmd());second=deepcopy(first);second.begin();replay=PremiumShopService().purchase(cmd(),second);self.assertTrue(replay.replayed);self.assertEqual(replay.receipt,original.receipt);self.assertEqual(second.account.expiry,NOW+timedelta(days=15))
if __name__=="__main__":unittest.main()
