#!/usr/bin/env python3
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT)) if str(ROOT) not in sys.path else None
from systems.story_boss_invocation_adapter import StoryBossInvocationState,build_story_boss_look_around_presentation,parse_story_boss_callback,story_boss_help_text
from data.story_quest_content import STORY_QUEST_REGISTRY
q99=next(q for q in STORY_QUEST_REGISTRY.values() if q.number==99)
assert q99.boss_key=='goblin_king'
s=StoryBossInvocationState(99,'ACTIVE',0,1,'dark_forest','dark_forest',False,False,False)
p=build_story_boss_look_around_presentation(s);assert p is not None
flat=[x for row in p.rows for x in row]
assert ('👑 Викликати Короля Гоблінів','sqboss:v1:invoke:99') in flat
assert ('🧭 Як знайти Короля Гоблінів','sqboss:v1:help:99') in flat
assert parse_story_boss_callback('sqboss:v1:help:99')[1]==99
assert 'Темний Бір' in story_boss_help_text(99) and 'Короля Гоблінів' in story_boss_help_text(99)
r=(ROOT/'handlers/story_quest_npc_runtime.py').read_text(encoding='utf-8-sig')
w=(ROOT/'handlers/story_boss_invocation_wiring.py').read_text(encoding='utf-8-sig')
assert "definition.number in (49,99)" in r and "Як знайти Короля Гоблінів" in r
assert "quest_number not in (49, 99)" in w and "expected_invoke" in w
print('PASS: Stage 19.33.4')
