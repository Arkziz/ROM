"""Pure Direct Trade application service and in-memory Unit of Work."""
from __future__ import annotations
from dataclasses import replace
from rom_v2.domain.direct_trade import *
class DirectTradeService:
 def __init__(self,uow):self.uow=uow
 def _eligible(self,trade,user_id):
  if not trade.is_participant(user_id):return "not_participant"
  if not self.uow.online(trade.initiator_id) or not self.uow.online(trade.recipient_id):return "player_offline"
  if self.uow.location(trade.initiator_id)!=trade.location_id or self.uow.location(trade.recipient_id)!=trade.location_id:return "location_changed"
  if self.uow.externally_busy(trade.initiator_id,trade.trade_id) or self.uow.externally_busy(trade.recipient_id,trade.trade_id):return "player_busy"
  return None
 def set_offer(self,trade_id,user_id,offer,expected_revision):
  trade=self.uow.trade(trade_id)
  if trade is None:return TradeResult(False,"trade_not_found")
  if trade.status in TERMINAL_STATUSES:return TradeResult(False,"trade_terminal",trade)
  if not trade.is_participant(user_id):return TradeResult(False,"not_participant",trade)
  if trade.revision!=expected_revision:return TradeResult(False,"stale_revision",trade)
  if offer.owner_user_id!=user_id:return TradeResult(False,"offer_owner_mismatch",trade)
  for item in offer.items:
   reason=item_policy(item)
   if reason:return TradeResult(False,reason,trade)
  if trade.offer_for(user_id)==offer:return TradeResult(True,trade=trade,changed=False)
  changed=trade.invalidate_confirmations()
  changed=replace(changed,initiator_offer=offer) if user_id==trade.initiator_id else replace(changed,recipient_offer=offer)
  self.uow.save(changed);self.uow.commit();return TradeResult(True,trade=changed,changed=True)
 def ready(self,trade_id,user_id,expected_revision):
  trade=self.uow.trade(trade_id)
  if trade is None:return TradeResult(False,"trade_not_found")
  if trade.status in TERMINAL_STATUSES:return TradeResult(False,"trade_terminal",trade)
  if trade.revision!=expected_revision:return TradeResult(False,"stale_revision",trade)
  reason=self._eligible(trade,user_id)
  if reason:return TradeResult(False,reason,trade)
  current=trade.initiator_ready if user_id==trade.initiator_id else trade.recipient_ready
  if current:return TradeResult(True,"already_ready",trade,False)
  changed=replace(trade,initiator_ready=True) if user_id==trade.initiator_id else replace(trade,recipient_ready=True)
  self.uow.save(changed);self.uow.commit();return TradeResult(True,trade=changed,changed=True)
 def return_to_editing(self,trade_id,user_id,expected_revision):
  trade=self.uow.trade(trade_id)
  if trade is None:return TradeResult(False,"trade_not_found")
  if not trade.is_participant(user_id):return TradeResult(False,"not_participant",trade)
  if trade.status in TERMINAL_STATUSES:return TradeResult(False,"trade_terminal",trade)
  if trade.revision!=expected_revision:return TradeResult(False,"stale_revision",trade)
  if not any((trade.initiator_ready,trade.recipient_ready,trade.initiator_confirmed,trade.recipient_confirmed)):return TradeResult(True,trade=trade,changed=False)
  changed=trade.invalidate_confirmations();self.uow.save(changed);self.uow.commit();return TradeResult(True,trade=changed,changed=True)
 def confirm(self,trade_id,user_id,expected_revision):
  trade=self.uow.trade(trade_id)
  if trade is None:return TradeResult(False,"trade_not_found")
  if trade.status is TradeStatus.COMPLETED:return TradeResult(True,"already_completed",trade,False)
  if trade.status in {TradeStatus.CANCELLED,TradeStatus.EXPIRED}:return TradeResult(False,"trade_terminal",trade)
  if trade.revision!=expected_revision:return TradeResult(False,"stale_revision",trade)
  reason=self._eligible(trade,user_id)
  if reason:return TradeResult(False,reason,trade)
  if not trade.initiator_ready or not trade.recipient_ready:return TradeResult(False,"not_ready",trade)
  already=trade.initiator_confirmed if user_id==trade.initiator_id else trade.recipient_confirmed
  if already:return TradeResult(True,"already_confirmed",trade,False,trade.initiator_confirmed and trade.recipient_confirmed)
  changed=replace(trade,initiator_confirmed=True) if user_id==trade.initiator_id else replace(trade,recipient_confirmed=True)
  settle=changed.initiator_confirmed and changed.recipient_confirmed
  if settle:
   reason=self.uow.validate_settlement(changed)
   if reason:return TradeResult(False,reason,trade)
   try:
    self.uow.apply_settlement(changed);changed=replace(changed,status=TradeStatus.COMPLETED);self.uow.save(changed);self.uow.release(changed.trade_id);self.uow.commit()
   except Exception:self.uow.rollback();raise
  else:self.uow.save(changed);self.uow.commit()
  return TradeResult(True,trade=changed,changed=True,settlement_required=settle)
 def cancel(self,trade_id,user_id,reason="user_cancelled"):
  trade=self.uow.trade(trade_id)
  if trade is None:return TradeResult(False,"trade_not_found")
  if not trade.is_participant(user_id):return TradeResult(False,"not_participant",trade)
  if trade.status is TradeStatus.COMPLETED:return TradeResult(False,"already_completed",trade)
  if trade.status in {TradeStatus.CANCELLED,TradeStatus.EXPIRED}:return TradeResult(True,"already_terminal",trade,False)
  changed=replace(trade,status=TradeStatus.CANCELLED);self.uow.save(changed);self.uow.release(trade_id);self.uow.record_terminal(trade_id,reason);self.uow.commit();return TradeResult(True,trade=changed,changed=True)
 def recover(self):
  out=[]
  for trade in self.uow.active_trades():
   if self.uow.expired(trade.trade_id):
    changed=replace(trade,status=TradeStatus.EXPIRED);self.uow.save(changed);self.uow.release(trade.trade_id);self.uow.record_terminal(trade.trade_id,"restart_expired");out.append((trade.trade_id,"expired"))
   else:
    changed=trade.invalidate_confirmations() if any((trade.initiator_ready,trade.recipient_ready,trade.initiator_confirmed,trade.recipient_confirmed)) else trade
    self.uow.save(changed);self.uow.reconcile_session(changed);out.append((trade.trade_id,"preserved"))
  self.uow.commit();return tuple(out)
class MemoryDirectTradeUow:
 def __init__(self,trades,locations,online=None):self.trades={t.trade_id:t for t in trades};self.locations=dict(locations);self.online_users=set(locations if online is None else online);self.busy=set();self.expired_ids=set();self.releases=[];self.settlements=[];self.terminals=[];self.sessions=[];self.commits=0;self.rollbacks=0;self.settlement_error=None
 def trade(self,i):return self.trades.get(i)
 def save(self,t):self.trades[t.trade_id]=t
 def online(self,u):return u in self.online_users
 def location(self,u):return self.locations.get(u)
 def externally_busy(self,u,trade_id):return u in self.busy
 def validate_settlement(self,t):return self.settlement_error
 def apply_settlement(self,t):self.settlements.append(t.trade_id)
 def release(self,t):self.releases.append(t)
 def record_terminal(self,t,r):self.terminals.append((t,r))
 def active_trades(self):return tuple(t for t in self.trades.values() if t.status not in TERMINAL_STATUSES)
 def expired(self,t):return t in self.expired_ids
 def reconcile_session(self,t):self.sessions.append(t.trade_id)
 def commit(self):self.commits+=1
 def rollback(self):self.rollbacks+=1
