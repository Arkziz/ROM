# Stage 21.8.3 — Existing V1 mana engine audit

- Status: **PASS**
- Conclusion: **GO_TO_SEMANTIC_REFINEMENT**
- V1 Python files scanned: **275**
- Contract rows: **26**
- Unresolved contracts: **0**
- Operational symbols: **2501**
- Runtime mutation: **False**
- Database opened: **False**
- Manual game check: **NOT_REQUIRED**

## Scope

Read-only static evidence for Max MP, current MP, skill costs, validation-before-debit, restore and potion flows, post-combat floor, stat-change semantics, restart persistence, class-resource separation and PvE/PvP/simulator consumers.

## Contract matrix

- `MANA_STATE`: **EVIDENCE_FOUND** (242 files, 336 matches)
- `MAX_MP_FORMULA`: **EVIDENCE_FOUND** (234 files, 457 matches)
- `MAX_MP_BASE`: **EVIDENCE_FOUND** (118 files, 182 matches)
- `MAX_MP_LEVEL_TERM`: **EVIDENCE_FOUND** (179 files, 307 matches)
- `MAX_MP_INT_TERM`: **EVIDENCE_FOUND** (230 files, 333 matches)
- `MAX_MP_WIS_TERM`: **EVIDENCE_FOUND** (170 files, 262 matches)
- `CURRENT_MP_CLAMP`: **EVIDENCE_FOUND** (97 files, 138 matches)
- `RESOURCE_PRESERVATION`: **EVIDENCE_FOUND** (123 files, 161 matches)
- `SKILL_MANA_COST`: **EVIDENCE_FOUND** (34 files, 47 matches)
- `PRECONDITION_BEFORE_DEBIT`: **EVIDENCE_FOUND** (85 files, 103 matches)
- `ATOMIC_MANA_DEBIT`: **EVIDENCE_FOUND** (50 files, 52 matches)
- `INSUFFICIENT_MANA`: **EVIDENCE_FOUND** (11 files, 14 matches)
- `MANA_RESTORE`: **EVIDENCE_FOUND** (12 files, 12 matches)
- `POTION_RESTORE`: **EVIDENCE_FOUND** (242 files, 276 matches)
- `POST_COMBAT_MP_FLOOR`: **EVIDENCE_FOUND** (9 files, 17 matches)
- `DEATH_DEFEAT_SEMANTICS`: **EVIDENCE_FOUND** (53 files, 68 matches)
- `RESTART_PERSISTENCE`: **EVIDENCE_FOUND** (91 files, 118 matches)
- `STAT_CHANGE_SEMANTICS`: **EVIDENCE_FOUND** (109 files, 171 matches)
- `CLASS_RESOURCE_SEPARATION`: **EVIDENCE_FOUND** (86 files, 149 matches)
- `PVE_CONSUMER`: **EVIDENCE_FOUND** (137 files, 240 matches)
- `PVP_CONSUMER`: **EVIDENCE_FOUND** (107 files, 195 matches)
- `SIMULATOR_CONSUMER`: **EVIDENCE_FOUND** (84 files, 95 matches)
- `PRESENTATION_CONSUMER`: **EVIDENCE_FOUND** (178 files, 247 matches)
- `SINGLE_POLICY_OWNER`: **EVIDENCE_FOUND** (39 files, 54 matches)
- `NO_DAMAGE_OR_REWARD`: **EVIDENCE_FOUND** (135 files, 215 matches)
- `FAILURE_SEMANTICS`: **EVIDENCE_FOUND** (160 files, 251 matches)

## Priority owner candidates

- `handlers/combat.py`: 26 contracts
- `systems/pvp_round_engine.py`: 26 contracts
- `data/mana_policy.py`: 24 contracts
- `systems/simulation/pve_battle.py`: 24 contracts
- `systems/simulation/world_progression.py`: 24 contracts
- `systems/potion_system.py`: 23 contracts
- `db_modules/__init__.py`: 22 contracts
- `systems/character_system.py`: 22 contracts
- `systems/pvp_action_validation.py`: 22 contracts
- `systems/pvp_battle_factory.py`: 21 contracts
- `systems/pvp_combat_log.py`: 21 contracts
- `systems/pvp_policy_metrics_audit.py`: 21 contracts
- `systems/simulation/combat_actor_stats.py`: 21 contracts
- `systems/simulation/survival_state.py`: 21 contracts
- `db_modules/character.py`: 20 contracts

## Boundary

Broad discovery evidence is not yet the final semantic policy. Mutation remains blocked until a dedicated semantic refinement confirms authoritative owners, exact formulas, ordering, atomicity and superseded paths.

## Suggested next patch

`patch_21_8_3a_refine_mana_engine_contract.py`
