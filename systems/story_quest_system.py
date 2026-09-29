"""Canonical lifecycle service for sequential ROM story quests.

This layer combines immutable definitions with explicit-connection persistence.
Public mutation operations own one BEGIN IMMEDIATE transaction so state checks
and writes cannot drift between concurrent callbacks. Completion and rewards are
not implemented here; they belong to the next exact-once transaction stage.
"""
from __future__ import annotations

from contextlib import contextmanager
from typing import Iterable, Mapping, Optional, Sequence

from data.story_quest_definitions import (
    DerivedQuestStatus,
    PersistentQuestStatus,
    QuestItemDefinition,
    QuestType,
    StoryQuestDefinition,
    validate_story_quest_pack,
)
from db_modules.story_quests import (
    StoryQuestConflictError,
    activate_story_quest,
    add_story_quest_item,
    get_active_story_quest,
    get_story_quest,
    get_story_quest_item_quantity,
    list_story_quest_journal,
    set_story_quest_progress,
    skip_active_story_quest,
)


class StoryQuestLifecycleError(RuntimeError):
    """A lifecycle transition is invalid for the current definition or state."""


class StoryQuestUnavailableError(StoryQuestLifecycleError):
    """A quest is LOCKED, already finalized, or blocked by another active quest."""


class StoryQuestObjectiveError(StoryQuestLifecycleError):
    """A progress operation does not match the active objective contract."""


@contextmanager
def immediate_transaction(connection):
    """Own a fail-safe write transaction without hiding commit boundaries.

    Lifecycle mutations begin with BEGIN IMMEDIATE so two Telegram callbacks
    cannot both pass an availability check and create conflicting active state.
    Every exception rolls back before it leaves this service.
    """
    connection.execute("BEGIN IMMEDIATE")
    try:
        yield
    except Exception:
        connection.rollback()
        raise
    else:
        connection.commit()


def build_story_quest_registry(
    packs: Iterable[Sequence[StoryQuestDefinition]],
) -> Mapping[str, StoryQuestDefinition]:
    """Validate ordered packs and construct one global immutable-style registry.

    Each pack is validated independently. This permits reviewed content batches
    of ten while global checks still prevent duplicate IDs, numbers and broken
    predecessor references across pack boundaries.
    """
    registry = {}
    numbers = {}
    ordered = []
    for pack in packs:
        validated = validate_story_quest_pack(pack)
        for quest in validated.values():
            if quest.quest_id in registry:
                raise StoryQuestLifecycleError(f"duplicate quest_id: {quest.quest_id}")
            if quest.number in numbers:
                raise StoryQuestLifecycleError(f"duplicate quest number: {quest.number}")
            registry[quest.quest_id] = quest
            numbers[quest.number] = quest.quest_id
            ordered.append(quest)
    if not registry:
        raise StoryQuestLifecycleError("story quest registry cannot be empty")
    ordered.sort(key=lambda quest: quest.number)
    for quest in ordered:
        predecessor = quest.previous_quest_id
        if predecessor is None:
            continue
        previous = registry.get(predecessor)
        if previous is None:
            raise StoryQuestLifecycleError(
                f"{quest.quest_id}: predecessor {predecessor} is not registered"
            )
        if previous.number + 1 != quest.number:
            raise StoryQuestLifecycleError(
                f"{quest.quest_id}: predecessor number is not consecutive"
            )
    return dict(registry)


def _definition(registry, quest_id: str) -> StoryQuestDefinition:
    try:
        return registry[str(quest_id)]
    except KeyError as error:
        raise StoryQuestLifecycleError(f"unknown story quest: {quest_id}") from error


def get_story_quest_status(
    connection,
    *,
    user_id: int,
    quest: StoryQuestDefinition,
    player_level: int,
) -> PersistentQuestStatus | DerivedQuestStatus:
    """Resolve persistent status first, otherwise derive LOCKED or AVAILABLE."""
    row = get_story_quest(connection, user_id, quest.quest_id)
    if row is not None:
        return PersistentQuestStatus(str(row["status"]))

    predecessor_completed = quest.previous_quest_id is None
    if quest.previous_quest_id is not None:
        predecessor = get_story_quest(connection, user_id, quest.previous_quest_id)
        predecessor_completed = bool(
            predecessor and predecessor["status"] in (PersistentQuestStatus.COMPLETED.value, PersistentQuestStatus.SKIPPED.value)
        )
    another_active = get_active_story_quest(connection, user_id) is not None
    if (
        int(player_level) < int(quest.unlock_level)
        or not predecessor_completed
        or another_active
    ):
        return DerivedQuestStatus.LOCKED
    return DerivedQuestStatus.AVAILABLE


def get_story_quest_view(
    connection,
    *,
    user_id: int,
    quest: StoryQuestDefinition,
    player_level: int,
) -> dict:
    """Build a read-only UI-neutral snapshot for journals and NPC screens."""
    status = get_story_quest_status(
        connection, user_id=user_id, quest=quest, player_level=player_level
    )
    row = get_story_quest(connection, user_id, quest.quest_id)
    progress = int(row["progress"]) if row else 0
    item_quantity = 0
    if quest.quest_item is not None:
        item_quantity = get_story_quest_item_quantity(
            connection, user_id, quest.quest_id, quest.quest_item.item_key
        )
    return {
        "quest_id": quest.quest_id,
        "number": quest.number,
        "title": quest.title,
        "quest_type": quest.quest_type.value,
        "status": status.value,
        "location_id": quest.location_id,
        "giver_npc_id": quest.giver_npc_id,
        "turn_in_npc_id": quest.turn_in_npc_id,
        "progress": progress,
        "target_quantity": quest.target_quantity,
        "quest_item_quantity": item_quantity,
        "objective_complete": max(progress, item_quantity) >= quest.target_quantity,
    }


def accept_story_quest(
    connection,
    *,
    registry: Mapping[str, StoryQuestDefinition],
    user_id: int,
    quest_id: str,
    player_level: int,
    timestamp: Optional[str] = None,
) -> dict:
    """Atomically accept exactly one AVAILABLE quest.

    Idempotent retry is permitted only for the same already-ACTIVE quest. The
    availability check is repeated inside BEGIN IMMEDIATE before insertion.
    """
    quest = _definition(registry, quest_id)
    with immediate_transaction(connection):
        existing = get_story_quest(connection, user_id, quest.quest_id)
        if existing is not None and existing["status"] == "ACTIVE":
            return existing
        status = get_story_quest_status(
            connection, user_id=user_id, quest=quest, player_level=player_level
        )
        if status is not DerivedQuestStatus.AVAILABLE:
            raise StoryQuestUnavailableError(
                f"quest {quest.quest_id} is not AVAILABLE: {status.value}"
            )
        return activate_story_quest(
            connection,
            user_id=user_id,
            quest_id=quest.quest_id,
            quest_number=quest.number,
            target_quantity=quest.target_quantity,
            timestamp=timestamp,
        )


def advance_region_kill_progress(
    connection,
    *,
    registry: Mapping[str, StoryQuestDefinition],
    user_id: int,
    location_id: str,
    amount: int = 1,
    timestamp: Optional[str] = None,
) -> dict:
    """Atomically advance the matching ACTIVE KILL_REGION objective.

    The caller supplies only the location and count. No concrete normal-mob ID
    is accepted, preserving the region-wide objective policy.
    """
    delta = int(amount)
    if delta <= 0:
        raise ValueError("amount must be positive")
    with immediate_transaction(connection):
        active = get_active_story_quest(connection, user_id)
        if active is None:
            return {"advanced": 0, "reason": "no_active_quest"}
        quest = _definition(registry, active["quest_id"])
        if quest.quest_type is not QuestType.KILL_REGION:
            return {"advanced": 0, "reason": "objective_type_mismatch"}
        if quest.location_id != str(location_id):
            return {"advanced": 0, "reason": "location_mismatch"}
        before = int(active["progress"])
        row = set_story_quest_progress(
            connection,
            user_id=user_id,
            quest_id=quest.quest_id,
            progress=before + delta,
            timestamp=timestamp,
        )
        return {
            "advanced": int(row["progress"]) - before,
            "progress": int(row["progress"]),
            "target_quantity": int(row["target_quantity"]),
            "objective_complete": int(row["progress"]) >= int(row["target_quantity"]),
        }


def collect_active_quest_item(
    connection,
    *,
    registry: Mapping[str, StoryQuestDefinition],
    user_id: int,
    location_id: str,
    item_key: str,
    amount: int = 1,
    timestamp: Optional[str] = None,
) -> dict:
    """Atomically grant a bounded item to the matching ACTIVE QUEST_ITEM quest."""
    with immediate_transaction(connection):
        active = get_active_story_quest(connection, user_id)
        if active is None:
            return {"granted": 0, "reason": "no_active_quest"}
        quest = _definition(registry, active["quest_id"])
        if quest.quest_type is not QuestType.QUEST_ITEM or quest.quest_item is None:
            return {"granted": 0, "reason": "objective_type_mismatch"}
        if quest.location_id != str(location_id):
            return {"granted": 0, "reason": "location_mismatch"}
        if quest.quest_item.item_key != str(item_key):
            return {"granted": 0, "reason": "item_key_mismatch"}
        result = add_story_quest_item(
            connection,
            user_id=user_id,
            quest_id=quest.quest_id,
            item_key=quest.quest_item.item_key,
            quantity=amount,
            required_quantity=quest.quest_item.required_quantity,
            timestamp=timestamp,
        )
        return {
            **result,
            "objective_complete": result["quantity"] >= result["required_quantity"],
        }


def skip_overlevel_active_quest(
    connection,
    *,
    registry: Mapping[str, StoryQuestDefinition],
    user_id: int,
    current_level: int,
    location_max_levels: Mapping[str, int],
    timestamp: Optional[str] = None,
) -> Optional[dict]:
    """Atomically SKIP an active quest after its location level range is exceeded.

    The operation gives no reward and relies on persistence to delete only the
    skipped quest's isolated item rows in the same transaction.
    """
    with immediate_transaction(connection):
        active = get_active_story_quest(connection, user_id)
        if active is None:
            return None
        quest = _definition(registry, active["quest_id"])
        if quest.location_id not in location_max_levels:
            raise StoryQuestLifecycleError(
                f"missing max level for location {quest.location_id}"
            )
        if int(current_level) <= int(location_max_levels[quest.location_id]):
            return None
        return skip_active_story_quest(
            connection,
            user_id=user_id,
            quest_id=quest.quest_id,
            timestamp=timestamp,
        )


def get_materialized_story_journal(connection, user_id: int) -> list[dict]:
    """Expose persisted ACTIVE/COMPLETED/SKIPPED rows without deriving content."""
    return list_story_quest_journal(connection, user_id)
