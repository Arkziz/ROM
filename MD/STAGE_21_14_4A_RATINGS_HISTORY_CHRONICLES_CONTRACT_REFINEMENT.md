# Stage 21.14.4a — Ratings/history/chronicles contract refinement

- Status: **PASS**
- Decision: **GO_TO_PARITY_RESOLUTION**
- Production mutation: **NO**
- Runtime/Telegram/persistence wiring: **NOT CONNECTED**
- Manual in-game verification: **NOT REQUIRED**
- `game.db-wal` / `game.db-shm`: **NOT MANIPULATED**

## Refined semantic areas

### ratings
- Status: **REFINED_REQUIRES_PARITY_RESOLUTION**
- Evidence entries: 198286
- Contract: A rating category needs an authoritative query/owner, deterministic ordering, stable tie-break rules, top-list boundary, page size, and own-position semantics before implementation.

### history
- Status: **REFINED_REQUIRES_PARITY_RESOLUTION**
- Evidence entries: 1979
- Contract: Each history type must define accepted terminal records, account/character scope, newest-first ordering, stable identity, retention, and exclusion of pending or non-result events.

### chronicles
- Status: **REFINED_REQUIRES_PARITY_RESOLUTION**
- Evidence entries: 536
- Contract: Chronicles require an authoritative event taxonomy, owner scope, persistent identity, deterministic newest-first ordering including equal timestamps, retention boundary, page size, and read-only presentation mapping.

### presentation_boundary
- Status: **REFINED**
- Evidence entries: 2106
- Contract: Buttons, callback payloads, localized labels and render formatting are presentation concerns and must not be promoted into domain ordering, retention or identity policy.

### persistence_boundary
- Status: **REFINED**
- Evidence entries: 6084
- Contract: Stage 21.14.4a does not authorize migrations, repositories, runtime wiring, Telegram handlers, cleanup jobs or background retention workers.

## Unresolved questions for Stage 21.14.4b

- Exact canonical rating categories and their authoritative owners.
- Exact top-list boundary, page size and own-position behavior per category.
- Stable tie-break fields when primary rating values are equal.
- Exact accepted trade/PvP history terminal states and account/character scope.
- Chronicles event taxonomy, scope, identity and equal-timestamp ordering.
- Retention count and any minimum time-retention rule for every history family.
- Whether retention is write-time bounded, query-time limited, or maintained by an existing cleanup owner.

## Explicit prohibitions

- Do not invent rating categories, limits, page sizes or tie-breakers.
- Do not merge trade history, PvP history and Chronicles into one semantic type without V1 evidence.
- Do not invent Chronicle event types, retention jobs or cleanup schedules.
- Do not connect runtime, Telegram or production persistence in refinement/parity stages.
- Do not manipulate game.db-wal or game.db-shm.

## Numeric evidence policy

Numbers discovered in the audit are recorded as candidates only. Stage 21.14.4b must verify each value against an authoritative V1 source owner before it can become canonical parity policy.
