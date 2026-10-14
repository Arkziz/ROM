#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Producer-to-consumer checks for reward previews and quest transitions."""
from __future__ import annotations
import sqlite3,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from data.story_quest_content import STORY_QUEST_REGISTRY
from handlers.story_quest_npc_runtime import _completion_receipt,_text
from systems.story_quest_completion_system import complete_active_story_quest
from systems.story_quest_system import get_story_quest_status,get_story_quest_view

def schema(c):
 c.executescript("CREATE TABLE users(user_id INTEGER PRIMARY KEY,level INTEGER,exp INTEGER,gold REAL);CREATE TABLE user_story_quests(user_id INTEGER,quest_id TEXT,status TEXT,progress INTEGER,target_quantity INTEGER,reward_claimed INTEGER,accepted_at TEXT,completed_at TEXT,skipped_at TEXT,updated_at TEXT,PRIMARY KEY(user_id,quest_id));CREATE TABLE user_story_quest_items(user_id INTEGER,quest_id TEXT,item_key TEXT,quantity INTEGER,updated_at TEXT,PRIMARY KEY(user_id,quest_id,item_key));")
def presentation(c,q,state,user_id=1):return {'npc_id':q.giver_npc_id,'npc_name':'NPC','state':state,'quest':get_story_quest_view(c,user_id=user_id,quest=q,player_level=1)}
def main():
 c=sqlite3.connect(':memory:');c.row_factory=sqlite3.Row;schema(c);c.execute('INSERT INTO users VALUES(1,1,0,0.0)');q2=STORY_QUEST_REGISTRY['start_path_002_clear_the_path'];available=_text(presentation(c,q2,'AVAILABLE'));assert '🎁 Нагорода:' in available and '• 30 EXP' in available and '• 0.27 золота' in available
 c.execute("INSERT INTO user_story_quests VALUES(1,?,'ACTIVE',3,3,0,'','','','')",(q2.quest_id,));c.commit();active=_text(presentation(c,q2,'ACTIVE'));assert '🎁 Нагорода:' in active and '📈 Прогрес:\n3/3' in active
 def shaped_reward_adapter(*,connection,user_id,quest,idempotency_key):
  connection.execute('UPDATE users SET exp=exp+?,gold=ROUND(gold+?,2) WHERE user_id=?',(quest.reward.exp,quest.reward.gold,user_id))
  return {'quest_id':quest.quest_id,'idempotency_key':idempotency_key,'exp_awarded':quest.reward.exp,'gold_awarded':quest.reward.gold,'gold_balance':0.27,'exp_result':{'exp_gained':quest.reward.exp}}
 result=complete_active_story_quest(c,registry=STORY_QUEST_REGISTRY,user_id=1,quest_id=q2.quest_id,reward_adapter=shaped_reward_adapter,expected_turn_in_npc_id='mercenary_head');receipt=_completion_receipt(c,1,q2,'mercenary_head',result);assert '✅ Квест завершено' in receipt and '🎁 Отримано:' in receipt and '• 30 EXP' in receipt and '• 0.27 золота' in receipt and '📜 3. Останній слід' in receipt and 'Новий квест можна прийняти' in receipt
 q3=STORY_QUEST_REGISTRY['start_path_003_last_report'];assert get_story_quest_status(c,user_id=1,quest=q3,player_level=1).value=='AVAILABLE';assert c.execute("SELECT COUNT(*) FROM user_story_quests WHERE quest_id=?",(q3.quest_id,)).fetchone()[0]==0
 replay=complete_active_story_quest(c,registry=STORY_QUEST_REGISTRY,user_id=1,quest_id=q2.quest_id,reward_adapter=lambda **kw: (_ for _ in ()).throw(AssertionError('reward replay')),expected_turn_in_npc_id='mercenary_head');replay_text=_completion_receipt(c,1,q2,'mercenary_head',replay);balance=c.execute('SELECT exp,gold FROM users WHERE user_id=1').fetchone();assert 'Нагороду було видано раніше.' in replay_text;assert int(balance['exp'])==30;assert abs(float(balance['gold'])-0.27)<1e-9
 c.execute("INSERT INTO user_story_quests VALUES(1,?,'COMPLETED',1,1,1,'','','','')",(q3.quest_id,));q4=STORY_QUEST_REGISTRY['start_path_004_guard_uniform_scrap'];same_npc=_completion_receipt(c,1,q3,'mercenary_head',{'already_processed':False,'reward':{'exp_awarded':30,'gold_awarded':0.27}});assert '📜 4. Клапоть форми' in same_npc and 'Новий квест можна прийняти у цього персонажа нижче.' in same_npc
 c.execute("INSERT INTO user_story_quests VALUES(1,?,'COMPLETED',1,1,1,'','','','')",(q4.quest_id,));q5=STORY_QUEST_REGISTRY['start_path_005_evidence_from_the_trail'];different_npc=_completion_receipt(c,1,q4,'mercenary_head',{'already_processed':False,'reward':{'exp_awarded':30,'gold_awarded':0.27}});assert '📜 5. Доказ із хащі' in different_npc and 'Ратуша' in different_npc and 'Староста' in different_npc
 for n in range(5,10):
  q=next(x for x in STORY_QUEST_REGISTRY.values() if x.number==n);c.execute("INSERT OR REPLACE INTO user_story_quests VALUES(1,?,'COMPLETED',1,1,1,'','','','')",(q.quest_id,))
 q10=next(x for x in STORY_QUEST_REGISTRY.values() if x.number==10);chapter=_completion_receipt(c,1,q10,'elder',{'already_processed':False,'reward':{'exp_awarded':30,'gold_awarded':0.27}});assert 'Наступна глава поки не активована.' in chapter and len(STORY_QUEST_REGISTRY)==10
 print('STORY QUEST REWARDS AND TRANSITIONS: PASS');return 0
if __name__=='__main__':raise SystemExit(main())
