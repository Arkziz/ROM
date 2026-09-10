#!/usr/bin/env python3
"""Migration 045: persist the concrete New Path Sphere selected for class change."""
def up(conn):
 cols={str(r[1]) for r in conn.execute("PRAGMA table_info(users)")}
 if "pending_class_change_inventory_id" not in cols:
  conn.execute("ALTER TABLE users ADD COLUMN pending_class_change_inventory_id INTEGER NULL")
 return {"column":"users.pending_class_change_inventory_id"}
