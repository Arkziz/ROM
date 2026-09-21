#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Seed item 501 before sphere presentation migrations 046-048.

Fresh databases run migrations before main.py calls init_class_reset_sphere().
Migration 046 requires both item 501 and item 504, while 044 already owns 504.
This dependency migration makes item 501 available in filename order without
moving startup calls or duplicating travel schema ownership.
"""
NEW_PATH_SPHERE_ITEM_ID = 501

def up(conn):
    row = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='items'"
    ).fetchone()
    if not row:
        raise RuntimeError('items table is required before sphere dependency seed')
    conn.execute(
        """
        INSERT INTO items (
            id, name, type, rarity, category, slot_key, weapon_hands,
            max_stack, sell_price, bonus_str, bonus_dex, bonus_int,
            bonus_wis, bonus_sta, pdef, mdef
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(id) DO UPDATE SET
            name=excluded.name,
            type=excluded.type,
            rarity=excluded.rarity,
            category=excluded.category,
            slot_key=excluded.slot_key,
            weapon_hands=excluded.weapon_hands,
            max_stack=excluded.max_stack,
            sell_price=excluded.sell_price
        """,
        (
            NEW_PATH_SPHERE_ITEM_ID,
            '🔮 Сфера нового шляху',
            'class_reset',
            'epic',
            'consumable',
            None,
            1,
            10,
            0.0,
            0, 0, 0, 0, 0, 0, 0,
        ),
    )
    seeded = conn.execute(
        "SELECT id, type, category, max_stack FROM items WHERE id=?",
        (NEW_PATH_SPHERE_ITEM_ID,),
    ).fetchone()
    if not seeded or int(seeded[0]) != NEW_PATH_SPHERE_ITEM_ID:
        raise RuntimeError('New Path Sphere dependency seed failed')
    return {
        'item_id': NEW_PATH_SPHERE_ITEM_ID,
        'type': str(seeded[1]),
        'category': str(seeded[2]),
        'max_stack': int(seeded[3]),
    }
