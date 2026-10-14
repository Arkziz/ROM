#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations
import sqlite3,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from data.story_quest_content import STORY_QUEST_REGISTRY
from handlers.story_quest_npc_runtime import _markup,_text
from systems.story_quest_npc_acceptance_system import build_npc_story_quest_presentation

def schema(c):c.executescript("CREATE TABLE user_story_quests(user_id INTEGER,quest_id TEXT,status TEXT,progress INTEGER,target_quantity INTEGER,reward_claimed INTEGER,accepted_at TEXT,completed_at TEXT,skipped_at TEXT,updated_at TEXT,PRIMARY KEY(user_id,quest_id));CREATE TABLE user_story_quest_items(user_id INTEGER,quest_id TEXT,item_key TEXT,quantity INTEGER,updated_at TEXT,PRIMARY KEY(user_id,quest_id,item_key));")
def labels(markup):return [button.text for row in markup.keyboard for button in row]
def main():
 c=sqlite3.connect(':memory:');c.row_factory=sqlite3.Row;schema(c);q4=next(q for q in STORY_QUEST_REGISTRY.values() if q.number==4)
 c.execute("INSERT INTO user_story_quests VALUES(1,?,'ACTIVE',0,1,0,'','','','')",(q4.quest_id,));c.execute("INSERT INTO user_story_quest_items VALUES(1,?,?,1,'')",(q4.quest_id,q4.quest_item.item_key));c.commit()
 giver=build_npc_story_quest_presentation(c,registry=STORY_QUEST_REGISTRY,user_id=1,npc_id='mercenary_head',player_level=1);elder=build_npc_story_quest_presentation(c,registry=STORY_QUEST_REGISTRY,user_id=1,npc_id='elder',player_level=1)
 assert giver['quest']['quest_id']==q4.quest_id and giver['npc_role']=='TURN_IN';assert elder['quest'] is None
 assert labels(_markup(giver,user_id=1,connection=c))==['✅ Доповісти про знахідку'];assert labels(_markup(elder,user_id=1,connection=c))==[]
 giver_text=_text(giver);assert 'Знахідку отримано:' in giver_text and 'Клапоть форми вартового' in giver_text and 'Кому передати:' not in giver_text
 c.execute('DELETE FROM user_story_quest_items');c.commit();giver_wait=build_npc_story_quest_presentation(c,registry=STORY_QUEST_REGISTRY,user_id=1,npc_id='mercenary_head',player_level=1);assert giver_wait['quest']['quest_id']==q4.quest_id and labels(_markup(giver_wait,user_id=1,connection=c))==[]
 c.execute('DELETE FROM user_story_quests');q7=next(q for q in STORY_QUEST_REGISTRY.values() if q.number==7);c.execute("INSERT INTO user_story_quests VALUES(1,?,'ACTIVE',0,1,0,'','','','')",(q7.quest_id,));c.execute("INSERT INTO user_story_quest_items VALUES(1,?,?,1,'')",(q7.quest_id,q7.quest_item.item_key));c.commit();g7=build_npc_story_quest_presentation(c,registry=STORY_QUEST_REGISTRY,user_id=1,npc_id='mercenary_head',player_level=1);b7=build_npc_story_quest_presentation(c,registry=STORY_QUEST_REGISTRY,user_id=1,npc_id='blacksmith',player_level=1);assert g7['npc_role']=='TURN_IN' and labels(_markup(g7,user_id=1,connection=c))==['✅ Доповісти про знахідку'] and b7['quest'] is None
 c.execute('DELETE FROM user_story_quest_items');c.execute('DELETE FROM user_story_quests');q2=next(q for q in STORY_QUEST_REGISTRY.values() if q.number==2);c.execute("INSERT INTO user_story_quests VALUES(1,?,'ACTIVE',3,3,0,'','','','')",(q2.quest_id,));c.commit();same=build_npc_story_quest_presentation(c,registry=STORY_QUEST_REGISTRY,user_id=1,npc_id='mercenary_head',player_level=1);assert same['npc_role']=='TURN_IN' and labels(_markup(same,user_id=1,connection=c))==['✅ Завершити квест']
 assert q4.quest_item.consume_on_completion is False and q7.quest_item.consume_on_completion is False
 print('STORY QUEST TURN-IN NPC ACTIONS: PASS');return 0
if __name__=='__main__':raise SystemExit(main())
