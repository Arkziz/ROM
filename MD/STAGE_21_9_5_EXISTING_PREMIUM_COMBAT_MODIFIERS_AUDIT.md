# Stage 21.9.5 - Existing V1 premium combat modifiers audit

- Status: **PASS**
- Conclusion: **GO_TO_SEMANTIC_REFINEMENT**
- V1 Python files: **275**
- Candidate symbols: **3612**
- Contract rows: **22**
- Review-required rows: **0**
- Production code changed: **False**
- Database opened: **False**
- V1 WAL/SHM manipulated: **False**
- Manual game check: **NOT_REQUIRED**

## Boundary

This is discovery evidence only. It does not authorize an premium combat modifiers implementation or reinterpret V1 behavior.
Runtime/Telegram dispatch and production persistence remain unconnected.

## Contract discovery matrix

- `PREMIUM_STATUS_OWNER`: **DISCOVERED**, evidence files: 23
- `PREMIUM_ACTIVE_CHECK`: **DISCOVERED**, evidence files: 132
- `EXACT_MULTIPLIER`: **DISCOVERED**, evidence files: 33
- `COMBAT_EXP_MODIFIER`: **DISCOVERED**, evidence files: 155
- `COMBAT_GOLD_MODIFIER`: **DISCOVERED**, evidence files: 151
- `EXP_ROUNDING`: **DISCOVERED**, evidence files: 234
- `GOLD_ROUNDING`: **DISCOVERED**, evidence files: 116
- `APPLICATION_ORDER`: **DISCOVERED**, evidence files: 96
- `NORMAL_ELITE_BOSS_SCOPE`: **DISCOVERED**, evidence files: 92
- `SETTLEMENT_BOUNDARY`: **DISCOVERED**, evidence files: 9
- `LEVEL_UP_GOLD_EXCLUSION`: **DISCOVERED**, evidence files: 31
- `QUEST_REWARD_EXCLUSION`: **DISCOVERED**, evidence files: 118
- `SALE_SHOP_EXCLUSION`: **DISCOVERED**, evidence files: 67
- `AUCTION_EXCLUSION`: **DISCOVERED**, evidence files: 38
- `ADMIN_EXCLUSION`: **DISCOVERED**, evidence files: 34
- `REFUND_COMPENSATION_EXCLUSION`: **DISCOVERED**, evidence files: 57
- `GUILD_REWARD_EXCLUSION`: **DISCOVERED**, evidence files: 115
- `LOOT_EXCLUSION`: **DISCOVERED**, evidence files: 129
- `EXPIRY_AND_TIME_OWNER`: **DISCOVERED**, evidence files: 72
- `SIMULATOR_DEV_PARITY`: **DISCOVERED**, evidence files: 78
- `PRESENTATION_BOUNDARY`: **DISCOVERED**, evidence files: 192
- `DUPLICATE_SHADOW_OWNERS`: **DISCOVERED**, evidence files: 2

## Priority candidate owner files

- `handlers/combat.py`: 21 contract groups
- `systems/player_interaction_system.py`: 21 contract groups
- `systems/simulation/parity_foundation.py`: 21 contract groups
- `systems/simulation/world_progression.py`: 21 contract groups
- `handlers/city.py`: 20 contract groups
- `systems/auction_house_system.py`: 20 contract groups
- `systems/reward_system.py`: 20 contract groups
- `systems/timed_exp_bonus_system.py`: 20 contract groups
- `data/drop_tables.py`: 19 contract groups
- `db_modules/__init__.py`: 19 contract groups
- `handlers/auction_house.py`: 19 contract groups
- `systems/name_rune_system.py`: 19 contract groups
- `handlers/dev.py`: 18 contract groups
- `handlers/inventory.py`: 18 contract groups
- `handlers/timed_exp_bonus.py`: 18 contract groups
- `migrations/040_generated_equipment_namespace.py`: 18 contract groups
- `systems/crystal_shop_system.py`: 18 contract groups
- `systems/item_id_allocator_system.py`: 18 contract groups
- `systems/premium_item_policy_system.py`: 18 contract groups
- `handlers/crystal_shop.py`: 17 contract groups

## Mandatory next step

`patch_21_9_5a_refine_premium_combat_modifiers_contract.py`

Semantic refinement must establish the authoritative Premium status owner, exact +25% combat EXP/gold arithmetic and rounding, application order, expiry/time semantics, settlement handoff, non-combat exclusions, loot exclusion, simulator parity, presentation boundary, and duplicate/shadow paths before implementation.
