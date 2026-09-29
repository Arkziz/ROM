"""Canonical extraction of a player's level for story-quest presentation."""
from __future__ import annotations
from collections.abc import Mapping
from typing import Any

def resolve_story_quest_player_level(stats: Any, *, default: int = 1) -> int:
    """Return a validated level from dict, Mapping, sqlite Row, or an object.

    Database helpers may return mapping-like row objects that are not ``dict``.
    Story journal and NPC presentation must therefore share this one adapter
    rather than silently falling back to level 1 for valid rows.
    """
    fallback=max(1,int(default))
    if stats is None:return fallback
    value=None
    if isinstance(stats,Mapping):
        value=stats.get("level",fallback)
    elif hasattr(stats,"keys") and callable(stats.keys):
        try:
            if "level" in stats.keys():value=stats["level"]
        except (KeyError,TypeError,IndexError):
            value=None
    if value is None:value=getattr(stats,"level",fallback)
    try:level=int(value)
    except (TypeError,ValueError):return fallback
    return level if level>=1 else fallback
