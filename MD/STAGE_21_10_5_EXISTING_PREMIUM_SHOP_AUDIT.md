# Stage 21.10.5 - Existing V1 premium shop audit

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

This is discovery evidence only. It does not authorize an premium shop implementation or reinterpret V1 behavior.
Runtime/Telegram dispatch and production persistence remain unconnected.

## Contract discovery matrix

- `PREMIUM_SHOP_OWNER`: **DISCOVERED**, evidence files: 54
- `PREMIUM_PLAN_CATALOG`: **DISCOVERED**, evidence files: 119
- `PLAN_15_PRICE`: **DISCOVERED**, evidence files: 128
- `PLAN_30_PRICE`: **DISCOVERED**, evidence files: 94
- `ACTIVATION`: **DISCOVERED**, evidence files: 39
- `EXTENSION`: **DISCOVERED**, evidence files: 47
- `ACTIVE_EXPIRY_BASE`: **DISCOVERED**, evidence files: 140
- `INACTIVE_EXPIRY_BASE`: **DISCOVERED**, evidence files: 99
- `CRYSTAL_DEBIT`: **DISCOVERED**, evidence files: 73
- `PRICE_SNAPSHOT`: **DISCOVERED**, evidence files: 73
- `CONFIRMATION_FLOW`: **DISCOVERED**, evidence files: 76
- `ATOMIC_ACTIVATION`: **DISCOVERED**, evidence files: 68
- `ATOMIC_EXTENSION`: **DISCOVERED**, evidence files: 86
- `IDEMPOTENCY`: **DISCOVERED**, evidence files: 54
- `ACCOUNT_LEVEL_SCOPE`: **DISCOVERED**, evidence files: 162
- `RESTART_SEMANTICS`: **DISCOVERED**, evidence files: 58
- `PURCHASE_HISTORY`: **DISCOVERED**, evidence files: 65
- `TIMEZONE_CLOCK`: **DISCOVERED**, evidence files: 72
- `ERROR_CONTRACT`: **DISCOVERED**, evidence files: 71
- `PRESENTATION_BOUNDARY`: **DISCOVERED**, evidence files: 136
- `SHADOW_OWNER_SCAN`: **DISCOVERED**, evidence files: 61

## Priority candidate owner files

- `systems/auction_house_system.py`: 21 contract groups
- `systems/player_interaction_system.py`: 21 contract groups
- `systems/premium_item_policy_system.py`: 21 contract groups
- `db_modules/__init__.py`: 20 contract groups
- `systems/crystal_shop_system.py`: 20 contract groups
- `systems/item_id_allocator_system.py`: 20 contract groups
- `systems/timed_exp_bonus_system.py`: 20 contract groups
- `handlers/auction_house.py`: 19 contract groups
- `handlers/city.py`: 19 contract groups
- `handlers/combat.py`: 19 contract groups
- `systems/name_rune_system.py`: 19 contract groups
- `handlers/dev.py`: 18 contract groups
- `handlers/inventory.py`: 18 contract groups
- `handlers/timed_exp_bonus.py`: 18 contract groups
- `systems/simulation/parity_foundation.py`: 18 contract groups
- `handlers/crystal_shop.py`: 17 contract groups
- `systems/crystal_bag_expansion_system.py`: 17 contract groups
- `systems/potion_system.py`: 17 contract groups
- `systems/reward_system.py`: 17 contract groups
- `data/drop_tables.py`: 16 contract groups

## Mandatory next step

`patch_21_10_5a_refine_premium_shop_contract.py`

Semantic refinement must establish authoritative post-combat event ownership, immutable payload and stable key, settlement ordering, victory/terminal scope, exact-once hook behavior, failure and rollback policy, retry/restart semantics, story/contract/history/notification boundaries, presentation, simulator consumers, and duplicate/shadow hook owners before implementation.
