# Stage 21.16.1a - Playable-slice architecture contract

## Decision

A ROM V2 capability is playable only when the complete path is implemented and registered:

`Telegram update -> V2 handler -> application service -> Unit of Work -> V2 repository -> V2 persistence -> typed result -> presenter -> Telegram response`.

## Mandatory rules

1. V1 is read-only audit/reference material. V2 production runtime must not import, call, register, share mutable state with, or fall back to V1 or future `legacy/v1`.
2. Changes edit the authoritative V2 owner directly. Overlay modules, monkey patches, runtime rebinding, shadow owners and import-order behavior are forbidden.
3. Presenter-only, handler-only, API-only and contract-only work is not `READY_FOR_UI`.
4. A persistence exemption is explicit and limited to a genuinely static/read-only flow.
5. Handlers parse and authorize input, construct a typed command/query, call one application boundary, and render a typed result. They contain no SQL or gameplay formulas.
6. Every mutation uses one Unit of Work. Repositories do not commit or rollback.
7. Runtime readiness requires composition-root registration and targeted tests, not merely importable classes.

## Acceptance effect

Stage 21.16.1a refines and enforces the architecture contract. It does not connect Telegram, open SQLite, or make the game manually playable. The next stage may close foundational runtime gaps under this contract.

## Manual game check

`NOT_REQUIRED`
