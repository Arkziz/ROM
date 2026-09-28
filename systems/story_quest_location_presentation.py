#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Canonical localized display names for story-quest locations."""
from __future__ import annotations

import re
from data.locations import LOCATIONS


def resolve_story_quest_location_name(location_id: str) -> str:
    """Return the canonical player-facing location name or fail closed.

    Story presentation must never derive user-facing text from technical IDs.
    Unknown IDs are content defects and therefore raise instead of leaking a
    value such as ``start_path`` or an artificial title-cased variant.
    """
    normalized = str(location_id or "").strip()
    if not normalized:
        raise ValueError("story quest location_id is empty")
    location = LOCATIONS.get(normalized)
    if location is None:
        raise KeyError(f"unknown story quest location_id: {normalized}")
    raw_name = location.get("name") if isinstance(location, dict) else getattr(location, "name", None)
    display_name = re.sub(r"^[^\w]+", "", str(raw_name or "").strip(), flags=re.UNICODE).strip()
    if not display_name:
        raise ValueError(f"location has no player-facing name: {normalized}")
    return display_name
