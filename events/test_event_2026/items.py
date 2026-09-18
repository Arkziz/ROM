# -*- coding: utf-8 -*-
from .config import EVENT_KEY

TEST_TOKEN_ITEM_ID = 4000
TEST_REWARD_ITEM_ID = 4001
EVENT_ITEMS = (
    {
        "event_key": EVENT_KEY,
        "item_key": "test_token",
        "id": TEST_TOKEN_ITEM_ID,
        "name": "🧪 Експериментальний жетон",
        "type": "test_event_token",
        "rarity": "common",
        "category": "material",
        "max_stack": 999,
        "sell_price": 0.0,
        "stackable": True,
        "tradeable": False,
        "sellable": False,
        "auctionable": False,
        "character_bound": True,
        "available_after_event": True,
    },
    {
        "event_key": EVENT_KEY,
        "item_key": "test_reward",
        "id": TEST_REWARD_ITEM_ID,
        "name": "🎁 Пам’ятний знак випробування",
        "type": "test_event_reward",
        "rarity": "uncommon",
        "category": "collectible",
        "max_stack": 10,
        "sell_price": 0.0,
        "stackable": True,
        "tradeable": False,
        "sellable": False,
        "auctionable": False,
        "character_bound": True,
        "available_after_event": True,
    },
)

def get_item_definitions():
    return EVENT_ITEMS

def get_event_item_id(item_key):
    key = str(item_key or "").strip()
    for item in EVENT_ITEMS:
        if item["item_key"] == key:
            return item["id"]
    raise KeyError(key)
