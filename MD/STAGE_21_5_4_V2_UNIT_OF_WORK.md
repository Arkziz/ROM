# Stage 21.5.4 — V2 Unit of Work

## Canonical adapter

`rom_v2.infrastructure.persistence.SQLiteUnitOfWork`

## Transaction contract

- One Unit of Work instance owns one read/write connection and one `BEGIN IMMEDIATE` transaction.
- `commit()` is the only successful mutation terminal.
- `rollback()` is an explicit non-success terminal.
- Exiting without `commit()` always rolls back.
- Exceptions always propagate and roll back uncommitted state.
- Reentry and reuse are forbidden.
- The connection closes exactly once at context exit.
- Repositories will receive the active Unit of Work connection and will not control transactions.
- A failure after a completed commit does not attempt an impossible database rollback.

## Acceptance

Focused tests prove commit, implicit rollback-on-exit, exception rollback, explicit rollback, one-shot lifecycle, and multi-statement atomicity. Manual game verification is not required.
