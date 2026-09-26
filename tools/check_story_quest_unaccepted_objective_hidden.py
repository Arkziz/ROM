#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Production-shaped checks for hidden objectives of unaccepted next quests."""
from __future__ import annotations
import sqlite3,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
import handlers.story_quest_npc_runtime as runtime
from data.story_quest_content import STORY_QUEST_REGISTRY

def schema(connection):
 connection.executescript("CREATE TABLE user_story_quests(user_id INTEGER,quest_id TEXT,status TEXT,progress INTEGER,target_quantity INTEGER,reward_claimed INTEGER,accepted_at TEXT,completed_at TEXT,skipped_at TEXT,updated_at TEXT,PRIMARY KEY(user_id,quest_id));CREATE TABLE user_story_quest_items(user_id INTEGER,quest_id TEXT,item_key TEXT,quantity INTEGER,updated_at TEXT,PRIMARY KEY(user_id,quest_id,item_key));")
def completed(connection,quest):
 connection.execute("INSERT INTO user_story_quests VALUES(1,?,'COMPLETED',1,1,1,'','','','')",(quest.quest_id,))
def main():
 connection=sqlite3.connect(':memory:');connection.row_factory=sqlite3.Row;schema(connection);runtime._level=lambda user_id:1
 q1=next(q for q in STORY_QUEST_REGISTRY.values() if q.number==1);completed(connection,q1);q2=next(q for q in STORY_QUEST_REGISTRY.values() if q.number==2)
 different=runtime._completion_receipt(connection,1,q1,'elder',{'already_processed':False,'reward':{'exp_awarded':30,'gold_awarded':0.27}})
 assert '✨ Доступний наступний квест:' in different and '📜 2. Перевірка стежки' in different and 'Гільдія Найманців' in different
 assert '🎯 Наступна мета:' not in different and q2.objective_text not in different
 completed(connection,q2);q3=next(q for q in STORY_QUEST_REGISTRY.values() if q.number==3)
 same=runtime._completion_receipt(connection,1,q2,'mercenary_head',{'already_processed':False,'reward':{'exp_awarded':30,'gold_awarded':0.27}})
 assert '📜 3. Останній слід' in same and 'Новий квест можна прийняти у цього персонажа нижче.' in same
 assert '🎯 Наступна мета:' not in same and q3.objective_text not in same
 available={'npc_id':'mercenary_head','npc_name':'Голова Найманців','state':'AVAILABLE','quest':runtime._presentation if False else {'quest_id':q3.quest_id,'number':q3.number,'title':q3.title,'quest_type':q3.quest_type.value,'progress':0,'quest_item_quantity':0}}
 card=runtime._text(available);assert q3.description in card or runtime.STORY_QUEST_TEXT[q3.quest_id]['acceptance_text'] in card
 assert len(STORY_QUEST_REGISTRY)==10 and 'start_path_011_unstable_glow' not in STORY_QUEST_REGISTRY
 print('STORY QUEST UNACCEPTED OBJECTIVE HIDDEN: PASS');return 0
if __name__=='__main__':raise SystemExit(main())
