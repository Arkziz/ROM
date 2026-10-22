# Stage 21.9.2a - Refined level-up gold contract

- Status: **PASS**
- Conclusion: **REVIEW_REQUIRED**
- V1-confirmed rows: **6**
- Review-required rows: **6**
- Production changed: **False**
- Database opened: **False**
- Manual game check: **NOT_REQUIRED**

## Authoritative context owners

- `matrix_and_calculators`: `systems/level_up_reward_system.py`
- `transactional_consumer`: `systems/player_system.py`
- `presentation`: `systems/level_up_reward_system.py`

## Contract matrix

- `GOLD_MATRIX_CONFIGURATION`: **V1_CONFIRMED** - Explicit reached-level gold matrix is owned by the level-up reward system.
- `SINGLE_LEVEL_REWARD_OWNER`: **V1_CONFIRMED** - Single-level calculator reads the explicit matrix and fails closed for an unconfigured level.
- `MULTI_LEVEL_REWARD_OWNER`: **V1_CONFIRMED** - Multi-level calculator evaluates every reached level and aggregates rows.
- `TRANSACTIONAL_SETTLEMENT_OWNER`: **V1_CONFIRMED** - Transactional settlement is separate from pure reward calculation.
- `PRESENTATION_OWNER`: **V1_CONFIRMED** - Reward message formatting is a downstream presentation boundary.
- `EXP_PIPELINE_CONSUMER`: **V1_CONFIRMED** - EXP transaction consumes the level-up reward subsystem but does not own the gold matrix; exact call names are resolved in the next parity step.
- `EXACT_MATRIX_VALUES`: **REVIEW_REQUIRED** - Exact configured keys and Decimal-compatible values require literal extraction.
- `CONFIGURED_LEVEL_RANGE`: **REVIEW_REQUIRED** - Minimum, maximum and any gaps in configured reached levels require an explicit contract.
- `NO_FALLBACK_AFTER_LEVEL_11`: **REVIEW_REQUIRED** - Absence of formula, last-value and legacy fallback after level 11 requires bounded confirmation.
- `MULTI_LEVEL_GOLD_ORDER`: **REVIEW_REQUIRED** - Exact reached-level ordering and gold accumulation semantics require source-level resolution.
- `DECIMAL_AND_RESULT_SHAPE`: **REVIEW_REQUIRED** - Exact numeric type, single-row keys and aggregate result shape require resolution.
- `SHADOW_OWNER_ABSENCE`: **REVIEW_REQUIRED** - Repository-wide absence of a second authoritative matrix requires a bounded scan.

## Unresolved contracts

- `EXACT_MATRIX_VALUES`
- `CONFIGURED_LEVEL_RANGE`
- `NO_FALLBACK_AFTER_LEVEL_11`
- `MULTI_LEVEL_GOLD_ORDER`
- `DECIMAL_AND_RESULT_SHAPE`
- `SHADOW_OWNER_ABSENCE`

Implementation remains unauthorized until exact matrix values, configured range, no-fallback policy, aggregation order, result shape and shadow-owner absence are resolved from V1 evidence.
