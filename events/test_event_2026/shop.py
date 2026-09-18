# -*- coding: utf-8 -*-
from .config import EVENT_KEY
from .items import TEST_REWARD_ITEM_ID, TEST_TOKEN_ITEM_ID

EVENT_SHOP_OFFERS = (
    {
        "event_key": EVENT_KEY,
        "offer_key": "test_reward_exchange",
        "operation_kind": "exchange",
        "reward_kind": "static_item",
        "cost_item_id": TEST_TOKEN_ITEM_ID,
        "cost_quantity": 3,
        "reward_item_id": TEST_REWARD_ITEM_ID,
        "reward_quantity": 1,
        "purchase_limit": None,
    },
)

def get_shop_offers():
    return EVENT_SHOP_OFFERS
