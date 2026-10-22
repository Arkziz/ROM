# Stage 21.9.5b - Resolved Premium combat modifiers parity

- Status: **PASS**
- Conclusion: **GO_TO_IMPLEMENTATION**
- Remaining unresolved contracts: **0**
- Implementation authorized: **True**
- Runtime integration authorized: **False**
- Production persistence authorized: **False**
- Manual game check: **NOT_REQUIRED**

## Resolved contracts

- `EXACT_PREMIUM_ACTIVE_CHECK`: **SOURCE_STATUS_SNAPSHOT** - Premium activity is resolved once from the V1 status owner; absent or expired status is inactive.
- `EXACT_UTC_CLOCK_BOUNDARY`: **UTC_EXPIRY_SNAPSHOT** - Expiry comparison uses one explicit UTC clock snapshot; equality at expiry is inactive.
- `EXACT_PLUS_25_PERCENT_MULTIPLIER`: **EXACT_1_25_ACTIVE_IDENTITY_INACTIVE** - Active Premium multiplier is exactly 1.25; inactive Premium is exactly 1.0.
- `COMBAT_EXP_ARITHMETIC_AND_ROUNDING`: **SOURCE_EXPRESSION_INTEGER_RESULT** - Combat EXP preserves the exact V1 source expression and integer conversion order.
- `COMBAT_GOLD_ARITHMETIC_AND_ROUNDING`: **SOURCE_EXPRESSION_CURRENCY_RESULT** - Combat gold preserves the exact V1 source expression and currency rounding boundary.
- `ELITE_BOSS_PREMIUM_ORDER`: **PREMIUM_AFTER_BASE_COMBAT_MODIFIERS** - Normal, elite and boss base combat reward modifiers resolve before the single Premium multiplier.
- `SETTLEMENT_INPUT_SHAPE`: **FINALIZED_COMBAT_VALUES_SINGLE_APPLICATION** - Settlement receives finalized combat EXP and combat gold plus an immutable Premium breakdown; it never reapplies Premium.
- `LEVEL_UP_GOLD_EXCLUSION`: **EXCLUDED_NON_COMBAT_GOLD** - Level-up gold is never Premium-modified.
- `QUEST_REWARD_EXCLUSION`: **EXCLUDED_NON_COMBAT_REWARD** - Quest and story rewards never invoke Premium combat calculators.
- `SALE_AUCTION_ADMIN_EXCLUSION`: **EXCLUDED_WALLET_SOURCES** - Sales, auctions and administrative wallet operations are outside Premium combat scope.
- `REFUND_GUILD_EXCLUSION`: **EXCLUDED_COMPENSATION_AND_GUILD** - Refund, compensation and guild rewards are outside Premium combat scope.
- `LOOT_TOTAL_EXCLUSION`: **NO_LOOT_INPUT_OR_EFFECT** - Premium cannot affect loot chance, weight, rarity, quantity, RNG or generated equipment.
- `SIMULATOR_DEV_PARITY`: **DELEGATE_SAME_PURE_MODIFIER** - Simulator and DEV paths delegate to the same modifier or prove exact fixtures; no alternate formula.
- `PRESENTATION_NO_RECALCULATION`: **DISPLAY_BREAKDOWN_ONLY** - Presentation displays finalized base, bonus and total values and never recalculates or mutates.
- `DUPLICATE_SHADOW_OWNER_CLASSIFICATION`: **TIMED_BONUS_OWNER_COMPATIBILITY_DELEGATES_ONLY** - Timed bonus policy is authoritative; other helpers are compatibility delegates or forbidden shadows.
- `V2_PREMIUM_COMBAT_API`: **PURE_COMBAT_MODIFIER_WITH_EXPLICIT_SNAPSHOT** - V2 implements a pure PremiumCombatModifier using explicit active snapshot and exact source-backed arithmetic.

## V2 Premium combat contract

- Service: `PremiumCombatModifier`
- Active multiplier: `1.25`
- Inactive multiplier: `1.0`
- Loot effect: `False`
- Non-combat effect: `False`
- Inputs: `base_combat_exp, base_combat_gold, premium_active_snapshot`
- Outputs: `final_combat_exp, final_combat_gold, premium_breakdown`

## Implementation boundary

Allowed:
- pure modifier DTOs and exact source-backed arithmetic
- explicit Premium snapshot input
- unit and scope fixtures for active, inactive and expiry boundaries

Forbidden:
- SQLite or Premium persistence adapters
- runtime or Telegram wiring
- non-combat reward modification
- loot modification
- multiplier rebalance

## Safety

V1 was inspected only as source text and AST. SQLite was not opened. `game.db-wal` and `game.db-shm` were not deleted, cleared, modified, or used for rollback.

## Next patch

`patch_21_9_5c_implement_premium_combat_modifiers.py`
