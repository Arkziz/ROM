#!/usr/bin/env python3
from pathlib import Path
import ast,os,sqlite3,sys,tempfile
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
os.environ.setdefault('ROM_ADMIN_USER_IDS','243129101')
from systems.admin_crystal_credit_system import init_admin_crystal_credit_system,get_admin_adjustment_history,get_admin_adjustment_detail
from handlers.admin_crystal_credit import _history_text,_history_kb,_detail_text,_button_name
p=Path(tempfile.mkdtemp())/'t.db';c=sqlite3.connect(p);c.executescript("CREATE TABLE users(user_id INTEGER PRIMARY KEY,character_name TEXT);CREATE TABLE crystal_transactions(id INTEGER PRIMARY KEY);INSERT INTO users VALUES(1,'Олег');INSERT INTO crystal_transactions VALUES(1);");c.commit();c.close();init_admin_crystal_credit_system(p);c=sqlite3.connect(p);c.execute("INSERT INTO admin_crystal_credit_audit(admin_user_id,target_user_id,operation,requested_amount,actual_amount,balance_before,balance_after,reason,idempotency_key,crystal_transaction_id,created_at) VALUES(?,?,?,?,?,?,?,?,?,?,?)",(243129101,1,'credit',100,100,0,100,'Test','k',1,'2026-09-02T20:00:00+00:00'));c.commit();c.close()
r=get_admin_adjustment_history(243129101,0,10,p);assert r['items'][0]['character_name']=='Олег';assert 'Оберіть операцію' in _history_text(r)
kb=_history_kb(r);payload=str(kb.to_dict());assert '#1 · ➕ Нарахування (Олег)' in payload and 'ac:history_detail:1:0' in payload
d=get_admin_adjustment_detail(243129101,1,p);assert d['success'];text=_detail_text(d['item']);assert 'Telegram user ID: 1' in text and 'Персонаж: Олег' in text
assert len(_button_name({'character_name':'ДужеДовгеІмяПерсонажа123456'},10))<=10
assert not get_admin_adjustment_detail(2,1,p)['success']
print('PASS: named inline list, admin-only detail and return-page contract')
