# Stage 21.8.8b - Resolved battle persistence parity

- Status: **PASS**
- Conclusion: **GO_TO_IMPLEMENTATION**
- Input unresolved contracts: **5**
- Remaining unresolved contracts: **0**
- Implementation authorized: **True**
- Runtime integration authorized: **False**
- Manual game check: **NOT_REQUIRED**

## Resolution principle

The authoritative V1 parity boundary is the narrow persisted PvE encounter lifecycle marker. V1 supports begin/read, exactly-once terminal claim, expiry and restart cleanup. The evidence does not support a complete resumable battle aggregate.

Negative classifications are bounded absence conclusions, not universal claims. They apply only to the audited V1 Python inventory and the exact identifier families recorded in the machine report.

## Resolved contracts

- `FULL_BATTLE_SNAPSHOT_SAVE`: **NOT_IMPLEMENTED_IN_V1** - Do not claim or implement complete per-action battle snapshot parity in Stage 21.8.8.
- `RESUME_EXACT_TURN_STATE`: **NOT_IMPLEMENTED_IN_V1** - Restart recovery may reproduce V1 encounter expiry/cleanup only; it must not restore exact turn, cooldown, effect, or RNG state.
- `STALE_ACTION_REVISION_TOKEN`: **V1_ACTIVE_ENCOUNTER_AND_TERMINAL_CLAIM_ONLY** - Protect stale terminal actions through active encounter identity and exactly-once terminal claim; do not invent a revision/version token.
- `SHARED_PVE_PVP_BOSS_REPOSITORY`: **NOT_IMPLEMENTED_IN_V1** - Keep Stage 21.8.8 bounded to the audited PvE encounter lifecycle; no unified PvE/PvP/boss repository is authorized.
- `SIMULATOR_PERSISTENCE_PARITY`: **NOT_IMPLEMENTED_IN_V1** - Simulator snapshot terminology is outside runtime persistence parity and must not authorize runtime save/resume behavior.

## Authorized implementation boundary

Model: `V1_PVE_ENCOUNTER_LIFECYCLE_MARKER`

Allowed:
- begin an active PvE encounter marker
- read the active encounter marker
- claim one terminal outcome exactly once
- find and expire stale active encounters
- recover after restart through V1-equivalent expiry/cleanup

Forbidden:
- full mutable battle aggregate snapshot persistence
- exact turn/cooldown/effect/RNG resume
- invented battle revision tokens
- unified PvE/PvP/boss repository semantics
- simulator-to-runtime persistence parity
- Telegram/runtime wiring in this implementation stage

## Safety

V1 was inspected only as source text/AST. SQLite was not opened. `game.db-wal` and `game.db-shm` were not deleted, cleared, modified, or used for rollback.

## Next patch

`patch_21_8_8c_implement_battle_persistence.py`
