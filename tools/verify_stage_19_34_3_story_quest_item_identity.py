#!/usr/bin/env python3
from pathlib import Path
import sqlite3,sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT)) if str(ROOT) not in sys.path else None
from data.story_quest_content import STORY_QUEST_REGISTRY
from data.story_quest_item_identity import (
    STORY_QUEST_ITEM_FORBIDDEN_COLUMNS, inspect_story_quest_item_schema,
    validate_story_quest_item_key, validate_story_quest_item_schema,
)
# Production content uses unique stable keys and never numeric item type IDs.
keys=[]
for quest in STORY_QUEST_REGISTRY.values():
    if quest.quest_item is not None:
        keys.append(validate_story_quest_item_key(quest.quest_item.item_key))
    for required in quest.required_quest_items:
        validate_story_quest_item_key(required.item_key)
assert len(keys)==len(set(keys))
# High AUTOINCREMENT row IDs are harmless and stay local to this table.
conn=sqlite3.connect(':memory:')
conn.execute('PRAGMA foreign_keys=ON')
conn.executescript("""CREATE TABLE user_story_quests(user_id INTEGER NOT NULL,quest_id TEXT NOT NULL,PRIMARY KEY(user_id,quest_id));CREATE TABLE user_story_quest_items(id INTEGER PRIMARY KEY AUTOINCREMENT,user_id INTEGER NOT NULL,quest_id TEXT NOT NULL,item_key TEXT NOT NULL,quantity INTEGER NOT NULL DEFAULT 0,updated_at TEXT NOT NULL,UNIQUE(user_id,quest_id,item_key),FOREIGN KEY(user_id,quest_id) REFERENCES user_story_quests(user_id,quest_id) ON DELETE CASCADE);""")
conn.execute("INSERT INTO user_story_quests VALUES(1,'fixture_quest')")
conn.execute("INSERT INTO sqlite_sequence(name,seq) VALUES('user_story_quest_items',999999)")
conn.execute("INSERT INTO user_story_quest_items(user_id,quest_id,item_key,quantity,updated_at) VALUES(1,'fixture_quest','fixture_high_row_id',1,'t')")
row=conn.execute('SELECT id,item_key FROM user_story_quest_items').fetchone();assert row==(1000000,'fixture_high_row_id')
r=validate_story_quest_item_schema(conn);assert r['status']=='PASS' and not r['forbidden_present'] and r['ordinary_items_id_used'] is False
# A schema that adds ordinary item identity must fail closed.
bad=sqlite3.connect(':memory:');bad.execute('CREATE TABLE user_story_quest_items(id INTEGER PRIMARY KEY,item_id INTEGER,user_id INTEGER,quest_id TEXT,item_key TEXT,quantity INTEGER,updated_at TEXT)')
assert 'item_id' in inspect_story_quest_item_schema(bad)['forbidden_present']
try: validate_story_quest_item_schema(bad)
except RuntimeError: pass
else: raise AssertionError('forbidden item_id schema accepted')
# Static isolation: persistence and drop owners do not write ordinary inventory.
for rel in ('db_modules/story_quests.py','systems/story_quest_item_drop_system.py'):
    text=(ROOT/rel).read_text(encoding='utf-8-sig').lower()
    assert 'insert into inventory' not in text and 'update inventory' not in text
print('PASS: Stage 19.34.3')
