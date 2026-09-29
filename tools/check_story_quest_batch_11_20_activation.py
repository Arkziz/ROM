#!/usr/bin/env python3
import sys
from pathlib import Path
R=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(R)) if str(R) not in sys.path else None
from data.story_quest_content import STORY_QUEST_REGISTRY as REG,STORY_QUEST_TEXT as TEXT
from data.story_quest_npcs import get_story_quest_npc
rows=tuple(REG.values());assert tuple(q.number for q in rows)==tuple(range(1,21))
by={q.number:q for q in rows};assert 21 not in by
assert [by[n].quest_type.value for n in range(11,21)]==['TALK', 'KILL_REGION', 'QUEST_ITEM', 'TURN_IN', 'QUEST_ITEM', 'TURN_IN', 'KILL_REGION', 'TALK', 'QUEST_ITEM', 'TURN_IN']
assert all(by[n].unlock_level==2 and by[n].reward.exp==36 and abs(by[n].reward.gold-.43)<1e-9 for n in range(11,21))
assert by[13].turn_in_npc_id==by[19].turn_in_npc_id=='rune_master'
assert by[14].required_quest_items[0].item_key=='start_path_runic_crystal_fragment'
assert by[16].required_quest_items[0].item_key=='start_path_runic_dust_sample'
assert by[20].required_quest_items[0].item_key=='start_path_guard_note'
assert all(get_story_quest_npc(x).production_route_exists for x in ('rune_master','alchemist','elder'))
assert all(TEXT[by[n].quest_id]['drop_message'] for n in (13,15,19))
print('STORY QUEST BATCH 11-20 ACTIVATION: PASS')
