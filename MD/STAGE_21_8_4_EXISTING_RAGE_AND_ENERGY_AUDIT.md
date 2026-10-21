# Stage 21.8.4 — Existing V1 Rage and Energy audit

- Status: **PASS**
- Conclusion: **GO_TO_SEMANTIC_REFINEMENT**
- V1 Python files scanned: **275**
- Contract rows: **30**
- Unresolved contracts: **0**
- Operational symbols: **1167**
- Runtime mutation: **False**
- Database opened: **False**
- Manual game check: **NOT_REQUIRED**

## Scope

Read-only static evidence for separate Rage and Energy state, initialization, gain/regeneration, costs, validation-before-debit, clamping, class routing, PvE/PvP/simulator consumers and restart semantics.

## Contract matrix

- `RAGE_STATE`: **EVIDENCE_FOUND** (67 files, 96 matches)
- `RAGE_MAXIMUM`: **EVIDENCE_FOUND** (112 files, 140 matches)
- `RAGE_START_VALUE`: **EVIDENCE_FOUND** (42 files, 42 matches)
- `RAGE_GAIN_ON_ATTACK`: **EVIDENCE_FOUND** (80 files, 112 matches)
- `RAGE_GAIN_ON_DAMAGE_TAKEN`: **EVIDENCE_FOUND** (52 files, 71 matches)
- `RAGE_EXTRA_GAIN`: **EVIDENCE_FOUND** (52 files, 82 matches)
- `RAGE_SKILL_COST`: **EVIDENCE_FOUND** (44 files, 50 matches)
- `RAGE_VALIDATE_BEFORE_DEBIT`: **EVIDENCE_FOUND** (105 files, 137 matches)
- `RAGE_CLAMP`: **EVIDENCE_FOUND** (167 files, 292 matches)
- `ENERGY_STATE`: **EVIDENCE_FOUND** (71 files, 99 matches)
- `ENERGY_MAXIMUM`: **EVIDENCE_FOUND** (113 files, 148 matches)
- `ENERGY_START_VALUE`: **EVIDENCE_FOUND** (71 files, 91 matches)
- `ENERGY_REGEN_PER_TURN`: **EVIDENCE_FOUND** (39 files, 57 matches)
- `ENERGY_SKILL_COST`: **EVIDENCE_FOUND** (40 files, 46 matches)
- `ENERGY_VALIDATE_BEFORE_DEBIT`: **EVIDENCE_FOUND** (103 files, 133 matches)
- `ENERGY_CLAMP`: **EVIDENCE_FOUND** (163 files, 288 matches)
- `RESOURCE_TYPE_ROUTING`: **EVIDENCE_FOUND** (86 files, 149 matches)
- `CLASS_RESOURCE_MAPPING`: **EVIDENCE_FOUND** (53 files, 125 matches)
- `PVE_INITIALIZATION`: **EVIDENCE_FOUND** (63 files, 82 matches)
- `PVE_REGENERATION`: **EVIDENCE_FOUND** (55 files, 61 matches)
- `PVE_PAYMENT`: **EVIDENCE_FOUND** (79 files, 124 matches)
- `PVP_VALIDATION`: **EVIDENCE_FOUND** (70 files, 90 matches)
- `PVP_PAYMENT`: **EVIDENCE_FOUND** (104 files, 174 matches)
- `PVP_SNAPSHOT`: **EVIDENCE_FOUND** (104 files, 156 matches)
- `SIMULATOR_CONSUMER`: **EVIDENCE_FOUND** (93 files, 136 matches)
- `RESTART_PERSISTENCE`: **EVIDENCE_FOUND** (94 files, 134 matches)
- `SEPARATE_TYPED_POLICIES`: **EVIDENCE_FOUND** (47 files, 48 matches)
- `NO_MANA_POLICY_DUPLICATION`: **EVIDENCE_FOUND** (89 files, 138 matches)
- `FAILURE_NO_MUTATION`: **EVIDENCE_FOUND** (91 files, 116 matches)
- `SINGLE_OWNER_PER_POLICY`: **EVIDENCE_FOUND** (155 files, 258 matches)

## Priority owner candidates

- `handlers/profile.py`: 30 contracts
- `systems/pvp_action_validation.py`: 29 contracts
- `systems/pvp_balance_simulator.py`: 29 contracts
- `systems/pvp_combat_log.py`: 29 contracts
- `systems/pvp_policy_metrics_audit.py`: 29 contracts
- `systems/pvp_real_actor_root_cause_audit.py`: 29 contracts
- `systems/pvp_root_cause_metric_semantics.py`: 29 contracts
- `systems/pvp_round_engine.py`: 29 contracts
- `systems/pvp_system.py`: 29 contracts
- `data/classes.py`: 28 contracts
- `handlers/combat.py`: 28 contracts
- `systems/pvp_config.py`: 28 contracts
- `systems/pvp_real_actor_state_replay.py`: 28 contracts
- `systems/pvp_round_ui.py`: 28 contracts
- `systems/simulation/pve_battle.py`: 28 contracts

## Boundary

Broad discovery evidence is not yet the final semantic policy. Mutation remains blocked until a dedicated semantic refinement confirms authoritative owners, exact formulas, ordering, atomicity and superseded paths.

## Suggested next patch

`patch_21_8_4a_refine_rage_and_energy_contract.py`
