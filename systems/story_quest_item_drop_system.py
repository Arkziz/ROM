"""Victory bridge for isolated, bounded story quest item drops."""
from __future__ import annotations
import random
from typing import Callable, Mapping

from data.story_quest_content import STORY_QUEST_REGISTRY
from data.story_quest_definitions import QuestType, StoryQuestDefinition
from db_modules.story_quests import get_active_story_quest, get_story_quest_item_quantity
from systems.story_quest_system import collect_active_quest_item


def process_story_quest_item_drop(
    *,
    user_id: int,
    location_id: str,
    registry: Mapping[str, StoryQuestDefinition] = STORY_QUEST_REGISTRY,
    connection=None,
    random_value: Callable[[], float] = random.random,
) -> dict:
    """Roll and grant one dedicated quest item after terminal victory.

    Ordinary inventory, bag capacity, mob identity and ordinary loot tables are
    intentionally excluded. The lifecycle owner rechecks ACTIVE/type/location/
    item-key state and persistence bounds quantity to the definition target.
    """
    if not registry:
        return {"granted": 0, "reason": "no_production_content"}
    if connection is None:
        import db
        connection = db.conn
    active = get_active_story_quest(connection, int(user_id))
    if active is None:
        return {"granted": 0, "reason": "no_active_quest"}
    quest = registry.get(str(active["quest_id"]))
    if quest is None:
        return {"granted": 0, "reason": "unknown_quest_definition"}
    if quest.quest_type is not QuestType.QUEST_ITEM or quest.quest_item is None:
        return {"granted": 0, "reason": "objective_type_mismatch"}
    if quest.location_id != str(location_id):
        return {"granted": 0, "reason": "location_mismatch"}
    current = get_story_quest_item_quantity(
        connection, int(user_id), quest.quest_id, quest.quest_item.item_key
    )
    required = int(quest.quest_item.required_quantity)
    if current >= required:
        return {
            "granted": 0,
            "quantity": current,
            "required_quantity": required,
            "objective_complete": True,
            "reason": "target_reached",
        }
    roll = float(random_value())
    if not 0.0 <= roll < 1.0:
        raise ValueError("random_value must return a value within [0, 1)")
    if roll >= float(quest.quest_item.drop_chance):
        return {
            "granted": 0,
            "quantity": current,
            "required_quantity": required,
            "objective_complete": False,
            "reason": "drop_missed",
        }
    result = collect_active_quest_item(
        connection,
        registry=registry,
        user_id=int(user_id),
        location_id=str(location_id),
        item_key=quest.quest_item.item_key,
        amount=1,
    )
    return {
        **result,
        "item_key": quest.quest_item.item_key,
        "display_name": quest.quest_item.display_name,
        "reason": "granted" if result.get("granted") else "target_reached",
    }
