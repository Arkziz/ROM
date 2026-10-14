#!/usr/bin/env python3
import sqlite3,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT)) if str(ROOT) not in sys.path else None
from data.story_quest_content import STORY_QUEST_REGISTRY
TARGETS={12: 8, 17: 10, 32: 8, 36: 10, 39: 10, 42: 8, 45: 10};EXCEPTIONS={2: 3, 6: 5, 9: 6};ROUTES={80: '🏙️ Місто → 📜 Гільдія Найманців → ⚔️ Голова Найманців', 90: '🏙️ Місто → ⚒️ Ремісничий квартал → 💠 Рунний Майстер'}
by={q.number:q for q in STORY_QUEST_REGISTRY.values()}
assert tuple(sorted(by))==tuple(range(1,101))
for n,v in TARGETS.items():
 q=by[n];assert q.target_quantity==v and f"{v} будь-яких істот" in q.objective_text
for n,v in EXCEPTIONS.items():assert by[n].target_quantity==v
for n,v in ROUTES.items():assert by[n].navigation.next_step_hint==v
# Full position policy except explicit introductory exceptions.
for start in range(1,101,10):
 kills=[q for q in by.values() if start<=q.number<=start+9 and q.quest_type.value=='KILL_REGION']
 for i,q in enumerate(sorted(kills,key=lambda x:x.number)):
  expected=EXCEPTIONS.get(q.number,8 if i==0 else 10);assert q.target_quantity==expected,(q.number,q.target_quantity,expected)
# Ukrainian numeric nouns remain correct for all static KILL objectives.
for q in by.values():
 if q.quest_type.value=='KILL_REGION':assert f"{q.target_quantity} будь-яких істот" in q.objective_text
# Migration contract: ACTIVE only, clamp without completion/reward.
import importlib;m=importlib.import_module('migrations.054_story_quest_kill_target_normalization')
c=sqlite3.connect(':memory:');c.execute('CREATE TABLE user_story_quests(quest_number INTEGER,status TEXT,progress INTEGER,target_quantity INTEGER,reward_claimed INTEGER,updated_at TEXT)')
c.executemany('INSERT INTO user_story_quests VALUES(?,?,?,?,?,?)',[(42,'ACTIVE',11,15,0,'t'),(45,'ACTIVE',2,15,0,'t'),(36,'COMPLETED',12,12,1,'t')]);m.up(c)
r=c.execute('SELECT status,progress,target_quantity,reward_claimed FROM user_story_quests WHERE quest_number=42').fetchone();assert r==('ACTIVE',8,8,0)
r=c.execute('SELECT status,progress,target_quantity,reward_claimed FROM user_story_quests WHERE quest_number=45').fetchone();assert r==('ACTIVE',2,10,0)
r=c.execute('SELECT status,progress,target_quantity,reward_claimed FROM user_story_quests WHERE quest_number=36').fetchone();assert r==('COMPLETED',12,12,1)
print('PASS: Stage 19.34.5')
