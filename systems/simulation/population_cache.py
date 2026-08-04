from __future__ import annotations

import json
from pathlib import Path
from typing import Mapping

from systems.simulation.balance_analyzer import ResultCache, ScenarioSpec


def _int(value, default=None):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _metadata_from_payload(payload):
    if not isinstance(payload, Mapping):
        return None
    character_class = str(payload.get("character_class") or "").strip()
    profile = str(payload.get("profile") or payload.get("profile_key") or "").strip()
    seed = _int(payload.get("seed"))
    target_level = _int(payload.get("target_level"), _int(payload.get("final_level")))
    if not character_class or not profile or seed is None or target_level is None:
        return None
    return character_class, profile, seed, target_level


def _resolve_capacity_from_cache_key(cache, path, metadata, max_days=365):
    character_class, profile, seed, target_level = metadata
    for inventory_capacity in (40, 60):
        spec = ScenarioSpec(
            character_class=character_class,
            profile=profile,
            seed=seed,
            target_level=target_level,
            inventory_capacity=inventory_capacity,
            max_days=max_days,
        )
        if cache.path_for(spec).name == path.name:
            return inventory_capacity
    return None


def load_progression_cache(root: Path, target_level: int | None = None, capacity: int | None = None):
    root = Path(root)
    cache = ResultCache(root)
    rows = []
    if not cache.directory.exists():
        return rows

    for path in sorted(cache.directory.glob("*.json")):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        if not isinstance(payload, Mapping):
            continue

        metadata = _metadata_from_payload(payload)
        if metadata is None:
            continue
        character_class, profile, seed, payload_target_level = metadata

        max_days = _int(payload.get("max_days"), 365)
        inventory_capacity = _int(payload.get("inventory_capacity"))
        if inventory_capacity not in (40, 60):
            inventory_capacity = _resolve_capacity_from_cache_key(
                cache,
                path,
                metadata,
                max_days=max_days,
            )
        if inventory_capacity not in (40, 60):
            continue

        if target_level is not None and payload_target_level != int(target_level):
            continue
        if capacity is not None and inventory_capacity != int(capacity):
            continue

        row = dict(payload)
        row["character_class"] = character_class
        row["profile"] = profile
        row["seed"] = seed
        row["target_level"] = payload_target_level
        row["inventory_capacity"] = inventory_capacity
        row["max_days"] = max_days
        rows.append(row)

    return rows
