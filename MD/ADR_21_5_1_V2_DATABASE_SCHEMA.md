# ADR 21.5.1 — Complete domain-oriented V2 database schema

## Status

`PROPOSED_FOR_EXPERT_ACCEPTANCE — canonical revision 21.5.1a`

## Database strategy

Create a new V2 database from a clean baseline migration. Do not migrate the disposable V1 test database. The V1 database remains an immutable behavioral reference only.

## Storage policies

- SQLite with foreign keys enabled by every connection.
- UTC ISO-8601 TEXT timestamps.
- Gold as integer minor units; crystals as integer units.
- Explicit type, nullability, default, generation owner, and checks for every column.
- Explicit `ON DELETE` and `ON UPDATE` actions for every foreign key.
- Append-only ledger, domain events, and migration history.
- Persistent operation records and outbox for exact-once settlement.

## Baseline scope

The 15 baseline tables cover account, character, stats, economy, inventory, equipment, story progress, exact-once operations, domain events, outbox, and migrations.

## Deferred domains

Travel, guild, direct trade, auction, PvP history, Premium, daily rewards, notifications, ratings/chronicles, events, and rune sockets remain explicitly deferred. No placeholder tables are created before each domain has an accepted persistence contract.

## Stage boundary

Stage 21.5.2 converts this accepted contract into migration `001_v2_baseline` and creates only an isolated `.runtime/v2/db` database.
