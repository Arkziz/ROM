# Stage 21.8.8a - Refined V1 battle persistence contract

- Status: **PASS**
- Conclusion: **REVIEW_REQUIRED**
- Semantic rows: **13**
- V1-confirmed rows: **8**
- Unresolved rows: **5**
- Database opened: **False**
- Production code changed: **False**
- Runtime/Telegram dispatch connected: **False**
- Production persistence connected: **False**
- Manual game check: **NOT_REQUIRED**

## Authority decision

V1 persists a narrow PvE encounter lifecycle marker through `systems/pve_auto_escape_system.py` and consumes it from `handlers/combat.py`. This evidence supports active-encounter read, terminal claim, expiry-once and restart cleanup. It does not prove persistence and exact resumption of the complete mutable battle aggregate.

PvP completion, boss/story consumers and simulator snapshots remain separate evidence boundaries. They are not treated as a shared battle repository or as proof of resumable-turn parity.

## Semantic matrix

- `V1_PERSISTENCE_OWNER`: **V1_CONFIRMED** - V1 persists a PvE encounter lifecycle marker.
- `ACTIVE_ENCOUNTER_READ`: **V1_CONFIRMED** - V1 reads the active persisted encounter marker.
- `TERMINAL_CLAIM`: **V1_CONFIRMED** - Terminal claim is guarded by the persisted active encounter.
- `RESTART_RECOVERY`: **V1_CONFIRMED** - Restart recovery expires or closes persisted PvE encounter markers.
- `EXPIRE_ONCE`: **V1_CONFIRMED** - Expiry uses a claim-once path rather than duplicate terminal mutation.
- `PVE_CONSUMER`: **V1_CONFIRMED** - PvE handler consumes begin/read encounter operations.
- `VICTORY_TERMINAL_CONSUMER`: **V1_CONFIRMED** - Victory consumes the terminal claim boundary.
- `PVP_TERMINAL_PERSISTENCE`: **V1_CONFIRMED** - PvP has a separate completion/persistence boundary and is not evidence of shared PvE save/resume.
- `FULL_BATTLE_SNAPSHOT_SAVE`: **UNRESOLVED** - No authoritative V1 owner proves persistence of the complete mutable battle aggregate after every action.
- `RESUME_EXACT_TURN_STATE`: **UNRESOLVED** - No authoritative V1 owner proves exact restart restoration of turn, cooldowns, effects and RNG position.
- `STALE_ACTION_REVISION_TOKEN`: **UNRESOLVED** - Encounter activity and terminal claims exist, but a canonical action revision/version token is not proven.
- `SHARED_PVE_PVP_BOSS_REPOSITORY`: **UNRESOLVED** - V1 evidence shows separate consumers; it does not prove one shared battle repository contract.
- `SIMULATOR_PERSISTENCE_PARITY`: **UNRESOLVED** - Simulator snapshot terminology does not prove runtime battle-persistence parity.

## Mutation gate

Battle-persistence implementation is **not authorized** while any semantic row remains `UNRESOLVED`. The next patch must resolve only the listed parity gaps from V1 evidence or formally classify them as not implemented in V1. It must not invent full-battle save/resume, RNG restoration, action versions, shared PvE/PvP storage, or simulator persistence.

Runtime/Telegram dispatch and production persistence remain unconnected. This stage does not claim `RUNTIME_READY`.

## Safety

V1 modules were parsed only as text/AST. SQLite was not opened. `game.db-wal` and `game.db-shm` were not deleted, cleared, modified, or used for rollback.

## Manual game check

`NOT_REQUIRED`. This is a read-only semantic refinement with no gameplay dispatch.

## Suggested next patch

`patch_21_8_8b_resolve_battle_persistence_parity.py`
