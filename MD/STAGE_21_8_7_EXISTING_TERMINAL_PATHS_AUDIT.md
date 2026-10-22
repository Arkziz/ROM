# Stage 21.8.7 - Existing V1 terminal battle paths audit

- Status: **PASS**
- Conclusion: **GO_TO_SEMANTIC_REFINEMENT**
- V1 Python files: **275**
- Candidate symbols: **3612**
- Contract rows: **17**
- Review-required rows: **0**
- Production code changed: **False**
- Database opened: **False**
- V1 WAL/SHM manipulated: **False**
- Manual game check: **NOT_REQUIRED**

## Boundary

This is discovery evidence only. It does not authorize an Effect Engine terminal-path implementation or reinterpret V1 behavior.
Runtime/Telegram dispatch and production persistence remain unconnected.

## Contract discovery matrix

- `TERMINAL_STATE_OWNERS`: **DISCOVERED**, evidence files: 54
- `VICTORY_PATH`: **DISCOVERED**, evidence files: 22
- `DEFEAT_PATH`: **DISCOVERED**, evidence files: 13
- `ESCAPE_PATH`: **DISCOVERED**, evidence files: 10
- `SETTLEMENT_OWNER`: **DISCOVERED**, evidence files: 159
- `EXACTLY_ONCE_GUARDS`: **DISCOVERED**, evidence files: 83
- `POST_TERMINAL_ACTION_GUARD`: **DISCOVERED**, evidence files: 31
- `DUPLICATE_DOMAIN_EVENTS`: **DISCOVERED**, evidence files: 162
- `DUPLICATE_MESSAGES`: **DISCOVERED**, evidence files: 94
- `REWARD_AND_LOOT_ORDERING`: **DISCOVERED**, evidence files: 182
- `DEATH_AND_DURABILITY`: **DISCOVERED**, evidence files: 66
- `QUEST_GUILD_EVENT_CONSUMERS`: **DISCOVERED**, evidence files: 167
- `PVE_CONSUMERS`: **DISCOVERED**, evidence files: 76
- `PVP_CONSUMERS`: **DISCOVERED**, evidence files: 46
- `BOSS_CONSUMERS`: **DISCOVERED**, evidence files: 93
- `SIMULATOR_CONSUMERS`: **DISCOVERED**, evidence files: 67
- `FAILURE_AND_RECOVERY`: **DISCOVERED**, evidence files: 111

## Priority candidate owner files

- `handlers/combat.py`: 16 contract groups
- `systems/pve_auto_escape_system.py`: 15 contract groups
- `systems/story_quest_boss_completion_system.py`: 14 contract groups
- `db_modules/__init__.py`: 13 contract groups
- `handlers/story_quests.py`: 13 contract groups
- `systems/equipment_system.py`: 13 contract groups
- `systems/guild_system.py`: 13 contract groups
- `systems/simulation/world_progression.py`: 13 contract groups
- `handlers/event_ui.py`: 12 contract groups
- `handlers/player_interaction.py`: 12 contract groups
- `main.py`: 12 contract groups
- `systems/player_interaction_system.py`: 12 contract groups
- `systems/profile_history_system.py`: 12 contract groups
- `systems/pvp_round_engine.py`: 12 contract groups
- `systems/simulation/class_progression.py`: 12 contract groups
- `systems/simulation/meta_progression.py`: 12 contract groups
- `db_modules/equipment.py`: 11 contract groups
- `handlers/city.py`: 11 contract groups
- `systems/reward_system.py`: 11 contract groups
- `systems/rune_system.py`: 11 contract groups

## Mandatory next step

`patch_21_8_7a_refine_terminal_paths_contract.py`

Semantic refinement must establish authoritative owners and exact victory/defeat/escape/settlement/idempotency ordering before any mutation implementation.
