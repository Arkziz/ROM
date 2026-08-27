import sqlite3,tempfile,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1]
if str(R) not in sys.path:sys.path.insert(0,str(R))
from systems.crystal_wallet_system import init_crystal_wallet_system,get_crystal_balance,credit_crystals,debit_crystals,get_crystal_transactions,compensate_crystal_transaction
with tempfile.TemporaryDirectory() as d:
 p=Path(d)/'test.db';c=sqlite3.connect(p);c.execute('CREATE TABLE users(user_id INTEGER PRIMARY KEY,character_name TEXT)');c.executemany('INSERT INTO users(user_id,character_name) VALUES(?,?)',[(101,'A'),(202,'B')]);c.commit();c.close()
 assert init_crystal_wallet_system(p)['wallets']==2 and get_crystal_balance(101,p)==0
 a=credit_crystals(101,50,'dev_credit','k1',db_path=p);assert a['success'] and a['balance']==50
 replay=credit_crystals(101,50,'dev_credit','k1',db_path=p);assert replay['idempotent_replay'] and get_crystal_balance(101,p)==50
 b=debit_crystals(101,20,'dev_debit','k2',db_path=p);assert b['success'] and b['balance']==30
 bad=debit_crystals(101,31,'dev_debit','k3',db_path=p);assert not bad['success'] and get_crystal_balance(101,p)==30
 comp=compensate_crystal_transaction(b['transaction_id'],'k4',db_path=p);assert comp['success'] and get_crystal_balance(101,p)==50
 rows=get_crystal_transactions(101,0,20,db_path=p)['items'];assert len(rows)==3
 c=sqlite3.connect(p);assert c.execute('PRAGMA quick_check').fetchone()[0]=='ok';assert not c.execute('PRAGMA foreign_key_check').fetchall();c.close()
print('[PASS] Stage 17.25.1 crystal wallet temporary-DB contracts')
