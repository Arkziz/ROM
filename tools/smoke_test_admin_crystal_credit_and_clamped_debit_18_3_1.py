#!/usr/bin/env python3
from pathlib import Path
import os,sqlite3,sys,tempfile
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
os.environ['ROM_ADMIN_USER_IDS']='243129101';os.environ['ROM_ADMIN_CRYSTAL_CREDIT_MAX']='10000';os.environ['ROM_ADMIN_CRYSTAL_DEBIT_MAX']='10000'
from systems.admin_crystal_credit_system import init_admin_crystal_credit_system,execute_admin_adjustment
p=Path(tempfile.mkdtemp())/'t.db';c=sqlite3.connect(p);c.executescript("CREATE TABLE users(user_id INTEGER PRIMARY KEY);CREATE TABLE crystal_wallets(user_id INTEGER PRIMARY KEY,balance INTEGER NOT NULL,created_at TEXT,updated_at TEXT);CREATE TABLE crystal_transactions(id INTEGER PRIMARY KEY AUTOINCREMENT,user_id INTEGER,operation TEXT,amount INTEGER,reason_code TEXT,balance_before INTEGER,balance_after INTEGER,idempotency_key TEXT UNIQUE,external_reference TEXT,metadata_json TEXT,compensates_transaction_id INTEGER,created_at TEXT);INSERT INTO users VALUES(1);INSERT INTO crystal_wallets VALUES(1,40,'x','x');");c.commit();c.close();init_admin_crystal_credit_system(p)
r=execute_admin_adjustment(243129101,1,'debit',100,'test','k1',p);assert r['success'] and r['actual_amount']==40 and r['balance']==0,r
r2=execute_admin_adjustment(243129101,1,'debit',100,'test','k1',p);assert r2['success'] and r2['idempotent_replay'],r2
r3=execute_admin_adjustment(243129101,1,'debit',1,'test','k2',p);assert not r3['success'],r3
print('PASS: authorized clamped debit, zero floor and idempotency')
