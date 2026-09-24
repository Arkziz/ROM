"""Combat bridge for bounded KILL_REGION story-quest progress."""
from __future__ import annotations
from typing import Mapping, Optional

from data.story_quest_content import STORY_QUEST_REGISTRY
from data.story_quest_definitions import StoryQuestDefinition
from systems.story_quest_system import advance_region_kill_progress


def process_region_kill_story_progress(
    *,
    user_id: int,
    location_id: str,
    registry: Mapping[str, StoryQuestDefinition] = STORY_QUEST_REGISTRY,
    connection=None,
) -> dict:
    """Advance one region kill after a canonical terminal victory claim.

    The combat owner supplies only user and location. Normal, elite and boss
    victories therefore count equally, while concrete mob IDs are intentionally
    excluded. Empty production content is a safe no-op. The lifecycle owner keeps
    progress bounded and rejects non-ACTIVE, wrong-type and wrong-location quests.
    """
    if not registry:
        return {"advanced": 0, "reason": "no_production_content"}
    if connection is None:
        import db
        connection = db.conn
    return advance_region_kill_progress(
        connection,
        registry=registry,
        user_id=int(user_id),
        location_id=str(location_id),
        amount=1,
    )
