#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Production-shaped checks for the TALK offer/conversation/completion flow."""
from __future__ import annotations
import sqlite3,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from data.story_quest_content import STORY_QUEST_REGISTRY,STORY_QUEST_TEXT
from handlers.story_quest_npc_runtime import _markup,_text
from systems.story_quest_system import get_story_quest_view

def schema(c):c.executescript("CREATE TABLE user_story_quests(user_id INTEGER,quest_id TEXT,status TEXT,progress INTEGER,target_quantity INTEGER,reward_claimed INTEGER,accepted_at TEXT,completed_at TEXT,skipped_at TEXT,updated_at TEXT,PRIMARY KEY(user_id,quest_id));CREATE TABLE user_story_quest_items(user_id INTEGER,quest_id TEXT,item_key TEXT,quantity INTEGER,updated_at TEXT,PRIMARY KEY(user_id,quest_id,item_key));")
def labels(markup):
 rows=getattr(markup,'keyboard',[]) or []
 return [b.get('text') if isinstance(b,dict) else getattr(b,'text',None) for row in rows for b in row]
def main():
 c=sqlite3.connect(':memory:');c.row_factory=sqlite3.Row;schema(c);talk=next(q for q in STORY_QUEST_REGISTRY.values() if q.number==1)
 available={'npc_id':'elder','npc_name':'Староста','state':'AVAILABLE','quest':get_story_quest_view(c,user_id=1,quest=talk,player_level=1)};offer=_text(available)
 assert '📖 Коротко:' in offer and talk.description in offer and STORY_QUEST_TEXT[talk.quest_id]['acceptance_text'] not in offer and '💬 Поговорити' in labels(_markup(available))
 c.execute("INSERT INTO user_story_quests VALUES(1,?,'ACTIVE',0,1,0,'','','','')",(talk.quest_id,));c.commit();active={'npc_id':'elder','npc_name':'Староста','state':'ACTIVE','quest':get_story_quest_view(c,user_id=1,quest=talk,player_level=1)};conversation=_text(active)
 assert '💬 Розмова:' in conversation and STORY_QUEST_TEXT[talk.quest_id]['acceptance_text'] in conversation and talk.objective_text not in conversation and '✅ Зрозуміло' in labels(_markup(active,user_id=1,connection=c))
 kill=next(q for q in STORY_QUEST_REGISTRY.values() if q.number==2);non_talk={'npc_id':'mercenary_head','npc_name':'Голова Найманців','state':'AVAILABLE','quest':get_story_quest_view(c,user_id=2,quest=kill,player_level=1)};assert '✅ Прийняти квест' in labels(_markup(non_talk)) and '💬 Поговорити' not in labels(_markup(non_talk))
 assert len(STORY_QUEST_REGISTRY)==10 and 'start_path_011_unstable_glow' not in STORY_QUEST_REGISTRY
 print('STORY QUEST TALK CONVERSATION FLOW: PASS');return 0
if __name__=='__main__':raise SystemExit(main())
