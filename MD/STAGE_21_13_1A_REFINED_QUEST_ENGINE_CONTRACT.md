# Stage 21.13.1a - Refined Quest Engine contract

- Status: **PASS**
- Conclusion: **REVIEW_REQUIRED**
- Contract matrix: **4 confirmed / 6 review-required / 10 total**
- Implementation authorized: **False**
- Manual game check: **NOT_REQUIRED**

## Refined unresolved contracts

### PREREQUISITE_AND_AVAILABILITY_POLICY

Confirmed:

- definitions carry stable IDs, location, order and requirement metadata
- availability is derived from player level, previous quest and current persisted state
- only one active story quest is materialized for the canonical chain
- registry lookup is separate from Telegram presentation

Remaining question: Resolve the exact order of level, location, previous-quest, active-quest, completed/skipped and overlevel checks, including machine-readable rejection reasons and repeated availability queries.

### PROGRESS_AND_COMPLETION_STATE_MACHINE

Confirmed:

- accept creates the persisted active state
- TALK, KILL_REGION, QUEST_ITEM, TURN_IN and BOSS use objective-specific progress paths
- progress is clamped and compared with the definition target
- journal materialization combines definitions with persisted state

Remaining question: Resolve legal state transitions, objective-specific completion triggers, duplicate event handling, progress monotonicity, BOSS exact-once evidence and behavior after restart or stale callbacks.

### REWARD_AND_EXACT_ONCE_TURN_IN

Confirmed:

- reward metadata belongs to the quest definition
- completion and reward operate against persisted quest identity
- TURN_IN and quest-item consumption have explicit paths
- completed state survives restart

Remaining question: Resolve the authoritative transaction boundary for validation, quest-item consumption, EXP/gold/item reward, completion status and next-quest availability, including retry after commit and rollback before commit.

### ENGINE_CONTENT_INDEPENDENCE

Confirmed:

- engine builds a registry from definition data
- objective dispatch is driven by objective type
- quest content is supplied by data/story_quest_definitions.py
- handler calls engine APIs instead of embedding chain mutation

Remaining question: Resolve the typed definition schema, objective strategy/validator boundary, prohibited quest-ID branches in engine/application code and an executable gate proving the engine does not depend on particular quest IDs, titles, NPC names or location prose.

### OVERLEVEL_AND_SKIP_INTERACTION

Confirmed:

- overlevel reconciliation and active-quest skip are distinct operations
- persisted skipped states are represented in the journal
- SKIP operates by canonical location/quest chain
- normal completion paths remain separate from skip paths

Remaining question: Resolve exact eligibility and ordering for automatic reconciliation versus explicit active SKIP, whether rewards and quest items are ever granted or consumed, next-quest availability, idempotent replay and interaction with completed/failed states.

### PRESENTATION_AND_HANDLER_BOUNDARY

Confirmed:

- story_quests handler consumes story_quest_system
- engine returns materialized quest views and journal data
- technical objective/state keys exist independently from localized text
- persistence owner is isolated from Telegram

Remaining question: Resolve typed commands/results, callback stable keys and expected revision tokens, localization ownership, one handler registration path and prohibition of reward/progress calculations or quest-ID branching in handlers.

No production mutation, reward grant, quest-item consumption, database access or runtime wiring is authorized.

## Next patch

`patch_21_13_1b_resolve_quest_engine_parity.py`
