import unittest
from copy import deepcopy
from rom_v2.application.admin_crystals import *
class F:
 def __init__(self,x=True):self.x=x
 def is_admin(self,u):return self.x
 def exists(self,u):return self.x
class W:
 def __init__(self,b=40):self.b=b
 def get_balance(self,u):return self.b
 def credit(self,u,a):self.b+=a;return self.b
 def debit(self,u,a):self.b-=a;return self.b
class R:
 def __init__(self):self.rows=[]
 def append(self,x):self.rows.append(x)
 def enqueue(self,x):self.rows.append(x)
class P:
 def __init__(self):self.rows={}
 def get_receipt(self,k):return self.rows.get(k)
 def save_receipt(self,r):self.rows[r.operation_key]=r
class U:
 def __init__(self,b=40,a=True,t=True,fail=False):self.authorization=F(a);self.accounts=F(t);self.wallet=W(b);self.ledger=R();self.receipts=P();self.notifications=R();self.fail=fail;self.snap=None
 def begin(self):self.snap=deepcopy((self.wallet,self.ledger,self.receipts,self.notifications))
 def commit(self):
  if self.fail:raise RuntimeError()
  self.snap=None
 def rollback(self):
  if self.snap:self.wallet,self.ledger,self.receipts,self.notifications=self.snap;self.snap=None
def c(k="op",kind="credit",amount=10,before=40,applied=10,target=2):return AdminCrystalAdjustmentCommand(k,1,target,kind,amount,before,applied,"audit")
def run(u,x):u.begin();return AdminCrystalAdjustmentService().execute(x,u)
class Tests(unittest.TestCase):
 def test_credit(self):self.assertEqual(run(U(),c()).receipt.balance_after,50)
 def test_clamped_zero(self):self.assertEqual(run(U(),c(kind="debit",amount=90,applied=40)).receipt.applied_amount,40);self.assertEqual(run(U(0),c("z","debit",9,0,0)).receipt.applied_amount,0)
 def test_guards_stale(self):
  with self.assertRaises(AdminCrystalsContractError):run(U(a=False),c())
  with self.assertRaises(AdminCrystalsContractError):run(U(t=False),c())
  with self.assertRaisesRegex(AdminCrystalsContractError,"stale_balance"):run(U(41),c())
 def test_replay_conflict(self):
  u=U();run(u,c());u.begin();self.assertTrue(AdminCrystalAdjustmentService().execute(c(),u).replayed);u.begin()
  with self.assertRaises(AdminCrystalsConflictError):AdminCrystalAdjustmentService().execute(c(target=3),u)
 def test_rollback_restart(self):
  u=U(fail=True)
  with self.assertRaises(RuntimeError):run(u,c())
  self.assertEqual(u.wallet.b,40);v=U();run(v,c());r=deepcopy(v);r.begin();self.assertTrue(AdminCrystalAdjustmentService().execute(c(),r).replayed)
if __name__=="__main__":unittest.main()
