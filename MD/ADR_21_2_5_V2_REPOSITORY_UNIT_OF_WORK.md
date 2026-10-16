# ADR 21.2.5 — ROM V2 Repository and Unit of Work

- **Status:** `ACCEPTED`
- **Repository ports owner:** `rom_v2.application.ports.repositories`
- **Unit of Work port owner:** `rom_v2.application.ports.unit_of_work`

## Decision

Repositories are aggregate-oriented application ports, return domain objects and never own transactions. One explicit Unit of Work owns all repositories, state changes, domain events and outbox records for one business operation.

## Atomicity

All preconditions precede mutation. There is one transaction and one commit point. Every non-success Result or exception rolls back. Nested UoW and implicit autocommit are forbidden.

## Optimistic concurrency

Updates require expected version compare-and-swap. Zero rows updated maps to `stale_state`; retry reloads and fully revalidates.

## Exact-once settlement

A persistent unique operation ID is claimed in the same transaction as mutation. Completed duplicates return `idempotent_repeat` without another mutation or event. In-progress duplicates return `retryable_error`.

## Automated evidence

- Physical V2 exists: **False**.
- Application DB imports: **0**.
- Repository transaction methods: **0**.
- Violations: **0**.

## Next roadmap stage

Stage 21.2.6 — Clock and RNG abstractions.
