#!/usr/bin/env python3
from __future__ import annotations
import ast,sqlite3,tempfile,sys
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
 sys.path.insert(0,str(ROOT))
def main():
 system=(ROOT/'systems/timed_exp_bonus_system.py').read_text(encoding='utf-8-sig');handler=(ROOT/'handlers/timed_exp_bonus.py').read_text(encoding='utf-8-sig')
 ast.parse(system);ast.parse(handler)
 assert system.count('PLANS={15:100,30:180}')==1
 assert handler.count("'15 днів — 100 💎'")==1
 assert handler.count("'30 днів — 180 💎'")==1
 assert '15 днів — 70 💎' not in handler and '30 днів — 120 💎' not in handler
 from systems.timed_exp_bonus_system import PLANS,init_timed_exp_bonus_system,preview_exp_bonus_purchase,purchase_exp_bonus
 assert PLANS=={15:100,30:180}
 with tempfile.TemporaryDirectory() as td:
  db=Path(td)/'premium.db';c=sqlite3.connect(db)
  c.executescript("""
   PRAGMA foreign_keys=ON;
   CREATE TABLE users(user_id INTEGER PRIMARY KEY,character_name TEXT);
   CREATE TABLE crystal_wallets(user_id INTEGER PRIMARY KEY,balance INTEGER NOT NULL DEFAULT 0 CHECK(balance>=0),created_at TEXT NOT NULL,updated_at TEXT NOT NULL,FOREIGN KEY(user_id) REFERENCES users(user_id) ON DELETE RESTRICT);
   CREATE TABLE crystal_transactions(id INTEGER PRIMARY KEY AUTOINCREMENT,user_id INTEGER NOT NULL,operation TEXT NOT NULL CHECK(operation IN ('credit','debit')),amount INTEGER NOT NULL CHECK(amount>0),reason_code TEXT NOT NULL,balance_before INTEGER NOT NULL CHECK(balance_before>=0),balance_after INTEGER NOT NULL CHECK(balance_after>=0),idempotency_key TEXT NOT NULL UNIQUE,external_reference TEXT,metadata_json TEXT NOT NULL DEFAULT '{}',compensates_transaction_id INTEGER,created_at TEXT NOT NULL,FOREIGN KEY(user_id) REFERENCES users(user_id) ON DELETE RESTRICT,FOREIGN KEY(compensates_transaction_id) REFERENCES crystal_transactions(id) ON DELETE RESTRICT);
   INSERT INTO users(user_id,character_name) VALUES(1,'Tester');
   INSERT INTO crystal_wallets(user_id,balance,created_at,updated_at) VALUES(1,500,'2026-10-12T00:00:00+00:00','2026-10-12T00:00:00+00:00');
  """);c.commit();c.close();init_timed_exp_bonus_system(db)
  now=datetime(2026,10,12,18,0,tzinfo=timezone.utc)
  p15=preview_exp_bonus_purchase(1,15,db,now);assert p15['price']==100 and p15['balance_after']==400
  r15=purchase_exp_bonus(1,15,'stage20.5.4:15',db,now);assert r15['success'] and r15['price']==100 and r15['balance']==400
  replay=purchase_exp_bonus(1,15,'stage20.5.4:15',db,now);assert replay['success'] and replay['idempotent_replay'] and replay['balance']==400
  p30=preview_exp_bonus_purchase(1,30,db,now);assert p30['price']==180 and p30['balance_after']==220
  r30=purchase_exp_bonus(1,30,'stage20.5.4:30',db,now);assert r30['success'] and r30['price']==180 and r30['balance']==220
  c=sqlite3.connect(db);wallet=c.execute('SELECT balance FROM crystal_wallets WHERE user_id=1').fetchone()[0];prices=c.execute('SELECT duration_days,price_crystals FROM exp_bonus_purchases ORDER BY id').fetchall();tx=c.execute('SELECT amount,balance_before,balance_after FROM crystal_transactions ORDER BY id').fetchall();exp=c.execute('SELECT expires_at FROM account_exp_bonus_entitlements WHERE user_id=1').fetchone()[0];c.close()
  assert wallet==220 and prices==[(15,100),(30,180)] and tx==[(100,500,400),(180,400,220)]
  assert exp.startswith('2026-11-26T18:00:00')
 print('[OK] Premium prices 15d=100 and 30d=180: preview, debit, history, replay, stacking PASS')
if __name__=='__main__':main()
