# Stage 21.10.8 - Existing V1 admin crystals audit

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

This is discovery evidence only. It does not authorize an admin crystals implementation or reinterpret V1 behavior.
Runtime/Telegram dispatch and production persistence remain unconnected.

## Contract discovery matrix

- `ADMIN_COMMAND_ENTRY`: **DISCOVERED**, evidence files: 38
- `ADMIN_AUTHORIZATION`: **DISCOVERED**, evidence files: 123
- `ADMIN_CREDIT`: **DISCOVERED**, evidence files: 63
- `ADMIN_DEBIT`: **DISCOVERED**, evidence files: 63
- `CLAMPED_DEBIT`: **DISCOVERED**, evidence files: 77
- `NON_NEGATIVE_BALANCE`: **DISCOVERED**, evidence files: 77
- `TARGET_ACCOUNT_LOOKUP`: **DISCOVERED**, evidence files: 173
- `AMOUNT_VALIDATION`: **DISCOVERED**, evidence files: 102
- `CONFIRMATION_FLOW`: **DISCOVERED**, evidence files: 74
- `STABLE_OPERATION_KEY`: **DISCOVERED**, evidence files: 41
- `IDEMPOTENT_REPLAY`: **DISCOVERED**, evidence files: 66
- `LEDGER_AUDIT`: **DISCOVERED**, evidence files: 49
- `ADMIN_ACTOR_METADATA`: **DISCOVERED**, evidence files: 112
- `RECIPIENT_NOTICE`: **DISCOVERED**, evidence files: 103
- `NOTICE_FAILURE_POLICY`: **DISCOVERED**, evidence files: 73
- `HISTORY_PAGINATION`: **DISCOVERED**, evidence files: 72
- `HISTORY_DETAIL`: **DISCOVERED**, evidence files: 76
- `ATOMIC_OPERATION`: **DISCOVERED**, evidence files: 80
- `RESTART_PERSISTENCE`: **DISCOVERED**, evidence files: 93
- `PRESENTATION_BOUNDARY`: **DISCOVERED**, evidence files: 107
- `SHADOW_MUTATION_SCAN`: **DISCOVERED**, evidence files: 87

## Priority candidate owner files

- `handlers/admin_crystal_credit.py`: 21 contract groups
- `systems/admin_crystal_credit_system.py`: 21 contract groups
- `systems/auction_house_system.py`: 21 contract groups
- `systems/crystal_shop_system.py`: 21 contract groups
- `systems/crystal_wallet_system.py`: 21 contract groups
- `systems/rune_system.py`: 21 contract groups
- `db_modules/dev_compat.py`: 20 contract groups
- `main.py`: 20 contract groups
- `systems/crystal_bag_expansion_system.py`: 20 contract groups
- `systems/timed_exp_bonus_system.py`: 20 contract groups
- `handlers/dev.py`: 19 contract groups
- `systems/premium_item_policy_system.py`: 19 contract groups
- `db_modules/__init__.py`: 18 contract groups
- `systems/level_up_reward_system.py`: 18 contract groups
- `handlers/auction_house.py`: 17 contract groups
- `handlers/city.py`: 17 contract groups
- `migrations/030_static_item_namespace.py`: 17 contract groups
- `systems/player_interaction_system.py`: 17 contract groups
- `handlers/combat.py`: 16 contract groups
- `handlers/crystal_shop.py`: 16 contract groups

## Mandatory next step

`patch_21_10_8a_refine_admin_crystals_contract.py`

Semantic refinement must establish authoritative post-combat event ownership, immutable payload and stable key, settlement ordering, victory/terminal scope, exact-once hook behavior, failure and rollback policy, retry/restart semantics, story/contract/history/notification boundaries, presentation, simulator consumers, and duplicate/shadow hook owners before implementation.
