# Stage 21.9.1a - Refined EXP and level-up contract

- Status: **PASS**
- Conclusion: **REVIEW_REQUIRED**
- V1-confirmed rows: **9**
- Review-required rows: **5**
- Production changed: **False**
- Database opened: **False**
- Manual game check: **NOT_REQUIRED**

## Authoritative context owners

- `curve_and_pure_transition`: `data/player_progression.py`
- `transaction_and_public_entrypoint`: `systems/player_system.py`
- `legacy_db_compat`: `db_modules/player.py`
- `victory_reward_producer`: `systems/reward_system.py`
- `profile_consumer`: `handlers/profile.py`
- `simulator_threshold_consumer`: `systems/simulation/progression_provider.py`

## Contract matrix

- `EXP_CURVE_CONFIGURATION`: **V1_CONFIRMED** - Canonical EXP threshold combines the accepted level table and conditional mobs-to-next policy.
- `BASE_EXP_OWNER`: **V1_CONFIRMED** - Base EXP lookup is owned by player progression data.
- `PURE_AWARD_OWNER`: **V1_CONFIRMED** - Pure EXP award transition owns residual and repeated level-up calculation.
- `TRANSACTION_OWNER`: **V1_CONFIRMED** - Player-system transaction applies the pure progression result to persisted player state.
- `PUBLIC_EXP_ENTRYPOINT`: **V1_CONFIRMED** - Public V1 EXP entrypoint delegates progression mutation.
- `DB_COMPAT_ENTRYPOINT`: **V1_CONFIRMED** - DB compatibility layer exposes EXP award to legacy consumers.
- `REWARD_PRODUCER`: **V1_CONFIRMED** - Victory rewards are an upstream EXP producer, not the progression formula owner.
- `PROFILE_CONSUMER`: **V1_CONFIRMED** - Profile presentation is a downstream level/EXP consumer.
- `SIMULATOR_CONSUMER`: **V1_CONFIRMED** - Simulator obtains thresholds through a progression provider boundary.
- `LEVEL_CAP_EXACT_SEMANTICS`: **REVIEW_REQUIRED** - Exact gameplay cap, prepared configuration range, and EXP-at-cap behavior require source-level semantic resolution.
- `LEVEL_UP_POINT_AWARD`: **REVIEW_REQUIRED** - Exact point types, quantities, and per-level ordering require refinement across mutation owners.
- `MULTI_LEVEL_EVENT_ORDER`: **REVIEW_REQUIRED** - Ordering of repeated level changes, rewards, notifications and downstream effects requires refinement.
- `INVALID_AND_BOUNDARY_INPUTS`: **REVIEW_REQUIRED** - Negative, zero, overflow, below-level-one and cap-boundary behavior requires an explicit contract.
- `IDEMPOTENCY_BOUNDARY`: **REVIEW_REQUIRED** - Discovery does not prove an operation-id idempotency owner for repeated external reward delivery.

## Unresolved contracts

- `LEVEL_CAP_EXACT_SEMANTICS`
- `LEVEL_UP_POINT_AWARD`
- `MULTI_LEVEL_EVENT_ORDER`
- `INVALID_AND_BOUNDARY_INPUTS`
- `IDEMPOTENCY_BOUNDARY`

Implementation remains unauthorized until level-cap semantics, point awards, multi-level event ordering, invalid inputs and idempotency boundaries are resolved from V1 evidence.
