# Stage 21.5.6 — V2 database integrity suite

## Canonical tool

`tools/run_v2_db_integrity.py`

## Integrity categories

1. Clean deterministic recreate from migration `001_v2_baseline`.
2. SQLite `quick_check`, `foreign_key_check`, and active FK enforcement.
3. Representative unique constraints for Telegram account identity and event streams.
4. Persistent idempotency for operation IDs and crystal-ledger settlement.
5. Exception rollback, late constraint rollback, and absence of partial mutation.
6. Restart-style reopen with committed-state recovery and repeated integrity checks.

## Isolation

Each category uses a separate clean temporary V2 database. The production V1 `game.db`, `game.db-wal`, and `game.db-shm` are never opened or manipulated. The ignored development V2 runtime database is backed up by the patch and is not used as accumulated fixture state.

## Acceptance

The full suite must pass twice from fresh workspaces, the normal six-gate CI must remain PASS, and protected/runtime evidence must remain unchanged. Manual game verification is not required.
