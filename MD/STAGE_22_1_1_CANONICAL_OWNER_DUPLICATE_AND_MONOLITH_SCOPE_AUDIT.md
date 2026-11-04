# Stage 22.1.1 - Canonical Owner, Duplicate and Monolith Scope Audit

- Status: **PASS_READ_ONLY**
- Parent: `56c18339c28df4f9e89c17d933572982e51aec79`
- Production Python files: **228**
- Files with same-file duplicates: **18**
- Duplicate module-level symbols: **123**
- Cross-file key-symbol collisions: **209**
- Monolith candidates >=500 lines: **37**
- Critical monoliths >=1200 lines: **15**
- `main.py` lines: **337**

## Safety decision

No deletion or extraction is authorized by this audit. Python last-definition behavior proves shadowing only; runtime ownership requires focused call-path and registration reconciliation.

## Highest-priority monoliths

| File | Lines | Severity | Duplicate symbols | Registrations |
|---|---:|---|---:|---:|
| `handlers/inventory.py` | 7858 | CRITICAL | 9 | 10 |
| `systems/auction_house_system.py` | 5545 | CRITICAL | 12 | 0 |
| `handlers/auction_house.py` | 5207 | CRITICAL | 19 | 84 |
| `systems/equipment_system.py` | 4026 | CRITICAL | 27 | 0 |
| `handlers/combat.py` | 3842 | CRITICAL | 0 | 17 |
| `handlers/guild.py` | 3017 | CRITICAL | 17 | 32 |
| `systems/guild_system.py` | 2833 | CRITICAL | 3 | 0 |
| `systems/player_interaction_system.py` | 2383 | CRITICAL | 0 | 0 |
| `handlers/player_interaction.py` | 2167 | CRITICAL | 0 | 47 |
| `systems/player_system.py` | 2160 | CRITICAL | 7 | 0 |
| `db_modules/dev_compat.py` | 1635 | CRITICAL | 0 | 0 |
| `systems/rune_system.py` | 1566 | CRITICAL | 4 | 0 |
| `systems/drop_system.py` | 1424 | CRITICAL | 0 | 0 |
| `handlers/city.py` | 1397 | CRITICAL | 10 | 43 |
| `db_modules/generated_equipment.py` | 1298 | CRITICAL | 0 | 0 |

## Same-file duplicate inventory

| File | Duplicate symbols |
|---|---:|
| `handlers/auction_house.py` | 19 |
| `handlers/blacksmith.py` | 1 |
| `handlers/blacksmith_repair_confirm.py` | 2 |
| `handlers/city.py` | 10 |
| `handlers/dev.py` | 1 |
| `handlers/guild.py` | 17 |
| `handlers/inventory.py` | 9 |
| `handlers/runes.py` | 1 |
| `handlers/start.py` | 3 |
| `handlers/story_quest_npc_runtime.py` | 2 |
| `systems/auction_house_system.py` | 12 |
| `systems/character_system.py` | 2 |
| `systems/equipment_system.py` | 27 |
| `systems/guild_system.py` | 3 |
| `systems/notifications.py` | 2 |
| `systems/player_system.py` | 7 |
| `systems/potion_system.py` | 1 |
| `systems/rune_system.py` | 4 |

## Decision

**RECONCILE_22_1_2_CANONICAL_OWNER_RUNTIME_CALL_PATHS_AND_REGISTRATIONS**

- Production mutations: **NONE**
- DB/WAL/SHM mutations: **NONE**
- Manual game check: **NOT_REQUIRED**
