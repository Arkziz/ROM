import sqlite3,sys,tempfile
from pathlib import Path
R=Path(__file__).resolve().parents[1]
if str(R) not in sys.path:sys.path.insert(0,str(R))
from systems.name_rune_system import *
with tempfile.TemporaryDirectory() as d:
 p=Path(d)/'x.db';c=sqlite3.connect(p);c.executescript("CREATE TABLE users(user_id INTEGER PRIMARY KEY,character_name TEXT);CREATE TABLE items(id INTEGER PRIMARY KEY,name TEXT,type TEXT,rarity TEXT,category TEXT,max_stack INTEGER,sell_price REAL,buy_price REAL,tradeable INTEGER,premium_bound INTEGER);CREATE TABLE inventory(id INTEGER PRIMARY KEY AUTOINCREMENT,user_id INTEGER,item_id INTEGER,quantity INTEGER);INSERT INTO users VALUES(1,'Alpha');INSERT INTO users VALUES(2,'Beta');");c.commit();c.close();init_name_rune_system(p);c=sqlite3.connect(p);c.execute('INSERT INTO inventory(user_id,item_id,quantity) VALUES(1,10000,2)');c.commit();c.close()
 assert not preview_name_change(1,'alpha',p)['success'];assert not preview_name_change(1,'BETA',p)['success'];a=rename_with_name_rune(1,'Gamma','k1',p);assert a['success'];b=rename_with_name_rune(1,'Gamma','k1',p);assert b['idempotent_replay'];c=sqlite3.connect(p);assert c.execute('SELECT character_name FROM users WHERE user_id=1').fetchone()[0]=='Gamma';assert c.execute('SELECT quantity FROM inventory WHERE user_id=1 AND item_id=10000').fetchone()[0]==1;assert c.execute('SELECT COUNT(*) FROM character_name_changes').fetchone()[0]==1;c.close()
print('[PASS] Stage 17.28.1 Name Rune contracts')
