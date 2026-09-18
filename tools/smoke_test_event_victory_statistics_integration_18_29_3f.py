# -*- coding: utf-8 -*-
import ast,sqlite3,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
source=(ROOT/"handlers"/"combat.py").read_text(encoding="utf-8-sig");tree=ast.parse(source)
fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=="process_victory")
segment=ast.get_source_segment(source,fn)
assert segment.count("ROM_STAGE_18_29_3F_EVENT_VICTORY_STATISTICS")==1
claim=segment.index("claim_pve_terminal(user_id, 'victory', encounter_id)");record=segment.index("record_event_mob_victory(");reward=segment.index("reward = process_victory_reward(")
assert claim < record < reward
assert 'event_key = str((mob or {}).get("event_key") or "").strip()' in segment
assert 'event_mob_key = str((mob or {}).get("event_mob_key") or "").strip()' in segment
assert 'terminal_event_id=encounter_id' in segment
from systems.event_statistics_system import record_event_mob_victory
c=sqlite3.connect(":memory:");c.executescript("CREATE TABLE users(user_id INTEGER PRIMARY KEY);INSERT INTO users VALUES(1);CREATE TABLE event_kill_receipts(event_key TEXT,terminal_event_id TEXT,user_id INTEGER,mob_key TEXT,recorded_at TEXT,PRIMARY KEY(event_key,terminal_event_id));CREATE TABLE event_kill_statistics(event_key TEXT,user_id INTEGER,mob_key TEXT,kills INTEGER,first_reached_at TEXT,updated_at TEXT,PRIMARY KEY(event_key,user_id,mob_key));")
assert record_event_mob_victory(c,"test_event_2026",1,"test_slime","enc-1")["recorded"]
assert record_event_mob_victory(c,"test_event_2026",1,"test_slime","enc-1")["duplicate"]
assert c.execute("SELECT kills FROM event_kill_statistics").fetchone()[0]==1
print("EVENT_VICTORY_STATISTICS_INTEGRATION_18_29_3F_OK")
