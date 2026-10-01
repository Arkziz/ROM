"""Exact-once completion bridge for canonical RNG location bosses."""
from __future__ import annotations
from typing import Mapping

from data.story_quest_content import STORY_QUEST_REGISTRY
from data.story_quest_definitions import QuestType, StoryQuestDefinition
from db_modules.story_quests import (
    get_active_story_quest, get_story_quest, set_story_quest_progress,
)


def process_rng_boss_story_completion(
    *,
    user_id: int,
    mob: dict,
    location_id: str,
    encounter_id,
    registry: Mapping[str, StoryQuestDefinition] = STORY_QUEST_REGISTRY,
    connection=None,
) -> dict:
    """Record a matching ACTIVE BOSS victory without completing the quest.

    Combat reward ownership remains in the combat pipeline. This bridge only
    advances the canonical BOSS objective to its bounded target. The quest stays
    ACTIVE, reward_claimed stays unchanged, and the NPC completion owner later
    completes and rewards the quest after the player reports the victory.

    Repeated delivery of the same terminal victory is idempotent because bounded
    progress is set to the same target. Defeat and escape never call this victory
    bridge, so they leave progress unchanged and allow another invocation.
    """
    if not registry:
        return {"advanced": False, "completed": False, "reason": "no_production_content"}
    if not bool((mob or {}).get("is_boss")):
        return {"advanced": False, "completed": False, "reason": "not_boss"}
    if connection is None:
        import db
        connection = db.conn

    active = get_active_story_quest(connection, int(user_id))
    if active is None:
        return {"advanced": False, "completed": False, "reason": "no_active_quest"}

    quest = registry.get(str(active["quest_id"]))
    if quest is None:
        return {"advanced": False, "completed": False, "reason": "unknown_quest_definition"}
    if quest.quest_type is not QuestType.BOSS:
        return {"advanced": False, "completed": False, "reason": "objective_type_mismatch"}
    if quest.location_id != str(location_id):
        return {"advanced": False, "completed": False, "reason": "location_mismatch"}
    if str(quest.boss_key) != str((mob or {}).get("boss_key") or ""):
        return {"advanced": False, "completed": False, "reason": "boss_key_mismatch"}

    before = int(active["progress"])
    target = int(quest.target_quantity)
    if before >= target:
        return {
            "advanced": False,
            "completed": False,
            "reason": "already_recorded",
            "quest_id": quest.quest_id,
            "progress": before,
            "target_quantity": target,
            "encounter_id": encounter_id,
            "status": str(active["status"]),
            "reward_claimed": int(active["reward_claimed"]),
        }

    with connection:
        row = set_story_quest_progress(
            connection,
            user_id=int(user_id),
            quest_id=quest.quest_id,
            progress=target,
        )

    after = int(row["progress"])
    return {
        "advanced": after > before,
        "completed": False,
        "reason": "progress_recorded" if after > before else "already_recorded",
        "quest_id": quest.quest_id,
        "progress": after,
        "target_quantity": target,
        "encounter_id": encounter_id,
        "status": str(row["status"]),
        "reward_claimed": int(row["reward_claimed"]),
    }
