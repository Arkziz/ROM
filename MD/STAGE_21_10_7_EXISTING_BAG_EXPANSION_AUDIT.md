# Stage 21.10.7 - Existing V1 bag expansion audit

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

This is discovery evidence only. It does not authorize an bag expansion implementation or reinterpret V1 behavior.
Runtime/Telegram dispatch and production persistence remain unconnected.

## Contract discovery matrix

- `BAG_EXPANSION_OWNER`: **DISCOVERED**, evidence files: 66
- `BASE_CAPACITY`: **DISCOVERED**, evidence files: 123
- `FIRST_EXPANSION`: **DISCOVERED**, evidence files: 88
- `SECOND_EXPANSION`: **DISCOVERED**, evidence files: 123
- `FIRST_EXPANSION_PRICE`: **DISCOVERED**, evidence files: 94
- `SECOND_EXPANSION_PRICE`: **DISCOVERED**, evidence files: 130
- `SEQUENTIAL_PROGRESSION`: **DISCOVERED**, evidence files: 152
- `ACCOUNT_LEVEL_SCOPE`: **DISCOVERED**, evidence files: 164
- `CAPACITY_READ`: **DISCOVERED**, evidence files: 240
- `PURCHASE_PREVIEW`: **DISCOVERED**, evidence files: 81
- `PURCHASE_CONFIRMATION`: **DISCOVERED**, evidence files: 70
- `CRYSTAL_DEBIT`: **DISCOVERED**, evidence files: 73
- `CAPACITY_MUTATION`: **DISCOVERED**, evidence files: 157
- `ATOMIC_PURCHASE`: **DISCOVERED**, evidence files: 77
- `IDEMPOTENCY`: **DISCOVERED**, evidence files: 56
- `PURCHASE_HISTORY`: **DISCOVERED**, evidence files: 78
- `CHARACTER_RESET_SURVIVAL`: **DISCOVERED**, evidence files: 116
- `RESTART_PERSISTENCE`: **DISCOVERED**, evidence files: 86
- `ERROR_CONTRACT`: **DISCOVERED**, evidence files: 75
- `PRESENTATION_BOUNDARY`: **DISCOVERED**, evidence files: 136
- `SHADOW_OWNER_SCAN`: **DISCOVERED**, evidence files: 88

## Priority candidate owner files

- `db_modules/__init__.py`: 21 contract groups
- `handlers/crystal_shop.py`: 21 contract groups
- `systems/auction_house_system.py`: 21 contract groups
- `systems/crystal_bag_expansion_system.py`: 21 contract groups
- `systems/potion_system.py`: 21 contract groups
- `systems/rune_system.py`: 21 contract groups
- `handlers/city.py`: 20 contract groups
- `handlers/combat.py`: 20 contract groups
- `systems/crystal_shop_system.py`: 20 contract groups
- `systems/equipment_system.py`: 20 contract groups
- `systems/event_shop_system.py`: 20 contract groups
- `systems/player_interaction_system.py`: 20 contract groups
- `db_modules/dev_compat.py`: 19 contract groups
- `db_modules/migrations.py`: 19 contract groups
- `db_modules/shop.py`: 19 contract groups
- `handlers/dev.py`: 19 contract groups
- `systems/simulation/world_progression.py`: 19 contract groups
- `systems/timed_exp_bonus_system.py`: 19 contract groups
- `db_modules/connection.py`: 18 contract groups
- `handlers/event_ui.py`: 18 contract groups

## Mandatory next step

`patch_21_10_7a_refine_bag_expansion_contract.py`

Semantic refinement must establish authoritative post-combat event ownership, immutable payload and stable key, settlement ordering, victory/terminal scope, exact-once hook behavior, failure and rollback policy, retry/restart semantics, story/contract/history/notification boundaries, presentation, simulator consumers, and duplicate/shadow hook owners before implementation.
