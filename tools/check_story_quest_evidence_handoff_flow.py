#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations
import json,sqlite3,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from data.story_quest_content import STORY_QUEST_REGISTRY,STORY_QUEST_TEXT
from handlers.story_quest_npc_runtime import _markup
from systems.story_quest_npc_acceptance_system import build_npc_story_quest_presentation

def schema(c):c.executescript("CREATE TABLE user_story_quests(user_id INTEGER,quest_id TEXT,status TEXT,progress INTEGER,target_quantity INTEGER,reward_claimed INTEGER,accepted_at TEXT,completed_at TEXT,skipped_at TEXT,updated_at TEXT,PRIMARY KEY(user_id,quest_id));CREATE TABLE user_story_quest_items(user_id INTEGER,quest_id TEXT,item_key TEXT,quantity INTEGER,updated_at TEXT,PRIMARY KEY(user_id,quest_id,item_key));")
def labels(markup):return [button.text for row in markup.keyboard for button in row]
def main():
 q4=next(q for q in STORY_QUEST_REGISTRY.values() if q.number==4);q5=next(q for q in STORY_QUEST_REGISTRY.values() if q.number==5);q7=next(q for q in STORY_QUEST_REGISTRY.values() if q.number==7);q8=next(q for q in STORY_QUEST_REGISTRY.values() if q.number==8)
 assert q4.giver_npc_id==q4.turn_in_npc_id=='mercenary_head';assert q7.giver_npc_id==q7.turn_in_npc_id=='mercenary_head';assert q5.giver_npc_id==q5.turn_in_npc_id=='elder';assert q8.giver_npc_id==q8.turn_in_npc_id=='blacksmith'
 assert q4.quest_item.consume_on_completion is False and q7.quest_item.consume_on_completion is False;assert q5.required_quest_items[0].consume is True and q8.required_quest_items[0].consume is True
 assert 'радить негайно показати його Старості' in STORY_QUEST_TEXT[q4.quest_id]['completion_text'];assert 'направляє героя до Коваля' in STORY_QUEST_TEXT[q7.quest_id]['completion_text']
 candidate=json.loads((ROOT/'Квести'/'ROM_квести_Початок_Шляху_candidate.json').read_text(encoding='utf-8-sig'));by={int(q['number']):q for q in candidate['quests']};assert by[4]['turn_in_npc_id']=='mercenary_head' and by[7]['turn_in_npc_id']=='mercenary_head';assert 'доповісти Голові Найманців' in by[4]['quest_item']['drop_message'] and 'доповісти Голові Найманців' in by[7]['quest_item']['drop_message']
 c=sqlite3.connect(':memory:');c.row_factory=sqlite3.Row;schema(c)
 for quest in (q4,q7):
  c.execute('DELETE FROM user_story_quests');c.execute('DELETE FROM user_story_quest_items');c.execute("INSERT INTO user_story_quests VALUES(1,?,'ACTIVE',0,1,0,'','','','')",(quest.quest_id,));c.execute("INSERT INTO user_story_quest_items VALUES(1,?,?,1,'')",(quest.quest_id,quest.quest_item.item_key));c.commit();giver=build_npc_story_quest_presentation(c,registry=STORY_QUEST_REGISTRY,user_id=1,npc_id='mercenary_head',player_level=1);assert giver['npc_role']=='TURN_IN' and labels(_markup(giver,user_id=1,connection=c))==['✅ Доповісти про знахідку']
  other='elder' if quest.number==4 else 'blacksmith';receiver=build_npc_story_quest_presentation(c,registry=STORY_QUEST_REGISTRY,user_id=1,npc_id=other,player_level=1);assert receiver['quest'] is None
 assert len(STORY_QUEST_REGISTRY)==10 and 'start_path_011_unstable_glow' not in STORY_QUEST_REGISTRY
 print('STORY QUEST EVIDENCE HANDOFF FLOW: PASS');return 0
if __name__=='__main__':raise SystemExit(main())
