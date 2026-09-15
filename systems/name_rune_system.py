# -*- coding: utf-8 -*-
from __future__ import annotations
import re,sqlite3,unicodedata
from datetime import datetime,timezone
from pathlib import Path
DB_PATH=Path(__file__).resolve().parents[1]/'game.db';NAME_RUNE_ITEM_ID=502;NAME_RUNE_PRICE=50
NAME_RUNE_DESCRIPTION = (
    "Дозволяє один раз змінити ім’я персонажа. "
    "Після успішного перейменування витрачається одна Руна імені. "
    "Нове ім’я має відповідати чинним правилам і не може бути зайняте іншим персонажем."
)
def _conn(path=None):
 c=sqlite3.connect(str(path or DB_PATH),timeout=30);c.row_factory=sqlite3.Row;c.execute('PRAGMA foreign_keys=ON');c.execute('PRAGMA busy_timeout=30000');return c
def normalize_name(value):return unicodedata.normalize('NFKC',str(value or '').strip())
def validate_name(value):
 name=normalize_name(value)
 if len(name)<3 or len(name)>20:return {'success':False,'message':'Ім’я має містити від 3 до 20 символів.'}
 if not re.fullmatch(r"[A-Za-zА-Яа-яІіЇїЄєҐґ0-9'’_-]+",name):return {'success':False,'message':'Ім’я містить недозволені символи.'}
 return {'success':True,'name':name,'key':name.casefold()}
def init_name_rune_system(db_path=None):
 c=_conn(db_path)
 try:
  row=c.execute('SELECT name FROM items WHERE id=?',(NAME_RUNE_ITEM_ID,)).fetchone()
  if row and str(row[0])!='✍️ Руна імені':raise RuntimeError('Item ID 10000 is occupied by another item')
  cols={r[1] for r in c.execute('PRAGMA table_info(items)')};values={'id':502,'name':'✍️ Руна імені','type':'material','rarity':'epic','category':'material','max_stack':10,'sell_price':0,'buy_price':0,'tradeable':0,'premium_bound':1}
  names=[k for k in values if k in cols]
  if not row:c.execute('INSERT INTO items('+','.join(names)+') VALUES('+','.join('?' for _ in names)+')',[values[k] for k in names])
  c.executescript("""CREATE TABLE IF NOT EXISTS character_name_changes(id INTEGER PRIMARY KEY AUTOINCREMENT,user_id INTEGER NOT NULL,old_name TEXT NOT NULL,new_name TEXT NOT NULL,normalized_new_name TEXT NOT NULL,inventory_id INTEGER NOT NULL,item_id INTEGER NOT NULL,idempotency_key TEXT NOT NULL UNIQUE,created_at TEXT NOT NULL,FOREIGN KEY(user_id) REFERENCES users(user_id) ON DELETE CASCADE,FOREIGN KEY(item_id) REFERENCES items(id) ON DELETE RESTRICT);CREATE INDEX IF NOT EXISTS ix_character_name_changes_user ON character_name_changes(user_id,id DESC);""");c.commit();return {'success':True,'item_id':502}
 finally:c.close()
def get_name_rune_inventory(user_id,db_path=None):
 c=_conn(db_path)
 try:
  row=c.execute('SELECT id,quantity FROM inventory WHERE user_id=? AND item_id=? AND quantity>0 ORDER BY id LIMIT 1',(int(user_id),502)).fetchone();return dict(row) if row else None
 finally:c.close()
def preview_name_change(user_id,new_name,db_path=None,inventory_id=None):
 v=validate_name(new_name)
 if not v['success']:return v
 c=_conn(db_path)
 try:
  row=c.execute('SELECT character_name FROM users WHERE user_id=?',(int(user_id),)).fetchone()
  if not row:return {'success':False,'message':'Персонажа не знайдено.'}
  old=str(row[0] or '')
  if normalize_name(old).casefold()==v['key']:return {'success':False,'message':'Нове ім’я збігається з поточним.'}
  for other in c.execute("SELECT user_id,character_name FROM users WHERE user_id<>? AND TRIM(COALESCE(character_name,''))<>''",(int(user_id),)):
   if normalize_name(other['character_name']).casefold()==v['key']:return {'success':False,'message':'Це ім’я вже зайняте.'}
  if inventory_id is None:rune=get_name_rune_inventory(user_id,db_path)
  else:rune=c.execute('SELECT id,quantity FROM inventory WHERE id=? AND user_id=? AND item_id=? AND quantity>0',(int(inventory_id),int(user_id),NAME_RUNE_ITEM_ID)).fetchone()
  if not rune:return {'success':False,'message':'Руну імені не знайдено в інвентарі.'}
  return {'success':True,'old_name':old,'new_name':v['name'],'inventory_id':int(rune['id'])}
 finally:c.close()
def rename_with_name_rune(user_id,new_name,idempotency_key,db_path=None,inventory_id=None):
 uid=int(user_id);key=str(idempotency_key or '').strip();v=validate_name(new_name)
 if not key:return {'success':False,'message':'Відсутній ключ операції.'}
 if not v['success']:return v
 c=_conn(db_path)
 try:
  c.execute('BEGIN IMMEDIATE');existing=c.execute('SELECT * FROM character_name_changes WHERE idempotency_key=?',(key,)).fetchone()
  if existing:c.commit();return {'success':True,'idempotent_replay':True,'change':dict(existing)}
  user=c.execute('SELECT character_name FROM users WHERE user_id=?',(uid,)).fetchone()
  if not user:c.rollback();return {'success':False,'message':'Персонажа не знайдено.'}
  old=str(user[0] or '')
  if normalize_name(old).casefold()==v['key']:c.rollback();return {'success':False,'message':'Нове ім’я збігається з поточним.'}
  for other in c.execute("SELECT character_name FROM users WHERE user_id<>? AND TRIM(COALESCE(character_name,''))<>''",(uid,)):
   if normalize_name(other[0]).casefold()==v['key']:c.rollback();return {'success':False,'message':'Це ім’я вже зайняте.'}
  if inventory_id is None:rune=c.execute('SELECT id,quantity FROM inventory WHERE user_id=? AND item_id=? AND quantity>0 ORDER BY id LIMIT 1',(uid,NAME_RUNE_ITEM_ID)).fetchone()
  else:rune=c.execute('SELECT id,quantity FROM inventory WHERE id=? AND user_id=? AND item_id=? AND quantity>0',(int(inventory_id),uid,NAME_RUNE_ITEM_ID)).fetchone()
  if not rune:c.rollback();return {'success':False,'message':'Руну імені не знайдено в інвентарі.'}
  if int(rune['quantity'])==1:c.execute('DELETE FROM inventory WHERE id=? AND user_id=?',(int(rune['id']),uid))
  else:c.execute('UPDATE inventory SET quantity=quantity-1 WHERE id=? AND user_id=? AND quantity>1',(int(rune['id']),uid))
  c.execute('UPDATE users SET character_name=? WHERE user_id=?',(v['name'],uid));now=datetime.now(timezone.utc).isoformat();cur=c.execute('INSERT INTO character_name_changes(user_id,old_name,new_name,normalized_new_name,inventory_id,item_id,idempotency_key,created_at) VALUES(?,?,?,?,?,?,?,?)',(uid,old,v['name'],v['key'],int(rune['id']),502,key,now));cid=int(cur.lastrowid);c.commit();return {'success':True,'idempotent_replay':False,'change_id':cid,'old_name':old,'new_name':v['name']}
 except Exception:c.rollback();raise
 finally:c.close()
