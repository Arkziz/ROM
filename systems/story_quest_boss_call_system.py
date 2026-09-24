"""Eligibility owner for the guaranteed ACTIVE story-boss call."""
from __future__ import annotations
from typing import Mapping
from data.story_quest_content import STORY_QUEST_REGISTRY
from data.story_quest_definitions import QuestType, StoryQuestDefinition
from db_modules.story_quests import get_active_story_quest

BOSS_CALL_BUTTON = "👑 Викликати сюжетного боса"


def get_active_story_boss_call(
    *, user_id: int, current_location_id: str,
    registry: Mapping[str, StoryQuestDefinition] = STORY_QUEST_REGISTRY,
    connection=None,
) -> dict:
    """Return a callable boss contract only for a matching ACTIVE BOSS quest.

    COMPLETED and SKIPPED rows are never callable because only the canonical
    ACTIVE row is considered. Consequently a successful kill, which Stage 19.19
    completes immediately, permanently removes the guaranteed call and prevents
    farming even if a stale Telegram button is pressed later.
    """
    if not registry:
        return {"allowed": False, "reason": "no_production_content"}
    if connection is None:
        import db
        connection = db.conn
    active=get_active_story_quest(connection,int(user_id))
    if active is None:
        return {"allowed":False,"reason":"no_active_quest"}
    quest=registry.get(str(active["quest_id"]))
    if quest is None:
        return {"allowed":False,"reason":"unknown_quest_definition"}
    if quest.quest_type is not QuestType.BOSS:
        return {"allowed":False,"reason":"objective_type_mismatch"}
    if quest.location_id != str(current_location_id):
        return {"allowed":False,"reason":"location_mismatch"}
    if int(active["progress"]) >= int(active["target_quantity"]):
        return {"allowed":False,"reason":"objective_already_complete"}
    return {"allowed":True,"reason":"active_boss_quest","quest_id":quest.quest_id,
            "boss_key":quest.boss_key,"location_id":quest.location_id}
