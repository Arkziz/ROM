#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Isolated semantic regression for Stage 19.23.2 contracts."""
from __future__ import annotations
import sqlite3
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))
from data.story_quest_definitions import QuestType, RequiredQuestItemDefinition, RewardDefinition, StoryQuestDefinition, validate_story_quest_definition
from systems.story_quest_completion_system import StoryQuestCompletionError, complete_active_story_quest

def schema(c):
 c.executescript("""CREATE TABLE users(user_id INTEGER PRIMARY KEY,level INTEGER,exp INTEGER,gold REAL); CREATE TABLE user_story_quests(user_id INTEGER,quest_id TEXT,status TEXT,progress INTEGER,target_quantity INTEGER,reward_claimed INTEGER,accepted_at TEXT,completed_at TEXT,skipped_at TEXT,updated_at TEXT,PRIMARY KEY(user_id,quest_id)); CREATE TABLE user_story_quest_items(user_id INTEGER,quest_id TEXT,item_key TEXT,quantity INTEGER,updated_at TEXT,PRIMARY KEY(user_id,quest_id,item_key));""")
def active(c,q): c.execute("INSERT INTO user_story_quests VALUES(?,?, 'ACTIVE',0,1,0,'','','','')",(1,q.quest_id))
def reward_adapter(**kw):
 c=kw['connection']; q=kw['quest']; c.execute("UPDATE users SET exp=exp+?,gold=ROUND(gold+?,2) WHERE user_id=?",(q.reward.exp,q.reward.gold,kw['user_id'])); return {'exp':q.reward.exp,'gold':q.reward.gold}
def q(qid,items,policy):
 x=StoryQuestDefinition(qid,1,'Fixture',QuestType.TURN_IN,'start_path',1,None,'elder','elder','Fixture','Fixture',required_quest_items=items,quest_item_consumption=policy,reward=RewardDefinition(7,0.27)); validate_story_quest_definition(x); return x
def main():
 c=sqlite3.connect(':memory:'); c.row_factory=sqlite3.Row; schema(c); c.execute("INSERT INTO users VALUES(1,1,0,0.0)")
 talk=StoryQuestDefinition('talk',1,'Talk',QuestType.TALK,'start_path',1,None,'trader','trader','Talk','Talk',required_quest_items=(RequiredQuestItemDefinition('ring',1,False),),quest_item_consumption='none',reward=RewardDefinition(7,0.27)); validate_story_quest_definition(talk); active(c,talk); c.execute("INSERT INTO user_story_quest_items VALUES(1,'source','ring',1,'1')"); c.commit()
 complete_active_story_quest(c,registry={'talk':talk},user_id=1,quest_id='talk',reward_adapter=reward_adapter,expected_turn_in_npc_id='trader'); assert c.execute("SELECT quantity FROM user_story_quest_items WHERE item_key='ring'").fetchone()[0]==1
 c.execute("DELETE FROM user_story_quests"); c.execute("DELETE FROM user_story_quest_items WHERE item_key='ring'"); multi=q('multi',(RequiredQuestItemDefinition('ring',1,True),RequiredQuestItemDefinition('shield',1,True),RequiredQuestItemDefinition('cloak',1,True)),'atomic_exact_once_all_or_nothing'); active(c,multi)
 for n,k in enumerate(('shield','cloak'),2): c.execute("INSERT INTO user_story_quest_items VALUES(1,?,?,1,?)",(f's{n}',k,str(n)))
 c.commit()
 before=tuple(c.execute("SELECT item_key,quantity FROM user_story_quest_items ORDER BY item_key"));
 try: complete_active_story_quest(c,registry={'multi':multi},user_id=1,quest_id='multi',reward_adapter=reward_adapter,expected_turn_in_npc_id='elder')
 except StoryQuestCompletionError: pass
 else: raise AssertionError('incomplete multi-item turn-in accepted')
 assert tuple(c.execute("SELECT item_key,quantity FROM user_story_quest_items ORDER BY item_key"))==before
 c.execute("INSERT INTO user_story_quest_items VALUES(1,'source','ring',1,'4') ON CONFLICT(user_id,quest_id,item_key) DO UPDATE SET quantity=1"); c.commit()
 complete_active_story_quest(c,registry={'multi':multi},user_id=1,quest_id='multi',reward_adapter=reward_adapter,expected_turn_in_npc_id='elder'); assert c.execute("SELECT COUNT(*) FROM user_story_quest_items WHERE item_key IN ('ring','shield','cloak')").fetchone()[0]==0
 exp,gold=c.execute("SELECT exp,gold FROM users WHERE user_id=1").fetchone(); assert exp==14 and abs(gold-0.54)<1e-9
 print('STORY QUEST CROSS-CUTTING RUNTIME GAPS: PASS'); return 0
if __name__=='__main__': raise SystemExit(main())
