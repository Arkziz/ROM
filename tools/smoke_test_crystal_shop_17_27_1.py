import sqlite3,sys,tempfile
from pathlib import Path
R=Path(__file__).resolve().parents[1]
if str(R) not in sys.path:sys.path.insert(0,str(R))
from systems.crystal_shop_system import *
with tempfile.TemporaryDirectory() as d:
 p=Path(d)/'t.db';c=sqlite3.connect(p);c.executescript("CREATE TABLE users(user_id INTEGER PRIMARY KEY,bag_slots INTEGER);CREATE TABLE items(id INTEGER PRIMARY KEY,name TEXT,max_stack INTEGER);CREATE TABLE inventory(id INTEGER PRIMARY KEY AUTOINCREMENT,user_id INTEGER,item_id INTEGER,quantity INTEGER,durability INTEGER);CREATE TABLE crystal_wallets(user_id INTEGER PRIMARY KEY,balance INTEGER,created_at TEXT,updated_at TEXT);CREATE TABLE crystal_transactions(id INTEGER PRIMARY KEY AUTOINCREMENT,user_id INTEGER,operation TEXT,amount INTEGER,reason_code TEXT,balance_before INTEGER,balance_after INTEGER,idempotency_key TEXT UNIQUE,external_reference TEXT,metadata_json TEXT,compensates_transaction_id INTEGER,created_at TEXT);CREATE TABLE premium_item_grants(id INTEGER PRIMARY KEY AUTOINCREMENT,user_id INTEGER,item_id INTEGER,quantity INTEGER,source TEXT,idempotency_key TEXT UNIQUE,external_reference TEXT,metadata_json TEXT,created_at TEXT);INSERT INTO users VALUES(1,2);INSERT INTO crystal_wallets VALUES(1,500,'x','x');INSERT INTO items VALUES(301,'Sphere',10);INSERT INTO items VALUES(402,'Rune',10);INSERT INTO items VALUES(528,'Extractor',999);");c.commit();c.close();init_crystal_shop_system(p)
 a=purchase_crystal_shop_item(1,301,2,'k1',p);assert a['success'] and a['balance']==200
 b=purchase_crystal_shop_item(1,301,2,'k1',p);assert b['idempotent_replay']
 c=sqlite3.connect(p);assert c.execute('SELECT balance FROM crystal_wallets').fetchone()[0]==200;assert c.execute('SELECT quantity FROM inventory').fetchone()[0]==2;assert c.execute('SELECT COUNT(*) FROM crystal_shop_purchases').fetchone()[0]==1;assert c.execute('SELECT COUNT(*) FROM crystal_transactions').fetchone()[0]==1;assert c.execute('SELECT COUNT(*) FROM premium_item_grants').fetchone()[0]==1;c.close()
 print('[PASS] Stage 17.27.1 atomic shop contracts')
