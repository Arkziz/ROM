# -*- coding: utf-8 -*-
from .config import EVENT_KEY

MOB_KEY = "test_slime"
EVENT_MOB_CANDIDATES = (
    {
        "event_key": EVENT_KEY,
        "mob_key": MOB_KEY,
        "weight": 1.0,
        "chance_percent": 25.0,
        "all_huntable_locations": True,
        "minimum_level": 1,
        "maximum_level": 30,
        "level_policy": "player_level",
        "mob_template": {
            "name": "🧪 Нестабільний слизень",
            "attack_type": "physical",
            "level_policy": "player_level",
            "primary_stat_profile": "canonical_normal_physical",
            "min_gold": 0.0,
            "max_gold": 0.0,
            "loot_chance": 0.0,
            "trash_items": [],
        },
    },
)

def get_mob_candidates(context=None):
    context = context if isinstance(context, dict) else {}
    player_level = int(context.get("player_level", 0) or 0)
    location_id = str(context.get("location_id") or "").strip()
    if not location_id or not 1 <= player_level <= 30:
        return ()
    return EVENT_MOB_CANDIDATES
