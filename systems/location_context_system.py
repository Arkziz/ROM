"""Authoritative keyboard and navigation context for a player's world node."""
from __future__ import annotations

from db import get_current_location
from data.location_graph import CITY_NODE, WORLD_NODES
from systems.travel_system import is_user_travelling


def get_location_context_kind(user_id):
    """Return travel, city, location, or invalid without changing location."""
    uid = int(user_id)
    if is_user_travelling(uid):
        return "travel"
    node = str(get_current_location(uid) or CITY_NODE)
    if node == CITY_NODE:
        return "city"
    profile = WORLD_NODES.get(node)
    if profile and profile.get("kind") == "location":
        return "location"
    return "invalid"


def get_location_context_kb(user_id):
    """Resolve the persistent ReplyKeyboard from authoritative DB state."""
    from keyboards import city_kb, main_kb, map_kb

    kind = get_location_context_kind(user_id)
    if kind == "travel":
        return map_kb()
    if kind == "city":
        return city_kb()
    if kind == "location":
        return main_kb()
    # Unknown location state must not expose hunting controls.
    return map_kb()


def get_location_context_return_text(user_id):
    kind = get_location_context_kind(user_id)
    if kind == "travel":
        return "🚶 Повернення до статусу подорожі."
    if kind == "city":
        return "🏙️ Повернення до Міста."
    if kind == "location":
        return "🏕️ Повернення до основного меню локації."
    return "⚠️ Не вдалося визначити поточне місцезнаходження. Відкрий мапу."
