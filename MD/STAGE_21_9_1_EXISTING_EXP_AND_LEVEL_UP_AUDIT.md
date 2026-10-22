# Stage 21.9.1 - Existing V1 EXP and level-up progression audit

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

This is discovery evidence only. It does not authorize an EXP/level-up implementation or reinterpret V1 behavior.
Runtime/Telegram dispatch and production persistence remain unconnected.

## Contract discovery matrix

- `EXP_OWNER`: **DISCOVERED**, evidence files: 12
- `SMOOTH_EXP_CURVE`: **DISCOVERED**, evidence files: 1
- `RESIDUAL_EXP`: **DISCOVERED**, evidence files: 42
- `MULTI_LEVEL_UP`: **DISCOVERED**, evidence files: 45
- `LEVEL_CAP`: **DISCOVERED**, evidence files: 11
- `LEVEL_UP_POINTS`: **DISCOVERED**, evidence files: 8
- `PLAYER_STATE_MUTATION`: **DISCOVERED**, evidence files: 62
- `REWARD_EXP_PRODUCERS`: **DISCOVERED**, evidence files: 11
- `PROFILE_PRESENTATION`: **DISCOVERED**, evidence files: 179
- `DEV_RESET_AND_CREATION`: **DISCOVERED**, evidence files: 179
- `SIMULATOR_PARITY`: **DISCOVERED**, evidence files: 65
- `CONFIGURATION_OWNER`: **DISCOVERED**, evidence files: 11
- `IDEMPOTENCY_AND_ATOMICITY`: **DISCOVERED**, evidence files: 80

## Priority candidate owner files

- `handlers/combat.py`: 11 contract groups
- `data/player_progression.py`: 10 contract groups
- `systems/contract_system.py`: 10 contract groups
- `systems/player_system.py`: 9 contract groups
- `systems/rune_system.py`: 9 contract groups
- `systems/simulation/meta_progression.py`: 9 contract groups
- `systems/guild_system.py`: 8 contract groups
- `db_modules/dev_compat.py`: 7 contract groups
- `handlers/dev.py`: 7 contract groups
- `handlers/refine.py`: 7 contract groups
- `systems/level_up_reward_system.py`: 7 contract groups
- `systems/player_interaction_system.py`: 7 contract groups
- `systems/refine_system.py`: 7 contract groups
- `systems/story_quest_system.py`: 7 contract groups
- `db_modules/player.py`: 6 contract groups
- `handlers/contracts.py`: 6 contract groups
- `systems/equipment_system.py`: 6 contract groups
- `systems/fatigue_artifact_system.py`: 6 contract groups
- `systems/notifications.py`: 6 contract groups
- `systems/reward_system.py`: 6 contract groups

## Mandatory next step

`patch_21_9_1a_refine_exp_and_level_up_contract.py`

Semantic refinement must establish authoritative EXP owners, exact curve inputs, residual and multi-level semantics, level-cap behavior, point awards, mutation ordering, and producer/consumer boundaries before any implementation.
