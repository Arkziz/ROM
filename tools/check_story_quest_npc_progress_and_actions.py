#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Production-shaped checks for NPC progress, readiness and journal UX."""
from __future__ import annotations
import sqlite3,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from data.story_quest_content import STORY_QUEST_REGISTRY
from handlers.story_quest_npc_runtime import _markup,_text
from handlers.story_quests import build_story_quest_detail_keyboard
from systems.story_quest_system import get_story_quest_view

def schema(c):
 c.executescript("CREATE TABLE user_story_quests(user_id INTEGER,quest_id TEXT,status TEXT,progress INTEGER,target_quantity INTEGER,reward_claimed INTEGER,accepted_at TEXT,completed_at TEXT,skipped_at TEXT,updated_at TEXT,PRIMARY KEY(user_id,quest_id));CREATE TABLE user_story_quest_items(user_id INTEGER,quest_id TEXT,item_key TEXT,quantity INTEGER,updated_at TEXT,PRIMARY KEY(user_id,quest_id,item_key));")
def buttons(markup):
 keyboard=getattr(markup,'keyboard',[]) or []
 return [getattr(b,'text',None) if not isinstance(b,dict) else b.get('text') for row in keyboard for b in row]
def main():
 c=sqlite3.connect(':memory:');c.row_factory=sqlite3.Row;schema(c);q=STORY_QUEST_REGISTRY['start_path_002_clear_the_path'];c.execute("INSERT INTO user_story_quests VALUES(1,?,'ACTIVE',0,3,0,'','','','')",(q.quest_id,));c.commit()
 view=get_story_quest_view(c,user_id=1,quest=q,player_level=1);p={'npc_id':'mercenary_head','npc_name':'Голова Найманців','state':'ACTIVE','quest':view};text=_text(p)
 assert 'Статус: 📖 Активний' in text and '📈 Прогрес:\n0/3' in text and 'Куди йти' not in text
 assert '✅ Завершити квест' not in buttons(_markup(p,user_id=1,connection=c))
 c.execute("UPDATE user_story_quests SET progress=3 WHERE user_id=1 AND quest_id=?",(q.quest_id,));c.commit();view=get_story_quest_view(c,user_id=1,quest=q,player_level=1);p['quest']=view
 assert '📈 Прогрес:\n3/3' in _text(p) and '✅ Завершити квест' in buttons(_markup(p,user_id=1,connection=c))
 talk=STORY_QUEST_REGISTRY['start_path_001_missing_patrol'];c.execute('DELETE FROM user_story_quests');c.execute("INSERT INTO user_story_quests VALUES(1,?,'ACTIVE',0,1,0,'','','','')",(talk.quest_id,));c.commit();tp={'npc_id':'elder','npc_name':'Староста','state':'ACTIVE','quest':get_story_quest_view(c,user_id=1,quest=talk,player_level=1)}
 assert '✅ Продовжити' in buttons(_markup(tp,user_id=1,connection=c))
 detail=build_story_quest_detail_keyboard(quest_id=q.quest_id,status='ACTIVE',page=0);labels=[b['text'] for row in detail for b in row]
 assert labels==['🔙 До журналу']
 print('STORY QUEST NPC PROGRESS AND ACTIONS: PASS');return 0
if __name__=='__main__':raise SystemExit(main())
