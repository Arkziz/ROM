#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))
from data.story_quest_content import STORY_QUEST_REGISTRY, STORY_QUEST_TEXT
from data.story_quest_hierarchy import get_story_section, get_story_section_for_quest_number, validate_story_hierarchy_metadata
nums=sorted(q.number for q in STORY_QUEST_REGISTRY.values())
assert nums==list(range(1,41)) and 41 not in nums
section=get_story_section("start_path_04")
assert section.display_title=="Розділ 4. Вовча загроза"
assert tuple(section.quest_numbers)==tuple(range(31,41))
assert section.required_level==4
assert get_story_section_for_quest_number(31).section_id=="start_path_04"
assert get_story_section_for_quest_number(40).section_id=="start_path_04"
q={x.number:x for x in STORY_QUEST_REGISTRY.values()}
for n in range(31,41):
 text=STORY_QUEST_TEXT[q[n].quest_id]
 assert set(text)=={"acceptance_text","completion_text","progress_text","drop_message"}
 assert text["acceptance_text"] and text["completion_text"] and text["progress_text"]
for n in range(31,41):
 assert q[n].navigation.location_id==q[n].location_id
 assert q[n].navigation.giver_npc_id==q[n].giver_npc_id
 assert q[n].navigation.turn_in_npc_id==(q[n].turn_in_npc_id or q[n].giver_npc_id)
assert [q[n].target_quantity for n in (32,36,39)]==[10,12,12]
for n,key in ((34,"start_path_runemarked_wolf_pelt"),(37,"start_path_runemarked_den_token")):
 assert q[n].quest_item.item_key==key and q[n].quest_item.drop_chance==0.15
for n,key in ((35,"start_path_runemarked_wolf_pelt"),(38,"start_path_runemarked_den_token")):
 assert len(q[n].required_quest_items)==1 and q[n].required_quest_items[0].item_key==key and q[n].required_quest_items[0].consume is True
 assert q[n].quest_item_consumption=="atomic_exact_once"
assert not q[40].required_quest_items
assert all(q[n].reward.exp==48 and abs(q[n].reward.gold-0.89)<1e-9 for n in range(31,41))
validate_story_hierarchy_metadata()
print("STORY QUEST BATCH 31-40 ACTIVATION: PASS")
