# Stage 21.11.1 - Existing V1 location catalog audit

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

This is discovery evidence only. It does not authorize an location catalog implementation or reinterpret V1 behavior.
Runtime/Telegram dispatch and production persistence remain unconnected.

## Contract discovery matrix

- `LOCATION_CATALOG_OWNER`: **DISCOVERED**, evidence files: 191
- `STABLE_LOCATION_IDS`: **DISCOVERED**, evidence files: 213
- `LOCALIZED_NAME_RESOLVER`: **DISCOVERED**, evidence files: 186
- `START_PATH_NAME`: **DISCOVERED**, evidence files: 186
- `LEVEL_REQUIREMENTS`: **DISCOVERED**, evidence files: 150
- `LOCATION_MOBS`: **DISCOVERED**, evidence files: 108
- `LOCATION_NPCS`: **DISCOVERED**, evidence files: 75
- `UNLOCK_POLICY`: **DISCOVERED**, evidence files: 103
- `REGION_RELATION`: **DISCOVERED**, evidence files: 116
- `TRAVEL_DESTINATION_SOURCE`: **DISCOVERED**, evidence files: 91
- `MAP_PRESENTATION_SOURCE`: **DISCOVERED**, evidence files: 206
- `QUEST_LOCATION_REFERENCE`: **DISCOVERED**, evidence files: 137
- `MOB_LOCATION_REFERENCE`: **DISCOVERED**, evidence files: 108
- `NPC_LOCATION_REFERENCE`: **DISCOVERED**, evidence files: 78
- `HUMAN_NAME_BOUNDARY`: **DISCOVERED**, evidence files: 174
- `TECHNICAL_ID_LEAK_SCAN`: **DISCOVERED**, evidence files: 149
- `CONTENT_VALIDATION`: **DISCOVERED**, evidence files: 134
- `CATALOG_ORDERING`: **DISCOVERED**, evidence files: 191
- `RESTART_SEMANTICS`: **DISCOVERED**, evidence files: 87
- `PRESENTATION_BOUNDARY`: **DISCOVERED**, evidence files: 136
- `SHADOW_CATALOG_SCAN`: **DISCOVERED**, evidence files: 86

## Priority candidate owner files

- `data/story_quest_definitions.py`: 21 contract groups
- `data/story_quest_hierarchy.py`: 21 contract groups
- `data/story_quest_npcs.py`: 21 contract groups
- `data/story_quests/start_path_01_10.py`: 21 contract groups
- `data/story_quests/start_path_21_30.py`: 21 contract groups
- `db_modules/__init__.py`: 21 contract groups
- `db_modules/systems_wrappers.py`: 21 contract groups
- `handlers/city.py`: 21 contract groups
- `handlers/combat.py`: 21 contract groups
- `handlers/player_interaction.py`: 21 contract groups
- `handlers/story_boss_invocation_wiring.py`: 21 contract groups
- `handlers/story_quest_hierarchy_ui.py`: 21 contract groups
- `handlers/story_quest_npc_runtime.py`: 21 contract groups
- `handlers/story_quests.py`: 21 contract groups
- `main.py`: 21 contract groups
- `systems/boss_system.py`: 21 contract groups
- `systems/player_interaction_system.py`: 21 contract groups
- `systems/simulation/progression_provider.py`: 21 contract groups
- `systems/simulation/world_progression.py`: 21 contract groups
- `systems/story_quest_item_drop_system.py`: 21 contract groups

## Mandatory next step

`patch_21_11_1a_refine_location_catalog_contract.py`

Semantic refinement must establish authoritative post-combat event ownership, immutable payload and stable key, settlement ordering, victory/terminal scope, exact-once hook behavior, failure and rollback policy, retry/restart semantics, story/contract/history/notification boundaries, presentation, simulator consumers, and duplicate/shadow hook owners before implementation.
