# Stage 21.4.4 — Generated equipment transaction atomicity

- Status: **PASS**
- Parent: `c27719dca7373bb5447b496cba3effa417c4c7f9`
- Canonical owner: `create_generated_equipment_item`
- Item row and inventory row: **ONE TRANSACTION**
- Commit on success: **YES**
- Rollback and re-raise on failure: **YES**
- Injected failure between rows: **PASS, BOTH ROWS ABSENT**
- Production SQLite/WAL/SHM patch mutations: **NONE**
- Manual game check: **REQUIRED**
