#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Canonical economic/source policy for the two sphere items."""
from __future__ import annotations
NEW_PATH_SPHERE_ITEM_ID = 501
REBIRTH_SPHERE_ITEM_ID = 504
SPHERE_ECONOMIC_POLICY = {
    NEW_PATH_SPHERE_ITEM_ID: {
        "premium_bound": True,
        "character_bound": True,
        "tradeable": False,
        "auctionable": False,
        "mob_drop_eligible": False,
        "crystal_shop_eligible": True,
    },
    REBIRTH_SPHERE_ITEM_ID: {
        "premium_bound": False,
        "character_bound": False,
        "tradeable": True,
        "auctionable": True,
        "mob_drop_eligible": True,
        "crystal_shop_eligible": False,
    },
}
def get_sphere_economic_policy(item_id):
    policy=SPHERE_ECONOMIC_POLICY.get(int(item_id))
    return None if policy is None else dict(policy)
