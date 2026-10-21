# Stage 21.8.5 — Existing V1 skill execution audit

- Status: **PASS**
- Conclusion: **GO_TO_SEMANTIC_REFINEMENT**
- V1 Python files scanned: **275**
- Contract rows: **32**
- Unresolved contracts: **0**
- Operational symbols: **3257**
- Runtime mutation: **False**
- Database opened: **False**
- Manual game check: **NOT_REQUIRED**

## Scope

Read-only static evidence for skill identity and definitions, availability, selection, costs, cooldowns, targeting, hit rolls, damage multipliers, special effects, deterministic outcomes and PvE/PvP/simulator execution paths.

## Contract matrix

- `SKILL_IDENTITY`: **EVIDENCE_FOUND** (202 files, 226 matches)
- `SKILL_DEFINITION`: **EVIDENCE_FOUND** (177 files, 240 matches)
- `CLASS_SKILL_CATALOG`: **EVIDENCE_FOUND** (44 files, 69 matches)
- `BASIC_ATTACK_TYPE`: **EVIDENCE_FOUND** (64 files, 128 matches)
- `ACTION_AVAILABILITY`: **EVIDENCE_FOUND** (133 files, 200 matches)
- `ACTION_SELECTION`: **EVIDENCE_FOUND** (99 files, 116 matches)
- `COST_CALCULATION`: **EVIDENCE_FOUND** (69 files, 89 matches)
- `VALIDATE_BEFORE_COST`: **EVIDENCE_FOUND** (40 files, 44 matches)
- `COST_PAYMENT`: **EVIDENCE_FOUND** (91 files, 134 matches)
- `COOLDOWN_VALIDATION`: **EVIDENCE_FOUND** (59 files, 78 matches)
- `COOLDOWN_START`: **EVIDENCE_FOUND** (253 files, 310 matches)
- `COOLDOWN_TICK`: **EVIDENCE_FOUND** (35 files, 46 matches)
- `TARGET_SELECTION`: **EVIDENCE_FOUND** (162 files, 245 matches)
- `HIT_ROLL`: **EVIDENCE_FOUND** (40 files, 45 matches)
- `DAMAGE_MULTIPLIER`: **EVIDENCE_FOUND** (61 files, 96 matches)
- `NO_DAMAGE_SKILL`: **EVIDENCE_FOUND** (19 files, 26 matches)
- `SPECIAL_EFFECT`: **EVIDENCE_FOUND** (57 files, 87 matches)
- `STUN_EFFECT`: **EVIDENCE_FOUND** (72 files, 90 matches)
- `DOT_EFFECT`: **EVIDENCE_FOUND** (44 files, 64 matches)
- `HOT_HEAL_EFFECT`: **EVIDENCE_FOUND** (93 files, 158 matches)
- `SHIELD_EFFECT`: **EVIDENCE_FOUND** (60 files, 111 matches)
- `RAGE_EXTRA_GAIN`: **EVIDENCE_FOUND** (52 files, 82 matches)
- `COMBO_REQUIREMENT`: **EVIDENCE_FOUND** (55 files, 77 matches)
- `RESOURCE_GAIN`: **EVIDENCE_FOUND** (24 files, 42 matches)
- `DETERMINISTIC_RESULT`: **EVIDENCE_FOUND** (152 files, 239 matches)
- `PVE_EXECUTION`: **EVIDENCE_FOUND** (65 files, 69 matches)
- `PVP_EXECUTION`: **EVIDENCE_FOUND** (23 files, 40 matches)
- `SIMULATOR_EXECUTION`: **EVIDENCE_FOUND** (51 files, 55 matches)
- `PRESENTATION_CONSUMER`: **EVIDENCE_FOUND** (146 files, 164 matches)
- `SINGLE_EXECUTION_OWNER`: **EVIDENCE_FOUND** (104 files, 104 matches)
- `FAILURE_NO_MUTATION`: **EVIDENCE_FOUND** (63 files, 81 matches)
- `NO_REWARD_SETTLEMENT`: **EVIDENCE_FOUND** (106 files, 159 matches)

## Priority owner candidates

- `handlers/combat.py`: 31 contracts
- `systems/pvp_policy_metrics_audit.py`: 29 contracts
- `systems/boss_system.py`: 28 contracts
- `systems/pvp_real_actor_root_cause_audit.py`: 28 contracts
- `systems/pvp_round_engine.py`: 27 contracts
- `systems/simulation/pve_battle.py`: 27 contracts
- `db_modules/__init__.py`: 25 contracts
- `systems/pvp_balance_simulator.py`: 25 contracts
- `systems/pvp_knight_judgement_terminal_audit.py`: 25 contracts
- `systems/pvp_system.py`: 25 contracts
- `handlers/profile.py`: 24 contracts
- `systems/pvp_combat_log.py`: 24 contracts
- `systems/pvp_production_calibration.py`: 24 contracts
- `systems/pvp_real_actor_state_replay.py`: 24 contracts
- `systems/pvp_action_validation.py`: 23 contracts

## Boundary

Broad discovery evidence is not yet the final semantic policy. Mutation remains blocked until a dedicated semantic refinement confirms authoritative owners, exact formulas, ordering, atomicity and superseded paths.

## Suggested next patch

`patch_21_8_5a_refine_skill_execution_contract.py`
