#!/usr/bin/env python3
from pathlib import Path
import json,sys
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from data.story_quest_content import STORY_QUEST_REGISTRY
report=json.loads((ROOT/'reports/stage_19_25_1_story_quests_21_30_audit.json').read_text(encoding='utf-8'))
assert report['stage']=='19.25.1'
assert report['candidate_audit']['quest_numbers']==list(range(21,31))
assert report['candidate_audit']['errors']==[]
assert sorted(q.number for q in STORY_QUEST_REGISTRY.values())==list(range(1,21))
assert report['production_database_mutation'] is False
print('STORY QUESTS 21-30 AUDIT: PASS')
