# Stage 21.5.5 — V2 repository base

## Canonical adapter

`rom_v2.infrastructure.persistence.SQLiteRepositoryBase`

## Contract

- A repository can be constructed only with an active Unit of Work transaction.
- A repository uses the exact Unit of Work connection and never opens its own connection.
- A repository never commits, rolls back, or starts transactions.
- SQL calls are parameterized and limited to one statement per repository operation.
- Query results use `sqlite3.Row`; `fetch_all` returns an immutable tuple snapshot.
- Missing required rows and stale row-count mismatches use stable machine-readable errors.
- Repository access after commit or rollback fails closed.

## Scope

This stage creates infrastructure primitives only. Domain-specific account, character, inventory, and other repository adapters remain owned by their future domain stages.

## Manual verification

Not required. Focused tests and CI verify transaction ownership, commit/rollback behavior, mapped rows, stale guards, and SQL boundary rules.
