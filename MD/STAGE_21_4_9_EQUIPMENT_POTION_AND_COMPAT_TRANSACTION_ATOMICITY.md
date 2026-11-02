# Stage 21.4.9 — Equipment, potion and compat transaction atomicity

- Status: **PASS**
- Selected owners: `_equipment_write_ensure_slots_v5`, `_equipment_write_set_slot_v5`, `apply_random_durability_wear_on_victory`, `ensure_equipment_slots`, `set_inventory_item_durability`, `use_potion_from_inventory`, `seed_class_reset_sphere_item`
- Rollback and re-raise: **YES**
- Injected-failure unchanged-state smoke: **PASS**
- Production SQLite/WAL/SHM patch mutations: **NONE**
- Manual game check: **REQUIRED**
