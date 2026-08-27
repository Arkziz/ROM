# -*- coding: utf-8 -*-
"""Account-level crystal wallet with an append-only, idempotent SQLite ledger."""
from __future__ import annotations
import json, sqlite3
from datetime import datetime, timezone
from pathlib import Path
DB_PATH=Path(__file__).resolve().parents[1]/"game.db"
CRYSTAL_HISTORY_PAGE_SIZE=10

def _utc():return datetime.now(timezone.utc).isoformat()
def _connect(db_path=None):
 c=sqlite3.connect(str(db_path or DB_PATH),timeout=30);c.row_factory=sqlite3.Row;c.execute('PRAGMA foreign_keys=ON');c.execute('PRAGMA busy_timeout=30000');return c
def init_crystal_wallet_system(db_path=None):
 c=_connect(db_path)
 try:
  c.executescript("""
  CREATE TABLE IF NOT EXISTS crystal_wallets(
   user_id INTEGER PRIMARY KEY,
   balance INTEGER NOT NULL DEFAULT 0 CHECK(balance>=0),
   created_at TEXT NOT NULL,
   updated_at TEXT NOT NULL,
   FOREIGN KEY(user_id) REFERENCES users(user_id) ON DELETE RESTRICT
  );
  CREATE TABLE IF NOT EXISTS crystal_transactions(
   id INTEGER PRIMARY KEY AUTOINCREMENT,
   user_id INTEGER NOT NULL,
   operation TEXT NOT NULL CHECK(operation IN ('credit','debit')),
   amount INTEGER NOT NULL CHECK(amount>0),
   reason_code TEXT NOT NULL,
   balance_before INTEGER NOT NULL CHECK(balance_before>=0),
   balance_after INTEGER NOT NULL CHECK(balance_after>=0),
   idempotency_key TEXT NOT NULL UNIQUE,
   external_reference TEXT,
   metadata_json TEXT NOT NULL DEFAULT '{}',
   compensates_transaction_id INTEGER,
   created_at TEXT NOT NULL,
   FOREIGN KEY(user_id) REFERENCES users(user_id) ON DELETE RESTRICT,
   FOREIGN KEY(compensates_transaction_id) REFERENCES crystal_transactions(id) ON DELETE RESTRICT
  );
  CREATE INDEX IF NOT EXISTS ix_crystal_transactions_user_created ON crystal_transactions(user_id,id DESC);
  CREATE INDEX IF NOT EXISTS ix_crystal_transactions_external_reference ON crystal_transactions(external_reference);
  """)
  now=_utc();c.execute("INSERT OR IGNORE INTO crystal_wallets(user_id,balance,created_at,updated_at) SELECT user_id,0,?,? FROM users",(now,now));c.commit()
  return {'success':True,'wallets':c.execute('SELECT COUNT(*) FROM crystal_wallets').fetchone()[0]}
 finally:c.close()
def _ensure_wallet(c,user_id):
 uid=int(user_id);row=c.execute('SELECT user_id FROM users WHERE user_id=?',(uid,)).fetchone()
 if not row:raise ValueError('Акаунт не знайдено. Спочатку натисни /start.')
 now=_utc();c.execute('INSERT OR IGNORE INTO crystal_wallets(user_id,balance,created_at,updated_at) VALUES(?,0,?,?)',(uid,now,now))
def get_crystal_wallet(user_id,db_path=None):
 c=_connect(db_path)
 try:
  c.execute('BEGIN IMMEDIATE');_ensure_wallet(c,user_id);row=c.execute('SELECT user_id,balance,created_at,updated_at FROM crystal_wallets WHERE user_id=?',(int(user_id),)).fetchone();c.commit();return dict(row)
 except Exception:c.rollback();raise
 finally:c.close()
def get_crystal_balance(user_id,db_path=None):return int(get_crystal_wallet(user_id,db_path)['balance'])
def _apply(user_id,amount,operation,reason_code,idempotency_key,external_reference=None,metadata=None,compensates_transaction_id=None,db_path=None):
 uid=int(user_id);amount=int(amount);key=str(idempotency_key or '').strip();reason=str(reason_code or '').strip()
 if amount<=0:return {'success':False,'message':'Кількість кристалів має бути більшою за нуль.'}
 if not key:return {'success':False,'message':'idempotency_key є обов’язковим.'}
 if not reason:return {'success':False,'message':'reason_code є обов’язковим.'}
 c=_connect(db_path)
 try:
  c.execute('BEGIN IMMEDIATE');existing=c.execute('SELECT * FROM crystal_transactions WHERE idempotency_key=?',(key,)).fetchone()
  if existing:
   c.commit();return {'success':True,'idempotent_replay':True,'transaction':dict(existing),'balance':int(existing['balance_after'])}
  _ensure_wallet(c,uid);before=int(c.execute('SELECT balance FROM crystal_wallets WHERE user_id=?',(uid,)).fetchone()[0]);after=before+amount if operation=='credit' else before-amount
  if after<0:c.rollback();return {'success':False,'message':'Недостатньо кристалів.','balance':before}
  now=_utc();changed=c.execute('UPDATE crystal_wallets SET balance=?,updated_at=? WHERE user_id=? AND balance=?',(after,now,uid,before)).rowcount
  if changed!=1:raise RuntimeError('Баланс змінився. Операцію скасовано.')
  payload=json.dumps(metadata or {},ensure_ascii=False,sort_keys=True,separators=(',',':'))
  cur=c.execute('INSERT INTO crystal_transactions(user_id,operation,amount,reason_code,balance_before,balance_after,idempotency_key,external_reference,metadata_json,compensates_transaction_id,created_at) VALUES(?,?,?,?,?,?,?,?,?,?,?)',(uid,operation,amount,reason,before,after,key,external_reference,payload,compensates_transaction_id,now));tid=int(cur.lastrowid);c.commit()
  return {'success':True,'idempotent_replay':False,'transaction_id':tid,'operation':operation,'amount':amount,'balance_before':before,'balance_after':after,'balance':after}
 except sqlite3.IntegrityError:
  c.rollback();row=c.execute('SELECT * FROM crystal_transactions WHERE idempotency_key=?',(key,)).fetchone()
  if row:return {'success':True,'idempotent_replay':True,'transaction':dict(row),'balance':int(row['balance_after'])}
  raise
 except Exception:c.rollback();raise
 finally:c.close()
def credit_crystals(user_id,amount,reason_code,idempotency_key,external_reference=None,metadata=None,db_path=None):return _apply(user_id,amount,'credit',reason_code,idempotency_key,external_reference,metadata,None,db_path)
def debit_crystals(user_id,amount,reason_code,idempotency_key,external_reference=None,metadata=None,db_path=None):return _apply(user_id,amount,'debit',reason_code,idempotency_key,external_reference,metadata,None,db_path)
def get_crystal_transactions(user_id,page=0,page_size=CRYSTAL_HISTORY_PAGE_SIZE,db_path=None):
 page=max(0,int(page));size=max(1,min(50,int(page_size)));c=_connect(db_path)
 try:
  rows=c.execute('SELECT * FROM crystal_transactions WHERE user_id=? ORDER BY id DESC LIMIT ? OFFSET ?',(int(user_id),size,page*size)).fetchall();total=c.execute('SELECT COUNT(*) FROM crystal_transactions WHERE user_id=?',(int(user_id),)).fetchone()[0];return {'items':[dict(x) for x in rows],'page':page,'total':int(total),'has_next':(page+1)*size<int(total)}
 finally:c.close()
def compensate_crystal_transaction(original_transaction_id,idempotency_key,reason_code='dev_compensation',db_path=None):
 c=_connect(db_path)
 try:row=c.execute('SELECT * FROM crystal_transactions WHERE id=?',(int(original_transaction_id),)).fetchone()
 finally:c.close()
 if not row:return {'success':False,'message':'Початкову транзакцію не знайдено.'}
 func=debit_crystals if row['operation']=='credit' else credit_crystals
 result=func(int(row['user_id']),int(row['amount']),reason_code,idempotency_key,external_reference=f"compensates:{int(row['id'])}",metadata={'original_transaction_id':int(row['id'])},db_path=db_path)
 if result.get('success') and not result.get('idempotent_replay'):
  c=_connect(db_path)
  try:c.execute('UPDATE crystal_transactions SET compensates_transaction_id=? WHERE id=? AND compensates_transaction_id IS NULL',(int(row['id']),int(result['transaction_id'])));c.commit()
  finally:c.close()
 return result
