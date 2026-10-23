# Stage 21.10.4 - Existing V1 potion trading audit

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

This is discovery evidence only. It does not authorize an potion trading implementation or reinterpret V1 behavior.
Runtime/Telegram dispatch and production persistence remain unconnected.

## Contract discovery matrix

- `TRADING_OWNER`: **DISCOVERED**, evidence files: 67
- `ALCHEMIST_BOUNDARY`: **DISCOVERED**, evidence files: 67
- `BUY_QUANTITY`: **DISCOVERED**, evidence files: 113
- `SELL_QUANTITY`: **DISCOVERED**, evidence files: 120
- `MAX_QUANTITY`: **DISCOVERED**, evidence files: 120
- `STACK_NORMALIZATION`: **DISCOVERED**, evidence files: 140
- `RESERVATION_AWARE`: **DISCOVERED**, evidence files: 119
- `ACCEPTED_BUY_PRICE`: **DISCOVERED**, evidence files: 105
- `ACCEPTED_SELL_PRICE`: **DISCOVERED**, evidence files: 105
- `PRICE_SNAPSHOT`: **DISCOVERED**, evidence files: 71
- `CONFIRMATION_FLOW`: **DISCOVERED**, evidence files: 82
- `GOLD_MUTATION`: **DISCOVERED**, evidence files: 114
- `INVENTORY_MUTATION`: **DISCOVERED**, evidence files: 162
- `ATOMIC_BUY`: **DISCOVERED**, evidence files: 74
- `ATOMIC_SELL`: **DISCOVERED**, evidence files: 84
- `IDEMPOTENCY`: **DISCOVERED**, evidence files: 61
- `ITEM_ALLOWLIST`: **DISCOVERED**, evidence files: 120
- `RECEIPT_HISTORY`: **DISCOVERED**, evidence files: 62
- `ERROR_CONTRACT`: **DISCOVERED**, evidence files: 65
- `PRESENTATION_BOUNDARY`: **DISCOVERED**, evidence files: 136
- `SHADOW_OWNER_SCAN`: **DISCOVERED**, evidence files: 59

## Priority candidate owner files

- `db_modules/dev_compat.py`: 21 contract groups
- `systems/auction_house_system.py`: 21 contract groups
- `systems/equipment_system.py`: 21 contract groups
- `systems/player_interaction_system.py`: 21 contract groups
- `db_modules/__init__.py`: 20 contract groups
- `db_modules/equipment.py`: 20 contract groups
- `handlers/auction_house.py`: 20 contract groups
- `handlers/city.py`: 20 contract groups
- `systems/rune_system.py`: 20 contract groups
- `db_modules/inventory.py`: 19 contract groups
- `db_modules/systems_wrappers.py`: 19 contract groups
- `handlers/combat.py`: 19 contract groups
- `systems/name_rune_system.py`: 19 contract groups
- `systems/potion_system.py`: 19 contract groups
- `db_modules/connection.py`: 18 contract groups
- `db_modules/inventory_compat.py`: 18 contract groups
- `db_modules/shop.py`: 18 contract groups
- `handlers/dev.py`: 18 contract groups
- `handlers/player_interaction.py`: 18 contract groups
- `handlers/profile.py`: 18 contract groups

## Mandatory next step

`patch_21_10_4a_refine_potion_trading_contract.py`

Semantic refinement must establish authoritative post-combat event ownership, immutable payload and stable key, settlement ordering, victory/terminal scope, exact-once hook behavior, failure and rollback policy, retry/restart semantics, story/contract/history/notification boundaries, presentation, simulator consumers, and duplicate/shadow hook owners before implementation.
