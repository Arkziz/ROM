# -*- coding: utf-8 -*-
"""Deterministic Stage 18 schema bootstrap orchestration.

Initializers remain authoritative owners of their tables. This module only
orders and invokes available idempotent initializers before handlers/polling.
"""
from __future__ import annotations

import importlib

INITIALIZERS = (
    ("systems.item_id_allocator_system", "init_item_id_allocator_system"),
    ("db_modules.daily_compat", "init_daily_quest_system"),
    ("db_modules.refine", "init_refine_system"),
    ("db_modules.shop", "init_shop_preview_system"),
    ("systems.crystal_system", "init_crystal_system"),
    ("systems.crystal_wallet_system", "init_crystal_wallet_system"),
    ("systems.premium_item_policy_system", "init_premium_item_policy_system"),
    ("systems.auction_house_system", "init_auction_house"),
    ("systems.guild_system", "init_guild_system"),
)


def run_fresh_database_schema_bootstrap():
    results = []
    seen = set()
    for module_name, function_name in INITIALIZERS:
        try:
            module = importlib.import_module(module_name)
        except ModuleNotFoundError as exc:
            if exc.name == module_name:
                results.append({"module": module_name, "function": function_name,
                                "status": "not_present"})
                continue
            raise
        fn = getattr(module, function_name, None)
        if not callable(fn):
            results.append({"module": module_name, "function": function_name,
                            "status": "not_present"})
            continue
        key = (module_name, function_name)
        if key in seen:
            continue
        seen.add(key)
        value = fn()
        results.append({"module": module_name, "function": function_name,
                        "status": "called", "result": repr(value)[:2000]})
    return {"success": True, "results": results}
