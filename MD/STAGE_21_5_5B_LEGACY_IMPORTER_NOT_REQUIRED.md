# Stage 21.5.5b — Optional legacy importer: NOT_REQUIRED

## Decision

Canonical Stage `21.5.5 — Optional legacy importer` is closed as `NOT_REQUIRED`.

ROM V2 will continue from a clean database created by migration `001_v2_baseline`. No V1 users, characters, balances, inventory, quests, migration history, or other runtime data will be imported.

## Rationale

- ROM V2 is pre-production.
- The current V1 database contains disposable development and test data.
- The accepted architecture is reset-first and clean-create.
- A legacy importer would add compatibility, mapping, reconciliation, and validation cost without protecting production data.
- V1 remains an immutable behavioral reference, not a V2 data source.

## Explicitly not implemented

- No V1-to-V2 importer module.
- No migration mapping tables.
- No compatibility columns or placeholder schema.
- No reads from `game.db`.
- No manipulation of `game.db-wal` or `game.db-shm`.
- No import CLI, startup hook, background job, or automatic conversion.

## Future exception policy

If real production V1 data ever requires transfer, that work must be opened as a new, separately designed stage with explicit mapping, reconciliation, dry-run, audit, rollback, and acceptance contracts. This closed optional stage must not be silently reopened.

## Next canonical stage

`21.5.6 — DB integrity suite`.

## Manual verification

Not required. This is a policy-only closure and changes no production code or database.
