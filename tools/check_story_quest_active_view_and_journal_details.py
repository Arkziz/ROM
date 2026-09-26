#!/usr/bin/env python3
from __future__ import annotations
import sqlite3,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from data.story_quest_content import STORY_QUEST_REGISTRY
from handlers.story_quest_npc_runtime import _text
from handlers.story_quests import build_production_story_quest_detail,render_story_quest_journal
from systems.story_quest_system import get_story_quest_view
def schema(c):c.executescript("CREATE TABLE user_story_quests(user_id INTEGER,quest_id TEXT,status TEXT,progress INTEGER,target_quantity INTEGER,reward_claimed INTEGER,accepted_at TEXT,completed_at TEXT,skipped_at TEXT,updated_at TEXT,PRIMARY KEY(user_id,quest_id));CREATE TABLE user_story_quest_items(user_id INTEGER,quest_id TEXT,item_key TEXT,quantity INTEGER,updated_at TEXT,PRIMARY KEY(user_id,quest_id,item_key));")
def main():
 c=sqlite3.connect(':memory:');c.row_factory=sqlite3.Row;schema(c);q=STORY_QUEST_REGISTRY['start_path_001_missing_patrol'];c.execute("INSERT INTO user_story_quests VALUES(1,?,'ACTIVE',0,1,0,'','','','')",(q.quest_id,));view=get_story_quest_view(c,user_id=1,quest=q,player_level=1);presentation={'npc_name':'Староста','state':'ACTIVE','quest':view};text=_text(presentation);assert q.objective_text in text and 'Статус: 📖 Активний' in text
 items=[get_story_quest_view(c,user_id=1,quest=x,player_level=1) for x in STORY_QUEST_REGISTRY.values()];journal=render_story_quest_journal(items);callbacks=[b['callback_data'] for row in journal['keyboard'] for b in row if isinstance(b,dict) and b.get('callback_data','').startswith('story_quest:detail:')];assert len(callbacks)==10
 detail=build_production_story_quest_detail(c,user_id=1,quest_id=q.quest_id,player_level=1);assert q.description in detail['text'] and q.objective_text in detail['text'] and 'Ратуша' in detail['text'] and '30 EXP' in detail['text'] and '0.27 золота' in detail['text'];assert any(b.get('text')=='🔙 До журналу' for row in detail['keyboard'] for b in row)
 locked=build_production_story_quest_detail(c,user_id=1,quest_id='start_path_002_clear_the_path',player_level=1);assert 'Для відкриття' in locked['text'] and 'завершити квест 1' in locked['text']
 print('STORY QUEST ACTIVE VIEW AND JOURNAL DETAILS: PASS');return 0
if __name__=='__main__':raise SystemExit(main())
