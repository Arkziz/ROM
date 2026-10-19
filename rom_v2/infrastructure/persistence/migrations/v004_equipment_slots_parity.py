"""Forward migration replacing provisional equipment_slots with inventory parity."""
from __future__ import annotations
from rom_v2.infrastructure.persistence.migrations.v001_v2_baseline import Migration
MIGRATION_SQL="""
PRAGMA foreign_keys = OFF;
DROP TABLE IF EXISTS equipment_slots;
CREATE TABLE equipment_slots (
 owner_user_id INTEGER NOT NULL,
 slot_key TEXT NOT NULL CHECK(slot_key IN ('main_hand','off_hand','helmet','shoulders','chest','gloves','legs','boots','necklace','ring')),
 inventory_id INTEGER NOT NULL UNIQUE,
 PRIMARY KEY(owner_user_id,slot_key),
 FOREIGN KEY(inventory_id) REFERENCES inventory_items(inventory_id) ON DELETE RESTRICT ON UPDATE CASCADE
) STRICT;
PRAGMA foreign_keys = ON;
"""
MIGRATION=Migration(version=4,key="equipment_slots_parity",sql=MIGRATION_SQL)
