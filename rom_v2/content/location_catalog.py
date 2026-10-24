"""Canonical immutable V2 catalog for the two V1-parity locations.

This module is pure content. It has no persistence, Telegram, clock or random
source dependency. Stable technical IDs are never reformatted for presentation.
"""
from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Mapping

CITY_NODE_ID = "city"
START_PATH_ID = "start_path"
DARK_FOREST_ID = "dark_forest"
UNKNOWN_LOCATION_NAME = "🧭 Невідома місцевість"

@dataclass(frozen=True, slots=True)
class LocationDefinition:
    """Immutable canonical definition of one huntable location."""
    location_id: str
    name: str
    description: str
    level_min: int
    level_max: int
    unlock_level: int
    boss_name: str
    mob_names: tuple[str, ...]

_START_PATH = LocationDefinition(
    location_id=START_PATH_ID,
    name="🌿 Початок Шляху",
    description=("Перші стежки за межами табору мандрівників. Тут ще не панує справжня темрява, "
                 "але за деревами вже чути рух диких звірів, шурхіт павутини та слабке світіння "
                 "рунічних рослин. Саме тут новачки вчаться виживати, берегти спорядження, "
                 "користуватися зіллями та повертатися до міста перед тим, як ризик стане занадто великим."),
    level_min=1, level_max=5, unlock_level=1, boss_name="🐺 Ватажок зграї",
    mob_names=("🐗 Дикий кабан","🌱 Рунічний паросток","🦡 Лісовий борсук","💎 Рунічний слимак",
               "🦇 Лісовий кажан","🪸 Печерний кровосос","🕷️ Малий павук","🧪 Павук-кислотник",
               "🐺 Молодий вовк","👻 Вовк-примара"),
)
_DARK_FOREST = LocationDefinition(
    location_id=DARK_FOREST_ID,
    name="🌲 Темний Бір",
    description=("Глибша частина лісу, куди не заходять випадкові подорожні. Між старими деревами "
                 "ховаються гоблінські дозори, шамани, берсерки та слуги темних рун. Повітря тут "
                 "важче, а кожен крок може привести до засідки або стародавніх руїн."),
    level_min=6, level_max=10, unlock_level=6, boss_name="👑 Король Гоблінів",
    mob_names=("👺 Малий гоблін","🧪 Гоблін-знахар","🗡️ Гоблін-розвідник","🧙 Гоблін-шаман",
               "🪓 Гоблін-берсерк","🔥 Гоблін-піроман","🛡️ Гоблін-страж","🏹 Гоблін-мисливець",
               "👹 Гоблін-ватажок","💀 Темний гоблін"),
)

LOCATION_ORDER: tuple[str, ...] = (START_PATH_ID, DARK_FOREST_ID)
LOCATIONS: Mapping[str, LocationDefinition] = MappingProxyType({
    START_PATH_ID: _START_PATH,
    DARK_FOREST_ID: _DARK_FOREST,
})
WORLD_NODE_ORDER: tuple[str, ...] = (CITY_NODE_ID, START_PATH_ID, DARK_FOREST_ID)
LOCATION_GRAPH: Mapping[str, tuple[str, ...]] = MappingProxyType({
    CITY_NODE_ID: (START_PATH_ID,),
    START_PATH_ID: (CITY_NODE_ID, DARK_FOREST_ID),
    DARK_FOREST_ID: (START_PATH_ID,),
})

def get_location(location_id: str) -> LocationDefinition | None:
    """Return a canonical location or None; never fabricate an unknown record."""
    return LOCATIONS.get(str(location_id or "").strip())

def require_location(location_id: str) -> LocationDefinition:
    """Return a canonical location and fail closed for unknown technical IDs."""
    normalized=str(location_id or "").strip(); location=LOCATIONS.get(normalized)
    if location is None: raise KeyError(f"unknown location_id: {normalized}")
    return location

def get_location_display_name(location_id: str) -> str:
    """Resolve the exact localized name without leaking/title-casing an ID."""
    return require_location(location_id).name

def is_location_unlocked(location_id: str, player_level: int) -> bool:
    """Apply the V1 unlock threshold for one known location."""
    if isinstance(player_level,bool) or not isinstance(player_level,int) or player_level<1:
        raise ValueError("player_level must be a positive integer")
    return player_level >= require_location(location_id).unlock_level

def get_unlocked_locations(player_level: int) -> tuple[LocationDefinition, ...]:
    """Enumerate unlocked locations in canonical catalog order."""
    if isinstance(player_level,bool) or not isinstance(player_level,int) or player_level<1:
        raise ValueError("player_level must be a positive integer")
    return tuple(LOCATIONS[key] for key in LOCATION_ORDER if player_level>=LOCATIONS[key].unlock_level)

def get_adjacent_nodes(node_id: str) -> tuple[str, ...]:
    """Return static adjacent nodes and fail closed for an unknown world node."""
    normalized=str(node_id or "").strip()
    if normalized not in LOCATION_GRAPH: raise KeyError(f"unknown world node: {normalized}")
    return LOCATION_GRAPH[normalized]

def are_adjacent(from_node: str, to_node: str) -> bool:
    """Check one canonical graph edge without permitting inferred travel."""
    normalized_to=str(to_node or "").strip()
    if normalized_to not in LOCATION_GRAPH: raise KeyError(f"unknown world node: {normalized_to}")
    return normalized_to in get_adjacent_nodes(from_node)

def validate_location_catalog() -> None:
    """Validate IDs, order, levels, references and symmetric graph integrity."""
    if tuple(LOCATIONS) != LOCATION_ORDER: raise ValueError("location order mismatch")
    if set(LOCATION_GRAPH) != set(WORLD_NODE_ORDER): raise ValueError("world graph node mismatch")
    for key, location in LOCATIONS.items():
        if key != location.location_id: raise ValueError(f"location identity mismatch: {key}")
        if not (1 <= location.level_min <= location.level_max): raise ValueError(f"invalid level range: {key}")
        if location.unlock_level != location.level_min: raise ValueError(f"unlock mismatch: {key}")
        if not location.name or not location.description or not location.boss_name or not location.mob_names:
            raise ValueError(f"incomplete location: {key}")
        if len(location.mob_names) != len(set(location.mob_names)): raise ValueError(f"duplicate mob: {key}")
    for node, neighbors in LOCATION_GRAPH.items():
        if len(neighbors) != len(set(neighbors)): raise ValueError(f"duplicate edge: {node}")
        for neighbor in neighbors:
            if node not in LOCATION_GRAPH.get(neighbor, ()): raise ValueError(f"asymmetric edge: {node}->{neighbor}")

validate_location_catalog()
