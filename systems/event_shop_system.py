# -*- coding: utf-8 -*-
"""Atomic server-authoritative event exchange service."""
from datetime import datetime,timezone

def _key(value,name):
 value=str(value or "").strip()
 if not value: raise ValueError(f"{name} must be non-empty")
 return value

def _offer(event_key,offer_key):
 import events
 events.load_event_modules()
 for module in events.get_registered_events():
  if module.config.EVENT_KEY!=event_key: continue
  provider=getattr(module,"get_shop_offers",None)
  for offer in (() if provider is None else provider()):
   if str(offer.get("offer_key"))==offer_key: return module,offer
 raise ValueError("event shop offer not found")

def _reserved(conn,user_id,item_id):
 if not conn.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='inventory_reservations'").fetchone(): return 0
 columns={r[1] for r in conn.execute("PRAGMA table_info(inventory_reservations)")}
 if not {"inventory_id","quantity"}.issubset(columns): return 0
 return int(conn.execute("""SELECT COALESCE(SUM(r.quantity),0) FROM inventory_reservations r
 JOIN inventory i ON i.id=r.inventory_id WHERE i.user_id=? AND i.item_id=? AND COALESCE(r.quantity,0)>0""",(user_id,item_id)).fetchone()[0] or 0)

def _consume(conn,user_id,item_id,quantity):
 remaining=quantity
 for row_id,current in conn.execute("SELECT id,quantity FROM inventory WHERE user_id=? AND item_id=? ORDER BY id",(user_id,item_id)).fetchall():
  take=min(remaining,int(current or 0)); new=int(current or 0)-take
  if new: conn.execute("UPDATE inventory SET quantity=? WHERE id=?",(new,row_id))
  else: conn.execute("DELETE FROM inventory WHERE id=?",(row_id,))
  remaining-=take
  if remaining==0: break
 if remaining: raise RuntimeError("insufficient quantity during debit")

def _award(conn,user_id,item_id,quantity):
 max_stack=int(conn.execute("SELECT COALESCE(max_stack,1) FROM items WHERE id=?",(item_id,)).fetchone()[0] or 1)
 partial=conn.execute("SELECT id,quantity FROM inventory WHERE user_id=? AND item_id=? AND quantity<? ORDER BY id",(user_id,item_id,max_stack)).fetchall()
 free=sum(max_stack-int(r[1] or 0) for r in partial); needed=max(0,quantity-free); new_stacks=(needed+max_stack-1)//max_stack
 capacity=int(conn.execute("SELECT COALESCE(bag_slots,60) FROM users WHERE user_id=?",(user_id,)).fetchone()[0] or 60); used=int(conn.execute("SELECT COUNT(*) FROM inventory WHERE user_id=?",(user_id,)).fetchone()[0])
 if used+new_stacks>capacity: raise ValueError("bag_full")
 remaining=quantity
 for row_id,current in partial:
  moved=min(remaining,max_stack-int(current or 0)); conn.execute("UPDATE inventory SET quantity=? WHERE id=?",(int(current or 0)+moved,row_id)); remaining-=moved
  if not remaining: break
 while remaining:
  amount=min(remaining,max_stack); conn.execute("INSERT INTO inventory(user_id,item_id,quantity,durability) VALUES(?,?,?,NULL)",(user_id,item_id,amount)); remaining-=amount

def exchange_event_shop_offer(conn,event_key,user_id,offer_key,idempotency_key,*,event_active=False,now=None):
 event_key=_key(event_key,"event_key"); offer_key=_key(offer_key,"offer_key"); idem=_key(idempotency_key,"idempotency_key"); user_id=int(user_id)
 module,offer=_offer(event_key,offer_key)
 if not event_active or not module.config.ENABLED: return {"success":False,"reason":"event_inactive"}
 if offer.get("operation_kind")!="exchange" or offer.get("reward_kind")!="static_item": raise ValueError("unsupported event shop operation")
 existing=conn.execute("SELECT id FROM event_shop_transactions WHERE idempotency_key=?",(idem,)).fetchone()
 if existing: return {"success":True,"duplicate":True,"transaction_id":int(existing[0])}
 cost_id=int(offer["cost_item_id"]); cost_q=int(offer["cost_quantity"]); reward_id=int(offer["reward_item_id"]); reward_q=int(offer["reward_quantity"])
 conn.execute("SAVEPOINT event_exchange")
 try:
  total=int(conn.execute("SELECT COALESCE(SUM(quantity),0) FROM inventory WHERE user_id=? AND item_id=?",(user_id,cost_id)).fetchone()[0] or 0)
  if total-_reserved(conn,user_id,cost_id)<cost_q: raise ValueError("insufficient_unreserved_currency")
  _award(conn,user_id,reward_id,reward_q); _consume(conn,user_id,cost_id,cost_q)
  cur=conn.execute("""INSERT INTO event_shop_transactions(idempotency_key,event_key,user_id,offer_key,operation_kind,reward_kind,cost_item_id,cost_quantity,reward_item_id,reward_quantity,created_at) VALUES(?,?,?,?,?,?,?,?,?,?,?)""",(idem,event_key,user_id,offer_key,"exchange","static_item",cost_id,cost_q,reward_id,reward_q,(now or datetime.now(timezone.utc)).isoformat()))
  conn.execute("RELEASE event_exchange"); return {"success":True,"duplicate":False,"transaction_id":int(cur.lastrowid)}
 except Exception:
  conn.execute("ROLLBACK TO event_exchange"); conn.execute("RELEASE event_exchange"); raise
