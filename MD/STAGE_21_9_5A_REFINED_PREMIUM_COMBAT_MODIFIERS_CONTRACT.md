# Stage 21.9.5a - Refined Premium combat modifiers contract

- Status: **PASS**
- Conclusion: **REVIEW_REQUIRED**
- V1-confirmed rows: **6**
- Review-required rows: **16**
- Production changed: **False**
- Database opened: **False**
- Manual game check: **NOT_REQUIRED**

## Authoritative context owners

- `premium_policy`: `systems/timed_exp_bonus_system.py`
- `victory_integration`: `systems/reward_system.py`
- `victory_presentation`: `handlers/combat.py`

## Contract matrix

- `PREMIUM_POLICY_OWNER`: **V1_CONFIRMED** - Timed bonus system is the V1 Premium combat policy context.
- `COMBAT_EXP_CALCULATOR_OWNER`: **V1_CONFIRMED** - Combat EXP Premium arithmetic is owned by the timed bonus system.
- `COMBAT_GOLD_PREMIUM_OWNER`: **V1_CONFIRMED** - Premium combat-gold arithmetic has a dedicated V1 calculator.
- `COMBAT_GOLD_CALCULATOR_OWNER`: **V1_CONFIRMED** - Final mob-kill gold is calculated in the timed bonus system.
- `VICTORY_INTEGRATION_OWNER`: **V1_CONFIRMED** - Victory reward flow is the current Premium combat integration boundary.
- `VICTORY_PRESENTATION_BOUNDARY`: **V1_CONFIRMED** - Victory text presents already-calculated combat rewards.
- `EXACT_PREMIUM_ACTIVE_CHECK`: **REVIEW_REQUIRED** - Premium field, expiry comparison, null handling and status output require exact source resolution.
- `EXACT_UTC_CLOCK_BOUNDARY`: **REVIEW_REQUIRED** - Timezone awareness, UTC normalization and equality-at-expiry semantics require proof.
- `EXACT_PLUS_25_PERCENT_MULTIPLIER`: **REVIEW_REQUIRED** - The exact 1.25 representation and inactive identity multiplier require resolution.
- `COMBAT_EXP_ARITHMETIC_AND_ROUNDING`: **REVIEW_REQUIRED** - The source expression, operation order and integer rounding for combat EXP require resolution.
- `COMBAT_GOLD_ARITHMETIC_AND_ROUNDING`: **REVIEW_REQUIRED** - The source expression, Decimal/float boundary and currency rounding require resolution.
- `ELITE_BOSS_PREMIUM_ORDER`: **REVIEW_REQUIRED** - Premium order relative to normal, elite, boss and level-difference multipliers requires proof.
- `SETTLEMENT_INPUT_SHAPE`: **REVIEW_REQUIRED** - RewardSettlementService must receive finalized combat-only values or an explicit Premium snapshot without duplicate application.
- `LEVEL_UP_GOLD_EXCLUSION`: **REVIEW_REQUIRED** - Level-up gold must remain outside Premium combat-gold modification.
- `QUEST_REWARD_EXCLUSION`: **REVIEW_REQUIRED** - Quest and story rewards must not call the Premium combat calculators.
- `SALE_AUCTION_ADMIN_EXCLUSION`: **REVIEW_REQUIRED** - Shop sales, auction and administrative wallet operations require explicit negative scope.
- `REFUND_GUILD_EXCLUSION`: **REVIEW_REQUIRED** - Refund, compensation and guild rewards require explicit negative scope.
- `LOOT_TOTAL_EXCLUSION`: **REVIEW_REQUIRED** - Premium must not affect loot chances, weights, rarity, quantities, RNG or generated equipment.
- `SIMULATOR_DEV_PARITY`: **REVIEW_REQUIRED** - Simulator and DEV consumers must delegate or prove exact parity without alternate formulas.
- `PRESENTATION_NO_RECALCULATION`: **REVIEW_REQUIRED** - Presentation may display Premium contribution but must not recalculate or mutate rewards.
- `DUPLICATE_SHADOW_OWNER_CLASSIFICATION`: **REVIEW_REQUIRED** - All Premium bonus helpers require authoritative, compatibility or shadow classification.
- `V2_PREMIUM_COMBAT_API`: **REVIEW_REQUIRED** - The pure V2 modifier API and its relation to progression and settlement require resolution.

## Unresolved contracts

- `EXACT_PREMIUM_ACTIVE_CHECK`
- `EXACT_UTC_CLOCK_BOUNDARY`
- `EXACT_PLUS_25_PERCENT_MULTIPLIER`
- `COMBAT_EXP_ARITHMETIC_AND_ROUNDING`
- `COMBAT_GOLD_ARITHMETIC_AND_ROUNDING`
- `ELITE_BOSS_PREMIUM_ORDER`
- `SETTLEMENT_INPUT_SHAPE`
- `LEVEL_UP_GOLD_EXCLUSION`
- `QUEST_REWARD_EXCLUSION`
- `SALE_AUCTION_ADMIN_EXCLUSION`
- `REFUND_GUILD_EXCLUSION`
- `LOOT_TOTAL_EXCLUSION`
- `SIMULATOR_DEV_PARITY`
- `PRESENTATION_NO_RECALCULATION`
- `DUPLICATE_SHADOW_OWNER_CLASSIFICATION`
- `V2_PREMIUM_COMBAT_API`

Implementation remains unauthorized until active/expiry semantics, UTC clock, exact +25% arithmetic, EXP/gold rounding, elite/boss ordering, settlement handoff, all non-combat exclusions, loot exclusion, simulator parity, presentation and shadow owners are resolved from V1 evidence.
