#!/usr/bin/env python3
from pathlib import Path
import ast,sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT)) if str(ROOT) not in sys.path else None
p=ROOT/'handlers/story_boss_invocation_wiring.py'
s=p.read_text(encoding='utf-8-sig');ast.parse(s)
block=s[s.index('def _active_story_boss_callback_call'):s.index('def register_story_boss_invocation_callbacks')]
assert 'get_active_story_quest' in block and 'QuestType.BOSS' in block
assert '_active_call(' not in block
assert 'expected_quest_number' in block and 'progress_current' in block
assert '_presentation_for_user(call.from_user.id)' in s
assert 'expected_invoke = f"sqboss:v1:invoke:{quest_number}"' in s
from systems.story_boss_invocation_adapter import story_boss_help_text
assert 'Темний Бір' in story_boss_help_text(99) and 'Початок Шляху' in story_boss_help_text(49)
print('PASS: Stage 19.33.5')
