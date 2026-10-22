# Stage 21.8.6 - Existing V1 status effects audit

- Status: **PASS**
- Conclusion: **GO_TO_SEMANTIC_REFINEMENT**
- V1 Python files: **275**
- Candidate symbols: **3612**
- Contract rows: **15**
- Review-required rows: **0**
- Production code changed: **False**
- Database opened: **False**
- V1 WAL/SHM manipulated: **False**
- Manual game check: **NOT_REQUIRED**

## Boundary

This is discovery evidence only. It does not authorize an Effect Engine implementation or reinterpret V1 behavior.
Runtime/Telegram dispatch and production persistence remain unconnected.

## Contract discovery matrix

- `EFFECT_IDENTITY_AND_TYPES`: **DISCOVERED**, evidence files: 55
- `APPLICATION_OWNER`: **DISCOVERED**, evidence files: 37
- `REMOVAL_AND_CLEANUP`: **DISCOVERED**, evidence files: 47
- `DURATION_AND_TURN_TIMING`: **DISCOVERED**, evidence files: 76
- `TICK_ORDERING`: **DISCOVERED**, evidence files: 21
- `STACK_REFRESH_REPLACE`: **DISCOVERED**, evidence files: 89
- `RESIST_IMMUNITY_COMPATIBILITY`: **DISCOVERED**, evidence files: 12
- `PVE_CONSUMERS`: **DISCOVERED**, evidence files: 71
- `PVP_CONSUMERS`: **DISCOVERED**, evidence files: 36
- `BOSS_CONSUMERS`: **DISCOVERED**, evidence files: 38
- `SIMULATOR_CONSUMERS`: **DISCOVERED**, evidence files: 48
- `PRIEST_HEAL_1_PLUS_2`: **DISCOVERED**, evidence files: 42
- `PERSISTENCE_AND_RESTART`: **DISCOVERED**, evidence files: 91
- `PRESENTATION_CONSUMERS`: **DISCOVERED**, evidence files: 106
- `FAILURE_NO_PARTIAL_MUTATION`: **DISCOVERED**, evidence files: 135

## Priority candidate owner files

- `handlers/combat.py`: 12 contract groups
- `systems/boss_system.py`: 12 contract groups
- `handlers/city.py`: 10 contract groups
- `systems/pvp_policy_metrics_audit.py`: 10 contract groups
- `db_modules/shop.py`: 9 contract groups
- `handlers/player_interaction.py`: 9 contract groups
- `systems/equipment_system.py`: 9 contract groups
- `systems/player_interaction_system.py`: 9 contract groups
- `systems/pvp_round_engine.py`: 9 contract groups
- `systems/rune_system.py`: 9 contract groups
- `systems/timed_exp_bonus_system.py`: 9 contract groups
- `db_modules/__init__.py`: 8 contract groups
- `db_modules/dev_compat.py`: 8 contract groups
- `handlers/pvp_round_ui.py`: 8 contract groups
- `systems/auction_house_system.py`: 8 contract groups
- `systems/character_system.py`: 8 contract groups
- `systems/pvp_combat_log.py`: 8 contract groups
- `systems/pvp_production_calibration.py`: 8 contract groups
- `systems/pvp_system.py`: 8 contract groups
- `systems/simulation/pve_battle.py`: 8 contract groups

## Mandatory next step

`patch_21_8_6a_refine_status_effects_contract.py`

Semantic refinement must establish authoritative owners and exact duration/tick/stack/cleanup ordering before any mutation implementation.
