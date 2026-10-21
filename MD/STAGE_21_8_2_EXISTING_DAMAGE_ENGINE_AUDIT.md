# Stage 21.8.2 — Existing V1 damage engine audit

- Status: **PASS**
- Conclusion: **GO_TO_SEMANTIC_REFINEMENT**
- V1 Python files scanned: **275**
- Contract rows: **26**
- Unresolved contracts: **0**
- Operational symbols: **967**
- Runtime mutation: **False**
- Database opened: **False**
- Manual game check: **NOT_REQUIRED**

## Scope

Read-only static evidence for PATK/MATK, PDEF/MDEF, physical and magical damage formulas, minimum damage, crit, evasion, rounding, RNG, elite/boss modifiers, no-weaker floors and PvE/PvP/simulator consumers.

## Contract matrix

- `DAMAGE_REQUEST`: **EVIDENCE_FOUND** (34 files, 46 matches)
- `DAMAGE_RESULT`: **EVIDENCE_FOUND** (1 files, 1 matches)
- `PHYSICAL_ATTACK_INPUT`: **EVIDENCE_FOUND** (34 files, 39 matches)
- `MAGICAL_ATTACK_INPUT`: **EVIDENCE_FOUND** (29 files, 33 matches)
- `PHYSICAL_DEFENSE_INPUT`: **EVIDENCE_FOUND** (74 files, 143 matches)
- `MAGICAL_DEFENSE_INPUT`: **EVIDENCE_FOUND** (59 files, 87 matches)
- `PHYSICAL_DAMAGE_FORMULA`: **EVIDENCE_FOUND** (61 files, 84 matches)
- `MAGICAL_DAMAGE_FORMULA`: **EVIDENCE_FOUND** (63 files, 89 matches)
- `MINIMUM_DAMAGE`: **EVIDENCE_FOUND** (81 files, 101 matches)
- `CRITICAL_CHANCE`: **EVIDENCE_FOUND** (29 files, 59 matches)
- `CRITICAL_MULTIPLIER`: **EVIDENCE_FOUND** (3 files, 3 matches)
- `EVASION_CHANCE`: **EVIDENCE_FOUND** (23 files, 39 matches)
- `CRIT_SOFT_CAP`: **EVIDENCE_FOUND** (72 files, 79 matches)
- `EVASION_SOFT_CAP`: **EVIDENCE_FOUND** (79 files, 80 matches)
- `RNG_BOUNDARY`: **EVIDENCE_FOUND** (83 files, 121 matches)
- `ROUNDING_POLICY`: **EVIDENCE_FOUND** (180 files, 264 matches)
- `ELITE_MODIFIER`: **EVIDENCE_FOUND** (24 files, 40 matches)
- `BOSS_MODIFIER`: **EVIDENCE_FOUND** (38 files, 46 matches)
- `NO_WEAKER_FLOOR`: **EVIDENCE_FOUND** (135 files, 159 matches)
- `DAMAGE_TYPE_ROUTING`: **EVIDENCE_FOUND** (54 files, 115 matches)
- `PVE_CONSUMER`: **EVIDENCE_FOUND** (112 files, 166 matches)
- `PVP_CONSUMER`: **EVIDENCE_FOUND** (84 files, 136 matches)
- `SIMULATOR_CONSUMER`: **EVIDENCE_FOUND** (46 files, 61 matches)
- `SINGLE_FORMULA_OWNER`: **EVIDENCE_FOUND** (1 files, 1 matches)
- `NO_REWARD_OR_SETTLEMENT`: **EVIDENCE_FOUND** (106 files, 159 matches)
- `FAILURE_SEMANTICS`: **EVIDENCE_FOUND** (160 files, 264 matches)

## Priority owner candidates

- `systems/combat_system.py`: 22 contracts
- `handlers/combat.py`: 21 contracts
- `systems/pvp_round_engine.py`: 20 contracts
- `systems/boss_system.py`: 19 contracts
- `systems/rune_system.py`: 19 contracts
- `systems/pvp_adaptive_balance_optimizer.py`: 18 contracts
- `systems/pvp_production_calibration.py`: 18 contracts
- `systems/simulation/pve_battle.py`: 18 contracts
- `db_modules/dev_compat.py`: 17 contracts
- `db_modules/shop.py`: 17 contracts
- `systems/equipment_system.py`: 17 contracts
- `systems/player_interaction_system.py`: 17 contracts
- `systems/player_system.py`: 17 contracts
- `systems/simulation/parity_foundation.py`: 17 contracts
- `systems/simulation/production_parity.py`: 17 contracts

## Boundary

Broad discovery evidence is not yet the final semantic policy. Mutation remains blocked until a dedicated semantic refinement confirms authoritative owners, exact formulas, ordering, atomicity and superseded paths.

## Suggested next patch

`patch_21_8_2a_refine_damage_engine_contract.py`
