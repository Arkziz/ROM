#!/usr/bin/env python3
from __future__ import annotations
import ast,sqlite3,sys,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
def main():
 main_text=(ROOT/'main.py').read_text(encoding='utf-8-sig');ast.parse(main_text)
 assert main_text.count('from systems.admin_crystal_credit_system import init_admin_crystal_credit_system')==1
 assert main_text.count('init_admin_crystal_credit_system()')==1
 assert main_text.index('init_admin_crystal_credit_system()')<main_text.index('register_admin_crystal_credit_handlers(bot)')
 import systems.admin_crystal_credit_system as a
 a.ROM_ADMIN_USER_IDS={9001};a.ROM_ADMIN_CRYSTAL_CREDIT_MAX=10000;a.ROM_ADMIN_CRYSTAL_DEBIT_MAX=10000
 with tempfile.TemporaryDirectory() as td:
  db=Path(td)/'test.db';c=sqlite3.connect(db)
  c.executescript("""
   PRAGMA foreign_keys=ON;
   CREATE TABLE users(user_id INTEGER PRIMARY KEY,character_name TEXT);
   CREATE TABLE crystal_wallets(user_id INTEGER PRIMARY KEY,balance INTEGER NOT NULL DEFAULT 0 CHECK(balance>=0),created_at TEXT NOT NULL,updated_at TEXT NOT NULL,FOREIGN KEY(user_id) REFERENCES users(user_id) ON DELETE RESTRICT);
   CREATE TABLE crystal_transactions(id INTEGER PRIMARY KEY AUTOINCREMENT,user_id INTEGER NOT NULL,operation TEXT NOT NULL CHECK(operation IN ('credit','debit')),amount INTEGER NOT NULL CHECK(amount>0),reason_code TEXT NOT NULL,balance_before INTEGER NOT NULL CHECK(balance_before>=0),balance_after INTEGER NOT NULL CHECK(balance_after>=0),idempotency_key TEXT NOT NULL UNIQUE,external_reference TEXT,metadata_json TEXT NOT NULL DEFAULT '{}',compensates_transaction_id INTEGER,created_at TEXT NOT NULL,FOREIGN KEY(user_id) REFERENCES users(user_id) ON DELETE RESTRICT,FOREIGN KEY(compensates_transaction_id) REFERENCES crystal_transactions(id) ON DELETE RESTRICT);
   INSERT INTO users(user_id,character_name) VALUES(42,'Target');
   INSERT INTO crystal_wallets(user_id,balance,created_at,updated_at) VALUES(42,0,'2026-10-12T00:00:00+00:00','2026-10-12T00:00:00+00:00');
  """);c.commit();c.close()
  a.init_admin_crystal_credit_system(db);a.init_admin_crystal_credit_system(db)
  credit=a.execute_admin_adjustment(9001,42,'credit',100,'test credit','k1',db);assert credit['success'] and credit['balance']==100 and credit['actual_amount']==100
  replay=a.execute_admin_adjustment(9001,42,'credit',100,'test credit','k1',db);assert replay['success'] and replay['idempotent_replay'] and replay['balance']==100
  debit=a.execute_admin_adjustment(9001,42,'debit',40,'test debit','k2',db);assert debit['success'] and debit['balance']==60 and not debit['clamped']
  clamp=a.execute_admin_adjustment(9001,42,'debit',100,'test clamp','k3',db);assert clamp['success'] and clamp['balance']==0 and clamp['actual_amount']==60 and clamp['clamped']
  zero=a.execute_admin_adjustment(9001,42,'debit',1,'test zero','k4',db);assert not zero['success']
  denied=a.execute_admin_adjustment(9002,42,'credit',1,'denied','k5',db);assert not denied['success']
  hist=a.get_admin_adjustment_history(9001,0,10,db);assert hist['success'] and hist['total']==3 and len(hist['items'])==3
  detail=a.get_admin_adjustment_detail(9001,credit['audit_id'],db);assert detail['success'] and detail['item']['actual_amount']==100
  c=sqlite3.connect(db);tables={x[0] for x in c.execute("SELECT name FROM sqlite_master WHERE type='table'")};indexes={x[0] for x in c.execute("SELECT name FROM sqlite_master WHERE type='index'")};wallet=c.execute('SELECT balance FROM crystal_wallets WHERE user_id=42').fetchone()[0];tx=c.execute('SELECT operation,amount FROM crystal_transactions ORDER BY id').fetchall();quick=c.execute('PRAGMA quick_check').fetchone()[0];fk=c.execute('PRAGMA foreign_key_check').fetchall();c.close()
  assert 'admin_crystal_credit_audit' in tables
  assert {'ix_admin_crystal_audit_admin_id','ix_admin_crystal_audit_target_id'}.issubset(indexes)
  assert wallet==0 and tx==[('credit',100),('debit',40),('debit',60)] and quick=='ok' and fk==[]
 print('[OK] admin crystal startup/schema/credit/debit/clamp/replay/history/detail PASS')
if __name__=='__main__':main()
