# ADR 21.5.1 — Domain-oriented V2 database schema

## Status

`PROPOSED_FOR_EXPERT_ACCEPTANCE`

## Decision

ROM V2 uses a clean, reset-first SQLite schema. Historical V1 migrations are not copied. The schema is organized by aggregate ownership, with explicit foreign keys, unique constraints, optimistic versions, exact-once operation records, append-only domain events, and an outbox. Money is stored as integer minor units; timestamps are UTC ISO-8601 text.

## ER inventory

- Account: `accounts`, `crystal_wallets`, `crystal_ledger`.
- Character/stats: `characters`, `character_primary_stats`, `gold_wallets`.
- Inventory/equipment: `item_instances`, `equipment_slots`, `item_reservations`.
- Story: `quest_progress`, `quest_item_balances`.
- Cross-cutting atomicity: `operation_records`, `domain_events`, `outbox_messages`.
- Infrastructure: `schema_migrations`.

## Invariants

- Foreign keys are enabled for every V2 connection.
- SQL remains inside infrastructure persistence adapters.
- Account and character ownership are separate.
- Ledger and event histories are append-only.
- `operation_id` is the exact-once key.
- No schema choice is constrained by preserving the V1 test database.
- DDL creation belongs to Stage 21.5.2.

## Expert acceptance

Review normalization, table ownership, constraints, indexes, UTC/money policies, and whether the ER inventory is sufficient for future domain stages.
