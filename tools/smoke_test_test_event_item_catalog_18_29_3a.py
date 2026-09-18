# -*- coding: utf-8 -*-
import sqlite3
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from systems.event_item_catalog_system import (
    get_registered_event_item_definitions, seed_event_item_catalog,
    validate_event_item_catalog_definitions,
)
items = validate_event_item_catalog_definitions()
import events
registered = events.get_registered_events()
assert len(registered) == 1 and registered[0].config.EVENT_KEY == "test_event_2026", registered
assert len(items) == 2, items
assert [item["id"] for item in items] == [4000, 4001]
assert [item["max_stack"] for item in items] == [999, 10]
assert all(item["tradeable"] is False for item in items)
assert all(item["sellable"] is False for item in items)
assert all(item["auctionable"] is False for item in items)
conn = sqlite3.connect(":memory:")
conn.execute("""CREATE TABLE items (
 id INTEGER PRIMARY KEY,name TEXT,type TEXT,rarity TEXT,category TEXT,
 slot_key TEXT,weapon_hands INTEGER,max_stack INTEGER,sell_price REAL,
 bonus_str INTEGER,bonus_dex INTEGER,bonus_int INTEGER,bonus_wis INTEGER,
 bonus_sta INTEGER,pdef INTEGER,mdef INTEGER)""")
first = seed_event_item_catalog(conn)
second = seed_event_item_catalog(conn)
assert first["item_ids"] == (4000, 4001) and second["seeded"] == 2
rows = conn.execute("SELECT id,name,type,rarity,category,max_stack,sell_price FROM items ORDER BY id").fetchall()
assert rows == [
 (4000, "🧪 Експериментальний жетон", "test_event_token", "common", "material", 999, 0.0),
 (4001, "🎁 Пам’ятний знак випробування", "test_event_reward", "uncommon", "collectible", 10, 0.0),
]
conn.close()
print("TEST_EVENT_ITEM_CATALOG_18_29_3A_OK")
