# Stage 21.8.7a - Refined terminal paths contract

- Status: **PASS**
- Conclusion: **REVIEW_REQUIRED**
- V1-confirmed rows: **18**
- Review-required rows: **7**
- Production changed: **False**
- Database opened: **False**
- Manual game check: **NOT_REQUIRED**

## Authoritative context owners

- `pve`: `handlers/combat.py`
- `boss`: `systems/boss_system.py`
- `pvp`: `systems/pvp_round_engine.py`
- `simulator`: `systems/simulation/pve_battle.py`
- `pve_terminal_claim`: `systems/pve_auto_escape_system.py`
- `pvp_completion`: `systems/pvp_completion_service.py`

## Contract matrix

- `PVE_VICTORY_OWNER`: **V1_CONFIRMED** - Canonical manual PvE victory orchestration candidate.
- `PVE_VICTORY_PRE_FINALIZE`: **V1_CONFIRMED** - PvE combat state is finalized before victory settlement/presentation.
- `PVE_VICTORY_HOT_COMPENSATION`: **V1_CONFIRMED** - Victory has an explicit turn-start HoT compensation boundary.
- `PVE_VICTORY_PRESENTATION`: **V1_CONFIRMED** - Victory text construction is separate from terminal mutation.
- `PVE_VICTORY_EVENT_DROP_PRESENTATION`: **V1_CONFIRMED** - Event-drop victory messages are a separate presentation consumer.
- `PVE_TERMINAL_CLAIM`: **V1_CONFIRMED** - Persistent PvE terminal claim candidate for exactly-once arbitration.
- `PVE_ENCOUNTER_BEGIN`: **V1_CONFIRMED** - PvE encounter lifecycle starts in the auto-escape subsystem.
- `PVE_ACTIVE_ENCOUNTER_LOOKUP`: **V1_CONFIRMED** - Active encounter lookup participates in post-terminal guarding.
- `PVE_AUTO_ESCAPE_EXPIRATION`: **V1_CONFIRMED** - Auto-escape expiry is an independent terminal producer.
- `PVE_RESTART_RECOVERY`: **V1_CONFIRMED** - Startup recovery is an independent terminal/recovery path.
- `PVE_VICTORY_REWARD`: **V1_CONFIRMED** - Victory reward calculation/mutation has a dedicated owner.
- `PVE_ENEMY_DROPS`: **V1_CONFIRMED** - Enemy drops have a dedicated owner separate from victory orchestration.
- `PVP_ROUND_TERMINAL`: **V1_CONFIRMED** - PvP round engine creates terminal round output.
- `PVP_COMPLETE_ONCE`: **V1_CONFIRMED** - PvP exposes an explicit exactly-once completion service.
- `PVP_TERMINAL_PRESENTATION`: **V1_CONFIRMED** - PvP terminal presentation is separated from completion.
- `PVP_TERMINAL_CLEANUP`: **V1_CONFIRMED** - PvP terminal session cleanup has a dedicated owner.
- `STORY_BOSS_COMPLETION`: **V1_CONFIRMED** - Story boss completion is a downstream victory consumer.
- `EVENT_VICTORY_STATISTICS`: **V1_CONFIRMED** - Event statistics are a downstream victory consumer.
- `SINGLE_PVE_TERMINAL_OWNER`: **REVIEW_REQUIRED** - Evidence must establish whether claim_pve_terminal arbitrates manual victory, defeat, manual escape, auto-escape and restart recovery.
- `PVE_DEFEAT_EXACT_PATH`: **REVIEW_REQUIRED** - The exact defeat symbol, ordering and settlement boundary require focused resolution.
- `PVE_MANUAL_ESCAPE_EXACT_PATH`: **REVIEW_REQUIRED** - The exact manual escape callback and its relationship to terminal claim require focused resolution.
- `PVE_SETTLEMENT_ORDERING`: **REVIEW_REQUIRED** - EXP, gold, loot, durability, quest, guild, event and story completion ordering is distributed.
- `DUPLICATE_MESSAGES_EVENTS`: **REVIEW_REQUIRED** - Exactly-once domain events and exactly-once presentation messages require separate explicit contracts.
- `POST_TERMINAL_ACTION_GUARD`: **REVIEW_REQUIRED** - The canonical guard against actions after terminal settlement is not yet proven.
- `PVE_PVP_BOSS_SIMULATOR_PARITY`: **REVIEW_REQUIRED** - Terminal semantics are context-specific and must not be unified without V1 evidence.

## Unresolved contracts

- `SINGLE_PVE_TERMINAL_OWNER`
- `PVE_DEFEAT_EXACT_PATH`
- `PVE_MANUAL_ESCAPE_EXACT_PATH`
- `PVE_SETTLEMENT_ORDERING`
- `DUPLICATE_MESSAGES_EVENTS`
- `POST_TERMINAL_ACTION_GUARD`
- `PVE_PVP_BOSS_SIMULATOR_PARITY`

Implementation remains unauthorized until terminal ownership, settlement ordering, idempotency and duplicate-output contracts are resolved from V1 evidence.
