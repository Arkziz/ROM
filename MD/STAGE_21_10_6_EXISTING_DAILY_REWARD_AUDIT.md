# Stage 21.10.6 - Existing V1 daily reward audit

- Status: **PASS**
- Conclusion: **GO_TO_SEMANTIC_REFINEMENT**
- V1 Python files: **275**
- Candidate symbols: **3612**
- Contract rows: **21**
- Review-required rows: **0**
- Production code changed: **False**
- Database opened: **False**
- V1 WAL/SHM manipulated: **False**
- Manual game check: **NOT_REQUIRED**

## Boundary

This is discovery evidence only. It does not authorize an daily reward implementation or reinterpret V1 behavior.
Runtime/Telegram dispatch and production persistence remain unconnected.

## Contract discovery matrix

- `DAILY_REWARD_OWNER`: **DISCOVERED**, evidence files: 161
- `REWARD_CATALOG`: **DISCOVERED**, evidence files: 114
- `SMALL_HP_POTION_REWARD`: **DISCOVERED**, evidence files: 184
- `PHIRIUS_TOKEN_REWARD`: **DISCOVERED**, evidence files: 201
- `ONCE_PER_PERIOD`: **DISCOVERED**, evidence files: 72
- `PERIOD_KEY`: **DISCOVERED**, evidence files: 164
- `ACCOUNT_LEVEL_SCOPE`: **DISCOVERED**, evidence files: 184
- `CLAIM_PREVIEW`: **DISCOVERED**, evidence files: 108
- `CLAIM_CONFIRMATION`: **DISCOVERED**, evidence files: 102
- `POTION_INVENTORY_GRANT`: **DISCOVERED**, evidence files: 162
- `TOKEN_WALLET_GRANT`: **DISCOVERED**, evidence files: 127
- `STACK_NORMALIZATION`: **DISCOVERED**, evidence files: 121
- `INVENTORY_CAPACITY`: **DISCOVERED**, evidence files: 116
- `ATOMIC_CLAIM`: **DISCOVERED**, evidence files: 76
- `IDEMPOTENCY`: **DISCOVERED**, evidence files: 62
- `CLAIM_HISTORY`: **DISCOVERED**, evidence files: 91
- `RESTART_SEMANTICS`: **DISCOVERED**, evidence files: 55
- `CLOCK_TIMEZONE`: **DISCOVERED**, evidence files: 160
- `ERROR_CONTRACT`: **DISCOVERED**, evidence files: 63
- `PRESENTATION_BOUNDARY`: **DISCOVERED**, evidence files: 136
- `SHADOW_OWNER_SCAN`: **DISCOVERED**, evidence files: 93

## Priority candidate owner files

- `db_modules/__init__.py`: 21 contract groups
- `db_modules/story_quests.py`: 21 contract groups
- `handlers/auction_house.py`: 21 contract groups
- `systems/auction_house_system.py`: 21 contract groups
- `systems/rune_system.py`: 21 contract groups
- `data/story_quest_definitions.py`: 20 contract groups
- `db_modules/daily_compat.py`: 20 contract groups
- `db_modules/quests.py`: 20 contract groups
- `db_modules/systems_wrappers.py`: 20 contract groups
- `handlers/combat.py`: 20 contract groups
- `systems/level_up_reward_system.py`: 20 contract groups
- `db_modules/dev_compat.py`: 19 contract groups
- `db_modules/migrations.py`: 19 contract groups
- `main.py`: 19 contract groups
- `migrations/053_story_quest_persistence_schema.py`: 19 contract groups
- `systems/player_interaction_system.py`: 19 contract groups
- `systems/premium_item_policy_system.py`: 19 contract groups
- `systems/simulation/economic_ledger.py`: 19 contract groups
- `systems/simulation/meta_progression.py`: 19 contract groups
- `systems/simulation/models.py`: 19 contract groups

## Mandatory next step

`patch_21_10_6a_refine_daily_reward_contract.py`

Semantic refinement must establish authoritative post-combat event ownership, immutable payload and stable key, settlement ordering, victory/terminal scope, exact-once hook behavior, failure and rollback policy, retry/restart semantics, story/contract/history/notification boundaries, presentation, simulator consumers, and duplicate/shadow hook owners before implementation.
