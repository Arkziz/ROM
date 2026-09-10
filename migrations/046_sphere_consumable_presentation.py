#!/usr/bin/env python3
"""Migration 046: place both premium spheres in Consumables."""
def up(conn):
 rows=conn.execute("SELECT id,name FROM items WHERE id IN (501,504) ORDER BY id").fetchall()
 if [int(r[0]) for r in rows] != [501,504]:raise RuntimeError(f"Sphere items missing: {rows}")
 conn.execute("UPDATE items SET category='consumable' WHERE id IN (501,504)")
 return {"updated":2,"item_ids":[501,504]}
