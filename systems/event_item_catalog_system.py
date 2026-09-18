# -*- coding: utf-8 -*-
"""Canonical persistent catalog adapter for registered static event items."""
from __future__ import annotations

ROM_STAGE_18_29_3A_EVENT_ITEM_CATALOG = True
CATALOG_COLUMNS = (
    "id", "name", "type", "rarity", "category", "slot_key", "weapon_hands",
    "max_stack", "sell_price", "bonus_str", "bonus_dex", "bonus_int",
    "bonus_wis", "bonus_sta", "pdef", "mdef",
)


def _catalog_row(item):
    return (
        int(item["id"]), str(item["name"]), str(item["type"]),
        str(item["rarity"]), str(item["category"]), None, 1,
        int(item["max_stack"]), float(item.get("sell_price", 0.0)),
        0, 0, 0, 0, 0, 0, 0,
    )


def get_registered_event_item_definitions():
    import events
    # Registry loading is explicit. A fresh interpreter has an empty runtime
    # registry even though EVENT_MODULES contains the production package.
    events.load_event_modules()
    collector = getattr(events, "collect_registered_event_items", None)
    if not callable(collector):
        raise RuntimeError("events.collect_registered_event_items is unavailable")
    definitions = tuple(collector())
    from events.item_namespace import validate_event_item_definitions
    return validate_event_item_definitions(definitions)


def validate_event_item_catalog_definitions(definitions=None):
    items = get_registered_event_item_definitions() if definitions is None else tuple(definitions)
    seen = set()
    for item in items:
        item_id = int(item["id"])
        if item_id in seen:
            raise ValueError("duplicate event item ID")
        seen.add(item_id)
        if not str(item.get("name") or "").strip():
            raise ValueError("event item name is required")
        if int(item.get("max_stack") or 0) <= 0:
            raise ValueError("event item max_stack must be positive")
        for flag in ("tradeable", "sellable", "auctionable"):
            if item.get(flag) is not False:
                raise ValueError(f"pilot item must explicitly set {flag}=False")
        if float(item.get("sell_price", 0.0)) != 0.0:
            raise ValueError("pilot item sell_price must be zero")
    return items


def seed_event_item_catalog(connection=None, *, commit=True):
    if connection is None:
        from db_modules.connection import conn as connection
    definitions = validate_event_item_catalog_definitions()
    sql = """
        INSERT INTO items (
            id,name,type,rarity,category,slot_key,weapon_hands,max_stack,sell_price,
            bonus_str,bonus_dex,bonus_int,bonus_wis,bonus_sta,pdef,mdef
        ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        ON CONFLICT(id) DO UPDATE SET
            name=excluded.name,type=excluded.type,rarity=excluded.rarity,
            category=excluded.category,slot_key=excluded.slot_key,
            weapon_hands=excluded.weapon_hands,max_stack=excluded.max_stack,
            sell_price=excluded.sell_price,bonus_str=excluded.bonus_str,
            bonus_dex=excluded.bonus_dex,bonus_int=excluded.bonus_int,
            bonus_wis=excluded.bonus_wis,bonus_sta=excluded.bonus_sta,
            pdef=excluded.pdef,mdef=excluded.mdef
    """
    rows = tuple(_catalog_row(item) for item in definitions)
    try:
        for row in rows:
            connection.execute(sql, row)
        if commit:
            connection.commit()
    except Exception:
        if commit:
            connection.rollback()
        raise
    return {"success": True, "seeded": len(rows), "item_ids": tuple(row[0] for row in rows)}
