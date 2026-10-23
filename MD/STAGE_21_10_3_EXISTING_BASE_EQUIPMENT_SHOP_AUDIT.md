# Stage 21.10.3 - Existing V1 base equipment shop audit

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

This is discovery evidence only. It does not authorize an base equipment shop implementation or reinterpret V1 behavior.
Runtime/Telegram dispatch and production persistence remain unconnected.

## Contract discovery matrix

- `SHOP_OWNER`: **DISCOVERED**, evidence files: 90
- `CLASS_AWARE_OFFERS`: **DISCOVERED**, evidence files: 147
- `OFFER_GENERATION`: **DISCOVERED**, evidence files: 97
- `PREVIEW_IDENTITY`: **DISCOVERED**, evidence files: 104
- `PREVIEW_NAMESPACE`: **DISCOVERED**, evidence files: 236
- `CONFIRMATION_FLOW`: **DISCOVERED**, evidence files: 76
- `PERMANENT_PROMOTION`: **DISCOVERED**, evidence files: 101
- `PERMANENT_ID_ALLOCATOR`: **DISCOVERED**, evidence files: 138
- `NEVER_REUSE_IDENTITY`: **DISCOVERED**, evidence files: 47
- `PRICE_CALCULATION`: **DISCOVERED**, evidence files: 128
- `GOLD_DEBIT_BOUNDARY`: **DISCOVERED**, evidence files: 115
- `ATOMIC_PURCHASE`: **DISCOVERED**, evidence files: 77
- `IDEMPOTENCY`: **DISCOVERED**, evidence files: 56
- `INVENTORY_CAPACITY`: **DISCOVERED**, evidence files: 116
- `ITEM_INSERTION`: **DISCOVERED**, evidence files: 198
- `EQUIPMENT_STATS_SNAPSHOT`: **DISCOVERED**, evidence files: 96
- `RUNE_AND_DURABILITY_STATE`: **DISCOVERED**, evidence files: 189
- `RECEIPT_HISTORY`: **DISCOVERED**, evidence files: 64
- `RESTART_SEMANTICS`: **DISCOVERED**, evidence files: 67
- `ERROR_CONTRACT`: **DISCOVERED**, evidence files: 65
- `PRESENTATION_BOUNDARY`: **DISCOVERED**, evidence files: 136
- `SHADOW_OWNER_SCAN`: **DISCOVERED**, evidence files: 69

## Priority candidate owner files

- `systems/rune_system.py`: 22 contract groups
- `db_modules/__init__.py`: 21 contract groups
- `db_modules/dev_compat.py`: 21 contract groups
- `db_modules/equipment.py`: 21 contract groups
- `db_modules/shop.py`: 21 contract groups
- `handlers/city.py`: 21 contract groups
- `systems/auction_house_system.py`: 21 contract groups
- `systems/equipment_system.py`: 21 contract groups
- `systems/player_interaction_system.py`: 21 contract groups
- `db_modules/systems_wrappers.py`: 20 contract groups
- `systems/event_shop_system.py`: 20 contract groups
- `systems/item_id_allocator_system.py`: 20 contract groups
- `handlers/combat.py`: 19 contract groups
- `handlers/player_interaction.py`: 19 contract groups
- `migrations/040_generated_equipment_namespace.py`: 19 contract groups
- `systems/simulation/world_progression.py`: 19 contract groups
- `handlers/crystal_shop.py`: 18 contract groups
- `systems/crystal_shop_system.py`: 18 contract groups
- `systems/potion_system.py`: 18 contract groups
- `db_modules/connection.py`: 17 contract groups

## Mandatory next step

`patch_21_10_3a_refine_base_equipment_shop_contract.py`

Semantic refinement must establish authoritative post-combat event ownership, immutable payload and stable key, settlement ordering, victory/terminal scope, exact-once hook behavior, failure and rollback policy, retry/restart semantics, story/contract/history/notification boundaries, presentation, simulator consumers, and duplicate/shadow hook owners before implementation.
