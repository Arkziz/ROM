"""Post-reward orchestration for overlevel story-quest skipping."""
from __future__ import annotations
from typing import Mapping, Optional

from data.locations import LOCATIONS
from data.story_quest_content import STORY_QUEST_REGISTRY
from data.story_quest_definitions import StoryQuestDefinition
from systems.story_quest_system import reconcile_overlevel_story_locations


def build_story_location_max_levels() -> dict[str, int]:
    """Read canonical location level ceilings without duplicating range policy."""
    return {
        str(location_id): int(location["level_max"])
        for location_id, location in LOCATIONS.items()
        if "level_max" in location
    }


def build_overlevel_story_skip_message(result: dict) -> str:
    """Build one concise notification for newly skipped story quests."""
    changed = int((result or {}).get("changed", 0) or 0)
    if changed <= 0:
        return ""
    names = {"start_path": "Початок Шляху", "dark_forest": "Темний Бір"}
    lines = ["⏭️ Сюжет попередньої локації пропущено", ""]
    for item in result.get("locations", []):
        if int(item.get("skipped_now", 0) or 0) <= 0:
            continue
        title = names.get(str(item["location_id"]), str(item["location_id"]))
        lines.extend([f"📖 Історія «{title}»:",
                      f"• Завершено раніше: {int(item['completed'])}",
                      f"• Пропущено без нагород: {int(item['skipped_now'])}"])
    lines.extend(["", "Пропущені квести зараховано для сюжетного ланцюжка без EXP, золота та предметів."])
    return "\n".join(lines)


def process_overlevel_story_quest_skip(
    *,
    user_id: int,
    current_level: int,
    registry: Mapping[str, StoryQuestDefinition] = STORY_QUEST_REGISTRY,
    connection=None,
    location_max_levels: Optional[Mapping[str, int]] = None,
):
    """Atomically reconcile all unfinished quests of exceeded story locations."""
    if not registry:
        return {"changed": 0, "locations": [], "current_level": int(current_level), "message": ""}
    if connection is None:
        import db
        connection = db.conn
    limits = dict(location_max_levels) if location_max_levels is not None else build_story_location_max_levels()
    result = reconcile_overlevel_story_locations(
        connection, registry=registry, user_id=int(user_id),
        current_level=int(current_level), location_max_levels=limits,
    )
    result["message"] = build_overlevel_story_skip_message(result)
    return result
