import os,sqlite3,sys,tempfile
from pathlib import Path
R=Path(__file__).resolve().parents[1]
if str(R) not in sys.path:sys.path.insert(0,str(R))
from systems.premium_item_policy_system import *
with tempfile.TemporaryDirectory() as d:
 p=Path(d)/'t.db';c=sqlite3.connect(p);c.executescript("CREATE TABLE users(user_id INTEGER PRIMARY KEY);CREATE TABLE items(id INTEGER PRIMARY KEY,name TEXT);CREATE TABLE inventory(id INTEGER PRIMARY KEY AUTOINCREMENT,user_id INTEGER,item_id INTEGER,quantity INTEGER,durability INTEGER,max_durability INTEGER,refine_level INTEGER);INSERT INTO users VALUES(1);INSERT INTO items VALUES(301,'Sphere');INSERT INTO items VALUES(402,'Success');INSERT INTO items VALUES(528,'Perfect');");c.commit();c.close();init_premium_item_policy(p)
 assert not can_grant_item_from_source(1,301,1,'dev_command',dev_mode=False,db_path=p)['success']
 a=grant_item_from_source(1,301,1,'dev_command','k1',dev_mode=True,db_path=p);assert a['success']
 b=grant_item_from_source(1,301,1,'dev_command','k1',dev_mode=True,db_path=p);assert b['idempotent_replay']
 assert not can_grant_item_from_source(1,402,1,'level_milestone_reward',milestone_level=5,db_path=p)['success']
 assert can_grant_item_from_source(1,301,1,'level_milestone_reward',milestone_level=5,db_path=p)['success']
 c=sqlite3.connect(p);assert c.execute('SELECT quantity FROM inventory WHERE user_id=1 AND item_id=301').fetchone()[0]==1;assert c.execute('SELECT COUNT(*) FROM premium_item_grants').fetchone()[0]==1;assert c.execute('PRAGMA quick_check').fetchone()[0]=='ok';c.close()
print('[PASS] Stage 17.26.1 premium policy temporary-DB contracts')
