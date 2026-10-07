#!/usr/bin/env python3
from pathlib import Path
import sqlite3,sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT)) if str(ROOT) not in sys.path else None
from data.story_quest_content import STORY_QUEST_REGISTRY
from systems.story_quest_boss_call_system import get_active_story_boss_call
from systems.story_boss_invocation_adapter import StoryBossInvocationState,build_story_boss_look_around_presentation
q99=next(q for q in STORY_QUEST_REGISTRY.values() if q.number==99)
assert q99.boss_key=='goblin_king'
# Isolate the contract with a minimal active-row provider by temporarily replacing the module owner.
import systems.story_quest_boss_call_system as owner
original=owner.get_active_story_quest
try:
 owner.get_active_story_quest=lambda connection,user_id:{'quest_id':q99.quest_id,'status':'ACTIVE','progress':0,'target_quantity':1}
 call=get_active_story_boss_call(user_id=1,current_location_id='dark_forest',connection=object())
finally:
 owner.get_active_story_quest=original
assert call['allowed'] is True and call['quest_number']==99 and call['quest_status']=='ACTIVE'
assert call['progress_current']==0 and call['progress_target']==1 and call['boss_key']=='goblin_king'
s=StoryBossInvocationState(call['quest_number'],call['quest_status'],call['progress_current'],call['progress_target'],call['location_id'],'dark_forest',False,False,False)
p=build_story_boss_look_around_presentation(s);flat=[x for row in p.rows for x in row]
assert ('👑 Викликати Короля Гоблінів','sqboss:v1:invoke:99') in flat
assert ('🧭 Як знайти Короля Гоблінів','sqboss:v1:help:99') in flat
print('PASS: Stage 19.33.6')
