# -*- coding: utf-8 -*-
from .config import (
    ARCHIVE_VISIBLE, DATE_POLICY, DISPLAY_NAME, ENABLED, END_AT, END_LOCAL,
    EVENT_ICON, EVENT_KEY, EVENT_NAME, EVENT_SHORT_DESCRIPTION, EVER_LAUNCHED,
    START_AT, START_LOCAL, TIMEZONE_NAME,
)
from .bosses import get_boss_candidates
from .drops import get_drop_rules
from .handlers import register_handlers
from .items import get_item_definitions


def get_items():
    return get_item_definitions()
from .mobs import get_mob_candidates
from .quests import get_quests
from .rewards import get_rewards
from .shop import get_shop_offers
from .statistics import get_statistics_definitions

__all__ = (
    "EVENT_KEY", "EVENT_NAME", "DISPLAY_NAME", "EVENT_ICON",
    "EVENT_SHORT_DESCRIPTION", "ENABLED", "ARCHIVE_VISIBLE", "EVER_LAUNCHED",
    "TIMEZONE_NAME", "START_LOCAL", "END_LOCAL", "START_AT", "END_AT",
    "DATE_POLICY", "get_mob_candidates", "get_boss_candidates",
    "get_drop_rules", "get_item_definitions", "get_items", "get_shop_offers",
    "get_statistics_definitions", "get_quests", "get_rewards", "register_handlers",
)


# Self-registration is required because load_event_modules imports packages but
# intentionally does not mutate EVENT_REGISTRY itself.
import sys as _sys
from events import register_event as _register_event
_register_event(EVENT_KEY, _sys.modules[__name__])
