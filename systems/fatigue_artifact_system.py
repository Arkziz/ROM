# -*- coding: utf-8 -*-
from __future__ import annotations
import json,math,sqlite3
from datetime import datetime,timezone
from pathlib import Path
FATIGUE_ARTIFACT_ITEM_ID=50000;MAX_STACK=10;DB_PATH=Path(__file__).resolve().parents[1]/'game.db'
def _conn(path=None):
 c=sqlite3.connect(str(path or DB_PATH),timeout=30);c.row_factory=sqlite3.Row;c.execute('PRAGMA foreign_keys=ON');c.execute('PRAGMA busy_timeout=30000');return c
def init_fatigue_artifact_system(db_path=None):
 c=_conn(db_path)
 try:
  c.executescript("""CREATE TABLE IF NOT EXISTS fatigue_artifact_usage_events(id INTEGER PRIMARY KEY AUTOINCREMENT,user_id INTEGER NOT NULL,inventory_id INTEGER NOT NULL,selected_quantity INTEGER NOT NULL,used_quantity INTEGER NOT NULL,fatigue_before INTEGER NOT NULL,fatigue_after INTEGER NOT NULL,idempotency_key TEXT NOT NULL UNIQUE,created_at TEXT NOT NULL,FOREIGN KEY(user_id) REFERENCES users(user_id) ON DELETE RESTRICT);CREATE INDEX IF NOT EXISTS ix_fatigue_artifact_usage_user ON fatigue_artifact_usage_events(user_id,id DESC);""")
  cols=[r[1] for r in c.execute('PRAGMA table_info(items)')];row=c.execute('SELECT name FROM items WHERE id=?',(FATIGUE_ARTIFACT_ITEM_ID,)).fetchone()
  if row and row[0]!='💠 Артефакт відновлення сил':raise RuntimeError('Item ID 50000 is occupied')
  values={'id':50000,'name':'💠 Артефакт відновлення сил','type':'consumable','rarity':'uncommon','category':'consumable','slot_key':'','weapon_hands':0,'max_stack':10,'sell_price':0,'item_level':1,'is_generated':0,'item_subtype':'fatigue_reducer'}
  if not row:
   names=[k for k in values if k in cols];c.execute('INSERT INTO items('+','.join(names)+') VALUES('+','.join('?' for _ in names)+')',[values[k] for k in names])
  else:c.execute('UPDATE items SET name=?,type=?,category=?,max_stack=?,sell_price=0,item_subtype=? WHERE id=?',('💠 Артефакт відновлення сил','consumable','consumable',10,'fatigue_reducer',50000))
  c.commit();return {'success':True,'item_id':50000}
 finally:c.close()
def _repack(c,user_id,total):
 rows=c.execute('SELECT id FROM inventory WHERE user_id=? AND item_id=? ORDER BY id',(int(user_id),50000)).fetchall();c.execute('DELETE FROM inventory WHERE user_id=? AND item_id=?',(int(user_id),50000));remaining=int(total)
 while remaining>0:
  qty=min(10,remaining);c.execute('INSERT INTO inventory(user_id,item_id,quantity) VALUES(?,?,?)',(int(user_id),50000,qty));remaining-=qty
def add_fatigue_artifacts(user_id,quantity,db_path=None):
 qty=max(0,int(quantity));c=_conn(db_path)
 try:
  c.execute('BEGIN IMMEDIATE');owned=int(c.execute('SELECT COALESCE(SUM(quantity),0) FROM inventory WHERE user_id=? AND item_id=?',(int(user_id),50000)).fetchone()[0]);slots=int(c.execute('SELECT COALESCE(bag_slots,60) FROM users WHERE user_id=?',(int(user_id),)).fetchone()[0]);used=int(c.execute('SELECT COUNT(*) FROM inventory WHERE user_id=?',(int(user_id),)).fetchone()[0]);capacity=max(0,(slots-used)*10 + (10-owned%10 if owned%10 else 0));added=min(qty,capacity);_repack(c,user_id,owned+added);c.commit();return {'success':True,'added':added,'lost':qty-added,'total':owned+added}
 except Exception:c.rollback();raise
 finally:c.close()
def get_total(user_id,db_path=None):
 c=_conn(db_path)
 try:return int(c.execute('SELECT COALESCE(SUM(quantity),0) FROM inventory WHERE user_id=? AND item_id=?',(int(user_id),50000)).fetchone()[0])
 finally:c.close()
def use_fatigue_artifacts(user_id,inventory_id,selected,idempotency_key,db_path=None):
 uid=int(user_id);inv=int(inventory_id);selected=max(1,int(selected));key=str(idempotency_key or '').strip();c=_conn(db_path)
 try:
  c.execute('BEGIN IMMEDIATE');old=c.execute('SELECT * FROM fatigue_artifact_usage_events WHERE idempotency_key=?',(key,)).fetchone()
  if old:c.commit();return {'success':True,'idempotent_replay':True,**dict(old)}
  target=c.execute('SELECT 1 FROM inventory WHERE id=? AND user_id=? AND item_id=?',(inv,uid,50000)).fetchone()
  if not target:c.rollback();return {'success':False,'message':'❌ Предмет більше недоступний.'}
  active=False
  if 'player_activity_sessions' in {r[0] for r in c.execute("SELECT name FROM sqlite_master WHERE type='table'")}:
   cols={r[1] for r in c.execute('PRAGMA table_info(player_activity_sessions)')}
   if 'user_id' in cols and 'activity_type' in cols:
    active=bool(c.execute("SELECT 1 FROM player_activity_sessions WHERE user_id=? AND lower(activity_type) LIKE '%combat%' LIMIT 1",(uid,)).fetchone())
  if active:c.rollback();return {'success':False,'message':'❌ Неможливо використати предмет під час бою.'}
  row=c.execute('SELECT energy FROM users WHERE user_id=?',(uid,)).fetchone();fatigue=max(0,int(row[0] if row else 0))
  if fatigue<=0:c.rollback();return {'success':False,'message':'❌ Персонаж не втомлений. Предмет не використано.'}
  owned=int(c.execute('SELECT COALESCE(SUM(quantity),0) FROM inventory WHERE user_id=? AND item_id=?',(uid,50000)).fetchone()[0]);actual=min(selected,owned,int(math.ceil(fatigue/5.0)));after=max(0,fatigue-actual*5)
  if actual<=0:c.rollback();return {'success':False,'message':'❌ Немає доступних артефактів.'}
  _repack(c,uid,owned-actual);c.execute('UPDATE users SET energy=?,energy_full_notified=? WHERE user_id=?',(after,1 if after<=0 else 0,uid));stamp=datetime.now(timezone.utc).isoformat();c.execute('INSERT INTO fatigue_artifact_usage_events(user_id,inventory_id,selected_quantity,used_quantity,fatigue_before,fatigue_after,idempotency_key,created_at) VALUES(?,?,?,?,?,?,?,?)',(uid,inv,selected,actual,fatigue,after,key,stamp));c.commit();return {'success':True,'idempotent_replay':False,'used_quantity':actual,'fatigue_before':fatigue,'fatigue_after':after,'remaining':owned-actual}
 except Exception as e:c.rollback();return {'success':False,'message':f'❌ Використання скасовано без списання: {e}'}
 finally:c.close()
