import ast,importlib.util,sqlite3,tempfile
from pathlib import Path
R=Path(__file__).resolve().parents[1]
for p in ('systems/crystal_bag_expansion_system.py','handlers/crystal_shop.py','db_modules/dev_compat.py','main.py','systems/fatigue_artifact_system.py'):ast.parse((R/p).read_text(encoding='utf-8'),filename=p)
spec=importlib.util.spec_from_file_location('bag',R/'systems/crystal_bag_expansion_system.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
with tempfile.TemporaryDirectory() as d:
 p=Path(d)/'t.db';c=sqlite3.connect(p);c.executescript("""PRAGMA foreign_keys=ON;CREATE TABLE users(user_id INTEGER PRIMARY KEY,bag_slots INTEGER);CREATE TABLE crystal_wallets(user_id INTEGER PRIMARY KEY,balance INTEGER,created_at TEXT,updated_at TEXT);CREATE TABLE crystal_transactions(id INTEGER PRIMARY KEY AUTOINCREMENT,user_id INTEGER,operation TEXT,amount INTEGER,reason_code TEXT,balance_before INTEGER,balance_after INTEGER,idempotency_key TEXT UNIQUE,external_reference TEXT,metadata_json TEXT,created_at TEXT);INSERT INTO users VALUES(1,60),(2,60),(3,80),(4,100),(5,120);INSERT INTO crystal_wallets VALUES(1,225,'',''),(2,74,'',''),(3,150,'',''),(4,999,'',''),(5,999,'','');""");c.commit();c.close();m.init_crystal_bag_expansion_system(p)
 a=m.purchase_crystal_bag_expansion(1,80,'k1',p);assert a['success'] and a['balance']==150 and a['current_capacity']==80
 replay=m.purchase_crystal_bag_expansion(1,80,'k1',p);assert replay['success'] and replay['idempotent_replay']
 duplicate=m.purchase_crystal_bag_expansion(1,80,'k2',p);assert not duplicate['success']
 b=m.purchase_crystal_bag_expansion(1,100,'k3',p);assert b['success'] and b['balance']==0 and b['current_capacity']==100
 assert not m.purchase_crystal_bag_expansion(2,80,'low',p)['success']
 assert m.purchase_crystal_bag_expansion(3,100,'k4',p)['success']
 assert not m.purchase_crystal_bag_expansion(4,100,'max',p)['success']
 assert not m.purchase_crystal_bag_expansion(5,100,'over',p)['success']
 c=sqlite3.connect(p);assert c.execute('SELECT bag_slots FROM users WHERE user_id=1').fetchone()[0]==100;assert c.execute('SELECT balance FROM crystal_wallets WHERE user_id=1').fetchone()[0]==0;assert c.execute('SELECT COUNT(*) FROM account_bag_expansion_purchases WHERE user_id=1').fetchone()[0]==2;assert c.execute('SELECT COUNT(*) FROM crystal_transactions WHERE user_id=1').fetchone()[0]==2;c.close()
text=(R/'db_modules/dev_compat.py').read_text(encoding='utf-8');assert 'max(int(globals().get("DEFAULT_BAG_SLOTS", 60)), int(get_bag_capacity(user_id)))' in text
handler=(R/'handlers/crystal_shop.py').read_text(encoding='utf-8');assert "BAG_EXPANSION_BUTTON='🎒 Розширення сумки'" in handler and "startswith('bg:')" in handler
print('[PASS] Stage 17.32.1 atomic, sequential, idempotent bag expansion contracts')
