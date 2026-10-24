"""Canonical immutable V2 World Graph for V1 parity.

The graph is pure static content. It owns world-node identity, adjacency and the
20-second travel duration, but no per-user travel state or persistence.
"""
from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import AbstractSet, Mapping

CITY_NODE_ID = "city"
START_PATH_ID = "start_path"
DARK_FOREST_ID = "dark_forest"
TRAVEL_SECONDS = 20

@dataclass(frozen=True, slots=True)
class WorldNode:
    """Immutable metadata for one canonical world node."""
    node_id: str
    name: str
    kind: str
    huntable: bool

_CITY = WorldNode(CITY_NODE_ID, "🏙️ Місто", "city", False)
_START_PATH = WorldNode(START_PATH_ID, "🌿 Початок Шляху", "location", True)
_DARK_FOREST = WorldNode(DARK_FOREST_ID, "🌲 Темний Бір", "location", True)

WORLD_NODE_ORDER: tuple[str, ...] = (CITY_NODE_ID, START_PATH_ID, DARK_FOREST_ID)
WORLD_NODES: Mapping[str, WorldNode] = MappingProxyType({
    CITY_NODE_ID: _CITY,
    START_PATH_ID: _START_PATH,
    DARK_FOREST_ID: _DARK_FOREST,
})
LOCATION_GRAPH: Mapping[str, tuple[str, ...]] = MappingProxyType({
    CITY_NODE_ID: (START_PATH_ID,),
    START_PATH_ID: (CITY_NODE_ID, DARK_FOREST_ID),
    DARK_FOREST_ID: (START_PATH_ID,),
})
TRANSPORT_REQUIREMENTS: tuple[()] = ()

def get_world_node(node_id: str) -> WorldNode | None:
    """Return a canonical node or None without applying a fallback."""
    return WORLD_NODES.get(str(node_id or "").strip())

def get_adjacent_nodes(node_id: str) -> tuple[str, ...]:
    """Return canonical neighbors, or an empty tuple for an unknown node."""
    return LOCATION_GRAPH.get(str(node_id or "").strip(), ())

def are_adjacent(from_node: str, to_node: str) -> bool:
    """Return False unless both IDs form an explicit directed graph edge."""
    source = str(from_node or "").strip()
    target = str(to_node or "").strip()
    if source not in WORLD_NODES or target not in WORLD_NODES:
        return False
    return target in LOCATION_GRAPH[source]

def validate_world_graph(*, location_ids: AbstractSet[str] | None = None) -> None:
    """Validate graph identity, symmetry, connectivity and catalog references."""
    if tuple(WORLD_NODES) != WORLD_NODE_ORDER:
        raise ValueError("world node order mismatch")
    if tuple(LOCATION_GRAPH) != WORLD_NODE_ORDER:
        raise ValueError("world graph order mismatch")
    if TRAVEL_SECONDS != 20:
        raise ValueError("travel duration mismatch")
    if TRANSPORT_REQUIREMENTS:
        raise ValueError("transport requirements are not part of V1 parity")
    for key, node in WORLD_NODES.items():
        if key != node.node_id:
            raise ValueError(f"world node identity mismatch: {key}")
        if node.kind not in {"city", "location"}:
            raise ValueError(f"invalid world node kind: {key}")
        if node.huntable != (node.kind == "location"):
            raise ValueError(f"huntability mismatch: {key}")
    visited = {CITY_NODE_ID}
    frontier = [CITY_NODE_ID]
    while frontier:
        current = frontier.pop()
        neighbors = LOCATION_GRAPH[current]
        if len(neighbors) != len(set(neighbors)):
            raise ValueError(f"duplicate edge: {current}")
        for neighbor in neighbors:
            if neighbor not in WORLD_NODES:
                raise ValueError(f"unknown neighbor: {neighbor}")
            if current not in LOCATION_GRAPH.get(neighbor, ()):
                raise ValueError(f"asymmetric edge: {current}->{neighbor}")
            if neighbor not in visited:
                visited.add(neighbor)
                frontier.append(neighbor)
    if visited != set(WORLD_NODES):
        raise ValueError("disconnected world graph")
    if DARK_FOREST_ID in LOCATION_GRAPH[CITY_NODE_ID]:
        raise ValueError("direct city-dark_forest route is forbidden")
    if location_ids is not None:
        huntable_ids = {key for key, node in WORLD_NODES.items() if node.huntable}
        if set(location_ids) != huntable_ids:
            raise ValueError("Location Catalog references do not match huntable graph nodes")

validate_world_graph()
