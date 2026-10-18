# Stage 21.5.2 — V2 baseline migration

## Result

Migration `001_v2_baseline` creates a new isolated ROM V2 SQLite database from scratch. The V1 `game.db` and its migration chain are not imported.

## Runtime ownership

The development database is created only at `.runtime/v2/db/rom_v2.db`, which is ignored by Git. Reset/recreate may delete only this V2 database and its own sidecars. V1 `game.db-wal` and `game.db-shm` remain prohibited rollback targets.

## Acceptance contract

- 15 user tables and 7 named indexes.
- `PRAGMA foreign_keys = ON`.
- `PRAGMA foreign_key_check` returns no rows.
- `PRAGMA quick_check` returns `ok`.
- Migration history contains exactly version `1` and key `001_v2_baseline`.
- Migration checksum is stable SHA-256.
- Recreate from empty storage is deterministic.
- Six-gate CI remains PASS.

## Manual verification

Not required in the game. The database is isolated and contains no gameplay data.
