# Stage 21.9.6b - Resolved post-combat hooks parity

- Status: **PASS**
- Conclusion: **GO_TO_IMPLEMENTATION**
- Remaining unresolved contracts: **0**
- Implementation authorized: **True**
- Runtime integration authorized: **False**
- Production persistence authorized: **False**
- Manual game check: **NOT_REQUIRED**

## Resolved contracts

- `VICTORY_DURABILITY_DUPLICATE_DEFINITIONS`: **LAST_DEFINITION_RUNTIME_BINDING_PRESERVED_AS_COMPATIBILITY** - Python binds the last V1 definition at runtime; V2 records one durability consumer key and does not copy duplicate definitions.
- `AUTHORITATIVE_V2_POST_COMBAT_OWNER`: **POST_COMBAT_HOOK_COORDINATOR** - A single application-level PostCombatHookCoordinator plans deterministic consumers from one immutable event.
- `IMMUTABLE_POST_COMBAT_EVENT_PAYLOAD`: **FROZEN_SETTLED_VICTORY_EVENT** - The event carries stable operation key, battle and actor IDs, enemy snapshot, location, terminal outcome, finalized settlement summary and committed status; no repositories or presentation text.
- `STABLE_EVENT_AND_OPERATION_KEY`: **REUSE_SETTLEMENT_OPERATION_KEY** - The settled reward operation key is the canonical event key and consumer idempotency prefix; no derived text keys.
- `SETTLEMENT_BEFORE_HOOK_ORDER`: **SETTLEMENT_COMMIT_PRECEDES_DISPATCH** - Durable reward settlement completes successfully before post-combat dispatch; consumers cannot mutate settlement outputs.
- `VICTORY_TERMINAL_SCOPE`: **SETTLED_VICTORY_ONLY** - Stage 21.9.6 dispatches only committed victory events; defeat and escape remain terminal-path concerns outside this hook set.
- `NORMAL_ELITE_BOSS_SCOPE`: **COMMON_EVENT_WITH_ENEMY_CLASS** - Normal, elite and boss victories share one event shape and expose enemy_class for consumer eligibility.
- `STORY_HOOK_ORDER_AND_IDEMPOTENCY`: **STORY_KILL_THEN_BOSS_THEN_ITEM** - Story consumers are ordered region-kill, boss completion, then quest-item drop; each uses event-key plus consumer-key exact-once identity.
- `QUEST_AND_CONTRACT_HOOK_ORDER`: **DAILY_QUEST_THEN_GUILD_CONTRACT** - Daily quest progress precedes guild contract progress and both are exact-once consumers of the settled event.
- `HISTORY_CHRONICLE_ACHIEVEMENT_SCOPE`: **OPTIONAL_REGISTERED_CONSUMERS_ONLY** - History, chronicles and achievements run only when an explicit consumer port is registered; absent V1 ownership is not invented.
- `EVENT_AND_DURABILITY_HOOK_ORDER`: **EVENT_STATISTICS_THEN_DURABILITY** - Event statistics precede durability wear; durability is represented by one consumer despite duplicate V1 definitions.
- `FAILURE_ROLLBACK_AND_PARTIAL_SUCCESS_POLICY`: **DURABLE_CONSUMERS_FAIL_CLOSED_BEFORE_COMMIT** - A coordinator Unit of Work commits all durable consumer marks and mutations once; any durable failure rolls back the hook transaction without touching the already-committed reward settlement.
- `POST_COMMIT_NOTIFICATION_POLICY`: **NOTIFICATIONS_AFTER_DURABLE_HOOK_COMMIT_FAIL_OPEN** - Presentation and notifications run only after durable hooks commit, never mutate gameplay state, and failures are reported without replaying settlement.
- `RETRY_RESTART_AND_PENDING_DELIVERY`: **CONSUMER_LEDGER_EXACT_ONCE_RETRY** - Retry uses event key plus consumer key; completed consumers are skipped, uncompleted consumers may retry, and settlement is never retried by this coordinator.
- `NO_DUPLICATE_REWARD_SETTLEMENT`: **EVENT_CONTAINS_SUMMARY_NOT_REWARD_COMMANDS** - Post-combat payload exposes finalized reward summaries only and contains no EXP, gold, loot or quest-reward mutation commands.
- `SIMULATOR_DEV_AND_SHADOW_OWNER_CLASSIFICATION`: **SIMULATOR_FIXTURE_CONSUMER_DEV_NO_ALTERNATE_OWNER** - Simulator may consume the same event contract for fixtures; DEV and compatibility paths cannot become alternate production dispatch owners.

## V2 post-combat contract

- Coordinator: `PostCombatHookCoordinator`
- Event: `SettledVictoryEvent`
- Scope: `settled_victory_only`
- Stable key source: `reward_settlement_operation_key`
- Reward mutation: `False`
- Consumer idempotency: `True`
- Single hook commit: `True`
- Durable order: `story_region_kill, story_boss_completion, story_item_drop, daily_quest, guild_contract, event_statistics, durability`

## Implementation boundary

Allowed:
- immutable event and result DTOs
- consumer and Unit-of-Work ports
- deterministic coordinator ordering
- exact-once consumer ledger semantics
- unit and integration fixtures with in-memory fakes

Forbidden:
- SQLite or production consumer adapters
- runtime or Telegram wiring
- changes to V1 duplicate durability definitions
- reward settlement replay or mutation
- invented history, chronicle or achievement behavior

## Safety

V1 was inspected only as source text and AST. SQLite was not opened. `game.db-wal` and `game.db-shm` were not deleted, cleared, modified, or used for rollback.

## Next patch

`patch_21_9_6c_implement_post_combat_hooks.py`
