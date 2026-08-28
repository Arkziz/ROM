# -*- coding: utf-8 -*-
from __future__ import annotations
import json,sqlite3
from datetime import datetime,timedelta,timezone
from pathlib import Path
DB_PATH=Path(__file__).resolve().parents[1]/'game.db';BONUS_PERCENT=25
PLANS={15:70,30:120}
def _utc():return datetime.now(timezone.utc)
def _parse(v):
 try:return datetime.fromisoformat(str(v).replace('Z','+00:00')).astimezone(timezone.utc)
 except Exception:return None
def _conn(path=None):
 c=sqlite3.connect(str(path or DB_PATH),timeout=30);c.row_factory=sqlite3.Row;c.execute('PRAGMA foreign_keys=ON');c.execute('PRAGMA busy_timeout=30000');return c
def init_timed_exp_bonus_system(db_path=None):
 c=_conn(db_path)
 try:
  c.executescript("""CREATE TABLE IF NOT EXISTS account_exp_bonus_entitlements(user_id INTEGER PRIMARY KEY,bonus_percent INTEGER NOT NULL DEFAULT 25 CHECK(bonus_percent=25),expires_at TEXT NOT NULL,created_at TEXT NOT NULL,updated_at TEXT NOT NULL,FOREIGN KEY(user_id) REFERENCES users(user_id) ON DELETE CASCADE);CREATE TABLE IF NOT EXISTS exp_bonus_purchases(id INTEGER PRIMARY KEY AUTOINCREMENT,user_id INTEGER NOT NULL,product_code TEXT NOT NULL,duration_days INTEGER NOT NULL CHECK(duration_days IN (15,30)),bonus_percent INTEGER NOT NULL CHECK(bonus_percent=25),price_crystals INTEGER NOT NULL,balance_before INTEGER NOT NULL,balance_after INTEGER NOT NULL,expires_at_before TEXT,expires_at_after TEXT NOT NULL,crystal_transaction_id INTEGER NOT NULL UNIQUE,idempotency_key TEXT NOT NULL UNIQUE,created_at TEXT NOT NULL,FOREIGN KEY(user_id) REFERENCES users(user_id) ON DELETE RESTRICT,FOREIGN KEY(crystal_transaction_id) REFERENCES crystal_transactions(id) ON DELETE RESTRICT);CREATE INDEX IF NOT EXISTS ix_exp_bonus_purchases_user ON exp_bonus_purchases(user_id,id DESC);""");c.commit();return {'success':True}
 finally:c.close()
def get_exp_bonus_status(user_id,db_path=None,now=None):
 c=_conn(db_path)
 try:
  row=c.execute('SELECT * FROM account_exp_bonus_entitlements WHERE user_id=?',(int(user_id),)).fetchone();dt=_parse(row['expires_at']) if row else None;n=now or _utc();active=bool(dt and dt>n);return {'active':active,'bonus_percent':25 if active else 0,'expires_at':dt.isoformat() if dt else None}
 finally:c.close()
def calculate_mob_kill_exp(user_id,base_exp,db_path=None,now=None):
 base=max(0,int(base_exp));st=get_exp_bonus_status(user_id,db_path,now);bonus=(base*25)//100 if st['active'] else 0;return {'active':st['active'],'base_exp':base,'bonus_exp':bonus,'final_exp':base+bonus,'expires_at':st['expires_at']}
def preview_exp_bonus_purchase(user_id,duration_days,db_path=None,now=None):
 days=int(duration_days);price=PLANS.get(days)
 if not price:return {'success':False,'message':'❌ Невідомий тариф.'}
 c=_conn(db_path)
 try:
  wallet=c.execute('SELECT balance FROM crystal_wallets WHERE user_id=?',(int(user_id),)).fetchone();balance=int(wallet[0]) if wallet else 0;n=now or _utc();st=get_exp_bonus_status(user_id,db_path,n);old=_parse(st['expires_at']);base=old if old and old>n else n;new=base+timedelta(days=days);return {'success':balance>=price,'duration_days':days,'price':price,'balance':balance,'balance_after':balance-price,'expires_at_before':old.isoformat() if old else None,'expires_at_after':new.isoformat(),'message':'OK' if balance>=price else '❌ Недостатньо кристалів.'}
 finally:c.close()
def purchase_exp_bonus(user_id,duration_days,idempotency_key,db_path=None,now=None):
 uid=int(user_id);days=int(duration_days);price=PLANS.get(days);key=str(idempotency_key or '').strip()
 if not price or not key:return {'success':False,'message':'❌ Некоректна покупка.'}
 c=_conn(db_path)
 try:
  c.execute('BEGIN IMMEDIATE');old=c.execute('SELECT * FROM exp_bonus_purchases WHERE idempotency_key=?',(key,)).fetchone()
  if old:c.commit();return {'success':True,'idempotent_replay':True,'purchase':dict(old),'balance':int(old['balance_after']),'expires_at_after':old['expires_at_after']}
  wallet=c.execute('SELECT balance FROM crystal_wallets WHERE user_id=?',(uid,)).fetchone()
  if not wallet:c.rollback();return {'success':False,'message':'❌ Гаманець не знайдено.'}
  before=int(wallet[0])
  if before<price:c.rollback();return {'success':False,'message':'❌ Недостатньо кристалів.'}
  n=now or _utc();ent=c.execute('SELECT expires_at,created_at FROM account_exp_bonus_entitlements WHERE user_id=?',(uid,)).fetchone();old_exp=_parse(ent['expires_at']) if ent else None;base=old_exp if old_exp and old_exp>n else n;new_exp=base+timedelta(days=days);after=before-price;stamp=n.isoformat()
  if c.execute('UPDATE crystal_wallets SET balance=?,updated_at=? WHERE user_id=? AND balance=?',(after,stamp,uid,before)).rowcount!=1:raise RuntimeError('wallet changed concurrently')
  txkey='exp_bonus:debit:'+key;cur=c.execute("INSERT INTO crystal_transactions(user_id,operation,amount,reason_code,balance_before,balance_after,idempotency_key,external_reference,metadata_json,created_at) VALUES(?,?,?,?,?,?,?,?,?,?)",(uid,'debit',price,'timed_exp_bonus_purchase',before,after,txkey,key,json.dumps({'duration_days':days,'bonus_percent':25},sort_keys=True),stamp));txid=int(cur.lastrowid)
  if ent:c.execute('UPDATE account_exp_bonus_entitlements SET bonus_percent=25,expires_at=?,updated_at=? WHERE user_id=?',(new_exp.isoformat(),stamp,uid))
  else:c.execute('INSERT INTO account_exp_bonus_entitlements(user_id,bonus_percent,expires_at,created_at,updated_at) VALUES(?,?,?,?,?)',(uid,25,new_exp.isoformat(),stamp,stamp))
  code=f'exp25_{days}d';cur=c.execute('INSERT INTO exp_bonus_purchases(user_id,product_code,duration_days,bonus_percent,price_crystals,balance_before,balance_after,expires_at_before,expires_at_after,crystal_transaction_id,idempotency_key,created_at) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)',(uid,code,days,25,price,before,after,old_exp.isoformat() if old_exp else None,new_exp.isoformat(),txid,key,stamp));pid=int(cur.lastrowid);c.commit();return {'success':True,'idempotent_replay':False,'purchase_id':pid,'duration_days':days,'price':price,'balance':after,'expires_at_after':new_exp.isoformat()}
 except Exception as e:
  c.rollback();return {'success':False,'message':f'❌ Покупку скасовано без списання: {e}'}
 finally:c.close()

# ROM Stage 17.30.1.1 account presentation helpers.
def get_exp_bonus_account_summary(user_id, db_path=None, now=None):
    uid = int(user_id)
    status = get_exp_bonus_status(uid, db_path=db_path, now=now)
    connection = _conn(db_path)
    try:
        columns = {str(row[1]) for row in connection.execute("PRAGMA table_info(users)")}
        registration_value = None
        registration_column = None
        for candidate in ("registered_at", "created_at", "registration_date", "registered_date"):
            if candidate in columns:
                registration_column = candidate
                row = connection.execute(f"SELECT {candidate} FROM users WHERE user_id=?", (uid,)).fetchone()
                registration_value = row[0] if row else None
                break
        registration_dt = _parse(registration_value) if registration_value else None
        return {
            "user_id": uid,
            "active": bool(status["active"]),
            "bonus_percent": int(status["bonus_percent"]),
            "expires_at": status["expires_at"],
            "registered_at": registration_dt.isoformat() if registration_dt else None,
            "registration_column": registration_column,
        }
    finally:
        connection.close()

