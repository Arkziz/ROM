# Stage 21.9.3a - Refined reward settlement contract

- Status: **PASS**
- Conclusion: **REVIEW_REQUIRED**
- V1-confirmed rows: **8**
- Review-required rows: **12**
- Production changed: **False**
- Database opened: **False**
- Manual game check: **NOT_REQUIRED**

## Authoritative context owners

- `combat_orchestration`: `handlers/combat.py`
- `combat_rewards`: `systems/reward_system.py`
- `exp_transaction`: `systems/player_system.py`
- `level_up_rewards`: `systems/level_up_reward_system.py`
- `story_rewards`: `systems/story_quest_reward_system.py`
- `terminal_claim`: `systems/pve_auto_escape_system.py`

## Contract matrix

- `COMBAT_SETTLEMENT_ENTRYPOINT`: **V1_CONFIRMED** - Combat victory handler is the orchestration entrypoint but is not yet proven to be one atomic settlement owner.
- `COMBAT_REWARD_OWNER`: **V1_CONFIRMED** - Combat gold and drop reward processing is owned by the reward system.
- `EXP_TRANSACTION_OWNER`: **V1_CONFIRMED** - EXP, reached levels and level-up side effects have a caller-owned transaction path.
- `EXP_PUBLIC_TRANSACTION_BOUNDARY`: **V1_CONFIRMED** - Public EXP entrypoint owns an outer commit/rollback boundary.
- `LEVEL_UP_REWARD_SETTLEMENT`: **V1_CONFIRMED** - Level-up reward settlement is separated from calculation and presentation.
- `LEVEL_UP_PENDING_ITEMS`: **V1_CONFIRMED** - Persistent pending-item retry exists for level-up item rewards.
- `STORY_REWARD_ADAPTER`: **V1_CONFIRMED** - Story quest rewards expose a separate adapter boundary.
- `TERMINAL_CLAIM_OWNER`: **V1_CONFIRMED** - PvE terminal claim is the known exactly-once terminal guard.
- `CANONICAL_SETTLEMENT_IDENTITY`: **REVIEW_REQUIRED** - The identity linking terminal claim, battle, reward application and duplicate callbacks requires exact resolution.
- `SINGLE_UNIT_OF_WORK_OWNER`: **REVIEW_REQUIRED** - No single owner for EXP, combat gold, loot, level-up rewards, quest progress and history is yet proven.
- `MUTATION_ORDER`: **REVIEW_REQUIRED** - Exact mutation order and which steps occur before or after terminal claim require source-level resolution.
- `COMBAT_GOLD_PREMIUM_SCOPE`: **REVIEW_REQUIRED** - Premium must be bounded to explicit combat-gold paths and excluded from level-up, quest and other gold.
- `LOOT_ATOMICITY_AND_CAPACITY`: **REVIEW_REQUIRED** - Combat loot capacity, partial insertion, pending behavior and rollback coupling require exact resolution.
- `QUEST_PROGRESS_ORDER`: **REVIEW_REQUIRED** - Combat/story/contract progress owners and ordering relative to rewards require refinement.
- `REWARD_HISTORY_OWNER`: **REVIEW_REQUIRED** - The canonical durable history/chronicle owner and payload require resolution.
- `DUPLICATE_CALLBACK_POLICY`: **REVIEW_REQUIRED** - Behavior for a repeated victory/terminal callback must be proven from V1 guards and constraints.
- `PARTIAL_FAILURE_ROLLBACK`: **REVIEW_REQUIRED** - Rollback coverage for every reward mutation and external side effect requires exact resolution.
- `PVE_PVP_BOSS_SCOPE`: **REVIEW_REQUIRED** - Whether PvE, boss and PvP share settlement semantics or remain distinct requires classification.
- `PRESENTATION_AFTER_COMMIT`: **REVIEW_REQUIRED** - Message construction and delivery must be separated from business mutation and ordered after durable outcome.
- `LEGACY_BYPASS_PATHS`: **REVIEW_REQUIRED** - Legacy public mutation entrypoints that bypass a future application service require a bounded inventory.

## Unresolved contracts

- `CANONICAL_SETTLEMENT_IDENTITY`
- `SINGLE_UNIT_OF_WORK_OWNER`
- `MUTATION_ORDER`
- `COMBAT_GOLD_PREMIUM_SCOPE`
- `LOOT_ATOMICITY_AND_CAPACITY`
- `QUEST_PROGRESS_ORDER`
- `REWARD_HISTORY_OWNER`
- `DUPLICATE_CALLBACK_POLICY`
- `PARTIAL_FAILURE_ROLLBACK`
- `PVE_PVP_BOSS_SCOPE`
- `PRESENTATION_AFTER_COMMIT`
- `LEGACY_BYPASS_PATHS`

Implementation remains unauthorized until settlement identity, one Unit of Work, mutation order, Premium scope, loot capacity, quest/history ordering, duplicate callbacks, rollback, mode scope, post-commit presentation and bypass paths are resolved from V1 evidence.
