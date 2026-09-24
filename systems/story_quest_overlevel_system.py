"""Post-reward orchestration for overlevel story-quest skipping."""
from __future__ import annotations
from typing import Mapping, Optional

from data.locations import LOCATIONS
from data.story_quest_content import STORY_QUEST_REGISTRY
from data.story_quest_definitions import StoryQuestDefinition
from systems.story_quest_system import skip_overlevel_active_quest


def build_story_location_max_levels() -> dict[str, int]:
    """Read canonical location level ceilings without duplicating range policy."""
    return {
        str(location_id): int(location["level_max"])
        for location_id, location in LOCATIONS.items()
        if "level_max" in location
    }


def process_overlevel_story_quest_skip(
    *,
    user_id: int,
    current_level: int,
    registry: Mapping[str, StoryQuestDefinition] = STORY_QUEST_REGISTRY,
    connection=None,
    location_max_levels: Optional[Mapping[str, int]] = None,
):
    """Skip one ACTIVE quest only after its location ceiling is exceeded.

    This service gives no compensation. The lifecycle owner atomically marks the
    quest SKIPPED and removes only that quest's isolated item rows. Empty
    production content is a safe no-op.
    """
    if not registry:
        return None
    if connection is None:
        import db
        connection = db.conn
    limits = (
        dict(location_max_levels)
        if location_max_levels is not None
        else build_story_location_max_levels()
    )
    return skip_overlevel_active_quest(
        connection,
        registry=registry,
        user_id=int(user_id),
        current_level=int(current_level),
        location_max_levels=limits,
    )
