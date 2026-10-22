# Stage 21.8.8c - Battle persistence implementation

- Status: **PASS**
- Conclusion: **API_READY**
- Runtime integration: **NOT_CONNECTED**
- Production persistence: **NOT_CONNECTED**
- Manual game check: **NOT_REQUIRED**

## Implemented boundary

A pure immutable PvE encounter lifecycle API now supports begin, active-marker read, exactly-once terminal claim, deterministic stale selection, expiry-once, and restart expiry/cleanup.

This is intentionally not a full battle snapshot. It does not persist or resume turn state, cooldowns, effects, RNG position, PvP/boss aggregates, or simulator state. It has no SQLite, repository, UoW, Telegram, handler, or wall-clock dependency.

## Verification

Targeted unit tests cover absorbing terminal state, operation-id idempotency, conflicting terminal claims, expiry boundary, deterministic restart recovery, duplicate active-marker fail-closed behavior, timezone validation, and absence of full-snapshot fields. Canonical V2 CI and the dedicated smoke check pass.

## Manual check

Not required because no gameplay/runtime adapter is connected.
