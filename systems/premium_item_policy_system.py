# -*- coding: utf-8 -*-
"""Canonical source policy for character-bound premium inventory grants."""
from __future__ import annotations
import json, os, sqlite3
from datetime import datetime, timezone
from pathlib import Path
DB_PATH=Path(__file__).resolve().parents[1]/'game.db'
SOURCE_DEV='dev_command';SOURCE_SHOP='crystal_shop';SOURCE_MILESTONE='level_milestone_reward';SOURCE_ADMIN='admin_compensation'
PREMIUM_ITEM_POLICY={
 301:{'name':'Сфера нового шляху','ownership':'character_bound','resethero':'delete','allowed_sources':frozenset((SOURCE_DEV,SOURCE_SHOP,SOURCE_MILESTONE,SOURCE_ADMIN)),'milestone_levels':frozenset((5,10))},
 402:{'name':'Руна Успіху','ownership':'character_bound','resethero':'delete','allowed_sources':frozenset((SOURCE_DEV,SOURCE_SHOP,SOURCE_ADMIN)),'milestone_levels':frozenset()},
 528:{'name':'Досконалий Екстрактор','ownership':'character_bound','resethero':'delete','allowed_sources':frozenset((SOURCE_DEV,SOURCE_SHOP,SOURCE_ADMIN)),'milestone_levels':frozenset()},
 10000:{'name':'Руна імені','ownership':'character_bound','resethero':'delete','allowed_sources':frozenset((SOURCE_DEV,SOURCE_SHOP,SOURCE_ADMIN)),'milestone_levels':frozenset()},
}
DENIED_TRANSFER_ITEM_IDS=frozenset(PREMIUM_ITEM_POLICY)

def _utc():return datetime.now(timezone.utc).isoformat()
def _conn(db_path=None):
 c=sqlite3.connect(str(db_path or DB_PATH),timeout=30);c.row_factory=sqlite3.Row;c.execute('PRAGMA foreign_keys=ON');c.execute('PRAGMA busy_timeout=30000');return c
def _dev_enabled(value=None):
 if value is not None:return bool(value)
 return str(os.getenv('DEV_MODE','false')).strip().lower()=='true'
def init_premium_item_policy(db_path=None):
 c=_conn(db_path)
 try:
  c.executescript("""
  CREATE TABLE IF NOT EXISTS premium_item_grants(
   id INTEGER PRIMARY KEY AUTOINCREMENT,user_id INTEGER NOT NULL,item_id INTEGER NOT NULL,quantity INTEGER NOT NULL CHECK(quantity>0),
   source TEXT NOT NULL,idempotency_key TEXT NOT NULL UNIQUE,external_reference TEXT,metadata_json TEXT NOT NULL DEFAULT '{}',created_at TEXT NOT NULL,
   FOREIGN KEY(user_id) REFERENCES users(user_id) ON DELETE CASCADE,FOREIGN KEY(item_id) REFERENCES items(id) ON DELETE RESTRICT
  );
  CREATE INDEX IF NOT EXISTS ix_premium_item_grants_user_created ON premium_item_grants(user_id,id DESC);
  CREATE INDEX IF NOT EXISTS ix_premium_item_grants_item_source ON premium_item_grants(item_id,source,id DESC);
  """);c.commit();return {'success':True}
 finally:c.close()
def get_premium_item_policy(item_id):
 p=PREMIUM_ITEM_POLICY.get(int(item_id));return None if p is None else {**p,'allowed_sources':sorted(p['allowed_sources']),'milestone_levels':sorted(p['milestone_levels'])}
def can_grant_item_from_source(user_id,item_id,quantity,source,*,milestone_level=None,dev_mode=None,db_path=None):
 try:uid=int(user_id);iid=int(item_id);qty=int(quantity)
 except Exception:return {'success':False,'reason':'invalid_arguments','message':'Некоректні параметри видачі.'}
 policy=PREMIUM_ITEM_POLICY.get(iid);src=str(source or '').strip()
 if not policy:return {'success':False,'reason':'not_premium_catalog_item','message':'Предмет відсутній у premium policy.'}
 if qty<=0:return {'success':False,'reason':'invalid_quantity','message':'Кількість має бути більшою за нуль.'}
 if src not in policy['allowed_sources']:return {'success':False,'reason':'source_denied','message':'Це джерело видачі заборонене для предмета.'}
 if src==SOURCE_DEV and not _dev_enabled(dev_mode):return {'success':False,'reason':'dev_mode_required','message':'DEV-видача вимкнена у цьому середовищі.'}
 if src==SOURCE_MILESTONE:
  try:level=int(milestone_level)
  except Exception:return {'success':False,'reason':'milestone_level_required','message':'Потрібно вказати milestone-рівень.'}
  if level not in policy['milestone_levels']:return {'success':False,'reason':'milestone_denied','message':'Цей milestone не дозволений для предмета.'}
 c=_conn(db_path)
 try:
  if not c.execute('SELECT 1 FROM users WHERE user_id=?',(uid,)).fetchone():return {'success':False,'reason':'user_missing','message':'Акаунт не знайдено.'}
  if not c.execute('SELECT 1 FROM items WHERE id=?',(iid,)).fetchone():return {'success':False,'reason':'item_missing','message':'Предмет не знайдено.'}
 finally:c.close()
 return {'success':True,'user_id':uid,'item_id':iid,'quantity':qty,'source':src,'milestone_level':milestone_level,'policy':get_premium_item_policy(iid)}
def _inventory_columns(c):return {r[1] for r in c.execute('PRAGMA table_info(inventory)')}
def _grant_stack(c,uid,iid,qty):
 cols=_inventory_columns(c);row=c.execute('SELECT id,quantity FROM inventory WHERE user_id=? AND item_id=? ORDER BY id LIMIT 1',(uid,iid)).fetchone()
 if row:c.execute('UPDATE inventory SET quantity=quantity+? WHERE id=?',(qty,int(row['id'])));return int(row['id'])
 names=['user_id','item_id','quantity'];values=[uid,iid,qty]
 if 'durability' in cols:names.append('durability');values.append(None)
 if 'max_durability' in cols:names.append('max_durability');values.append(None)
 if 'refine_level' in cols:names.append('refine_level');values.append(0)
 cur=c.execute('INSERT INTO inventory('+','.join(names)+') VALUES('+','.join('?' for _ in names)+')',values);return int(cur.lastrowid)
def grant_item_from_source(user_id,item_id,quantity,source,idempotency_key,*,external_reference=None,metadata=None,milestone_level=None,dev_mode=None,db_path=None):
 check=can_grant_item_from_source(user_id,item_id,quantity,source,milestone_level=milestone_level,dev_mode=dev_mode,db_path=db_path)
 if not check['success']:return check
 key=str(idempotency_key or '').strip()
 if not key:return {'success':False,'reason':'idempotency_required','message':'idempotency_key є обов’язковим.'}
 c=_conn(db_path)
 try:
  c.execute('BEGIN IMMEDIATE');existing=c.execute('SELECT * FROM premium_item_grants WHERE idempotency_key=?',(key,)).fetchone()
  if existing:c.commit();return {'success':True,'idempotent_replay':True,'grant':dict(existing)}
  payload=dict(metadata or {})
  if milestone_level is not None:payload['milestone_level']=int(milestone_level)
  inventory_id=_grant_stack(c,check['user_id'],check['item_id'],check['quantity']);now=_utc()
  cur=c.execute('INSERT INTO premium_item_grants(user_id,item_id,quantity,source,idempotency_key,external_reference,metadata_json,created_at) VALUES(?,?,?,?,?,?,?,?)',(check['user_id'],check['item_id'],check['quantity'],check['source'],key,external_reference,json.dumps(payload,ensure_ascii=False,sort_keys=True,separators=(',',':')),now));grant_id=int(cur.lastrowid);c.commit()
  return {'success':True,'idempotent_replay':False,'grant_id':grant_id,'inventory_id':inventory_id,**check}
 except sqlite3.IntegrityError:
  c.rollback();row=c.execute('SELECT * FROM premium_item_grants WHERE idempotency_key=?',(key,)).fetchone()
  if row:return {'success':True,'idempotent_replay':True,'grant':dict(row)}
  raise
 except Exception:c.rollback();raise
 finally:c.close()
def get_premium_item_grants(user_id,page=0,page_size=20,db_path=None):
 c=_conn(db_path)
 try:return [dict(r) for r in c.execute('SELECT * FROM premium_item_grants WHERE user_id=? ORDER BY id DESC LIMIT ? OFFSET ?',(int(user_id),max(1,min(100,int(page_size))),max(0,int(page))*max(1,min(100,int(page_size))))).fetchall()]
 finally:c.close()
