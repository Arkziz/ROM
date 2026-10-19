"""Migration 003: separate catalog definitions from owned item instances."""
from __future__ import annotations
from rom_v2.infrastructure.persistence.migrations.v001_v2_baseline import Migration

MIGRATION_SQL=r"""
CREATE TABLE item_definitions (
 item_id INTEGER PRIMARY KEY NOT NULL CHECK(item_id>0),
 name TEXT NOT NULL CHECK(length(trim(name))>0),
 item_type TEXT NOT NULL CHECK(length(trim(item_type))>0),
 metadata_json TEXT NOT NULL DEFAULT '{}' CHECK(json_valid(metadata_json))
) STRICT;
CREATE TABLE inventory_items (
 inventory_id INTEGER PRIMARY KEY NOT NULL CHECK(inventory_id>0),
 owner_user_id INTEGER NOT NULL CHECK(owner_user_id>0),
 item_id INTEGER NOT NULL CHECK(item_id>0),
 quantity INTEGER NOT NULL DEFAULT 1 CHECK(quantity>0),
 instance_metadata_json TEXT NOT NULL DEFAULT '{}' CHECK(json_valid(instance_metadata_json)),
 FOREIGN KEY(item_id) REFERENCES item_definitions(item_id) ON DELETE RESTRICT ON UPDATE CASCADE
) STRICT;
CREATE INDEX ix_inventory_items_owner ON inventory_items(owner_user_id,inventory_id);
CREATE INDEX ix_inventory_items_definition ON inventory_items(item_id,inventory_id);
"""
MIGRATION=Migration(version=3,key="item_identity_parity",sql=MIGRATION_SQL)
