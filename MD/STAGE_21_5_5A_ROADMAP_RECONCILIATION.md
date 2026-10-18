# Stage 21.5.5a — Roadmap reconciliation and reset-policy closure

## Decision

No production rollback or commit renaming is required. The implementations are technically valid, but historical implementation labels `21.5.4` and `21.5.5` are reclassified as slices of canonical roadmap Stage `21.5.3 — Repository implementations`.

## Canonical mapping

- **21.5.1 — Domain-oriented schema design:** `ACCEPTED` through revisions 21.5.1, 21.5.1a, and 21.5.1b.
- **21.5.2 — Baseline migration:** `COMPLETED` by migration `001_v2_baseline`.
- **21.5.3 — Repository implementations:** `COMPLETED` by connection factory, Unit of Work, repository base, and transaction tests.
- **21.5.4 — Reset-first development policy:** `IMPLEMENTED` by the isolated ignored runtime DB, deterministic recreate, clean baseline, and V1 isolation.
- **21.5.5 — Optional legacy importer:** `NOT_STARTED`; the historical implementation label 21.5.5 does not implement this canonical stage.
- **21.5.6 — DB integrity suite:** `NOT_STARTED`.

## Historical implementation labels preserved

- `19a699f7...` retained as historical Stage 21.5.3 connection-factory commit.
- `82a04116...` retained as historical Stage 21.5.4 Unit-of-Work slice.
- `0270d5ea...` retained as historical Stage 21.5.5 repository-base slice.

The Git history, filenames, reports, and commits are not rewritten. Canonical roadmap reporting must use the mapping above.

## Reset-first policy closure

The V2 development database is `.runtime/v2/db/rom_v2.db`; it is ignored and untracked. It may be deleted and recreated from `001_v2_baseline`. The V1 `game.db`, `game.db-wal`, and `game.db-shm` remain outside the V2 ownership and rollback boundary.

## Next canonical stage

`21.5.5 — Optional legacy importer` requires a separate decision. Based on the accepted clean V2 strategy and disposable V1 test data, the expected decision is `NOT_REQUIRED`, but this reconciliation patch does not pre-close it.

## Manual verification

Not required. This patch is policy-only and changes no production code or database.
