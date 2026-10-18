# ADR 21.5.1 — Complete domain-oriented V2 database schema

## Status

`PROPOSED_FOR_EXPERT_ACCEPTANCE — canonical revision 21.5.1b`

## Strategy

Create a new reset-first V2 SQLite database from migration `001_v2_baseline`. Do not migrate the disposable V1 test database or copy the V1 migration chain.

## Strengthened lifecycle invariants

- Quest `completed_at_utc` is present if and only if `state_key = completed`.
- Operation `completed_at_utc` is present if and only if `status_key = completed`.
- Crystal ledger entries reference persistent `operation_records` with `ON DELETE RESTRICT`.
- Item reservations reference persistent `operation_records` with `ON DELETE CASCADE`.
- Both exact-once links use `ON UPDATE CASCADE`.

## Existing accepted policies

All 91 columns retain explicit type, nullability, default, generation owner, and checks. All foreign keys retain explicit lifecycle actions. Money uses integer units and timestamps use UTC ISO-8601 text. Eleven future domains remain deferred without placeholder tables.

## Stage boundary

Stage 21.5.2 may generate SQL only after expert acceptance of revision 21.5.1b.
