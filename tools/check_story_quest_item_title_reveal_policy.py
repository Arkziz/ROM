#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import ast,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
EXPECTED=json.loads('{"start_path_004_guard_uniform_scrap": "Слід патруля", "start_path_007_broken_guard_lantern": "Знахідка біля мосту", "start_path_013_runic_crystal_fragment": "Матеріальний слід аномалії", "start_path_019_guards_note": "Слід зниклого патруля", "start_path_023_guards_ring": "Особиста річ вартового", "start_path_029_torn_guard_cloak": "Слід нападу", "start_path_034_runemarked_wolf_pelt": "Матеріал для Коваля", "start_path_043_pack_leader_seal": "Незвичайна мітка", "start_path_046_pack_leader_fur": "Матеріал зі слідом Ватажка"}')
from data.story_quest_content import STORY_QUEST_REGISTRY
from data.story_quest_definitions import QuestType
from data.story_quest_title_presentation import PRE_REVEAL_TITLE_BY_QUEST_ID,resolve_story_quest_presentation_title
assert dict(PRE_REVEAL_TITLE_BY_QUEST_ID)==EXPECTED
by_number={q.number:q for q in STORY_QUEST_REGISTRY.values()}
for number,quest in sorted(by_number.items()):
 if quest.quest_type is QuestType.QUEST_ITEM:
  required=quest.quest_item.required_quantity
  before=resolve_story_quest_presentation_title(quest,"AVAILABLE",0)
  active=resolve_story_quest_presentation_title(quest,"ACTIVE",0)
  revealed=resolve_story_quest_presentation_title(quest,"ACTIVE",required)
  completed=resolve_story_quest_presentation_title(quest,"COMPLETED",required)
  if quest.quest_id in EXPECTED:
   assert before==active==EXPECTED[quest.quest_id]
   assert revealed==completed==quest.title
  else:
   assert before==active==revealed==completed==quest.title
 else:assert resolve_story_quest_presentation_title(quest,"LOCKED",0)==quest.title
for number in (15,26,37):assert by_number[number].quest_id not in EXPECTED
# Every pre-reveal title is unique and differs from canonical title.
assert len(set(EXPECTED.values()))==len(EXPECTED)==9
for quest_id,title in EXPECTED.items():assert title!=STORY_QUEST_REGISTRY[quest_id].title
# All four pre-reveal surfaces call the one canonical resolver.
surfaces={"hierarchy":"handlers/story_quest_hierarchy_ui.py","journal":"handlers/story_quests.py","npc":"handlers/story_quest_npc_runtime.py"}
source={k:(ROOT/v).read_text(encoding="utf-8") for k,v in surfaces.items()}
assert "title_reader(user_id, quest)" in source["hierarchy"]
assert source["journal"].count("resolve_story_quest_presentation_title")>=3
assert source["npc"].count("resolve_story_quest_presentation_title")>=2
assert "next_quest.title" not in source["npc"]
# Drop reveal remains exact item display_name and does not use neutral titles.
drop=(ROOT/"systems/story_quest_item_drop_system.py").read_text(encoding="utf-8")
assert "quest.quest_item.display_name" in drop and "PRE_REVEAL_TITLE" not in drop
print("STORY QUEST ITEM TITLE REVEAL POLICY: PASS")
