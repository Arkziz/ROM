# Stage 21.9.3b - Resolved reward settlement parity

- Status: **PASS**
- Conclusion: **GO_TO_IMPLEMENTATION**
- Remaining unresolved contracts: **0**
- Implementation authorized: **True**
- Runtime integration authorized: **False**
- Production persistence authorized: **False**
- Manual game check: **NOT_REQUIRED**

## Resolved contracts

- `CANONICAL_SETTLEMENT_IDENTITY`: **TERMINAL_OPERATION_KEY_REQUIRED_BY_APPLICATION_PORT** - The V2 service accepts a caller-supplied stable terminal operation key; it must not derive identity from message IDs or timestamps. Infrastructure enforces uniqueness. V1 terminal claim remains behavior evidence, not a V2 runtime dependency.
- `SINGLE_UNIT_OF_WORK_OWNER`: **ONE_APPLICATION_SERVICE_ONE_CALLER_OWNED_UOW** - One V2 application service owns orchestration through one explicit Unit of Work port. Domain calculators never commit. Infrastructure commits once after every required mutation succeeds or rolls back once on failure.
- `MUTATION_ORDER`: **VALIDATE_THEN_CLAIM_THEN_APPLY_THEN_RECORD_THEN_COMMIT** - Validate immutable inputs before mutation; claim settlement identity; apply EXP/levels and level-up rewards; apply combat gold; apply loot/pending outcome; apply eligible quest/contract progress; append reward history; mark settlement complete; commit once. Presentation follows commit.
- `COMBAT_GOLD_PREMIUM_SCOPE`: **PREMIUM_COMBAT_GOLD_ONLY** - Premium is an explicit combat-gold input only. It must not modify level-up gold, quest gold, story rewards, loot quantities, or unrelated reward sources.
- `LOOT_ATOMICITY_AND_CAPACITY`: **REPOSITORY_OUTCOME_REQUIRED_NO_PARTIAL_SILENT_SUCCESS** - Loot application returns an explicit applied/pending/rejected outcome through the UoW. Partial silent insertion is forbidden. Existing source-specific pending behavior is preserved only where a bounded repository adapter explicitly supports it.
- `QUEST_PROGRESS_ORDER`: **ELIGIBLE_COMBAT_PROGRESS_INSIDE_SAME_UOW_AFTER_REWARDS** - Only progress explicitly produced by the combat outcome is applied in the settlement UoW, after monetary/item reward mutations and before history/completion. Story completion adapters remain separate sources and are not automatically folded into combat settlement.
- `REWARD_HISTORY_OWNER`: **APPEND_ONLY_SETTLEMENT_RECORD_PORT** - The application service writes one append-only settlement record containing operation key, source, actor, reward summary and completion status. It does not reuse presentation messages as history payloads.
- `DUPLICATE_CALLBACK_POLICY`: **DUPLICATE_RETURNS_PRIOR_COMPLETED_RESULT_NO_REAPPLY** - A duplicate stable operation key returns the previously completed result and applies no mutation. A duplicate while in progress fails closed as unavailable/conflict; it does not start a second settlement.
- `PARTIAL_FAILURE_ROLLBACK`: **ALL_DURABLE_MUTATIONS_ROLL_BACK_TOGETHER** - Any failure before completion rolls back settlement claim, EXP, level, attribute points, gold, loot/pending state, quest progress and history in the same UoW. External messages are never sent inside the transaction.
- `PVE_PVP_BOSS_SCOPE`: **PVE_AND_PVE_BOSS_SHARE_SOURCE_TYPE_PVP_EXCLUDED** - The Stage 21.9.3 service accepts ordinary PvE and PvE boss source types where V1 uses the combat victory reward path. PvP completion remains a separate contract and is not routed through this service in this stage.
- `PRESENTATION_AFTER_COMMIT`: **RETURN_DTO_THEN_PRESENT_AFTER_SUCCESSFUL_COMMIT** - The service returns a deterministic settlement result DTO. Handler/adapters build and send messages only after successful commit. Presentation failure cannot roll back or repeat rewards.
- `LEGACY_BYPASS_PATHS`: **COMPATIBILITY_ADAPTERS_MAY_DELEGATE_BUT_NOT_PARALLEL_MUTATE** - Legacy add_exp, reward and quest entrypoints remain outside V2 runtime for now. Future adapters may delegate to the application service, but must not perform parallel reward mutation or own an independent commit within settlement.

## V2 application contract

- Service: `RewardSettlementService`
- Commit count: `1`
- Rollback on any failure: `True`
- Presentation inside transaction: `False`

## Implementation boundary

Allowed:
- application service and pure DTOs
- abstract ports/protocols for one Unit of Work
- in-memory integration fixtures proving exact-once and rollback
- composition of existing V2 progression and level-up-gold APIs

Forbidden:
- SQLite schema or production repository integration
- Telegram/runtime wiring
- new gameplay formulas, reward values, loot chances or Premium rules
- routing PvP through PvE settlement
- sending messages inside the transaction

## Safety

V1 was inspected only as source text and AST. SQLite was not opened. `game.db-wal` and `game.db-shm` were not deleted, cleared, modified, or used for rollback.

## Next patch

`patch_21_9_3c_implement_reward_settlement.py`
