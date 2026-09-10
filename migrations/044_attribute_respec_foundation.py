#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ROM migration 044: Attribute Respec audit and Rebirth Sphere item."""
from __future__ import annotations
REBIRTH_SPHERE_ITEM_ID=504
def _columns(conn,table):return {str(r[1]) for r in conn.execute(f"PRAGMA table_info({table})")}
def up(conn):
 conn.execute("""CREATE TABLE IF NOT EXISTS attribute_respec_events(
  id INTEGER PRIMARY KEY AUTOINCREMENT,user_id INTEGER NOT NULL,
  operation_type TEXT NOT NULL CHECK(operation_type IN ('attribute_respec','class_change')),
  old_class TEXT,new_class TEXT,returned_points INTEGER NOT NULL,
  returned_strength INTEGER NOT NULL,returned_dexterity INTEGER NOT NULL,
  returned_intelligence INTEGER NOT NULL,returned_wisdom INTEGER NOT NULL,
  returned_stamina INTEGER NOT NULL,source_inventory_id INTEGER,source_item_id INTEGER,
  idempotency_key TEXT NOT NULL UNIQUE,created_at TEXT NOT NULL,
  FOREIGN KEY(user_id) REFERENCES users(user_id) ON DELETE CASCADE)""")
 conn.execute("CREATE INDEX IF NOT EXISTS ix_attribute_respec_events_user ON attribute_respec_events(user_id,id DESC)")
 cols=_columns(conn,"items")
 if not cols:raise RuntimeError("items table missing")
 existing=conn.execute("SELECT name,type FROM items WHERE id=?",(REBIRTH_SPHERE_ITEM_ID,)).fetchone()
 if existing and (str(existing[0])!="♻️ Сфера Переродження" or str(existing[1])!="attribute_respec"):
  raise RuntimeError(f"Item ID {REBIRTH_SPHERE_ITEM_ID} already occupied: {existing}")
 values={"id":REBIRTH_SPHERE_ITEM_ID,"name":"♻️ Сфера Переродження","type":"attribute_respec","rarity":"epic","category":"consumable","slot_key":"","weapon_hands":0,"max_stack":1,"sell_price":0,"item_level":1,"is_generated":0,"item_subtype":"attribute_respec"}
 if not existing:
  names=[k for k in values if k in cols];conn.execute("INSERT INTO items("+",".join(names)+") VALUES("+",".join("?" for _ in names)+")",[values[k] for k in names])
 return {"item_id":REBIRTH_SPHERE_ITEM_ID,"table":"attribute_respec_events"}
