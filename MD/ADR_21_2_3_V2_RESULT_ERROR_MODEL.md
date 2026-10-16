# ADR 21.2.3 — ROM V2 Result and error model

- **Status:** `ACCEPTED`
- **Canonical owner:** `rom_v2.application.result`
- **Physical implementation:** reserved for Stage 21.3.1 or later

## Decision

All application operations return one typed `Result[T]`. Expected business outcomes are data, not presentation strings or uncontrolled exceptions.

## Statuses

- `success`
- `business_rejection`
- `validation_error`
- `stale_state`
- `idempotent_repeat`
- `retryable_error`
- `consistency_error`

## Atomicity and idempotency

All mutation belongs to an application service with an explicit Unit of Work. Preconditions are checked before the first mutation. Non-success paths roll back. `idempotent_repeat` returns the prior outcome without mutation.

## Presentation separation

Stable keys and structured details cross the application boundary. Localization and Telegram formatting belong to delivery adapters.

## Automated evidence

- Status count: **7**.
- Violations: **0**.
- Physical Result model exists: **False**.

## Next roadmap stage

Stage 21.2.4 — Domain event model.
