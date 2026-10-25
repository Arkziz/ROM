# Stage 21.13.1b - Resolved Quest Engine parity

- Status: **PASS**
- Conclusion: **GO_TO_IMPLEMENTATION**
- Contract matrix: **4 previously confirmed + 6 resolved = 10/10**
- Remaining unresolved contracts: **0**
- Implementation authorized: **True**
- Engine content independence gate: **REQUIRED**
- Exact-once turn-in: **REQUIRED**
- Runtime integration authorized: **False**
- Production persistence authorized: **False**
- Production reward authorized: **False**
- Production quest-item consumption authorized: **False**
- Manual game check: **NOT_REQUIRED**

## Resolutions

### PREREQUISITE_AND_AVAILABILITY_POLICY

Availability is evaluated in this order: definition exists, persisted state is neither completed nor skipped, no conflicting active story quest exists, canonical location matches, player level meets the definition, and the previous quest is completed or skipped according to the chain policy. Overlevel reconciliation runs before normal availability materialization. Queries are read-only and repeated calls return the same stable machine reason until persisted inputs change.

### PROGRESS_AND_COMPLETION_STATE_MACHINE

Legal states are unavailable, available, active, ready_to_turn_in, completed and skipped. Accept is allowed only from available. TALK completes its objective through the canonical conversation event; KILL_REGION and BOSS consume matching exact-once event identities; QUEST_ITEM derives readiness from the isolated quest-item store; TURN_IN requires explicit submission. Progress is monotonic and clamped to target. Duplicate or stale events perform no second mutation. Restart reconstructs state exclusively from persisted quest and quest-item records.

### REWARD_AND_EXACT_ONCE_TURN_IN

One Unit of Work revalidates active quest, objective readiness and expected revision, consumes required quest items exactly once, grants definition-declared EXP, gold and item rewards, marks the quest completed, records the reward idempotency key, and exposes the next quest. The idempotency key is quest_id plus user_id plus completion revision. Failure before commit rolls back consumption, rewards and completion; retry after commit returns the persisted completed result without another grant.

### ENGINE_CONTENT_INDEPENDENCE

The engine consumes typed QuestDefinition data and objective strategy ports keyed only by objective type. Reusable domain/application code may not branch on concrete quest IDs, ranges, titles, NPC names, location display text or story prose. Quest-specific targets, rewards, prerequisites and presentation metadata remain in data definitions. Stage 21.13.1c must include an executable gate that fails on concrete quest-ID literals or content strings in the reusable engine and application modules.

### OVERLEVEL_AND_SKIP_INTERACTION

Automatic overlevel reconciliation runs before normal availability evaluation and may mark eligible unstarted chain entries skipped according to the existing V1 policy. Explicit active SKIP is a separate idempotent command restricted to the canonical eligible active quest/location. Neither path grants EXP, gold or items and neither consumes quest items. Skipped quests satisfy the chain predecessor requirement and appear as skipped in the journal. Completed quests are never converted to skipped; repeated reconciliation or SKIP performs no second mutation.

### PRESENTATION_AND_HANDLER_BOUNDARY

One Quest Engine application service owns availability, accept, progress events, turn-in, overlevel reconciliation, SKIP and journal queries through typed commands/results. Commands carry stable quest_id, objective/event key and expected revision. Handlers own callback parsing, keyboards and Ukrainian text, and register one canonical route. Handlers may not calculate rewards or progress, consume quest items, branch on concrete quest IDs, or mutate persistence directly.

## Implementation boundary

Stage 21.13.1c may implement pure Quest Engine DTOs, generic policies, state machines, in-memory Unit of Work, tests, smoke verification and a content-independence gate. It may not connect SQLite, Telegram, runtime rewards or real quest-item consumption.

## Next patch

`patch_21_13_1c_implement_quest_engine.py`
