# -*- coding: utf-8 -*-
from .config import EVENT_KEY
from .mobs import MOB_KEY

EVENT_STATISTICS = (
    {
        "event_key": EVENT_KEY,
        "metric_key": "event_mob_kills",
        "mob_key": MOB_KEY,
        "top_size": 100,
        "page_size": 10,
        "ordering": ("value_desc", "first_reached_at_asc", "user_id_asc"),
        "exactly_once": True,
        "completed_read_only": True,
    },
)

def get_statistics_definitions():
    return EVENT_STATISTICS
