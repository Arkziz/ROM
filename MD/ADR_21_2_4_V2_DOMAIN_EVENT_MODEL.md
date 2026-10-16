# ADR 21.2.4 — ROM V2 Domain event model

- **Status:** `ACCEPTED`
- **Canonical owner:** `rom_v2.domain.events`
- **Physical implementation:** reserved for Stage 21.3.1 or later

## Decision

Domain events are immutable, typed, stable-key records. Events contain domain facts, not Telegram presentation.

## Naming and payload

Event keys use lowercase dot-separated past-tense machine keys. Published keys are never renamed. Payloads are typed, immutable, schema-versioned and presentation-free.

## Ordering

Ordering is authoritative per aggregate stream by `aggregate_version` and transaction-local `sequence`. UTC occurrence time is metadata, not ordering authority. Consumers deduplicate by `event_id`.

## Persistence and delivery

Events are appended in the same Unit of Work as state changes. External publication occurs after commit through an outbox with at-least-once delivery. Consumers are idempotent. Restart reloads unpublished outbox records.

## Presentation separation

Application projections or app delivery adapters localize and format events. Telegram objects, markup and text do not enter domain event payloads.

## Result integration

Failed operations persist no events. Idempotent repeats emit no duplicate event. Retryable delivery keeps the outbox pending. Consistency errors block commit.

## Automated evidence

- Required fields: **11**.
- Violations: **0**.
- Physical event model exists: **False**.

## Next roadmap stage

Stage 21.2.5 — Repository/Unit of Work.
