"""Pure Auction application service and in-memory Unit of Work."""
from __future__ import annotations
from dataclasses import replace
from rom_v2.domain.auction import *
class AuctionService:
 def __init__(self,uow):self.uow=uow
 def list_item(self,lot_id,seller_id,snapshot,price,now):
  try:price=normalize_price(price);category=normalize_category(snapshot.category)
  except ValueError as e:return AuctionResult(False,str(e))
  if self.uow.active_count(seller_id)>=MAX_ACTIVE_LOTS:return AuctionResult(False,"active_limit")
  reason=self.uow.validate_listing(seller_id,snapshot)
  if reason:return AuctionResult(False,reason)
  if self.uow.lot(lot_id) is not None:return AuctionResult(False,"duplicate_lot")
  lot=AuctionLot(lot_id,seller_id,replace(snapshot,category=category),price,expires_at=now+ACTIVE_DAYS)
  try:self.uow.consume_listing(snapshot);self.uow.save(lot);self.uow.history(lot_id,"listed");self.uow.commit()
  except Exception:self.uow.rollback();raise
  return AuctionResult(True,lot=lot,changed=True)
 def browse(self,buyer_id,category=None,limit=8,offset=0,now=0):
  cat=normalize_category(category) if category else None;size=max(1,min(100,int(limit)));start=max(0,int(offset));rows=[x for x in self.uow.lots() if x.status is LotStatus.ACTIVE and x.expires_at>now and x.seller_user_id!=buyer_id and (cat is None or x.snapshot.category==cat)];rows.sort(key=lambda x:x.lot_id);return AuctionPage(tuple(rows[start:start+size]),len(rows),size,start)
 def buy(self,lot_id,buyer_id,now):
  lot=self.uow.lot(lot_id)
  if lot is None:return AuctionResult(False,"lot_not_found")
  if lot.seller_user_id==buyer_id:return AuctionResult(False,"self_purchase",lot)
  if lot.status is not LotStatus.ACTIVE:return AuctionResult(False,"lot_unavailable",lot)
  if lot.expires_at<=now:return AuctionResult(False,"lot_expired",lot)
  reason=self.uow.validate_purchase(buyer_id,lot)
  if reason:return AuctionResult(False,reason,lot)
  changed=replace(lot,status=LotStatus.SOLD_UNCLAIMED,buyer_user_id=buyer_id)
  try:self.uow.apply_purchase(buyer_id,lot);self.uow.save(changed);self.uow.history(lot_id,"sold");self.uow.commit()
  except Exception:self.uow.rollback();raise
  return AuctionResult(True,lot=changed,changed=True,transfer_required=True)
 def acknowledge_sale(self,lot_id,seller_id):
  lot=self.uow.lot(lot_id)
  if lot is None:return AuctionResult(False,"lot_not_found")
  if lot.seller_user_id!=seller_id:return AuctionResult(False,"permission_denied",lot)
  if lot.status is LotStatus.SOLD_CLAIMED:return AuctionResult(True,"already_claimed",lot)
  if lot.status is not LotStatus.SOLD_UNCLAIMED:return AuctionResult(False,"invalid_status",lot)
  changed=replace(lot,status=LotStatus.SOLD_CLAIMED);self.uow.save(changed);self.uow.history(lot_id,"sale_acknowledged");self.uow.commit();return AuctionResult(True,lot=changed,changed=True)
 def cancel(self,lot_id,seller_id):
  lot=self.uow.lot(lot_id)
  if lot is None:return AuctionResult(False,"lot_not_found")
  if lot.seller_user_id!=seller_id:return AuctionResult(False,"permission_denied",lot)
  if lot.status is LotStatus.CANCELLED:return AuctionResult(True,"already_terminal",lot)
  if lot.status is not LotStatus.ACTIVE:return AuctionResult(False,"lot_unavailable",lot)
  reason=self.uow.validate_restore(seller_id,lot)
  if reason:return AuctionResult(False,reason,lot)
  changed=replace(lot,status=LotStatus.CANCELLED)
  try:self.uow.restore_item(seller_id,lot);self.uow.save(changed);self.uow.history(lot_id,"cancelled");self.uow.commit()
  except Exception:self.uow.rollback();raise
  return AuctionResult(True,lot=changed,changed=True,transfer_required=True)
 def expire(self,now):
  out=[]
  for lot in self.uow.lots():
   if lot.status is LotStatus.ACTIVE and lot.expires_at<=now:
    changed=replace(lot,status=LotStatus.EXPIRED_UNCLAIMED);self.uow.save(changed);self.uow.history(lot.lot_id,"expired");out.append(lot.lot_id)
  self.uow.commit();return tuple(out)
 def claim_expired(self,lot_id,seller_id):
  lot=self.uow.lot(lot_id)
  if lot is None:return AuctionResult(False,"lot_not_found")
  if lot.seller_user_id!=seller_id:return AuctionResult(False,"permission_denied",lot)
  if lot.status is LotStatus.EXPIRED_CLAIMED:return AuctionResult(True,"already_claimed",lot)
  if lot.status is not LotStatus.EXPIRED_UNCLAIMED:return AuctionResult(False,"invalid_status",lot)
  reason=self.uow.validate_restore(seller_id,lot)
  if reason:return AuctionResult(False,reason,lot)
  changed=replace(lot,status=LotStatus.EXPIRED_CLAIMED)
  try:self.uow.restore_item(seller_id,lot);self.uow.save(changed);self.uow.history(lot_id,"expiry_claimed");self.uow.commit()
  except Exception:self.uow.rollback();raise
  return AuctionResult(True,lot=changed,changed=True,transfer_required=True)
class MemoryAuctionUow:
 def __init__(self,lots=()):self.rows={x.lot_id:x for x in lots};self.events=[];self.consumed=[];self.restored=[];self.purchases=[];self.commits=0;self.rollbacks=0;self.listing_error=None;self.purchase_error=None;self.restore_error=None
 def lot(self,i):return self.rows.get(i)
 def lots(self):return tuple(self.rows.values())
 def save(self,x):self.rows[x.lot_id]=x
 def active_count(self,u):return sum(x.seller_user_id==u and x.status is LotStatus.ACTIVE for x in self.rows.values())
 def validate_listing(self,u,s):return self.listing_error
 def consume_listing(self,s):self.consumed.append(s.inventory_id)
 def validate_purchase(self,u,l):return self.purchase_error
 def apply_purchase(self,u,l):self.purchases.append((u,l.lot_id))
 def validate_restore(self,u,l):return self.restore_error
 def restore_item(self,u,l):self.restored.append((u,l.lot_id))
 def history(self,l,e):
  key=(l,e)
  if key not in self.events:self.events.append(key)
 def commit(self):self.commits+=1
 def rollback(self):self.rollbacks+=1
