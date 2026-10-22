# Stage 21.9.6a - Refined post-combat hooks contract

- Status: **PASS**
- Conclusion: **REVIEW_REQUIRED**
- V1-confirmed rows: **8**
- Review-required rows: **16**
- Production changed: **False**
- Database opened: **False**
- Manual game check: **NOT_REQUIRED**

## Authoritative context owners

- `victory_orchestration`: `handlers/combat.py`
- `reward_settlement`: `systems/reward_system.py`
- `story_region_kill`: `systems/story_quest_combat_progress_system.py`
- `story_boss_completion`: `systems/story_quest_boss_completion_system.py`
- `story_item_drop`: `systems/story_quest_item_drop_system.py`
- `guild_contracts`: `systems/contract_system.py`
- `daily_quests`: `db_modules/quests.py`
- `event_statistics`: `systems/event_statistics_system.py`
- `victory_durability`: `systems/equipment_system.py`

## Contract matrix

- `VICTORY_ORCHESTRATION_OWNER`: **V1_CONFIRMED** - V1 combat handler orchestrates the victory terminal path and its downstream hooks.
- `REWARD_SETTLEMENT_BOUNDARY`: **V1_CONFIRMED** - Reward mutation has a distinct V1 boundary that hooks must not duplicate.
- `STORY_REGION_KILL_OWNER`: **V1_CONFIRMED** - Region-kill story progression has a dedicated V1 owner.
- `STORY_BOSS_COMPLETION_OWNER`: **V1_CONFIRMED** - RNG boss story completion has a dedicated V1 owner.
- `STORY_ITEM_DROP_OWNER`: **V1_CONFIRMED** - Story quest item drops remain a separate V1 post-combat boundary.
- `GUILD_CONTRACT_PROGRESS_OWNER`: **V1_CONFIRMED** - Guild contract kill progress has a dedicated V1 owner.
- `DAILY_QUEST_PROGRESS_OWNER`: **V1_CONFIRMED** - Daily quest kill progress has a dedicated V1 owner.
- `EVENT_STATISTICS_OWNER`: **V1_CONFIRMED** - Event mob-victory statistics have a dedicated V1 owner.
- `VICTORY_DURABILITY_DUPLICATE_DEFINITIONS`: **REVIEW_REQUIRED** - V1 contains two same-name durability definitions; authoritative runtime binding and compatibility intent require parity resolution.
- `AUTHORITATIVE_V2_POST_COMBAT_OWNER`: **REVIEW_REQUIRED** - The exact V2 application owner and event dispatch boundary require resolution.
- `IMMUTABLE_POST_COMBAT_EVENT_PAYLOAD`: **REVIEW_REQUIRED** - Stable fields for battle, actor, enemy, location, settlement and terminal outcome require proof.
- `STABLE_EVENT_AND_OPERATION_KEY`: **REVIEW_REQUIRED** - The canonical key for exact-once consumer handling and restart safety requires resolution.
- `SETTLEMENT_BEFORE_HOOK_ORDER`: **REVIEW_REQUIRED** - The precise order between durable settlement and every post-combat mutation requires proof.
- `VICTORY_TERMINAL_SCOPE`: **REVIEW_REQUIRED** - Victory, defeat, escape, auto-escape and recovered terminal paths require explicit scope classification.
- `NORMAL_ELITE_BOSS_SCOPE`: **REVIEW_REQUIRED** - Normal, elite and boss consumer differences require a source-backed matrix.
- `STORY_HOOK_ORDER_AND_IDEMPOTENCY`: **REVIEW_REQUIRED** - Story kill, boss completion and item-drop order plus duplicate behavior require resolution.
- `QUEST_AND_CONTRACT_HOOK_ORDER`: **REVIEW_REQUIRED** - Daily quest and guild contract ordering, eligibility and exact-once behavior require resolution.
- `HISTORY_CHRONICLE_ACHIEVEMENT_SCOPE`: **REVIEW_REQUIRED** - Battle history, reward history, chronicles and achievements require authoritative or absent classification.
- `EVENT_AND_DURABILITY_HOOK_ORDER`: **REVIEW_REQUIRED** - Event statistics and durability wear ordering and failure behavior require proof.
- `FAILURE_ROLLBACK_AND_PARTIAL_SUCCESS_POLICY`: **REVIEW_REQUIRED** - Durable hooks need explicit fail-closed/rollback policy; optional hooks need explicit isolation policy.
- `POST_COMMIT_NOTIFICATION_POLICY`: **REVIEW_REQUIRED** - Notifications and presentation must occur after durable outcome and must not own mutations.
- `RETRY_RESTART_AND_PENDING_DELIVERY`: **REVIEW_REQUIRED** - Retry, restart and pending consumer semantics require a source-backed contract.
- `NO_DUPLICATE_REWARD_SETTLEMENT`: **REVIEW_REQUIRED** - Post-combat consumers must never re-award EXP, combat gold, level-up gold, loot or quest rewards.
- `SIMULATOR_DEV_AND_SHADOW_OWNER_CLASSIFICATION`: **REVIEW_REQUIRED** - Simulator, DEV, compatibility wrappers and shadow hook owners require classification.

## Unresolved contracts

- `VICTORY_DURABILITY_DUPLICATE_DEFINITIONS`
- `AUTHORITATIVE_V2_POST_COMBAT_OWNER`
- `IMMUTABLE_POST_COMBAT_EVENT_PAYLOAD`
- `STABLE_EVENT_AND_OPERATION_KEY`
- `SETTLEMENT_BEFORE_HOOK_ORDER`
- `VICTORY_TERMINAL_SCOPE`
- `NORMAL_ELITE_BOSS_SCOPE`
- `STORY_HOOK_ORDER_AND_IDEMPOTENCY`
- `QUEST_AND_CONTRACT_HOOK_ORDER`
- `HISTORY_CHRONICLE_ACHIEVEMENT_SCOPE`
- `EVENT_AND_DURABILITY_HOOK_ORDER`
- `FAILURE_ROLLBACK_AND_PARTIAL_SUCCESS_POLICY`
- `POST_COMMIT_NOTIFICATION_POLICY`
- `RETRY_RESTART_AND_PENDING_DELIVERY`
- `NO_DUPLICATE_REWARD_SETTLEMENT`
- `SIMULATOR_DEV_AND_SHADOW_OWNER_CLASSIFICATION`

Implementation remains unauthorized until authoritative event ownership, immutable payload, stable keys, settlement order, terminal and enemy scope, consumer ordering, exact-once behavior, failure/rollback, notifications, retry/restart, no-duplicate-settlement and shadow paths are resolved from V1 evidence.
