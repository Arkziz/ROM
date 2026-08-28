import ast,sqlite3,sys,tempfile
from pathlib import Path
R=Path(__file__).resolve().parents[1]
for p in ('main.py','handlers/inventory.py','handlers/fatigue_artifact.py','systems/fatigue_artifact_system.py','systems/reward_system.py','systems/auction_house_system.py'):ast.parse((R/p).read_text(encoding='utf-8'))
assert 'give_fatigue_artifact' in (R/'handlers/fatigue_artifact.py').read_text(encoding='utf-8');assert '✍️' not in (R/'handlers/fatigue_artifact.py').read_text(encoding='utf-8')
if str(R) not in sys.path:sys.path.insert(0,str(R))
from systems.fatigue_artifact_system import *
with tempfile.TemporaryDirectory() as d:
 p=Path(d)/'t.db';c=sqlite3.connect(p);c.executescript("CREATE TABLE users(user_id INTEGER PRIMARY KEY,energy INTEGER,energy_full_notified INTEGER,bag_slots INTEGER);CREATE TABLE items(id INTEGER PRIMARY KEY,name TEXT,type TEXT,rarity TEXT,category TEXT,slot_key TEXT,weapon_hands INTEGER,max_stack INTEGER,sell_price REAL,item_level INTEGER,is_generated INTEGER,item_subtype TEXT);CREATE TABLE inventory(id INTEGER PRIMARY KEY AUTOINCREMENT,user_id INTEGER,item_id INTEGER,quantity INTEGER);INSERT INTO users VALUES(1,17,0,40);");c.commit();c.close();init_fatigue_artifact_system(p);add_fatigue_artifacts(1,12,p);c=sqlite3.connect(p);inv=c.execute('SELECT id FROM inventory WHERE user_id=1 AND item_id=50000 ORDER BY id LIMIT 1').fetchone()[0];c.close();a=use_fatigue_artifacts(1,inv,3,'k1',p);assert a['used_quantity']==3 and a['fatigue_after']==2 and a['remaining']==9;b=use_fatigue_artifacts(1,inv,3,'k1',p);assert b['idempotent_replay'];c=sqlite3.connect(p);assert c.execute('SELECT group_concat(quantity) FROM inventory WHERE item_id=50000').fetchone()[0]=='9';c.close()
print('[PASS] Stage 17.31.1.2 artifact, stack normalization and idempotency contracts')
