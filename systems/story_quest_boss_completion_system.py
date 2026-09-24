"""Exact-once completion bridge for canonical RNG location bosses."""
from __future__ import annotations
from typing import Mapping

from data.story_quest_content import STORY_QUEST_REGISTRY
from data.story_quest_definitions import QuestType, StoryQuestDefinition
from db_modules.story_quests import (
    get_active_story_quest, get_story_quest, set_story_quest_progress,
)
from systems.story_quest_completion_system import complete_active_story_quest
from systems.story_quest_reward_system import build_story_quest_reward_adapter


def process_rng_boss_story_completion(
    *,
    user_id: int,
    mob: dict,
    location_id: str,
    encounter_id,
    registry: Mapping[str, StoryQuestDefinition] = STORY_QUEST_REGISTRY,
    connection=None,
) -> dict:
    """Complete a matching ACTIVE BOSS quest after terminal victory claim.

    Normal and elite enemies are ignored. Both canonical boss_key and location
    must match. Progress preparation, reward and COMPLETED status execute inside
    the completion owner's single transaction. An empty production registry is
    a safe no-op and the normal RNG boss encounter policy remains untouched.
    """
    if not registry:
        return {"completed": False, "reason": "no_production_content"}
    if not bool((mob or {}).get("is_boss")):
        return {"completed": False, "reason": "not_boss"}
    if connection is None:
        import db
        connection = db.conn
    active = get_active_story_quest(connection, int(user_id))
    if active is not None:
        quest = registry.get(str(active["quest_id"]))
        if quest is None:
            return {"completed": False, "reason": "unknown_quest_definition"}
        if quest.quest_type is not QuestType.BOSS:
            return {"completed": False, "reason": "objective_type_mismatch"}
        if quest.location_id != str(location_id):
            return {"completed": False, "reason": "location_mismatch"}
        if str(quest.boss_key) != str((mob or {}).get("boss_key") or ""):
            return {"completed": False, "reason": "boss_key_mismatch"}
    else:
        # A repeated terminal delivery has no ACTIVE row after the first success.
        # Resolve only an already-COMPLETED matching boss quest so the canonical
        # completion owner can return its idempotent replay without re-awarding.
        matching = [
            candidate for candidate in registry.values()
            if candidate.quest_type is QuestType.BOSS
            and candidate.location_id == str(location_id)
            and str(candidate.boss_key) == str((mob or {}).get("boss_key") or "")
        ]
        completed = []
        for candidate in matching:
            row = get_story_quest(connection, int(user_id), candidate.quest_id)
            if row is not None and row["status"] == "COMPLETED" and int(row["reward_claimed"]) == 1:
                completed.append(candidate)
        if not completed:
            return {"completed": False, "reason": "no_active_quest"}
        quest = max(completed, key=lambda candidate: candidate.number)

    def prepare_objective(*, connection, user_id, quest, row):
        """Mark the matched boss objective ready within completion transaction."""
        return set_story_quest_progress(
            connection,
            user_id=int(user_id),
            quest_id=quest.quest_id,
            progress=int(quest.target_quantity),
        )

    reward_adapter = build_story_quest_reward_adapter(
        exp=int(quest.reward.exp), gold=float(quest.reward.gold)
    )
    result = complete_active_story_quest(
        connection,
        registry=registry,
        user_id=int(user_id),
        quest_id=quest.quest_id,
        reward_adapter=reward_adapter,
        objective_preparer=prepare_objective,
        idempotency_key=(
            f"story_boss:{int(user_id)}:{quest.quest_id}:{encounter_id}"
        ),
    )
    return {**result, "reason": "completed" if result["completed"] else "replayed"}
