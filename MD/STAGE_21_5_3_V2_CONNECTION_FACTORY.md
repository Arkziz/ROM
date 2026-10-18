# Stage 21.5.3 — V2 connection factory

## Canonical owner

`rom_v2.infrastructure.persistence.V2ConnectionFactory`

## Connection policy

- Database path must be below the explicit `.runtime/v2/db` owner root.
- Database filename must be `rom_v2.db`.
- Every connection enables foreign keys and a 5000 ms busy timeout.
- Read/write mode uses WAL, synchronous NORMAL, `sqlite3.Row`, and `isolation_level=None`.
- Application Unit of Work will own explicit transaction start/commit/rollback.
- Read-only mode uses SQLite URI `mode=ro` plus `PRAGMA query_only=ON`.
- The factory cannot open V1 `game.db`.

## Safety

The V1 DB/WAL/SHM remain unchanged. The isolated V2 runtime database is ignored and untracked. Manual game verification is not required.
