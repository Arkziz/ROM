# Stage 21.4.3 — Inventory transaction atomicity

- Status: **PASS**
- Parent: `eb8b2d6b5b42f20cb7c7febbebfd775b0e12200d`
- Canonical owner file: `db_modules/inventory.py`
- Functions hardened: `consume_inventory_item`, `consume_user_item_by_item_id`
- Commit on success: **YES**
- Rollback and re-raise on failure: **YES**
- Injected-failure unchanged-state smoke: **PASS**
- Production SQLite/WAL/SHM patch mutations: **NONE**
- Manual game check: **REQUIRED**
