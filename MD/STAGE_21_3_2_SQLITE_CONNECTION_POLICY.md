# Stage 21.3.2 — SQLite connection policy

- Status: **PASS**
- Parent: `514709cd3dd534b8a8d5a3c0aa77325db02495b1`
- Canonical helper: `systems/sqlite_connection_policy.py`
- Migrated runtime owners: `17`
- Direct production connections before: `21`
- Canonical helper internal direct connection: `1`
- Explicit special-consumer direct connections after: `4`
- Total direct `sqlite3.connect` calls after: `5`
- Default timeout: `30s`
- Default busy timeout: `30000ms`
- Default foreign keys: `ON`
- Query-only: opt-in
- Journal mode changes in helper: **NONE**
- Transaction ownership changes: **NONE**
- Connection lifecycle changes: **NONE**
- Production SQLite/WAL/SHM patch mutations: **NONE**
- Manual game check: **REQUIRED**
