# Stage 21.13.2b - Resolved Quest Item Store parity

- Status: **PASS**
- Conclusion: **GO_TO_IMPLEMENTATION**
- Contract matrix: **8/8 RESOLVED**
- No regular inventory leakage: **REQUIRED**
- Production quantity mutation: **NOT_AUTHORIZED**
- Production turn-in: **NOT_AUTHORIZED**
- Runtime integration: **NOT_AUTHORIZED**
- Production persistence: **NOT_AUTHORIZED**
- Manual game check: **NOT_REQUIRED**

## Resolved contracts

### QUEST_ITEM_IDENTITY_AND_SCOPE

The canonical store key is scoped by user_id, quest_id and item_key. A per-quest query reads only that key; total quantity is an explicit aggregate across quest scopes and never changes ownership. Identical item keys in different quests remain distinct persisted balances. Source/objective metadata may validate collection but is not a second balance owner.

Typed reasons: invalid_identity, quest_not_active, item_not_required

### EXACT_QUANTITY_AND_NON_NEGATIVE_INVARIANT

Quantities are non-negative integers. Add requires a positive integer. Consume requires a positive integer and succeeds only when the scoped balance is sufficient. Insufficient quantity returns a typed result without mutation. Zero balances are observationally equivalent to an absent row and may be deleted atomically. Concurrent add/consume is serialized by one Unit of Work with conditional quantity update.

Typed reasons: invalid_quantity, insufficient_quantity, stale_revision

### COLLECTION_IDEMPOTENCY_AND_EVENT_IDENTITY

Collection identity is user_id + quest_id + event_id. The engine validates the active QUEST_ITEM objective, source/item match and event identity before mutation. Chance evaluation belongs to the upstream drop/event producer and is not repeated by the store. A committed event replay returns already_collected without adding again. Stored quantity may exceed the current target only when V1 producer semantics explicitly deliver surplus; readiness remains clamped to the objective target.

Typed reasons: duplicate_event, objective_mismatch, source_mismatch

### TURN_IN_CONSUMPTION_ATOMICITY

Quest Item Store exposes the canonical consume primitive, while Quest Engine turn-in service owns orchestration. Stage 21.13.2 does not invent a second V1 caller. The V2 Unit of Work must recheck readiness and revision, conditionally consume the exact scoped quantity, grant rewards, persist completion and record the completion idempotency key in one atomic commit. Failure before commit rolls all parts back; retry after commit returns the persisted completed result without another consume or reward.

Typed reasons: quest_not_ready, insufficient_quantity, stale_revision, already_completed

### OVERLEVEL_SKIP_AND_CLEANUP

Automatic overlevel reconciliation and explicit SKIP never consume quest items, never grant rewards and never move quest items into regular inventory. Existing scoped balances are preserved as inert persisted evidence until a separately authorized cleanup policy exists. Completed quest turn-in may consume only its own scoped requirement. Repeated reconciliation or SKIP is idempotent and never deletes unrelated quest balances.

Typed reasons: already_skipped, already_completed, cleanup_not_authorized

## Next patch

`patch_21_13_2c_implement_quest_item_store.py`
