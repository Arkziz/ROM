# Stage 18.18.0: PvE Auto-Escape Read-only Audit

**Status:** PASS
**Production mutation:** none

## Approved policy

- Deadline: 300 seconds from authoritative encounter start.
- HP and MP remain at their actual values.
- Energy is not refunded.
- No extra durability or death penalty is applied.
- No EXP, gold, loot, kill, quest, contract, boss or event progress is awarded.
- Normal, elite and boss encounters use the same timeout policy.
- Restart preserves the original deadline.
- First atomic terminal completion wins; later attacks become stale.

## Audit summary

- Python files scanned: `593`.
- Combat-related functions: `194`.
- State globals: `['ALL_MOBS', 'ATTRIBUTE_ALLOCATION_STATE', 'AUCTION_BUY_STATE', 'AUCTION_HISTORY_STATE_V1', 'AUCTION_MARKET_PRICE_SEARCH_STATE_V1', 'AUCTION_SEARCH_STATE_V1', 'AUCTION_SELL_INLINE_STATE', 'AUCTION_SELL_REVIEW_STATE', 'AUCTION_SELL_STATE', 'AUCTION_SELL_STATE_V2', 'BOSS_ATTACK_MULTIPLIER', 'BOSS_CORE_STAT_MULTIPLIER', 'BOSS_DEFINITIONS', 'BOSS_ENCOUNTERS_ENABLED', 'BOSS_ENCOUNTER_CHANCE_PERCENT', 'BOSS_ENRAGE_HP_PERCENT', 'BOSS_HP_MULTIPLIER', 'BOSS_KEY_BY_LOCATION', 'BOSS_SCHEMA_VERSION', 'COMBAT_PATH', 'CONDITIONAL_MOBS_TO_NEXT_BY_LEVEL', 'CONTRACT_MOBS_EQUIVALENT', 'DARK_FOREST_MOBS', 'GUILD_APPLICATION_REVIEW_STATE', 'GUILD_BROWSE_STATE', 'GUILD_CREATE_STATE', 'GUILD_LOGS_STATE', 'GUILD_MEMBER_MANAGE_STATE', 'LOCATION_1_MOBS', 'LOCATION_MOBS_BY_LOCATION', 'MP_POST_COMBAT_FLOOR_PERCENT_17_15_1', 'PLACEHOLDER_ACCEPTED_TRADE_SESSION_TTL_SECONDS', 'PLAYER_BOSS_BLEED_EFFECT_KEY', 'PVP_COMBAT_ENERGY_MAX', 'PVP_PRODUCTION_STATE_MUTATION', 'SESSION_PREFIX', 'SPECIAL_MATERIAL_MOB_DROP_DENYLIST', 'SPECIAL_MATERIAL_MOB_DROP_POLICY_VERSION', 'START_PATH_MOBS', 'TRADE_AMOUNT_INPUT_STATE_12_6_3', '_COMBAT_CALLBACK_DEBOUNCE_SECONDS_11_3_1', '_COMBAT_CALLBACK_LAST_ACTION_11_3_1', '_COMBAT_SEND_WRAPPER_INSTALLED_11_3_1', '_COMBAT_TELEGRAM_BLOCKED_UNTIL_11_3_1', '_GUILD_LEADERSHIP_STATE_17_22_1', '_RUNE_MASTER_SHOP_QUANTITY_STATE_10_13_0', '_STATE_LOCK', 'boss', 'boss_builder_present', 'boss_reference_signals', 'boss_samples', 'boss_system_path', 'boss_system_text', 'combat', 'combat_path', 'combat_system_path', 'combat_system_text', 'combat_text', 'mob', 'states']`.
- Relevant DB tables: `['inactivity_reminders', 'player_activity_sessions', 'pvp_battles', 'pvp_events', 'pvp_participants', 'pvp_round_actions', 'user_active_contracts', 'user_daily_quests', 'users']`.
- Persistent deadline found: `False`.
- Findings: `1`.

## Findings

- **BLOCKER NO_PERSISTENT_DEADLINE**: No authoritative PvE started_at/deadline persistence was found.

## Required mutation architecture

- Persistent authoritative started_at/deadline.
- One atomic terminal completion API shared by attack and timeout.
- Restart recovery and one sweeper owner.
- Rewards committed only by victory completion, never by timeout.
- User notification only after escape commit.

## Database safety

- quick_check: `ok`.
- FK violations: `0`.
- DB unchanged: `True`.
