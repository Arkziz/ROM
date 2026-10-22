# Stage 21.8.8 - Existing V1 battle persistence and restart recovery audit

- Status: **PASS**
- Conclusion: **GO_TO_SEMANTIC_REFINEMENT**
- V1 Python files: **275**
- Candidate symbols: **3612**
- Contract rows: **13**
- Review-required rows: **0**
- Production code changed: **False**
- Database opened: **False**
- V1 WAL/SHM manipulated: **False**
- Manual game check: **NOT_REQUIRED**

## Boundary

This is discovery evidence only. It does not authorize an Effect Engine terminal-path implementation or reinterpret V1 behavior.
Runtime/Telegram dispatch and production persistence remain unconnected.

## Contract discovery matrix

- `V1_PERSISTENCE_OWNER`: **DISCOVERED**, evidence files: 3
- `SAVE_RESUME`: **DISCOVERED**, evidence files: 39
- `RESTART_RECOVERY`: **DISCOVERED**, evidence files: 26
- `STALE_ACTION_PROTECTION`: **DISCOVERED**, evidence files: 87
- `SNAPSHOT_INTEGRITY`: **DISCOVERED**, evidence files: 1
- `TERMINAL_INTERACTION`: **DISCOVERED**, evidence files: 33
- `IDEMPOTENCY`: **DISCOVERED**, evidence files: 50
- `FAILURE_ATOMICITY`: **DISCOVERED**, evidence files: 107
- `REPOSITORY_UOW`: **DISCOVERED**, evidence files: 30
- `PVE_CONSUMERS`: **DISCOVERED**, evidence files: 3
- `PVP_PERSISTENCE`: **DISCOVERED**, evidence files: 74
- `BOSS_STORY_CONSUMERS`: **DISCOVERED**, evidence files: 97
- `SIMULATOR_BOUNDARY`: **DISCOVERED**, evidence files: 75

## Priority candidate owner files

- `handlers/combat.py`: 11 contract groups
- `systems/pve_auto_escape_system.py`: 10 contract groups
- `db_modules/__init__.py`: 9 contract groups
- `systems/auction_house_system.py`: 9 contract groups
- `systems/player_interaction_system.py`: 9 contract groups
- `handlers/story_quests.py`: 8 contract groups
- `systems/pvp_completion_service.py`: 8 contract groups
- `systems/pvp_system.py`: 8 contract groups
- `systems/story_quest_system.py`: 8 contract groups
- `db_modules/systems_wrappers.py`: 7 contract groups
- `handlers/player_interaction.py`: 7 contract groups
- `main.py`: 7 contract groups
- `systems/guild_system.py`: 7 contract groups
- `systems/story_quest_npc_acceptance_system.py`: 7 contract groups
- `systems/world_chronicle_system.py`: 7 contract groups
- `data/guild_resource_policy.py`: 6 contract groups
- `db_modules/story_quests.py`: 6 contract groups
- `handlers/auction_house.py`: 6 contract groups
- `handlers/pvp_interaction.py`: 6 contract groups
- `systems/boss_system.py`: 6 contract groups

## Mandatory next step

`patch_21_8_8a_refine_battle_persistence_contract.py`

Semantic refinement must establish authoritative owners and exact save/resume/restart/stale-action/idempotency ordering before any mutation implementation.
