import ast,sqlite3,sys,tempfile
from datetime import datetime,timezone
from pathlib import Path
R=Path(__file__).resolve().parents[1]
for p in ('main.py','handlers/crystal_shop.py','handlers/timed_exp_bonus.py','systems/timed_exp_bonus_system.py','systems/reward_system.py'):ast.parse((R/p).read_text(encoding='utf-8'))
assert 'calculate_mob_kill_exp' in (R/'systems/reward_system.py').read_text(encoding='utf-8');assert 'contract_system' not in (R/'systems/timed_exp_bonus_system.py').read_text(encoding='utf-8')
if str(R) not in sys.path:sys.path.insert(0,str(R))
from systems.timed_exp_bonus_system import *
with tempfile.TemporaryDirectory() as d:
 p=Path(d)/'t.db';c=sqlite3.connect(p);c.executescript("CREATE TABLE users(user_id INTEGER PRIMARY KEY);CREATE TABLE crystal_wallets(user_id INTEGER PRIMARY KEY,balance INTEGER,created_at TEXT,updated_at TEXT);CREATE TABLE crystal_transactions(id INTEGER PRIMARY KEY AUTOINCREMENT,user_id INTEGER,operation TEXT,amount INTEGER,reason_code TEXT,balance_before INTEGER,balance_after INTEGER,idempotency_key TEXT UNIQUE,external_reference TEXT,metadata_json TEXT,created_at TEXT);INSERT INTO users VALUES(1);INSERT INTO crystal_wallets VALUES(1,500,'','');");c.commit();c.close();init_timed_exp_bonus_system(p);a=purchase_exp_bonus(1,15,'k1',p);assert a['success'] and a['balance']==430;b=purchase_exp_bonus(1,15,'k1',p);assert b['idempotent_replay'] and b['balance']==430;x=calculate_mob_kill_exp(1,100,p);assert x['bonus_exp']==25 and x['final_exp']==125;c=sqlite3.connect(p);assert c.execute('SELECT COUNT(*) FROM exp_bonus_purchases').fetchone()[0]==1;c.close()
print('[PASS] Stage 17.30.1 timed mob-kill EXP bonus contracts')
