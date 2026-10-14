#!/usr/bin/env python3
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from data.story_quest_content import STORY_QUEST_REGISTRY
by={q.number:q for q in STORY_QUEST_REGISTRY.values()}
assert tuple(q.number for q in STORY_QUEST_REGISTRY.values())==tuple(range(1,21))
assert by[11].previous_quest_id==by[10].quest_id
assert by[11].unlock_level==2
print('QUEST 11 RUNTIME AVAILABILITY AUDIT CHECKER: PASS')
