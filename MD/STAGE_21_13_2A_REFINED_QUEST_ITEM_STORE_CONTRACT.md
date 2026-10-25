# Stage 21.13.2a - Refined Quest Item Store contract

- Status: **PASS**
- Conclusion: **REVIEW_REQUIRED**
- Contract matrix: **3 confirmed / 5 review-required / 8 total**
- No regular inventory leakage: **CONFIRMED BOUNDARY**
- Direct engine consume call: **NOT FOUND; REQUIRES RESOLUTION**
- Implementation authorized: **False**
- Manual game check: **NOT_REQUIRED**

## Refined unresolved contracts

### QUEST_ITEM_IDENTITY_AND_SCOPE

Confirmed:

- quest items are stored by the story quest persistence owner
- objective definitions identify QUEST_ITEM requirements
- collection is associated with the active quest path
- regular inventory handlers do not own add or consume operations

Remaining question: Resolve the exact canonical key: user, quest, item type and optional source/objective identity; determine whether identical item keys may be shared across quests and how total quantity differs from per-quest quantity.

### EXACT_QUANTITY_AND_NON_NEGATIVE_INVARIANT

Confirmed:

- per-quest and total quantity queries exist
- add and consume primitives are separate operations
- quantity belongs to isolated persistent storage
- normal inventory capacity is not part of the store API

Remaining question: Resolve integer validation, zero handling, upper bounds if any, insufficient-consume result, non-negative enforcement, row deletion at zero and transaction/concurrency semantics for simultaneous add/consume.

### COLLECTION_IDEMPOTENCY_AND_EVENT_IDENTITY

Confirmed:

- Quest Engine owns collect_active_quest_item
- collection delegates to add_story_quest_item
- active quest context is available to the engine
- handlers do not mutate the store directly

Remaining question: Resolve the exact collection event identity, drop/source matching, duplicate delivery behavior, chance evaluation boundary, target clamping versus surplus retention and retry after commit.

### TURN_IN_CONSUMPTION_ATOMICITY

Confirmed:

- consume_story_quest_item_quantity exists as the canonical primitive
- direct consume call is not present in story_quest_system
- Quest Engine exact-once turn-in contract requires atomic consumption
- completed quest state persists across restart

Remaining question: Locate the actual V1 caller and authoritative Unit of Work for readiness recheck, exact quantity consumption, reward grant and completion; resolve rollback-before-commit, retry-after-commit and delegated completion boundaries without inventing a new caller.

### OVERLEVEL_SKIP_AND_CLEANUP

Confirmed:

- overlevel reconciliation and explicit SKIP exist
- SKIP is separate from normal completion
- quest items remain isolated from ordinary inventory
- completed and skipped states persist

Remaining question: Resolve whether automatic reconciliation or explicit SKIP deletes, preserves or ignores accumulated quest items; define quest-chain scoping, orphan cleanup timing, idempotency and the guarantee that SKIP never consumes items or grants rewards.

No production mutation, quantity change, turn-in consumption, database access or runtime wiring is authorized.

## Next patch

`patch_21_13_2b_resolve_quest_item_store_parity.py`
