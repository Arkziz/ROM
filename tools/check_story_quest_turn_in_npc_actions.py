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
 assert giver['quest']['quest_id']==q4.quest_id and giver['npc_role']=='GIVER';assert elder['quest']['quest_id']==q4.quest_id and elder['npc_role']=='TURN_IN'
 assert labels(_markup(giver,user_id=1,connection=c))==[];assert labels(_markup(elder,user_id=1,connection=c))==['✅ Передати доказ']
 giver_text=_text(giver);elder_text=_text(elder);assert 'Кому передати:' in giver_text and 'Староста' in giver_text;assert 'Знахідку отримано:' in elder_text and 'Клапоть форми вартового' in elder_text
 # Before acquisition the receiver still recognizes the active quest but offers no completion.
 c.execute('DELETE FROM user_story_quest_items');c.commit();elder_wait=build_npc_story_quest_presentation(c,registry=STORY_QUEST_REGISTRY,user_id=1,npc_id='elder',player_level=1);assert elder_wait['quest']['quest_id']==q4.quest_id and labels(_markup(elder_wait,user_id=1,connection=c))==[]
 # Cross-NPC quest 7 follows the same giver/receiver ownership policy.
 c.execute('DELETE FROM user_story_quests');q7=next(q for q in STORY_QUEST_REGISTRY.values() if q.number==7);c.execute("INSERT INTO user_story_quests VALUES(1,?,'ACTIVE',0,1,0,'','','','')",(q7.quest_id,));c.execute("INSERT INTO user_story_quest_items VALUES(1,?,?,1,'')",(q7.quest_id,q7.quest_item.item_key));c.commit();g7=build_npc_story_quest_presentation(c,registry=STORY_QUEST_REGISTRY,user_id=1,npc_id='mercenary_head',player_level=1);b7=build_npc_story_quest_presentation(c,registry=STORY_QUEST_REGISTRY,user_id=1,npc_id='blacksmith',player_level=1);assert labels(_markup(g7,user_id=1,connection=c))==[] and labels(_markup(b7,user_id=1,connection=c))==['✅ Передати доказ']
 # Same-NPC ownership remains valid.
 c.execute('DELETE FROM user_story_quest_items');c.execute('DELETE FROM user_story_quests');q2=next(q for q in STORY_QUEST_REGISTRY.values() if q.number==2);c.execute("INSERT INTO user_story_quests VALUES(1,?,'ACTIVE',3,3,0,'','','','')",(q2.quest_id,));c.commit();same=build_npc_story_quest_presentation(c,registry=STORY_QUEST_REGISTRY,user_id=1,npc_id='mercenary_head',player_level=1);assert same['npc_role']=='TURN_IN' and labels(_markup(same,user_id=1,connection=c))==['✅ Завершити квест']
 assert q4.quest_item.consume_on_completion is False and q7.quest_item.consume_on_completion is False
 print('STORY QUEST TURN-IN NPC ACTIONS: PASS');return 0
if __name__=='__main__':raise SystemExit(main())
