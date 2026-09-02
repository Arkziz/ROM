# -*- coding: utf-8 -*-
"""Production-safe admin crystal adjustments with immutable audit records."""
import json, sqlite3
from datetime import datetime, timezone
from pathlib import Path
from config import ROM_ADMIN_USER_IDS, ROM_ADMIN_CRYSTAL_CREDIT_MAX, ROM_ADMIN_CRYSTAL_DEBIT_MAX
DB_PATH=Path(__file__).resolve().parents[1]/"game.db"
def _utc():return datetime.now(timezone.utc).isoformat()
def _connect(db_path=None):
 c=sqlite3.connect(str(db_path or DB_PATH));c.row_factory=sqlite3.Row;return c
def is_admin(user_id):return int(user_id) in ROM_ADMIN_USER_IDS
def init_admin_crystal_credit_system(db_path=None):
 c=_connect(db_path)
 try:
  c.executescript("""CREATE TABLE IF NOT EXISTS admin_crystal_credit_audit(id INTEGER PRIMARY KEY AUTOINCREMENT,admin_user_id INTEGER NOT NULL,target_user_id INTEGER NOT NULL,operation TEXT NOT NULL CHECK(operation IN ('credit','debit')),requested_amount INTEGER NOT NULL CHECK(requested_amount>0),actual_amount INTEGER NOT NULL CHECK(actual_amount>0),balance_before INTEGER NOT NULL CHECK(balance_before>=0),balance_after INTEGER NOT NULL CHECK(balance_after>=0),reason TEXT NOT NULL,idempotency_key TEXT NOT NULL UNIQUE,crystal_transaction_id INTEGER NOT NULL UNIQUE,created_at TEXT NOT NULL,FOREIGN KEY(target_user_id) REFERENCES users(user_id) ON DELETE RESTRICT,FOREIGN KEY(crystal_transaction_id) REFERENCES crystal_transactions(id) ON DELETE RESTRICT);CREATE INDEX IF NOT EXISTS ix_admin_crystal_audit_admin_id ON admin_crystal_credit_audit(admin_user_id,id DESC);CREATE INDEX IF NOT EXISTS ix_admin_crystal_audit_target_id ON admin_crystal_credit_audit(target_user_id,id DESC);""");c.commit()
 finally:c.close()
def preview_admin_adjustment(admin_user_id,target_user_id,operation,requested_amount,reason,db_path=None):
 if not is_admin(admin_user_id):return {'success':False,'message':'Доступ заборонено.'}
 try:target=int(target_user_id);amount=int(requested_amount)
 except Exception:return {'success':False,'message':'ID користувача та сума мають бути цілими числами.'}
 op=str(operation);limit=ROM_ADMIN_CRYSTAL_CREDIT_MAX if op=='credit' else ROM_ADMIN_CRYSTAL_DEBIT_MAX
 if op not in ('credit','debit'):return {'success':False,'message':'Невідома операція.'}
 if amount<1 or amount>limit:return {'success':False,'message':f'Сума має бути від 1 до {limit}.'}
 reason=str(reason or '').strip()
 if not reason:return {'success':False,'message':'Причина є обов’язковою.'}
 c=_connect(db_path)
 try:
  user=c.execute('SELECT user_id FROM users WHERE user_id=?',(target,)).fetchone()
  if not user:return {'success':False,'message':'Користувача не знайдено.'}
  c.execute('INSERT OR IGNORE INTO crystal_wallets(user_id,balance,created_at,updated_at) VALUES(?,0,?,?)',(target,_utc(),_utc()));c.commit();before=int(c.execute('SELECT balance FROM crystal_wallets WHERE user_id=?',(target,)).fetchone()[0])
 finally:c.close()
 actual=amount if op=='credit' else min(amount,before)
 if op=='debit' and actual==0:return {'success':False,'message':'У користувача немає кристалів для вилучення.','balance':0}
 return {'success':True,'admin_user_id':int(admin_user_id),'target_user_id':target,'operation':op,'requested_amount':amount,'actual_amount':actual,'balance_before':before,'balance_after':before+actual if op=='credit' else before-actual,'reason':reason,'clamped':op=='debit' and actual<amount}
def execute_admin_adjustment(admin_user_id,target_user_id,operation,requested_amount,reason,idempotency_key,db_path=None):
 key=str(idempotency_key or '').strip()
 if not key:return {'success':False,'message':'Відсутній idempotency key.'}
 c=_connect(db_path)
 try:
  c.execute('BEGIN IMMEDIATE');existing=c.execute('SELECT * FROM admin_crystal_credit_audit WHERE idempotency_key=?',(key,)).fetchone()
  if existing:c.commit();return {'success':True,'idempotent_replay':True,'audit':dict(existing),'balance':int(existing['balance_after'])}
  if not is_admin(admin_user_id):raise ValueError('Доступ заборонено.')
  target=int(target_user_id);amount=int(requested_amount);op=str(operation);reason=str(reason or '').strip();limit=ROM_ADMIN_CRYSTAL_CREDIT_MAX if op=='credit' else ROM_ADMIN_CRYSTAL_DEBIT_MAX
  if op not in ('credit','debit') or amount<1 or amount>limit or not reason:raise ValueError('Параметри операції більше не валідні.')
  if not c.execute('SELECT 1 FROM users WHERE user_id=?',(target,)).fetchone():raise ValueError('Користувача не знайдено.')
  now=_utc();c.execute('INSERT OR IGNORE INTO crystal_wallets(user_id,balance,created_at,updated_at) VALUES(?,0,?,?)',(target,now,now));before=int(c.execute('SELECT balance FROM crystal_wallets WHERE user_id=?',(target,)).fetchone()[0]);actual=amount if op=='credit' else min(amount,before)
  if actual<=0:raise ValueError('У користувача немає кристалів для вилучення.')
  after=before+actual if op=='credit' else before-actual
  changed=c.execute('UPDATE crystal_wallets SET balance=?,updated_at=? WHERE user_id=? AND balance=?',(after,now,target,before)).rowcount
  if changed!=1:raise RuntimeError('Баланс змінився. Операцію скасовано.')
  txkey='admin:'+key;cur=c.execute('INSERT INTO crystal_transactions(user_id,operation,amount,reason_code,balance_before,balance_after,idempotency_key,external_reference,metadata_json,created_at) VALUES(?,?,?,?,?,?,?,?,?,?)',(target,op,actual,'admin_crystal_'+op,before,after,txkey,key,json.dumps({'admin_operation':True,'requested_amount':amount,'reason':reason},ensure_ascii=False,sort_keys=True),now));txid=int(cur.lastrowid)
  cur=c.execute('INSERT INTO admin_crystal_credit_audit(admin_user_id,target_user_id,operation,requested_amount,actual_amount,balance_before,balance_after,reason,idempotency_key,crystal_transaction_id,created_at) VALUES(?,?,?,?,?,?,?,?,?,?,?)',(int(admin_user_id),target,op,amount,actual,before,after,reason,key,txid,now));aid=int(cur.lastrowid);c.commit();return {'success':True,'idempotent_replay':False,'audit_id':aid,'transaction_id':txid,'operation':op,'requested_amount':amount,'actual_amount':actual,'balance_before':before,'balance_after':after,'balance':after,'clamped':op=='debit' and actual<amount}
 except Exception as e:c.rollback();return {'success':False,'message':f'Операцію скасовано: {e}'}
 finally:c.close()
def get_admin_adjustment_history(admin_user_id,page=0,page_size=10,db_path=None):
 if not is_admin(admin_user_id):return {'success':False,'message':'Доступ заборонено.'}
 size=max(1,min(20,int(page_size)));page=max(0,int(page));c=_connect(db_path)
 try:
  total=int(c.execute('SELECT COUNT(*) FROM admin_crystal_credit_audit').fetchone()[0]);rows=[dict(r) for r in c.execute("SELECT a.*,TRIM(COALESCE(u.character_name,'')) AS character_name FROM admin_crystal_credit_audit a LEFT JOIN users u ON u.user_id=a.target_user_id ORDER BY a.id DESC LIMIT ? OFFSET ?",(size,page*size)).fetchall()];total_pages=max(1,(total+size-1)//size);return {'success':True,'items':rows,'page':page,'page_size':size,'total':total,'total_pages':total_pages,'has_next':page+1<total_pages,'has_previous':page>0}
 finally:c.close()

def get_admin_adjustment_detail(admin_user_id,audit_id,db_path=None):
 if not is_admin(admin_user_id):return {'success':False,'message':'Доступ заборонено.'}
 try:identifier=int(audit_id)
 except Exception:return {'success':False,'message':'Некоректний номер операції.'}
 if identifier<=0:return {'success':False,'message':'Некоректний номер операції.'}
 c=_connect(db_path)
 try:
  row=c.execute("SELECT a.*,TRIM(COALESCE(u.character_name,'')) AS character_name FROM admin_crystal_credit_audit a LEFT JOIN users u ON u.user_id=a.target_user_id WHERE a.id=?",(identifier,)).fetchone()
  return {'success':True,'item':dict(row)} if row else {'success':False,'message':'Операцію не знайдено.'}
 finally:c.close()
