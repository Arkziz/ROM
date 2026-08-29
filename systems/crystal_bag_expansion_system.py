# -*- coding: utf-8 -*-
"""Account-level, atomic and idempotent crystal bag expansion."""
from __future__ import annotations
import json, sqlite3
from datetime import datetime, timezone
from pathlib import Path
DB_PATH=Path(__file__).resolve().parents[1]/'game.db'
BASE_BAG_CAPACITY=60
MAX_BAG_CAPACITY=100
BAG_EXPANSION_TIERS={60:{'target_capacity':80,'price':75},80:{'target_capacity':100,'price':150}}
def _utc():return datetime.now(timezone.utc).isoformat()
def _connect(path=None):
 c=sqlite3.connect(str(path or DB_PATH),timeout=30);c.row_factory=sqlite3.Row;c.execute('PRAGMA foreign_keys=ON');c.execute('PRAGMA busy_timeout=30000');return c
def init_crystal_bag_expansion_system(db_path=None):
 c=_connect(db_path)
 try:
  c.executescript("""CREATE TABLE IF NOT EXISTS account_bag_expansion_purchases(id INTEGER PRIMARY KEY AUTOINCREMENT,user_id INTEGER NOT NULL,from_capacity INTEGER NOT NULL,to_capacity INTEGER NOT NULL,crystal_price INTEGER NOT NULL,balance_before INTEGER NOT NULL,balance_after INTEGER NOT NULL,idempotency_key TEXT NOT NULL UNIQUE,crystal_transaction_id INTEGER NOT NULL UNIQUE,created_at TEXT NOT NULL,UNIQUE(user_id,to_capacity),FOREIGN KEY(user_id) REFERENCES users(user_id) ON DELETE RESTRICT,FOREIGN KEY(crystal_transaction_id) REFERENCES crystal_transactions(id) ON DELETE RESTRICT);CREATE INDEX IF NOT EXISTS ix_account_bag_expansion_user ON account_bag_expansion_purchases(user_id,id DESC);""");c.commit();return {'success':True}
 finally:c.close()
def _state(c,user_id):
 user=c.execute('SELECT COALESCE(bag_slots,60) AS bag_slots FROM users WHERE user_id=?',(int(user_id),)).fetchone()
 if not user:return None
 capacity=max(BASE_BAG_CAPACITY,int(user['bag_slots'] or BASE_BAG_CAPACITY));wallet=c.execute('SELECT balance FROM crystal_wallets WHERE user_id=?',(int(user_id),)).fetchone();balance=int(wallet['balance']) if wallet else 0;tier=BAG_EXPANSION_TIERS.get(capacity)
 return {'user_id':int(user_id),'current_capacity':capacity,'maximum_capacity':MAX_BAG_CAPACITY,'balance':balance,'next_capacity':tier['target_capacity'] if tier else None,'price':tier['price'] if tier else None,'maximum_reached':capacity>=MAX_BAG_CAPACITY,'supported_capacity':capacity in BAG_EXPANSION_TIERS or capacity>=MAX_BAG_CAPACITY}
def get_crystal_bag_expansion_state(user_id,db_path=None):
 c=_connect(db_path)
 try:return _state(c,user_id)
 finally:c.close()
def preview_crystal_bag_expansion(user_id,db_path=None):
 state=get_crystal_bag_expansion_state(user_id,db_path)
 if not state:return {'success':False,'message':'❌ Користувача не знайдено.'}
 if state['maximum_reached']:return {**state,'success':False,'message':f"🎒 Сумка вже має максимальну місткість: {state['current_capacity']} слотів."}
 if not state['supported_capacity']:return {**state,'success':False,'message':'❌ Поточний рівень сумки не підтримує автоматичне розширення.'}
 ok=state['balance']>=state['price'];return {**state,'success':ok,'balance_after':state['balance']-state['price'],'message':'OK' if ok else '❌ Недостатньо кристалів.'}
def purchase_crystal_bag_expansion(user_id,target_capacity,idempotency_key,db_path=None):
 uid=int(user_id);target=int(target_capacity);key=str(idempotency_key or '').strip()
 if not key:return {'success':False,'message':'❌ Відсутній ключ операції.'}
 c=_connect(db_path)
 try:
  c.execute('BEGIN IMMEDIATE')
  previous=c.execute('SELECT * FROM account_bag_expansion_purchases WHERE idempotency_key=?',(key,)).fetchone()
  if previous:
   c.commit();row=dict(previous);row.update({'success':True,'idempotent_replay':True,'current_capacity':int(row['to_capacity']),'balance':int(row['balance_after'])});return row
  state=_state(c,uid)
  if not state:c.rollback();return {'success':False,'message':'❌ Користувача не знайдено.'}
  if state['maximum_reached']:c.rollback();return {**state,'success':False,'message':f"🎒 Сумка вже має максимальну місткість: {state['current_capacity']} слотів."}
  tier=BAG_EXPANSION_TIERS.get(state['current_capacity'])
  if not tier or target!=tier['target_capacity']:c.rollback();return {**state,'success':False,'message':'❌ Доступне лише наступне послідовне розширення сумки.'}
  price=int(tier['price']);before=int(state['balance'])
  if before<price:c.rollback();return {**state,'success':False,'message':'❌ Недостатньо кристалів.'}
  after=before-price;now=_utc();txkey='bag_expansion:debit:'+key
  tx=c.execute("INSERT INTO crystal_transactions(user_id,operation,amount,reason_code,balance_before,balance_after,idempotency_key,external_reference,metadata_json,created_at) VALUES(?,?,?,?,?,?,?,?,?,?)",(uid,'debit',price,'bag_expansion_purchase',before,after,txkey,key,json.dumps({'from_capacity':state['current_capacity'],'to_capacity':target},sort_keys=True),now));txid=int(tx.lastrowid)
  changed=c.execute('UPDATE crystal_wallets SET balance=?,updated_at=? WHERE user_id=? AND balance=?',(after,now,uid,before)).rowcount
  if changed!=1:raise RuntimeError('wallet concurrent update')
  changed=c.execute('UPDATE users SET bag_slots=? WHERE user_id=? AND COALESCE(bag_slots,60)=?',(target,uid,state['current_capacity'])).rowcount
  if changed!=1:raise RuntimeError('bag capacity concurrent update')
  cur=c.execute('INSERT INTO account_bag_expansion_purchases(user_id,from_capacity,to_capacity,crystal_price,balance_before,balance_after,idempotency_key,crystal_transaction_id,created_at) VALUES(?,?,?,?,?,?,?,?,?)',(uid,state['current_capacity'],target,price,before,after,key,txid,now));pid=int(cur.lastrowid);c.commit();return {'success':True,'idempotent_replay':False,'purchase_id':pid,'transaction_id':txid,'from_capacity':state['current_capacity'],'to_capacity':target,'current_capacity':target,'price':price,'balance_before':before,'balance_after':after,'balance':after}
 except sqlite3.IntegrityError:
  c.rollback();row=c.execute('SELECT * FROM account_bag_expansion_purchases WHERE idempotency_key=?',(key,)).fetchone()
  if row:
   data=dict(row);data.update({'success':True,'idempotent_replay':True,'current_capacity':int(data['to_capacity']),'balance':int(data['balance_after'])});return data
  return {'success':False,'message':'❌ Це розширення вже придбано.'}
 except Exception as error:c.rollback();return {'success':False,'message':f'❌ Покупку не завершено: {error}'}
 finally:c.close()
def get_crystal_bag_expansion_purchases(user_id,db_path=None):
 c=_connect(db_path)
 try:return [dict(row) for row in c.execute('SELECT * FROM account_bag_expansion_purchases WHERE user_id=? ORDER BY id DESC',(int(user_id),)).fetchall()]
 finally:c.close()
