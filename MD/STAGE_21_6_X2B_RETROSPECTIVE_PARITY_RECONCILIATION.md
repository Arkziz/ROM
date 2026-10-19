# Stage 21.6.X2b — Retrospective parity reconciliation

## Decision

The two blocking findings from Stage 21.6.X2a are reconciled without inventing V1 gameplay rules and without rewriting migration 001.

## Provisional persistence

`item_instances`, `equipment_slots`, `item_reservations`, `quest_progress`, and `quest_item_balances` remain physically present but are explicitly classified as `PROVISIONAL_RESERVED`. Production adapters are guarded against using these contracts before the matching V1 audit and forward migration.

## Snapshot integration evidence

The shared full-stat snapshot is classified as `API_READY`. Profile, combat, and simulator adapter wiring, runtime dispatch, and end-to-end acceptance remain deferred.

## Production impact

No gameplay formula, schema migration, database row, V1 source, or class/resource/equipment compatibility rule is changed.

## Acceptance

After focused regression and the canonical six-gate CI pass, the retrospective audit chain may be closed and Stage 21.7 may proceed with its own mandatory read-only V1 audit.

## Manual game check

`NOT_REQUIRED`. This reconciliation changes governance guards and documentation only; no gameplay dispatch exists for the affected future domains.
