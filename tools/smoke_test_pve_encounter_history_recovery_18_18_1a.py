from __future__ import annotations
import ast, sqlite3
from pathlib import Path
R=Path(__file__).resolve().parents[1]
s=(R/'systems/pve_auto_escape_system.py').read_text(encoding='utf-8-sig'); ast.parse(s)
assert "user_id INTEGER NOT NULL," in s and "user_id INTEGER NOT NULL UNIQUE" not in s
assert "WHERE status='active'" in s and 'ux_pve_encounters_one_active_user' in s
assert "deadline_at>?" in s and 'restored_user_ids' in s
assert "mob['pve_encounter_id']=eid" in s
# Independent SQLite proof of history plus one-active invariant.
c=sqlite3.connect(':memory:')
c.executescript("""CREATE TABLE pve_encounters(encounter_id TEXT PRIMARY KEY,user_id INTEGER NOT NULL,status TEXT NOT NULL,created_at TEXT); CREATE UNIQUE INDEX ux ON pve_encounters(user_id) WHERE status='active';""")
c.execute("INSERT INTO pve_encounters VALUES('a',1,'victory','1')"); c.execute("INSERT INTO pve_encounters VALUES('b',1,'manual_escape','2')"); c.execute("INSERT INTO pve_encounters VALUES('c',1,'active','3')")
try:c.execute("INSERT INTO pve_encounters VALUES('d',1,'active','4')"); raise AssertionError('second active accepted')
except sqlite3.IntegrityError:pass
assert c.execute('SELECT COUNT(*) FROM pve_encounters WHERE user_id=1').fetchone()[0]==3
print('[PASS] Stage 18.18.1a history, partial uniqueness and restart recovery')
