#!/usr/bin/env python3
import ast,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from data.story_quest_content import STORY_QUEST_REGISTRY,STORY_QUEST_TEXT
from data.story_quests.start_path_01_10 import QUEST_ROWS as Q01
from data.story_quests.start_path_11_20 import QUEST_ROWS as Q11
assert tuple(row['definition']['number'] for row in Q01)==tuple(range(1,11))
assert tuple(row['definition']['number'] for row in Q11)==tuple(range(11,21))
assert tuple(q.number for q in STORY_QUEST_REGISTRY.values())==tuple(range(1,21))
assert 21 not in [q.number for q in STORY_QUEST_REGISTRY.values()]
assert set(STORY_QUEST_TEXT)==set(STORY_QUEST_REGISTRY)
source=(ROOT/'data'/'story_quest_content.py').read_text(encoding='utf-8-sig')
assert 'json.loads(' not in source
assert 'START_PATH_01_10' in source and 'START_PATH_11_20' in source
ast.parse(source)
print('STORY CONTENT MODULARIZATION: PASS')
