# Stage 21.8.1a — Refined V1 battle aggregate contract

- Status: **PASS**
- Conclusion: **GO_TO_IMPLEMENTATION**
- Explicit owner files: **13**
- Semantic rows: **24**
- Unresolved rows: **0**
- Database opened: **False**
- Production changed: **False**
- Manual game check: **NOT_REQUIRED**

## Authority

- `handlers/combat.py`: authoritative V1 PvE runtime orchestration/state path, not the future pure V2 aggregate owner.
- `systems/pvp_system.py`: authoritative V1 persisted PvP lifecycle and completion owner.
- `systems/pvp_round_engine.py`: deterministic PvP round resolver; `systems/pvp_battle_factory.py`: participant snapshot factory.
- reward settlement, presentation, boss, escape and simulator modules remain consumers or adjacent boundaries.

## Semantic matrix

- `PVE_RUNTIME_STATE_OWNER`: **V1_CONFIRMED**
- `PVP_PERSISTED_AGGREGATE_OWNER`: **V1_CONFIRMED**
- `PVP_ROUND_DETERMINISTIC_OWNER`: **V1_CONFIRMED**
- `PVP_FACTORY_SNAPSHOT_OWNER`: **V1_CONFIRMED**
- `PVE_AND_PVP_IDENTITIES_DISTINCT`: **V1_CONFIRMED**
- `ACTOR_SNAPSHOT_BOUNDARY`: **V1_CONFIRMED**
- `CURRENT_RESOURCE_STATE`: **V1_CONFIRMED**
- `TURN_AND_ROUND_ORDER`: **V1_CONFIRMED**
- `ACTION_INPUT_BOUNDARY`: **V1_CONFIRMED**
- `ACTION_RESULT_BOUNDARY`: **V1_CONFIRMED**
- `PVP_RESOLUTION_CLAIM`: **V1_CONFIRMED**
- `PVP_TERMINAL_COMPLETION`: **V1_CONFIRMED**
- `PVE_VICTORY_COMPLETION`: **V1_CONFIRMED**
- `PVE_DEFEAT_COMPLETION`: **V1_CONFIRMED**
- `PVE_ESCAPE_COMPLETION`: **V1_CONFIRMED**
- `TERMINAL_STATE_SINGLE_CLAIM`: **V1_CONFIRMED**
- `PERSISTENCE_RESTART_BOUNDARY`: **V1_CONFIRMED**
- `PRESENTATION_IS_CONSUMER`: **V1_CONFIRMED**
- `REWARD_SETTLEMENT_OUTSIDE_AGGREGATE`: **V1_CONFIRMED**
- `SIMULATOR_REUSES_ACTOR_CONTRACT`: **V1_CONFIRMED**
- `BOSS_IS_ENCOUNTER_CONSUMER`: **V1_CONFIRMED**
- `NO_PRESENTATION_TEXT_IDENTITY`: **V1_CONFIRMED**
- `FAILURE_SEMANTICS`: **V1_CONFIRMED**
- `PARALLEL_PATHS_CLASSIFIED`: **V1_CONFIRMED**

## Boundary

No implementation is permitted unless every semantic row is resolved. Exact aggregate fields, transition order and completion semantics remain bound to the V1 owner evidence and must be consumed without reinterpretation by the implementation patch.

## Suggested next patch

`patch_21_8_1b_implement_battle_aggregate.py`
