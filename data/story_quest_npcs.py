"""Canonical NPC identities and navigation routes for story quests.

Quest definitions store stable NPC IDs only. UI, content packs and lifecycle
services resolve display names and city routes through this registry, so button
labels or menu structure can change without rewriting every quest definition.
This module is data-only and does not register Telegram handlers.
"""
from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Mapping, Optional, Tuple


class StoryQuestNpcRegistryError(ValueError):
    """An NPC definition or requested route violates the canonical contract."""


@dataclass(frozen=True)
class StoryQuestNpcDefinition:
    """Immutable identity and navigation contract for one story-capable NPC."""

    npc_id: str
    display_name: str
    button_label: str
    world_location_id: str
    city_section_id: str
    city_section_label: str
    route_labels: Tuple[str, ...]
    can_give_quests: bool = True
    can_receive_turn_in: bool = True
    production_route_exists: bool = True
    service_owner: Optional[str] = None

    @property
    def route_text(self) -> str:
        """Return a compact route suitable for the Profile quest journal."""
        return " → ".join(self.route_labels)


# Stable IDs remain English machine keys. User-visible labels remain Ukrainian.
# The three missing production routes are explicitly marked false and will be
# created separately in Stage 19.12 without changing quest definitions.
_NPC_DEFINITIONS = (
    StoryQuestNpcDefinition(
        npc_id="elder",
        display_name="Староста",
        button_label="🗣️ Староста",
        world_location_id="start_path",
        city_section_id="townhall",
        city_section_label="🏛️ Ратуша",
        route_labels=("🏙️ Місто", "🏛️ Ратуша", "🗣️ Староста"),
        production_route_exists=False,
    ),
    StoryQuestNpcDefinition(
        npc_id="mercenary_head",
        display_name="Голова Найманців",
        button_label="⚔️ Голова Найманців",
        world_location_id="start_path",
        city_section_id="mercenary_guild",
        city_section_label="📜 Гільдія Найманців",
        route_labels=(
            "🏙️ Місто", "📜 Гільдія Найманців", "⚔️ Голова Найманців"
        ),
        production_route_exists=False,
    ),
    StoryQuestNpcDefinition(
        npc_id="blacksmith",
        display_name="Коваль",
        button_label="⚒️ Коваль",
        world_location_id="start_path",
        city_section_id="craft_district",
        city_section_label="⚒️ Ремісничий квартал",
        route_labels=("🏙️ Місто", "⚒️ Ремісничий квартал", "⚒️ Коваль"),
        service_owner="handlers.blacksmith",
    ),
    StoryQuestNpcDefinition(
        npc_id="alchemist",
        display_name="Алхімік",
        button_label="🧪 Алхімік",
        world_location_id="start_path",
        city_section_id="craft_district",
        city_section_label="⚒️ Ремісничий квартал",
        route_labels=("🏙️ Місто", "⚒️ Ремісничий квартал", "🧪 Алхімік"),
        service_owner="handlers.city",
    ),
    StoryQuestNpcDefinition(
        npc_id="rune_master",
        display_name="Рунний Майстер",
        button_label="💠 Рунний Майстер",
        world_location_id="start_path",
        city_section_id="craft_district",
        city_section_label="⚒️ Ремісничий квартал",
        route_labels=(
            "🏙️ Місто", "⚒️ Ремісничий квартал", "💠 Рунний Майстер"
        ),
        service_owner="handlers.runes",
    ),
    StoryQuestNpcDefinition(
        npc_id="trader",
        display_name="Торговець",
        button_label="🧙 Торговець",
        world_location_id="start_path",
        city_section_id="trade_district",
        city_section_label="🛒 Торговий ряд",
        route_labels=("🏙️ Місто", "🛒 Торговий ряд", "🧙 Торговець"),
        service_owner="handlers.city",
    ),
    StoryQuestNpcDefinition(
        npc_id="bartender",
        display_name="Бармен",
        button_label="🍺 Бармен",
        world_location_id="start_path",
        city_section_id="tavern",
        city_section_label="🍺 Таверна",
        route_labels=("🏙️ Місто", "🍺 Таверна", "🍺 Бармен"),
        production_route_exists=False,
    ),
)


def validate_story_quest_npc_registry(
    definitions: tuple[StoryQuestNpcDefinition, ...] = _NPC_DEFINITIONS,
) -> Mapping[str, StoryQuestNpcDefinition]:
    """Validate identities, routes and labels, then return an immutable registry."""
    if not definitions:
        raise StoryQuestNpcRegistryError("NPC registry cannot be empty")
    registry = {}
    button_labels = set()
    for npc in definitions:
        if not npc.npc_id or not npc.npc_id.replace("_", "").isalnum():
            raise StoryQuestNpcRegistryError(f"invalid npc_id: {npc.npc_id!r}")
        if npc.npc_id in registry:
            raise StoryQuestNpcRegistryError(f"duplicate npc_id: {npc.npc_id}")
        if not npc.display_name.strip() or not npc.button_label.strip():
            raise StoryQuestNpcRegistryError(f"missing NPC presentation: {npc.npc_id}")
        if npc.button_label in button_labels:
            raise StoryQuestNpcRegistryError(
                f"duplicate NPC button label: {npc.button_label}"
            )
        if not npc.world_location_id or not npc.city_section_id:
            raise StoryQuestNpcRegistryError(f"missing NPC context: {npc.npc_id}")
        if len(npc.route_labels) < 3:
            raise StoryQuestNpcRegistryError(
                f"NPC route must include city, section and NPC: {npc.npc_id}"
            )
        if npc.route_labels[-1] != npc.button_label:
            raise StoryQuestNpcRegistryError(
                f"route terminal must match button label: {npc.npc_id}"
            )
        registry[npc.npc_id] = npc
        button_labels.add(npc.button_label)
    return MappingProxyType(registry)


STORY_QUEST_NPCS = validate_story_quest_npc_registry()


def get_story_quest_npc(npc_id: str) -> StoryQuestNpcDefinition:
    """Resolve a stable NPC ID or fail closed for invalid quest content."""
    key = str(npc_id or "").strip()
    try:
        return STORY_QUEST_NPCS[key]
    except KeyError as error:
        raise StoryQuestNpcRegistryError(f"unknown story quest NPC: {key}") from error


def resolve_story_quest_navigation(npc_id: str) -> dict:
    """Build a UI-neutral navigation snapshot for journal and NPC screens."""
    npc = get_story_quest_npc(npc_id)
    return {
        "npc_id": npc.npc_id,
        "display_name": npc.display_name,
        "button_label": npc.button_label,
        "world_location_id": npc.world_location_id,
        "city_section_id": npc.city_section_id,
        "city_section_label": npc.city_section_label,
        "route_labels": npc.route_labels,
        "route_text": npc.route_text,
        "production_route_exists": npc.production_route_exists,
    }


def validate_story_quest_npc_references(
    *, giver_npc_id: str, turn_in_npc_id: Optional[str] = None,
) -> None:
    """Validate the stable NPC references used by one quest definition."""
    giver = get_story_quest_npc(giver_npc_id)
    if not giver.can_give_quests:
        raise StoryQuestNpcRegistryError(
            f"NPC cannot give quests: {giver.npc_id}"
        )
    if turn_in_npc_id is not None:
        receiver = get_story_quest_npc(turn_in_npc_id)
        if not receiver.can_receive_turn_in:
            raise StoryQuestNpcRegistryError(
                f"NPC cannot receive quest turn-in: {receiver.npc_id}"
            )


def get_missing_story_quest_npc_routes() -> tuple[StoryQuestNpcDefinition, ...]:
    """Return registry members that still require production city handlers."""
    return tuple(
        npc for npc in STORY_QUEST_NPCS.values() if not npc.production_route_exists
    )
