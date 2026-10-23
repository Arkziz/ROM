import unittest
from copy import deepcopy
from datetime import datetime, timezone
from rom_v2.application.crystal_wallet_ledger import *
class Repo:
 def __init__(self,balance=0): self.b={1:balance};self.by_key={};self.by_id={}
 def get_balance(self,u):return self.b.get(u,0)
 def set_balance(self,u,b):self.b[u]=b
 def get_by_idempotency_key(self,k):return self.by_key.get(k)
 def get_transaction(self,t):return self.by_id.get(t)
 def get_compensation(self,o):return next((x for x in self.by_id.values() if x.original_transaction_id==o),None)
 def append_transaction(self,t):
  if t.idempotency_key in self.by_key:raise RuntimeError("duplicate_key")
  self.by_key[t.idempotency_key]=t;self.by_id[t.transaction_id]=t
class Uow:
 def __init__(self,b=0,fail=False):self.wallet=Repo(b);self.fail=fail;self.n=0;self.commits=0;self.rollbacks=0;self.snap=None
 def begin(self):self.snap=deepcopy((self.wallet.b,self.wallet.by_key,self.wallet.by_id))
 def next_transaction_id(self):self.n+=1;return f"tx-{self.n}"
 def now(self):return datetime(2026,1,1,tzinfo=timezone.utc)
 def commit(self):
  if self.fail:raise RuntimeError("commit_failure")
  self.commits+=1;self.snap=None
 def rollback(self):
  self.rollbacks+=1
  if self.snap:self.wallet.b,self.wallet.by_key,self.wallet.by_id=self.snap;self.snap=None
def cmd(k="k1",d=CrystalDirection.CREDIT,a=5):return CrystalWalletCommand(k,1,d,a,"test","unit")
class Tests(unittest.TestCase):
 def run_cmd(self,u,c):u.begin();return CrystalWalletLedgerService().execute(c,u)
 def test_credit_and_debit(self):
  u=Uow(2);self.assertEqual(self.run_cmd(u,cmd()).transaction.balance_after,7);self.assertEqual(self.run_cmd(u,cmd("k2",CrystalDirection.DEBIT,3)).transaction.balance_after,4)
 def test_insufficient_fails_closed(self):
  u=Uow(1)
  with self.assertRaisesRegex(CrystalWalletContractError,"insufficient_crystals"):self.run_cmd(u,cmd(d=CrystalDirection.DEBIT,a=2))
  self.assertEqual(u.wallet.get_balance(1),1);self.assertFalse(u.wallet.by_id)
 def test_same_replay_and_changed_conflict(self):
  u=Uow();first=self.run_cmd(u,cmd());u.begin();self.assertTrue(CrystalWalletLedgerService().execute(cmd(),u).replayed);u.begin()
  with self.assertRaises(CrystalWalletConflictError):CrystalWalletLedgerService().execute(cmd(a=6),u)
  self.assertEqual(u.wallet.get_balance(1),5);self.assertEqual(first.transaction.transaction_id,"tx-1")
 def test_compensation_exact_once(self):
  u=Uow();original=self.run_cmd(u,cmd()).transaction;u.begin();service=CrystalWalletLedgerService();comp=service.compensate(original_transaction_id=original.transaction_id,idempotency_key="c1",reason_code="reverse",source="unit",uow=u)
  self.assertEqual(comp.transaction.balance_after,0);u.begin();self.assertTrue(service.compensate(original_transaction_id=original.transaction_id,idempotency_key="c1",reason_code="reverse",source="unit",uow=u).replayed);u.begin()
  with self.assertRaises(CrystalWalletConflictError):service.compensate(original_transaction_id=original.transaction_id,idempotency_key="c2",reason_code="reverse",source="unit",uow=u)
 def test_compensation_of_compensation_forbidden(self):
  u=Uow();o=self.run_cmd(u,cmd()).transaction;u.begin();c=CrystalWalletLedgerService().compensate(original_transaction_id=o.transaction_id,idempotency_key="c1",reason_code="r",source="u",uow=u).transaction;u.begin()
  with self.assertRaisesRegex(CrystalWalletContractError,"compensation_of_compensation_forbidden"):CrystalWalletLedgerService().compensate(original_transaction_id=c.transaction_id,idempotency_key="c2",reason_code="r",source="u",uow=u)
 def test_commit_failure_rolls_back(self):
  u=Uow(fail=True)
  with self.assertRaisesRegex(RuntimeError,"commit_failure"):self.run_cmd(u,cmd())
  self.assertEqual(u.wallet.get_balance(1),0);self.assertFalse(u.wallet.by_id)
 def test_int_and_positive_validation(self):
  for value in (1.0,True):
   with self.assertRaisesRegex(CrystalWalletContractError,"amount_must_be_int"):CrystalWalletLedgerService().execute(cmd(a=value),Uow())
  with self.assertRaisesRegex(CrystalWalletContractError,"amount_must_be_positive"):CrystalWalletLedgerService().execute(cmd(a=0),Uow())
 def test_immutable_transaction(self):
  t=self.run_cmd(Uow(),cmd()).transaction
  with self.assertRaises(Exception):t.amount=99
 def test_restart_replay(self):
  first=Uow();original=self.run_cmd(first,cmd());second=Uow();second.wallet=deepcopy(first.wallet);second.begin();replay=CrystalWalletLedgerService().execute(cmd(),second);self.assertTrue(replay.replayed);self.assertEqual(replay.transaction,original.transaction)
if __name__=="__main__":unittest.main()
