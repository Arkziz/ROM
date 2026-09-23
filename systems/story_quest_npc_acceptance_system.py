"""NPC-owned presentation and acceptance for sequential story quests.

The Profile journal remains navigation-only. This service resolves which quest
an NPC may present, builds a UI-neutral dialogue snapshot, and delegates the
actual AVAILABLE -> ACTIVE transition to the canonical lifecycle engine.
Production handlers and content packs are intentionally not registered here.
"""
from __future__ import annotations

from typing import Mapping, Optional

from data.story_quest_definitions import DerivedQuestStatus, StoryQuestDefinition
from data.story_quest_npcs import get_story_quest_npc, resolve_story_quest_navigation
from systems.story_quest_system import (
    StoryQuestUnavailableError,
    accept_story_quest,
    get_story_quest_status,
    get_story_quest_view,
)


class StoryQuestNpcAcceptanceError(RuntimeError):
    """An NPC presentation or acceptance request violates the quest contract."""


def _ordered_definitions(
    registry: Mapping[str, StoryQuestDefinition],
) -> tuple[StoryQuestDefinition, ...]:
    """Return deterministic canonical quest order for NPC presentation."""
    return tuple(sorted(registry.values(), key=lambda quest: (quest.number, quest.quest_id)))


def find_npc_story_quest(
    connection,
    *,
    registry: Mapping[str, StoryQuestDefinition],
    user_id: int,
    npc_id: str,
    player_level: int,
) -> Optional[StoryQuestDefinition]:
    """Resolve the one quest this NPC should currently present to the player.

    ACTIVE quests owned by the NPC take precedence over AVAILABLE quests. This
    gives repeated NPC visits a stable dialogue and prevents a later available
    quest from hiding the current objective.
    """
    npc = get_story_quest_npc(npc_id)
    active_match = None
    available_match = None
    for quest in _ordered_definitions(registry):
        if quest.giver_npc_id != npc.npc_id:
            continue
        status = get_story_quest_status(
            connection,
            user_id=user_id,
            quest=quest,
            player_level=player_level,
        )
        if status.value == "ACTIVE":
            active_match = quest
            break
        if status is DerivedQuestStatus.AVAILABLE and available_match is None:
            available_match = quest
    return active_match or available_match


def build_npc_story_quest_presentation(
    connection,
    *,
    registry: Mapping[str, StoryQuestDefinition],
    user_id: int,
    npc_id: str,
    player_level: int,
) -> dict:
    """Build a handler-neutral NPC screen with only policy-valid actions."""
    npc = get_story_quest_npc(npc_id)
    quest = find_npc_story_quest(
        connection,
        registry=registry,
        user_id=user_id,
        npc_id=npc.npc_id,
        player_level=player_level,
    )
    if quest is None:
        return {
            "npc_id": npc.npc_id,
            "npc_name": npc.display_name,
            "state": "NO_QUEST",
            "quest": None,
            "actions": (),
            "navigation": resolve_story_quest_navigation(npc.npc_id),
        }
    view = get_story_quest_view(
        connection,
        user_id=user_id,
        quest=quest,
        player_level=player_level,
    )
    actions = ("ACCEPT",) if view["status"] == "AVAILABLE" else ()
    return {
        "npc_id": npc.npc_id,
        "npc_name": npc.display_name,
        "state": view["status"],
        "quest": view,
        "actions": actions,
        "navigation": resolve_story_quest_navigation(npc.npc_id),
    }


def accept_story_quest_from_npc(
    connection,
    *,
    registry: Mapping[str, StoryQuestDefinition],
    user_id: int,
    npc_id: str,
    quest_id: str,
    player_level: int,
    timestamp: Optional[str] = None,
) -> dict:
    """Accept one quest only from its canonical giver NPC.

    The lifecycle engine performs the transactional availability recheck and
    idempotent retry behavior. This boundary only proves NPC ownership and blocks
    stale or forged callbacks that reference a different giver.
    """
    npc = get_story_quest_npc(npc_id)
    try:
        quest = registry[str(quest_id)]
    except KeyError as error:
        raise StoryQuestNpcAcceptanceError(
            f"unknown story quest: {quest_id}"
        ) from error
    if quest.giver_npc_id != npc.npc_id:
        raise StoryQuestNpcAcceptanceError(
            f"quest {quest.quest_id} does not belong to NPC {npc.npc_id}"
        )
    presentation = build_npc_story_quest_presentation(
        connection,
        registry=registry,
        user_id=user_id,
        npc_id=npc.npc_id,
        player_level=player_level,
    )
    if (
        presentation["quest"] is None
        or presentation["quest"]["quest_id"] != quest.quest_id
        or presentation["state"] not in {"AVAILABLE", "ACTIVE"}
    ):
        raise StoryQuestUnavailableError(
            f"quest {quest.quest_id} is not presentable by NPC {npc.npc_id}"
        )
    accepted = accept_story_quest(
        connection,
        registry=registry,
        user_id=user_id,
        quest_id=quest.quest_id,
        player_level=player_level,
        timestamp=timestamp,
    )
    return {
        "accepted": True,
        "already_active": presentation["state"] == "ACTIVE",
        "npc_id": npc.npc_id,
        "quest": accepted,
    }
