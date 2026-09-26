#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations
import sqlite3,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from handlers.story_quests import build_production_story_quest_detail
from data.story_quest_content import STORY_QUEST_REGISTRY

def schema(c):c.executescript("CREATE TABLE user_story_quests(user_id INTEGER,quest_id TEXT,status TEXT,progress INTEGER,target_quantity INTEGER,reward_claimed INTEGER,accepted_at TEXT,completed_at TEXT,skipped_at TEXT,updated_at TEXT,PRIMARY KEY(user_id,quest_id));CREATE TABLE user_story_quest_items(user_id INTEGER,quest_id TEXT,item_key TEXT,quantity INTEGER,updated_at TEXT,PRIMARY KEY(user_id,quest_id,item_key));")
def main():
 c=sqlite3.connect(':memory:');c.row_factory=sqlite3.Row;schema(c);q4=STORY_QUEST_REGISTRY['start_path_004_guard_uniform_scrap'];c.execute("INSERT INTO user_story_quests VALUES(1,?,'ACTIVE',0,1,0,'','','','')",(q4.quest_id,));c.commit()
 before=build_production_story_quest_detail(c,user_id=1,quest_id=q4.quest_id,player_level=1)['text'];assert '📈 Прогрес:\n0/1' in before and '🔎 Стан пошуку:\nДоказ ще не знайдено.' in before and '🧭 Де шукати:' in before and 'Староста' not in before
 c.execute("INSERT INTO user_story_quest_items VALUES(1,?,?,1,'')",(q4.quest_id,q4.quest_item.item_key));c.commit();after=build_production_story_quest_detail(c,user_id=1,quest_id=q4.quest_id,player_level=1)['text'];assert '📈 Прогрес:\n1/1' in after and '✅ Знахідку отримано:\nКлапоть форми вартового' in after and '🧭 Наступний крок:' in after and 'Староста' in after
 q2=STORY_QUEST_REGISTRY['start_path_002_clear_the_path'];c.execute('DELETE FROM user_story_quests');c.execute('DELETE FROM user_story_quest_items');c.execute("INSERT INTO user_story_quests VALUES(1,?,'ACTIVE',1,3,0,'','','','')",(q2.quest_id,));c.commit();kill=build_production_story_quest_detail(c,user_id=1,quest_id=q2.quest_id,player_level=1)['text'];assert '📈 Прогрес:\n1/3' in kill and 'Стан пошуку' not in kill and 'Знахідку отримано' not in kill
 q7=next(q for q in STORY_QUEST_REGISTRY.values() if q.number==7);assert q7.quest_id=='start_path_007_broken_guard_lantern' and q7.quest_item.item_key=='start_path_broken_guard_lantern' and q7.quest_item.display_name=='Зламаний ліхтар вартового' and abs(q7.quest_item.drop_chance-0.15)<1e-12
 assert len(STORY_QUEST_REGISTRY)==10 and 'start_path_011_unstable_glow' not in STORY_QUEST_REGISTRY
 print('STORY QUEST ITEM JOURNAL PROGRESS: PASS');return 0
if __name__=='__main__':raise SystemExit(main())
