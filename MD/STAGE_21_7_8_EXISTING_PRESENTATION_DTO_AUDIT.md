# Stage 21.7.8 — Existing V1 presentation DTO audit

- Status: **PASS**
- Conclusion: **GO_TO_SEMANTIC_REFINEMENT**
- V1 Python files scanned: **275**
- Contract rows: **24**
- Unresolved contracts: **0**
- Operational symbols: **1932**
- Runtime mutation: **False**
- Database opened: **False**
- Manual game check: **NOT_REQUIRED**

## Scope

Read-only static evidence for one deterministic description/comparison model, stable technical keys, item/equipment/rune/enhancement fields, Telegram and test consumers, formatter boundaries, missing-field semantics, duplicate presentation paths and absence of business mutation or formulas.

## Contract matrix

- `DTO_IDENTITY`: **EVIDENCE_FOUND** (32 files, 32 matches)
- `DESCRIPTION_MODEL`: **EVIDENCE_FOUND** (46 files, 50 matches)
- `COMPARISON_MODEL`: **EVIDENCE_FOUND** (31 files, 36 matches)
- `STABLE_TECHNICAL_KEYS`: **EVIDENCE_FOUND** (104 files, 190 matches)
- `NO_TEXT_AS_IDENTITY`: **EVIDENCE_FOUND** (214 files, 406 matches)
- `TYPED_RESULT`: **EVIDENCE_FOUND** (40 files, 40 matches)
- `DETERMINISTIC_ORDERING`: **EVIDENCE_FOUND** (105 files, 133 matches)
- `OPTIONAL_FIELDS`: **EVIDENCE_FOUND** (225 files, 451 matches)
- `EQUIPMENT_FIELDS`: **EVIDENCE_FOUND** (52 files, 138 matches)
- `PRIMARY_STAT_FIELDS`: **EVIDENCE_FOUND** (18 files, 76 matches)
- `DEFENSE_FIELDS`: **EVIDENCE_FOUND** (60 files, 121 matches)
- `DAMAGE_FIELDS`: **EVIDENCE_FOUND** (23 files, 76 matches)
- `RUNE_FIELDS`: **EVIDENCE_FOUND** (54 files, 70 matches)
- `ENHANCEMENT_FIELDS`: **EVIDENCE_FOUND** (30 files, 38 matches)
- `RARITY_AND_LEVEL_FIELDS`: **EVIDENCE_FOUND** (59 files, 91 matches)
- `OWNED_INSTANCE_IDENTITY`: **EVIDENCE_FOUND** (132 files, 192 matches)
- `TELEGRAM_CONSUMER`: **EVIDENCE_FOUND** (109 files, 211 matches)
- `TEST_CONSUMER`: **EVIDENCE_FOUND** (68 files, 87 matches)
- `FORMATTER_BOUNDARY`: **EVIDENCE_FOUND** (165 files, 277 matches)
- `NO_BUSINESS_MUTATION`: **EVIDENCE_FOUND** (99 files, 238 matches)
- `NO_BUSINESS_FORMULA`: **EVIDENCE_FOUND** (124 files, 193 matches)
- `FAILURE_SEMANTICS`: **EVIDENCE_FOUND** (162 files, 274 matches)
- `CONSUMER_PARITY`: **EVIDENCE_FOUND** (131 files, 225 matches)
- `DUPLICATE_PRESENTATION_PATHS`: **EVIDENCE_FOUND** (39 files, 41 matches)

## Priority owner candidates

- `systems/auction_house_system.py`: 23 contracts
- `handlers/inventory.py`: 21 contracts
- `systems/equipment_system.py`: 21 contracts
- `systems/player_interaction_system.py`: 21 contracts
- `handlers/player_interaction.py`: 20 contracts
- `systems/rune_system.py`: 20 contracts
- `db_modules/dev_compat.py`: 19 contracts
- `handlers/auction_house.py`: 19 contracts
- `handlers/city.py`: 18 contracts
- `handlers/combat.py`: 18 contracts
- `data/story_quest_definitions.py`: 16 contracts
- `db_modules/__init__.py`: 16 contracts
- `db_modules/connection.py`: 16 contracts
- `db_modules/generated_equipment.py`: 16 contracts
- `db_modules/shop.py`: 16 contracts

## Boundary

Broad discovery evidence is not yet the final semantic policy. Mutation remains blocked until a dedicated semantic refinement confirms authoritative owners, exact formulas, ordering, atomicity and superseded paths.

## Suggested next patch

`patch_21_7_8a_refine_presentation_dto_contract.py`
