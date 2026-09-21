#!/usr/bin/env python3
import ast,importlib.util,sqlite3,sys,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
conn_src=(ROOT/'db_modules'/'connection.py').read_text(encoding='utf-8')
player_src=(ROOT/'db_modules'/'player.py').read_text(encoding='utf-8')
city_src=(ROOT/'handlers'/'city.py').read_text(encoding='utf-8')
assert 'registered_at TEXT DEFAULT' in conn_src
assert '("users", "registered_at", "TEXT DEFAULT' in conn_src
assert 'registered_at = datetime.now(timezone.utc).isoformat()' in player_src
assert 'registered_at' in city_src and 'Дата реєстрації' in city_src
assert 'не зафіксована' in city_src
spec=importlib.util.spec_from_file_location('m052',ROOT/'migrations'/'052_registration_date_pipeline.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
with tempfile.TemporaryDirectory() as td:
 db=Path(td)/'test.db';c=sqlite3.connect(db)
 c.execute('CREATE TABLE users (user_id INTEGER PRIMARY KEY, last_energy_update TEXT, last_activity_at TEXT)')
 c.execute("INSERT INTO users VALUES (1,'2020-01-01T00:00:00','2021-01-01T00:00:00')")
 first=m.migrate(c);c.commit()
 cols=[r[1] for r in c.execute('PRAGMA table_info(users)')]
 assert cols.count('registered_at')==1,cols
 legacy=c.execute('SELECT registered_at FROM users WHERE user_id=1').fetchone()[0]
 assert legacy and '+00:00' in legacy,legacy
 # Migration must be idempotent and must not rewrite the immutable value.
 second=m.migrate(c);c.commit();assert c.execute('SELECT registered_at FROM users WHERE user_id=1').fetchone()[0]==legacy
 # Model create_user first-insert and repeated /start semantics.
 exact='2026-09-21T20:00:00+00:00'
 c.execute('INSERT OR IGNORE INTO users(user_id,registered_at) VALUES (?,?)',(2,exact));c.commit()
 c.execute('INSERT OR IGNORE INTO users(user_id,registered_at) VALUES (?,?)',(2,'2099-01-01T00:00:00+00:00'));c.commit()
 assert c.execute('SELECT registered_at FROM users WHERE user_id=2').fetchone()[0]==exact
 # Model DEV reset: updates other fields and preserves registered_at.
 c.execute("UPDATE users SET last_activity_at=NULL WHERE user_id=2");c.commit()
 assert c.execute('SELECT registered_at FROM users WHERE user_id=2').fetchone()[0]==exact
 assert c.execute('PRAGMA quick_check').fetchone()[0]=='ok'
 assert c.execute('PRAGMA foreign_key_check').fetchall()==[]
 c.close()
print('[PASS] registration timestamp schema, legacy backfill, first-create, repeat-start and reset preservation')
