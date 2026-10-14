#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations
import sqlite3,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from data.story_quest_content import STORY_QUEST_REGISTRY
from systems.story_quest_item_drop_system import process_story_quest_item_drop

def schema(c):c.executescript("CREATE TABLE user_story_quests(user_id INTEGER,quest_id TEXT,status TEXT,progress INTEGER,target_quantity INTEGER,reward_claimed INTEGER,accepted_at TEXT,completed_at TEXT,skipped_at TEXT,updated_at TEXT,PRIMARY KEY(user_id,quest_id));CREATE TABLE user_story_quest_items(user_id INTEGER,quest_id TEXT,item_key TEXT,quantity INTEGER,updated_at TEXT,PRIMARY KEY(user_id,quest_id,item_key));")
def main():
 c=sqlite3.connect(':memory:');c.row_factory=sqlite3.Row;schema(c);q=STORY_QUEST_REGISTRY['start_path_004_guard_uniform_scrap'];c.execute("INSERT INTO user_story_quests VALUES(1,?,'ACTIVE',0,1,0,'','','','')",(q.quest_id,));c.commit()
 hit=process_story_quest_item_drop(user_id=1,location_id='start_path',connection=c,random_value=lambda:0.0);assert hit['granted']==1 and hit['drop_message']==f'🧩 Сюжетна знахідка: {q.quest_item.display_name}' and hit['objective_complete'] is True
 reached=process_story_quest_item_drop(user_id=1,location_id='start_path',connection=c,random_value=lambda:0.0);assert reached['granted']==0 and reached.get('drop_message') is None and reached['reason']=='target_reached'
 c.execute('DELETE FROM user_story_quest_items');c.commit();miss=process_story_quest_item_drop(user_id=1,location_id='start_path',connection=c,random_value=lambda:q.quest_item.drop_chance);assert miss['granted']==0 and miss.get('drop_message') is None and miss['reason']=='drop_missed'
 wrong=process_story_quest_item_drop(user_id=1,location_id='other',connection=c,random_value=lambda:0.0);assert wrong['granted']==0 and wrong.get('drop_message') is None
 assert abs(q.quest_item.drop_chance-0.15)<1e-12
 combat=(ROOT/'handlers'/'combat.py').read_text(encoding='utf-8-sig');assert 'int(story_item_result.get("granted", 0) or 0) > 0' in combat and 'bot.send_message(chat_id, story_drop_message)' in combat
 print('STORY QUEST ITEM DROP NOTIFICATION: PASS');return 0
if __name__=='__main__':raise SystemExit(main())
