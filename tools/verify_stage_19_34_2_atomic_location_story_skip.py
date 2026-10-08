#!/usr/bin/env python3
import sqlite3,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT)) if str(ROOT) not in sys.path else None
from data.story_quest_content import STORY_QUEST_REGISTRY
from systems.story_quest_system import reconcile_overlevel_story_locations
from systems.story_quest_overlevel_system import build_overlevel_story_skip_message
conn=sqlite3.connect(':memory:');conn.row_factory=sqlite3.Row
conn.executescript("""CREATE TABLE user_story_quests(id INTEGER PRIMARY KEY AUTOINCREMENT,user_id INTEGER NOT NULL,quest_id TEXT NOT NULL,quest_number INTEGER NOT NULL,status TEXT NOT NULL,progress INTEGER NOT NULL,target_quantity INTEGER NOT NULL,reward_claimed INTEGER NOT NULL,started_at TEXT NOT NULL,completed_at TEXT,skipped_at TEXT,updated_at TEXT NOT NULL,UNIQUE(user_id,quest_id));CREATE UNIQUE INDEX ux_active ON user_story_quests(user_id) WHERE status='ACTIVE';CREATE TABLE user_story_quest_items(id INTEGER PRIMARY KEY AUTOINCREMENT,user_id INTEGER NOT NULL,quest_id TEXT NOT NULL,item_key TEXT NOT NULL,quantity INTEGER NOT NULL,updated_at TEXT NOT NULL,UNIQUE(user_id,quest_id,item_key));""")
reg={q.quest_id:q for q in STORY_QUEST_REGISTRY.values() if q.number<=100}
q1=next(q for q in reg.values() if q.number==1);q4=next(q for q in reg.values() if q.number==4);q51=next(q for q in reg.values() if q.number==51)
conn.execute("INSERT INTO user_story_quests(user_id,quest_id,quest_number,status,progress,target_quantity,reward_claimed,started_at,completed_at,skipped_at,updated_at) VALUES(1,?,1,'COMPLETED',1,1,1,'t','t',NULL,'t')",(q1.quest_id,))
conn.execute("INSERT INTO user_story_quests(user_id,quest_id,quest_number,status,progress,target_quantity,reward_claimed,started_at,completed_at,skipped_at,updated_at) VALUES(1,?,4,'ACTIVE',0,1,0,'t',NULL,NULL,'t')",(q4.quest_id,))
conn.execute("INSERT INTO user_story_quest_items(user_id,quest_id,item_key,quantity,updated_at) VALUES(1,?,?,1,'t')",(q4.quest_id,q4.quest_item.item_key))
# Fixture setup uses SQLite's implicit transaction; commit it before invoking
# the lifecycle owner, which must start and own its own BEGIN IMMEDIATE.
conn.commit()
r=reconcile_overlevel_story_locations(conn,registry=reg,user_id=1,current_level=6,location_max_levels={'start_path':5,'dark_forest':10})
rows=conn.execute("SELECT quest_number,status,reward_claimed FROM user_story_quests WHERE user_id=1 ORDER BY quest_number").fetchall();assert len(rows)==50
assert rows[0]['status']=='COMPLETED' and rows[0]['reward_claimed']==1
assert all(x['status']=='SKIPPED' and x['reward_claimed']==0 for x in rows[1:])
assert conn.execute('SELECT COUNT(*) FROM user_story_quest_items').fetchone()[0]==0
assert r['changed']==49 and r['locations'][0]['completed']==1 and r['locations'][0]['skipped_now']==49
assert 'Пропущено без нагород: 49' in build_overlevel_story_skip_message(r)
r2=reconcile_overlevel_story_locations(conn,registry=reg,user_id=1,current_level=6,location_max_levels={'start_path':5,'dark_forest':10});assert r2['changed']==0
# Level 11 also reconciles Dark Forest while preserving all earlier finalized rows.
r3=reconcile_overlevel_story_locations(conn,registry=reg,user_id=1,current_level=11,location_max_levels={'start_path':5,'dark_forest':10});assert r3['changed']==50
assert conn.execute("SELECT COUNT(*) FROM user_story_quests WHERE status='SKIPPED'").fetchone()[0]==99
print('PASS: Stage 19.34.2')
