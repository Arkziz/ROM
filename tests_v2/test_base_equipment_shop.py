import unittest
from copy import deepcopy
from datetime import datetime,timezone
from rom_v2.application.base_equipment_shop import *
ITEM=EquipmentSnapshot("sword","main_hand","sword","warrior",(("str",2),),"common",100)
PREVIEW=ShopPreview(1001,1,"main_hand","sword","warrior",ITEM,10,datetime(2026,1,1,tzinfo=timezone.utc))
class Shop:
 def __init__(self):self.previews={1001:PREVIEW};self.receipts={}
 def get_preview(self,i):return self.previews.get(i)
 def get_receipt(self,k):return self.receipts.get(k)
 def save_receipt(self,r):self.receipts[r.operation_key]=r
 def invalidate_preview(self,i):self.previews.pop(i,None)
class Wallet:
 def __init__(self,b=20):self.b=b
 def get_balance(self,u):return self.b
 def debit(self,u,a):
  if self.b<a:raise ShopContractError("insufficient_gold")
  self.b-=a;return self.b
class Inventory:
 def __init__(self,capacity=True):self.capacity=capacity;self.rows=[]
 def has_capacity(self,u):return self.capacity
 def insert(self,u,p,item):self.rows.append((u,p,item));return len(self.rows)
class Allocator:
 def __init__(self):self.n=20000;self.map={}
 def promote(self,p,item):
  if p not in self.map:self.map[p]=self.n;self.n+=1
  return self.map[p]
class Uow:
 def __init__(self,b=20,capacity=True,fail=False):self.shop=Shop();self.wallet=Wallet(b);self.inventory=Inventory(capacity);self.allocator=Allocator();self.fail=fail;self.commits=0;self.rollbacks=0;self.snap=None
 def begin(self):self.snap=deepcopy((self.shop,self.wallet,self.inventory,self.allocator))
 def commit(self):
  if self.fail:raise RuntimeError("commit_failure")
  self.commits+=1;self.snap=None
 def rollback(self):
  self.rollbacks+=1
  if self.snap:self.shop,self.wallet,self.inventory,self.allocator=self.snap;self.snap=None
def execute(u,c=ConfirmPurchase("op",1,1001)):u.begin();return BaseEquipmentShopService().confirm(c,u)
class Tests(unittest.TestCase):
 def test_purchase(self):
  u=Uow();r=execute(u);self.assertEqual(r.receipt.price,10);self.assertEqual(u.wallet.b,10);self.assertEqual(len(u.inventory.rows),1);self.assertEqual(u.commits,1)
 def test_replay(self):
  u=Uow();first=execute(u);u.begin();again=BaseEquipmentShopService().confirm(ConfirmPurchase("op",1,1001),u);self.assertTrue(again.replayed);self.assertEqual(first.receipt,again.receipt);self.assertEqual(u.commits,1)
 def test_changed_replay_conflicts(self):
  u=Uow();execute(u);u.begin()
  with self.assertRaises(ShopConflictError):BaseEquipmentShopService().confirm(ConfirmPurchase("op",2,1001),u)
 def test_inventory_full_prevents_mutation(self):
  u=Uow(capacity=False)
  with self.assertRaisesRegex(ShopContractError,"inventory_full"):execute(u)
  self.assertEqual(u.wallet.b,20);self.assertFalse(u.inventory.rows)
 def test_insufficient_gold_prevents_promotion(self):
  u=Uow(b=9)
  with self.assertRaisesRegex(ShopContractError,"insufficient_gold"):execute(u)
  self.assertFalse(u.allocator.map);self.assertFalse(u.inventory.rows)
 def test_owner_and_stale_rejected(self):
  u=Uow()
  with self.assertRaisesRegex(ShopContractError,"preview_owner_mismatch"):execute(u,ConfirmPurchase("x",2,1001))
  u=Uow();u.shop.previews.clear()
  with self.assertRaisesRegex(ShopContractError,"preview_not_found_or_expired"):execute(u)
 def test_commit_failure_rolls_back_all(self):
  u=Uow(fail=True)
  with self.assertRaisesRegex(RuntimeError,"commit_failure"):execute(u)
  self.assertEqual(u.wallet.b,20);self.assertFalse(u.inventory.rows);self.assertFalse(u.allocator.map);self.assertIn(1001,u.shop.previews)
 def test_immutable_preview(self):
  with self.assertRaises(Exception):PREVIEW.quoted_price=1
 def test_restart_replay(self):
  first=Uow();original=execute(first);second=deepcopy(first);second.begin();replay=BaseEquipmentShopService().confirm(ConfirmPurchase("op",1,1001),second);self.assertTrue(replay.replayed);self.assertEqual(replay.receipt,original.receipt)
if __name__=="__main__":unittest.main()
