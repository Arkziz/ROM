"""Canonical extraction of a player's level for story-quest presentation."""
from __future__ import annotations
from collections.abc import Mapping
from typing import Any

def resolve_story_quest_player_level(stats: Any, *, default: int = 1) -> int:
    """Return a validated level from canonical stats and row-like objects.

    ``db.get_player_stats`` returns ``(STR, DEX, INT, WIS, STA, level)``.
    Story journal and NPC presentation also accept mapping and object forms.
    """
    fallback = max(1, int(default))
    if stats is None:
        return fallback

    value = None
    if isinstance(stats, (tuple, list)):
        # Canonical positional contract: level is the sixth field.
        value = stats[5] if len(stats) > 5 else fallback
    elif isinstance(stats, Mapping):
        value = stats.get("level", fallback)
    elif hasattr(stats, "keys") and callable(stats.keys):
        try:
            if "level" in stats.keys():
                value = stats["level"]
        except (KeyError, TypeError, IndexError):
            value = None

    if value is None:
        value = getattr(stats, "level", fallback)
    try:
        level = int(value)
    except (TypeError, ValueError):
        return fallback
    return level if level >= 1 else fallback
