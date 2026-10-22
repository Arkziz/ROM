# Stage 21.9.6 - Existing V1 post-combat hooks audit

- Status: **PASS**
- Conclusion: **GO_TO_SEMANTIC_REFINEMENT**
- V1 Python files: **275**
- Candidate symbols: **3612**
- Contract rows: **24**
- Review-required rows: **0**
- Production code changed: **False**
- Database opened: **False**
- V1 WAL/SHM manipulated: **False**
- Manual game check: **NOT_REQUIRED**

## Boundary

This is discovery evidence only. It does not authorize an post-combat hooks implementation or reinterpret V1 behavior.
Runtime/Telegram dispatch and production persistence remain unconnected.

## Contract discovery matrix

- `VICTORY_HOOK_ENTRYPOINTS`: **DISCOVERED**, evidence files: 25
- `STORY_QUEST_PROGRESS`: **DISCOVERED**, evidence files: 146
- `ORDINARY_QUEST_PROGRESS`: **DISCOVERED**, evidence files: 123
- `GUILD_CONTRACT_PROGRESS`: **DISCOVERED**, evidence files: 143
- `BATTLE_HISTORY`: **DISCOVERED**, evidence files: 93
- `REWARD_HISTORY`: **DISCOVERED**, evidence files: 144
- `CHRONICLES`: **DISCOVERED**, evidence files: 104
- `ACHIEVEMENT_HOOKS`: **DISCOVERED**, evidence files: 76
- `NOTIFICATION_HOOKS`: **DISCOVERED**, evidence files: 93
- `EVENT_POST_COMBAT_HOOKS`: **DISCOVERED**, evidence files: 116
- `NORMAL_ELITE_BOSS_SCOPE`: **DISCOVERED**, evidence files: 92
- `VICTORY_TERMINAL_SCOPE`: **DISCOVERED**, evidence files: 72
- `SETTLEMENT_ORDER`: **DISCOVERED**, evidence files: 131
- `EXACT_ONCE_DUPLICATE_PROTECTION`: **DISCOVERED**, evidence files: 75
- `HOOK_FAILURE_POLICY`: **DISCOVERED**, evidence files: 169
- `ROLLBACK_BOUNDARY`: **DISCOVERED**, evidence files: 66
- `POST_COMMIT_DISPATCH`: **DISCOVERED**, evidence files: 93
- `RETRY_RESTART_SEMANTICS`: **DISCOVERED**, evidence files: 51
- `STABLE_EVENT_KEY`: **DISCOVERED**, evidence files: 29
- `IMMUTABLE_EVENT_PAYLOAD`: **DISCOVERED**, evidence files: 136
- `NO_DUPLICATE_SETTLEMENT`: **DISCOVERED**, evidence files: 159
- `PRESENTATION_BOUNDARY`: **DISCOVERED**, evidence files: 168
- `SIMULATOR_DEV_CONSUMERS`: **DISCOVERED**, evidence files: 64
- `DUPLICATE_SHADOW_HOOK_OWNERS`: **DISCOVERED**, evidence files: 12

## Priority candidate owner files

- `handlers/combat.py`: 24 contract groups
- `db_modules/__init__.py`: 23 contract groups
- `db_modules/systems_wrappers.py`: 21 contract groups
- `systems/guild_system.py`: 21 contract groups
- `handlers/story_quests.py`: 20 contract groups
- `systems/player_interaction_system.py`: 20 contract groups
- `systems/reward_system.py`: 20 contract groups
- `db_modules/dev_compat.py`: 19 contract groups
- `db_modules/story_quests.py`: 19 contract groups
- `systems/drop_system.py`: 19 contract groups
- `systems/simulation/world_progression.py`: 19 contract groups
- `systems/auction_house_system.py`: 18 contract groups
- `systems/level_up_reward_system.py`: 18 contract groups
- `systems/pve_auto_escape_system.py`: 18 contract groups
- `systems/pvp_system.py`: 18 contract groups
- `systems/rune_system.py`: 18 contract groups
- `systems/simulation/economic_ledger.py`: 18 contract groups
- `systems/story_quest_system.py`: 18 contract groups
- `handlers/auction_house.py`: 17 contract groups
- `handlers/dev.py`: 17 contract groups

## Mandatory next step

`patch_21_9_6a_refine_post_combat_hooks_contract.py`

Semantic refinement must establish authoritative post-combat event ownership, immutable payload and stable key, settlement ordering, victory/terminal scope, exact-once hook behavior, failure and rollback policy, retry/restart semantics, story/contract/history/notification boundaries, presentation, simulator consumers, and duplicate/shadow hook owners before implementation.
