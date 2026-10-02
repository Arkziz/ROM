#!/usr/bin/env python3
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from systems.story_boss_invocation_adapter import *
assert parse_story_boss_callback(INVOKE_CALLBACK)==(StoryBossAction.INVOKE,49)
assert parse_story_boss_callback(HELP_CALLBACK)==(StoryBossAction.HELP,49)
assert parse_story_boss_callback(RETURN_CALLBACK)==(StoryBossAction.RETURN,49)
assert parse_story_boss_callback("sqboss:v2:invoke:49") is None
assert max(len(x.encode("utf-8")) for x in (INVOKE_CALLBACK,HELP_CALLBACK,RETURN_CALLBACK))<=64
base=dict(quest_number=49,quest_status="ACTIVE",progress_current=0,progress_target=1,expected_location_id="start_path",current_location_id="start_path",has_active_encounter=False,has_active_travel=False,is_busy=False)
state=StoryBossInvocationState(**base)
assert evaluate_story_boss_invocation(state) is StoryBossInvocationDecision.ALLOW
for key,value,decision in (("progress_current",1,StoryBossInvocationDecision.ALREADY_DEFEATED),("current_location_id","city",StoryBossInvocationDecision.WRONG_LOCATION),("has_active_encounter",True,StoryBossInvocationDecision.ACTIVE_ENCOUNTER),("has_active_travel",True,StoryBossInvocationDecision.ACTIVE_TRAVEL),("is_busy",True,StoryBossInvocationDecision.BUSY)):
 data=dict(base);data[key]=value;assert evaluate_story_boss_invocation(StoryBossInvocationState(**data)) is decision
p=build_story_boss_look_around_presentation(state);assert p and p.rows[0][0][1]==INVOKE_CALLBACK and p.rows[1][0][1]==HELP_CALLBACK
data=dict(base);data["progress_current"]=1;p=build_story_boss_look_around_presentation(StoryBossInvocationState(**data));assert p and p.rows==((("🧭 Куди повернутися",RETURN_CALLBACK),),)
assert "Початок Шляху" in story_boss_help_text()
from data.story_quest_content import STORY_QUEST_REGISTRY
assert tuple(q.number for q in STORY_QUEST_REGISTRY.values())==tuple(range(1,51))
print("STORY BOSS INVOCATION ADAPTER: PASS")
