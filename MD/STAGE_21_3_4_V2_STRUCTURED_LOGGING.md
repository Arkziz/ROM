# Stage 21.3.4 — ROM V2 structured logging

- **Status:** `IMPLEMENTED`
- **Canonical owner:** `rom_v2.structured_logging`
- **Format:** one JSON object per line

## Required diagnostic fields

`timestamp_utc`, `level`, `event`, `correlation_id`, `operation`, `error_category`, and structured `details`.

## Safety

Sensitive keys are recursively redacted. Unsupported objects are never stringified. Free-form exception payloads, tokens, passwords, authorization headers, cookies, API keys, and private keys are not logged.

## Stable identifiers

Event and operation identifiers are machine-readable keys without whitespace. Error categories are restricted to a closed canonical set.

## Next roadmap stage

Stage 21.3.5 — Architecture enforcement.
