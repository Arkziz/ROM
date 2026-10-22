# Stage 21.9.4 - Existing V1 central loot pipeline audit

- Status: **PASS**
- Conclusion: **GO_TO_SEMANTIC_REFINEMENT**
- V1 Python files: **275**
- Candidate symbols: **3612**
- Contract rows: **23**
- Review-required rows: **0**
- Production code changed: **False**
- Database opened: **False**
- V1 WAL/SHM manipulated: **False**
- Manual game check: **NOT_REQUIRED**

## Boundary

This is discovery evidence only. It does not authorize an central loot pipeline implementation or reinterpret V1 behavior.
Runtime/Telegram dispatch and production persistence remain unconnected.

## Contract discovery matrix

- `LOOT_ENTRYPOINTS`: **DISCOVERED**, evidence files: 45
- `NORMAL_ELITE_BOSS_SCOPE`: **DISCOVERED**, evidence files: 92
- `GROUP_CHANCES`: **DISCOVERED**, evidence files: 106
- `INTERNAL_ITEM_WEIGHTS`: **DISCOVERED**, evidence files: 32
- `RARITY_SELECTION`: **DISCOVERED**, evidence files: 60
- `EQUIPMENT_GENERATION`: **DISCOVERED**, evidence files: 76
- `CLASS_AWARE_EQUIPMENT`: **DISCOVERED**, evidence files: 128
- `CONSUMABLE_DROPS`: **DISCOVERED**, evidence files: 80
- `RUNE_DROPS`: **DISCOVERED**, evidence files: 54
- `ENHANCEMENT_STONE_DROPS`: **DISCOVERED**, evidence files: 57
- `QUEST_ITEM_DROPS`: **DISCOVERED**, evidence files: 95
- `EVENT_DROPS`: **DISCOVERED**, evidence files: 91
- `TROPHY_AND_GRAY_LOOT`: **DISCOVERED**, evidence files: 18
- `INVENTORY_INSERTION`: **DISCOVERED**, evidence files: 124
- `INVENTORY_FULL_OUTCOME`: **DISCOVERED**, evidence files: 74
- `GENERATED_ID_NAMESPACE`: **DISCOVERED**, evidence files: 66
- `BATTLE_REWARD_INTEGRATION`: **DISCOVERED**, evidence files: 100
- `PREMIUM_BOUNDARY`: **DISCOVERED**, evidence files: 137
- `RNG_OWNERSHIP`: **DISCOVERED**, evidence files: 57
- `DEV_SIMULATOR_CONSUMERS`: **DISCOVERED**, evidence files: 72
- `PRESENTATION_BOUNDARY`: **DISCOVERED**, evidence files: 173
- `DUPLICATE_SHADOW_OWNERS`: **DISCOVERED**, evidence files: 1
- `SETTLEMENT_APPLICATION_BOUNDARY`: **DISCOVERED**, evidence files: 42

## Priority candidate owner files

- `systems/reward_system.py`: 22 contract groups
- `systems/drop_system.py`: 21 contract groups
- `systems/player_interaction_system.py`: 21 contract groups
- `db_modules/__init__.py`: 20 contract groups
- `handlers/city.py`: 19 contract groups
- `handlers/combat.py`: 19 contract groups
- `handlers/dev.py`: 19 contract groups
- `systems/simulation/loot_equipment_city.py`: 19 contract groups
- `systems/simulation/world_progression.py`: 19 contract groups
- `db_modules/dev_compat.py`: 18 contract groups
- `data/drop_tables.py`: 17 contract groups
- `systems/rune_system.py`: 17 contract groups
- `db_modules/systems_wrappers.py`: 16 contract groups
- `systems/auction_house_system.py`: 16 contract groups
- `db_modules/shop.py`: 15 contract groups
- `handlers/auction_house.py`: 15 contract groups
- `systems/equipment_system.py`: 15 contract groups
- `systems/simulation/progression_economy_reporting.py`: 15 contract groups
- `db_modules/generated_equipment.py`: 14 contract groups
- `handlers/player_interaction.py`: 14 contract groups

## Mandatory next step

`patch_21_9_4a_refine_central_loot_pipeline_contract.py`

Semantic refinement must establish authoritative loot entrypoints, exact normal/elite/boss group chances, internal weights, rarity and equipment-generation ownership, inventory outcomes, RNG injection, event/quest boundaries, and duplicate/shadow paths before implementation.
