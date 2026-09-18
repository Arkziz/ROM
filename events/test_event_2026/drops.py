# -*- coding: utf-8 -*-
from .config import EVENT_KEY
from .items import TEST_TOKEN_ITEM_ID
from .mobs import MOB_KEY

EVENT_DROP_RULES = (
    {
        "rule_id": "test_event_2026:test_token",
        "event_key": EVENT_KEY,
        "mob_key": MOB_KEY,
        "item_id": TEST_TOKEN_ITEM_ID,
        "quantity": 1,
        "chance_percent": 100.0,
    },
)

def get_drop_rules(context=None):
    context = context if isinstance(context, dict) else {}
    event_key = str(context.get("event_key") or "").strip()
    mob_key = str(context.get("event_mob_key") or context.get("mob_key") or "").strip()
    if event_key and event_key != EVENT_KEY:
        return ()
    if mob_key and mob_key != MOB_KEY:
        return ()
    return EVENT_DROP_RULES
