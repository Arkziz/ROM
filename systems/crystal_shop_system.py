# -*- coding: utf-8 -*-
"""Atomic crystal shop. Telegram Stars and XTR payments are intentionally absent."""
from __future__ import annotations
import json, sqlite3
from datetime import datetime, timezone
from pathlib import Path
DB_PATH=Path(__file__).resolve().parents[1]/'game.db'
CRYSTAL_SHOP_CATALOG={301:{'name':'🔮 Сфера нового шляху','price':150},402:{'name':'🍀 Руна Успіху','price':40},528:{'name':'💠 Досконалий Екстрактор','price':25},10000:{'name':'✍️ Руна імені','price':50}}
def _utc():return datetime.now(timezone.utc).isoformat()
def _connect(path=None):
 c=sqlite3.connect(str(path or DB_PATH),timeout=30);c.row_factory=sqlite3.Row;c.execute('PRAGMA foreign_keys=ON');c.execute('PRAGMA busy_timeout=30000');return c
def init_crystal_shop_system(db_path=None):
 c=_connect(db_path)
 try:
  c.executescript("""CREATE TABLE IF NOT EXISTS crystal_shop_purchases(id INTEGER PRIMARY KEY AUTOINCREMENT,user_id INTEGER NOT NULL,item_id INTEGER NOT NULL,quantity INTEGER NOT NULL CHECK(quantity>0),unit_price INTEGER NOT NULL CHECK(unit_price>0),total_price INTEGER NOT NULL CHECK(total_price>0),balance_before INTEGER NOT NULL CHECK(balance_before>=0),balance_after INTEGER NOT NULL CHECK(balance_after>=0),idempotency_key TEXT NOT NULL UNIQUE,crystal_transaction_id INTEGER NOT NULL UNIQUE,premium_grant_id INTEGER NOT NULL UNIQUE,created_at TEXT NOT NULL,FOREIGN KEY(user_id) REFERENCES users(user_id) ON DELETE RESTRICT,FOREIGN KEY(item_id) REFERENCES items(id) ON DELETE RESTRICT,FOREIGN KEY(crystal_transaction_id) REFERENCES crystal_transactions(id) ON DELETE RESTRICT,FOREIGN KEY(premium_grant_id) REFERENCES premium_item_grants(id) ON DELETE RESTRICT);CREATE INDEX IF NOT EXISTS ix_crystal_shop_purchases_user ON crystal_shop_purchases(user_id,id DESC);""");c.commit();return {'success':True}
 finally:c.close()
def get_crystal_shop_catalog():return {k:dict(v) for k,v in CRYSTAL_SHOP_CATALOG.items()}
def _capacity(c,uid,iid,qty):
 item=c.execute('SELECT COALESCE(max_stack,1) FROM items WHERE id=?',(iid,)).fetchone();max_stack=max(1,int(item[0] or 1));used=int(c.execute('SELECT COUNT(*) FROM inventory WHERE user_id=? AND COALESCE(quantity,0)>0',(uid,)).fetchone()[0]);cap=int(c.execute('SELECT COALESCE(bag_slots,60) FROM users WHERE user_id=?',(uid,)).fetchone()[0]);rows=c.execute('SELECT COALESCE(quantity,0) FROM inventory WHERE user_id=? AND item_id=? AND COALESCE(quantity,0)<?',(uid,iid,max_stack)).fetchall();free=sum(max_stack-int(x[0]) for x in rows);remain=max(0,qty-free);needed=(remain+max_stack-1)//max_stack;return used,cap,needed,max_stack
def preview_crystal_shop_purchase(user_id,item_id,quantity,db_path=None):
 try:uid=int(user_id);iid=int(item_id);qty=int(quantity)
 except Exception:return {'success':False,'message':'❌ Некоректні дані покупки.'}
 if iid not in CRYSTAL_SHOP_CATALOG:return {'success':False,'message':'❌ Предмет відсутній у магазині.'}
 if qty<=0:return {'success':False,'message':'❌ Кількість має бути більшою за нуль.'}
 c=_connect(db_path)
 try:
  wallet=c.execute('SELECT balance FROM crystal_wallets WHERE user_id=?',(uid,)).fetchone()
  if not wallet:return {'success':False,'message':'❌ Гаманець кристалів не знайдено.'}
  used,cap,needed,_=_capacity(c,uid,iid,qty);price=CRYSTAL_SHOP_CATALOG[iid]['price'];total=price*qty;balance=int(wallet[0]);return {'success':balance>=total and used+needed<=cap,'item_id':iid,'name':CRYSTAL_SHOP_CATALOG[iid]['name'],'quantity':qty,'unit_price':price,'total_price':total,'balance':balance,'balance_after':balance-total,'used_slots':used,'capacity':cap,'needed_slots':needed,'message':'OK' if balance>=total and used+needed<=cap else ('🎒 Сумка переповнена. Кристали не списано.' if used+needed>cap else '❌ Недостатньо кристалів.')}
 finally:c.close()
def _stack(c,uid,iid,qty,max_stack):
 first=None
 for row in c.execute('SELECT id,COALESCE(quantity,0) FROM inventory WHERE user_id=? AND item_id=? AND COALESCE(quantity,0)<? ORDER BY id',(uid,iid,max_stack)).fetchall():
  if qty<=0:break
  moved=min(qty,max_stack-int(row[1]));c.execute('UPDATE inventory SET quantity=quantity+? WHERE id=?',(moved,int(row[0])));first=first or int(row[0]);qty-=moved
 while qty>0:
  moved=min(qty,max_stack);cur=c.execute('INSERT INTO inventory(user_id,item_id,quantity,durability) VALUES(?,?,?,NULL)',(uid,iid,moved));first=first or int(cur.lastrowid);qty-=moved
 return first
def purchase_crystal_shop_item(user_id,item_id,quantity,idempotency_key,db_path=None):
 try:uid=int(user_id);iid=int(item_id);qty=int(quantity)
 except Exception:return {'success':False,'message':'❌ Некоректні дані покупки.'}
 key=str(idempotency_key or '').strip()
 if iid not in CRYSTAL_SHOP_CATALOG or qty<=0 or not key:return {'success':False,'message':'❌ Некоректна або неповна покупка.'}
 c=_connect(db_path)
 try:
  c.execute('BEGIN IMMEDIATE');old=c.execute('SELECT * FROM crystal_shop_purchases WHERE idempotency_key=?',(key,)).fetchone()
  if old:c.commit();return {'success':True,'idempotent_replay':True,'purchase':dict(old),'balance':int(old['balance_after'])}
  allowed={301:{'crystal_shop'},402:{'crystal_shop'},528:{'crystal_shop'},10000:{'crystal_shop'}}
  if 'crystal_shop' not in allowed.get(iid,set()):c.rollback();return {'success':False,'message':'❌ Джерело видачі заборонене.'}
  wallet=c.execute('SELECT balance FROM crystal_wallets WHERE user_id=?',(uid,)).fetchone();item=c.execute('SELECT id FROM items WHERE id=?',(iid,)).fetchone()
  if not wallet or not item:c.rollback();return {'success':False,'message':'❌ Гаманець або предмет не знайдено.'}
  before=int(wallet[0]);unit=int(CRYSTAL_SHOP_CATALOG[iid]['price']);total=unit*qty;used,cap,needed,max_stack=_capacity(c,uid,iid,qty)
  if used+needed>cap:c.rollback();return {'success':False,'message':'🎒 Сумка переповнена. Кристали не списано.','balance':before}
  if before<total:c.rollback();return {'success':False,'message':'❌ Недостатньо кристалів.','balance':before}
  after=before-total;now=_utc();changed=c.execute('UPDATE crystal_wallets SET balance=?,updated_at=? WHERE user_id=? AND balance=?',(after,now,uid,before)).rowcount
  if changed!=1:raise RuntimeError('Баланс змінився. Покупку скасовано.')
  tx_key='shop:debit:'+key;cur=c.execute("INSERT INTO crystal_transactions(user_id,operation,amount,reason_code,balance_before,balance_after,idempotency_key,external_reference,metadata_json,created_at) VALUES(?,?,?,?,?,?,?,?,?,?)",(uid,'debit',total,'crystal_shop_purchase',before,after,tx_key,key,json.dumps({'item_id':iid,'quantity':qty},sort_keys=True),now));txid=int(cur.lastrowid)
  inv_id=_stack(c,uid,iid,qty,max_stack);grant_key='shop:grant:'+key;cur=c.execute('INSERT INTO premium_item_grants(user_id,item_id,quantity,source,idempotency_key,external_reference,metadata_json,created_at) VALUES(?,?,?,?,?,?,?,?)',(uid,iid,qty,'crystal_shop',grant_key,key,json.dumps({'total_price':total},sort_keys=True),now));gid=int(cur.lastrowid)
  cur=c.execute('INSERT INTO crystal_shop_purchases(user_id,item_id,quantity,unit_price,total_price,balance_before,balance_after,idempotency_key,crystal_transaction_id,premium_grant_id,created_at) VALUES(?,?,?,?,?,?,?,?,?,?,?)',(uid,iid,qty,unit,total,before,after,key,txid,gid,now));pid=int(cur.lastrowid);c.commit();return {'success':True,'idempotent_replay':False,'purchase_id':pid,'transaction_id':txid,'grant_id':gid,'inventory_id':inv_id,'item_id':iid,'name':CRYSTAL_SHOP_CATALOG[iid]['name'],'quantity':qty,'unit_price':unit,'total_price':total,'balance_before':before,'balance_after':after,'balance':after}
 except Exception as e:c.rollback();return {'success':False,'message':f'❌ Покупку скасовано: {e}'}
 finally:c.close()
def get_crystal_shop_purchases(user_id,page=0,page_size=20,db_path=None):
 c=_connect(db_path)
 try:return [dict(r) for r in c.execute('SELECT * FROM crystal_shop_purchases WHERE user_id=? ORDER BY id DESC LIMIT ? OFFSET ?',(int(user_id),max(1,min(100,int(page_size))),max(0,int(page))*max(1,min(100,int(page_size))))).fetchall()]
 finally:c.close()
