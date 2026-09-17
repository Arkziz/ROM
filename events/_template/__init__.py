# -*- coding: utf-8 -*-
"""Non-production event template. Never add to EVENT_MODULES."""
from . import bosses, config, drops, handlers, items, mobs, quests, rewards, shop, statistics
from .bosses import get_boss_candidates
from .drops import get_drop_rules
from .items import get_items
from .mobs import get_mob_candidates

__all__ = (
    "bosses", "config", "drops", "handlers", "items", "mobs",
    "quests", "rewards", "shop", "statistics",
    "get_boss_candidates", "get_drop_rules", "get_items", "get_mob_candidates",
)
