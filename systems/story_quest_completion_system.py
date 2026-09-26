"""Atomic exact-once completion for active story quests.

The caller supplies a reward adapter that writes through the same SQLite
connection. This keeps objective validation, quest-item consumption, reward
credit and COMPLETED state inside one BEGIN IMMEDIATE transaction.
"""
from __future__ import annotations

from typing import Callable, Mapping, Optional

from data.story_quest_definitions import QuestType, StoryQuestDefinition
from db_modules.story_quests import (
    get_active_story_quest,
    get_story_quest,
    consume_story_quest_item_quantity,
    get_story_quest_item_quantity,
    get_total_story_quest_item_quantity,
    utc_now_iso,
)
from systems.story_quest_system import StoryQuestLifecycleError, immediate_transaction


class StoryQuestCompletionError(StoryQuestLifecycleError):
    """Completion was rejected because state or objective is incomplete."""


class StoryQuestRewardError(StoryQuestCompletionError):
    """The transaction-scoped reward adapter rejected or failed the reward."""


def _definition(registry, quest_id: str) -> StoryQuestDefinition:
    try:
        return registry[str(quest_id)]
    except KeyError as error:
        raise StoryQuestCompletionError(f"unknown story quest: {quest_id}") from error


def _objective_ready(connection, user_id: int, quest, row) -> bool:
    """Evaluate objective and cross-quest prerequisite readiness."""
    for required in quest.required_quest_items:
        quantity = get_total_story_quest_item_quantity(
            connection, user_id, required.item_key
        )
        if quantity < required.quantity:
            return False
    if quest.quest_type is QuestType.QUEST_ITEM:
        if quest.quest_item is None:
            raise StoryQuestCompletionError("QUEST_ITEM definition has no item contract")
        quantity = get_story_quest_item_quantity(
            connection, user_id, quest.quest_id, quest.quest_item.item_key
        )
        return quantity >= quest.quest_item.required_quantity
    if quest.quest_type in {QuestType.KILL_REGION, QuestType.BOSS}:
        return int(row["progress"]) >= int(row["target_quantity"])
    # TALK and TURN_IN become complete when their matching interaction invokes
    # this service. NPC identity is checked by expected_turn_in_npc_id below.
    return quest.quest_type in {QuestType.TALK, QuestType.TURN_IN}


def is_story_quest_objective_ready(
    connection,
    *,
    registry: Mapping[str, StoryQuestDefinition],
    user_id: int,
    quest_id: str,
) -> bool:
    """Return current completion readiness without mutating quest state.

    This is the canonical UI readiness boundary. It uses the same persisted
    objective check as completion, including retained and multi-item contracts.
    """
    quest = _definition(registry, quest_id)
    row = get_story_quest(connection, int(user_id), quest.quest_id)
    if row is None or row["status"] != "ACTIVE" or int(row["reward_claimed"]) != 0:
        return False
    active = get_active_story_quest(connection, int(user_id))
    if active is None or active["quest_id"] != quest.quest_id:
        return False
    return bool(_objective_ready(connection, int(user_id), quest, row))


def complete_active_story_quest(
    connection,
    *,
    registry: Mapping[str, StoryQuestDefinition],
    user_id: int,
    quest_id: str,
    reward_adapter: Callable,
    objective_preparer: Optional[Callable] = None,
    expected_turn_in_npc_id: Optional[str] = None,
    idempotency_key: Optional[str] = None,
    timestamp: Optional[str] = None,
) -> dict:
    """Complete and reward one quest exactly once in a single transaction.

    The reward adapter receives ``connection``, ``user_id``, ``quest`` and
    ``idempotency_key``. It must use only the supplied connection and must not
    commit or roll back. Any exception rolls back item consumption, reward
    writes and quest status together.
    """
    quest = _definition(registry, quest_id)
    key = str(idempotency_key or f"story_quest:{user_id}:{quest.quest_id}")
    with immediate_transaction(connection):
        row = get_story_quest(connection, user_id, quest.quest_id)
        if row is None:
            raise StoryQuestCompletionError("quest has no persistent state")

        # A repeated callback after a successful commit is a safe read-only
        # replay and never invokes the reward adapter again.
        if row["status"] == "COMPLETED" and int(row["reward_claimed"]) == 1:
            return {
                "completed": True,
                "already_processed": True,
                "quest": row,
                "reward": None,
            }
        if row["status"] != "ACTIVE" or int(row["reward_claimed"]) != 0:
            raise StoryQuestCompletionError("quest is not an unclaimed ACTIVE quest")
        active = get_active_story_quest(connection, user_id)
        if active is None or active["quest_id"] != quest.quest_id:
            raise StoryQuestCompletionError("active quest changed")

        if expected_turn_in_npc_id is not None:
            expected = str(quest.turn_in_npc_id or quest.giver_npc_id)
            if expected != str(expected_turn_in_npc_id):
                raise StoryQuestCompletionError("turn-in NPC does not match definition")
        if objective_preparer is not None:
            objective_preparer(
                connection=connection,
                user_id=int(user_id),
                quest=quest,
                row=row,
            )
            row = get_story_quest(connection, user_id, quest.quest_id)
        if not _objective_ready(connection, user_id, quest, row):
            raise StoryQuestCompletionError("quest objective is incomplete")

        # Consumption occurs inside the same BEGIN IMMEDIATE transaction as
        # reward and COMPLETED. Retained clues remain until a later definition
        # explicitly lists the item as a consuming prerequisite.
        if quest.quest_type is QuestType.QUEST_ITEM and quest.quest_item.consume_on_completion:
            consume_story_quest_item_quantity(
                connection,
                user_id=int(user_id),
                item_key=quest.quest_item.item_key,
                quantity=int(quest.quest_item.required_quantity),
            )
        for required in quest.required_quest_items:
            if required.consume:
                consume_story_quest_item_quantity(
                    connection,
                    user_id=int(user_id),
                    item_key=required.item_key,
                    quantity=int(required.quantity),
                )

        try:
            reward_result = reward_adapter(
                connection=connection,
                user_id=int(user_id),
                quest=quest,
                idempotency_key=key,
            )
        except Exception as error:
            raise StoryQuestRewardError("story quest reward failed") from error
        if reward_result is False:
            raise StoryQuestRewardError("story quest reward adapter rejected reward")

        now = str(timestamp or utc_now_iso())
        updated = connection.execute(
            """UPDATE user_story_quests
            SET status='COMPLETED', reward_claimed=1,
                completed_at=?, updated_at=?
            WHERE user_id=? AND quest_id=?
              AND status='ACTIVE' AND reward_claimed=0""",
            (now, now, int(user_id), quest.quest_id),
        )
        if updated.rowcount != 1:
            raise StoryQuestCompletionError("quest changed concurrently during completion")
        completed = get_story_quest(connection, user_id, quest.quest_id)
        return {
            "completed": True,
            "already_processed": False,
            "quest": completed,
            "reward": reward_result,
        }
