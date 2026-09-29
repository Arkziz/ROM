"""Authoritative production story content: Start Path quests 1-20."""
from __future__ import annotations
from data.story_quests.start_path_01_10 import QUEST_ROWS as START_PATH_01_10
from data.story_quests.start_path_11_20 import QUEST_ROWS as START_PATH_11_20
from types import MappingProxyType
from data.story_quest_definitions import NavigationDefinition,QuestItemDefinition,RequiredQuestItemDefinition,RewardDefinition,StoryQuestDefinition,QuestType,validate_story_quest_pack
_DATA=list((*START_PATH_01_10, *START_PATH_11_20))
def _definition(row):
 d=row["definition"]; item=d.get("quest_item"); nav=d["navigation"]
 return StoryQuestDefinition(quest_id=d["quest_id"],number=d["number"],title=d["title"],quest_type=QuestType(d["quest_type"]),location_id=d["location_id"],unlock_level=d["unlock_level"],previous_quest_id=d.get("previous_quest_id"),giver_npc_id=d["giver_npc_id"],turn_in_npc_id=d.get("turn_in_npc_id"),description=d["description"],objective_text=d["objective_text"],target_quantity=d["target_quantity"],boss_key=d.get("boss_key"),quest_item=QuestItemDefinition(**item) if item else None,required_quest_items=tuple(RequiredQuestItemDefinition(**x) for x in d.get("required_quest_items",[])),quest_item_consumption=d.get("quest_item_consumption","default"),reward=RewardDefinition(**d["reward"]),navigation=NavigationDefinition(**nav))
STORY_QUEST_REGISTRY=validate_story_quest_pack(tuple(_definition(row) for row in _DATA))
STORY_QUEST_TEXT=MappingProxyType({row["definition"]["quest_id"]:MappingProxyType({"acceptance_text":row["acceptance_text"],"completion_text":row["completion_text"],"progress_text":row["progress_text"],"drop_message":row.get("drop_message","")}) for row in _DATA})
assert tuple(q.number for q in STORY_QUEST_REGISTRY.values())==tuple(range(1,21))
