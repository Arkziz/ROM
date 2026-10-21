# Stage 21.8.1 — Existing V1 battle aggregate audit

- Status: **PASS**
- Conclusion: **GO_TO_SEMANTIC_REFINEMENT**
- V1 Python files scanned: **275**
- Contract rows: **24**
- Unresolved contracts: **0**
- Operational symbols: **3122**
- Runtime mutation: **False**
- Database opened: **False**
- Manual game check: **NOT_REQUIRED**

## Scope

Read-only static evidence for the V1 battle state aggregate, actor snapshots, current resources, turn ordering, action inputs/results, deterministic transitions, terminal states, domain events, serialization, consumer boundaries and duplicate completion paths.

## Contract matrix

- `BATTLE_AGGREGATE_IDENTITY`: **EVIDENCE_FOUND** (12 files, 12 matches)
- `ACTOR_IDENTITY`: **EVIDENCE_FOUND** (123 files, 125 matches)
- `PLAYER_SNAPSHOT`: **EVIDENCE_FOUND** (63 files, 105 matches)
- `ENEMY_SNAPSHOT`: **EVIDENCE_FOUND** (47 files, 62 matches)
- `CURRENT_RESOURCES`: **EVIDENCE_FOUND** (71 files, 102 matches)
- `TURN_ORDER`: **EVIDENCE_FOUND** (256 files, 406 matches)
- `BATTLE_STATUS`: **EVIDENCE_FOUND** (93 files, 118 matches)
- `TERMINAL_STATE`: **EVIDENCE_FOUND** (66 files, 84 matches)
- `ACTION_INPUT`: **EVIDENCE_FOUND** (155 files, 208 matches)
- `ACTION_RESULT`: **EVIDENCE_FOUND** (139 files, 231 matches)
- `DETERMINISTIC_TRANSITION`: **EVIDENCE_FOUND** (18 files, 21 matches)
- `PURE_AGGREGATE_BOUNDARY`: **EVIDENCE_FOUND** (140 files, 189 matches)
- `NO_DIRECT_SQL`: **EVIDENCE_FOUND** (91 files, 215 matches)
- `NO_REWARD_SETTLEMENT`: **EVIDENCE_FOUND** (159 files, 282 matches)
- `NO_PRESENTATION_TEXT_ID`: **EVIDENCE_FOUND** (163 files, 284 matches)
- `DOMAIN_EVENT_OUTPUT`: **EVIDENCE_FOUND** (91 files, 92 matches)
- `FAILURE_REASON`: **EVIDENCE_FOUND** (161 files, 250 matches)
- `IDEMPOTENCY`: **EVIDENCE_FOUND** (47 files, 61 matches)
- `RESTART_SERIALIZATION`: **EVIDENCE_FOUND** (64 files, 80 matches)
- `PVE_CONSUMER`: **EVIDENCE_FOUND** (117 files, 168 matches)
- `PVP_CONSUMER`: **EVIDENCE_FOUND** (81 files, 126 matches)
- `SIMULATOR_CONSUMER`: **EVIDENCE_FOUND** (65 files, 90 matches)
- `SINGLE_COMPLETION_PATH`: **EVIDENCE_FOUND** (31 files, 31 matches)
- `DUPLICATE_AGGREGATE_PATHS`: **EVIDENCE_FOUND** (1 files, 1 matches)

## Priority owner candidates

- `handlers/combat.py`: 23 contracts
- `systems/pvp_system.py`: 21 contracts
- `systems/player_interaction_system.py`: 19 contracts
- `systems/boss_system.py`: 18 contracts
- `handlers/player_interaction.py`: 17 contracts
- `systems/pvp_production_calibration.py`: 17 contracts
- `systems/pvp_real_actor_state_replay.py`: 17 contracts
- `systems/rune_system.py`: 17 contracts
- `db_modules/systems_wrappers.py`: 16 contracts
- `systems/player_system.py`: 16 contracts
- `systems/pvp_anti_stall_survivability_candidate_sandbox.py`: 16 contracts
- `systems/pvp_balance_simulator.py`: 16 contracts
- `systems/pvp_policy_metrics_audit.py`: 16 contracts
- `systems/pvp_round_engine.py`: 16 contracts
- `systems/simulation/world_progression.py`: 16 contracts

## Boundary

Broad discovery evidence is not yet the final semantic policy. Mutation remains blocked until a dedicated semantic refinement confirms authoritative owners, exact formulas, ordering, atomicity and superseded paths.

## Suggested next patch

`patch_21_8_1a_refine_battle_aggregate_contract.py`
