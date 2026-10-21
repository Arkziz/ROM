# Stage 21.8.5a — Refined V1 skill execution contract

- Status: **PASS**
- Conclusion: **REVIEW_REQUIRED**
- Explicit owner files: **12**
- Semantic rows: **32**
- Unresolved rows: **1**
- Database opened: **False**
- Production changed: **False**
- Manual game check: **NOT_REQUIRED**

## Authority

- `handlers/combat.py`: authoritative V1 PvE skill orchestration path for selection, cost payment, cooldowns and special effects.
- `systems/pve_skill_action_state.py`: read-only PvE availability owner; `data/classes.py`: class skill catalog source.
- `systems/pvp_action_validation.py` and `systems/pvp_round_engine.py`: PvP validation and deterministic execution owners requiring parity.
- skill execution require separate typed V2 policies; Mana, presentation, persistence and skill execution remain external boundaries.

## Semantic matrix

- `PVE_SKILL_CATALOG_OWNER`: **V1_CONFIRMED**
- `TECHNICAL_SKILL_IDENTITY`: **V1_CONFIRMED**
- `SKILL_DEFINITION_FIELDS`: **V1_CONFIRMED**
- `PVE_ACTION_AVAILABILITY`: **V1_CONFIRMED**
- `PVE_EFFECTIVE_COST`: **V1_CONFIRMED**
- `PVE_SELECTION_BOUNDARY`: **V1_CONFIRMED**
- `PVE_VALIDATE_BEFORE_PAYMENT`: **V1_CONFIRMED**
- `PVE_COOLDOWN_VALIDATION`: **V1_CONFIRMED**
- `PVE_COOLDOWN_START`: **V1_CONFIRMED**
- `PVE_COOLDOWN_TICK`: **V1_CONFIRMED**
- `PVE_HIT_ROLL_ROUTING`: **V1_CONFIRMED**
- `BASIC_ATTACK_TYPE_ROUTING`: **UNRESOLVED**
- `DAMAGE_MULTIPLIER_CONTRACT`: **V1_CONFIRMED**
- `NO_DAMAGE_SKILL_CONTRACT`: **V1_CONFIRMED**
- `PVE_SPECIAL_EFFECT_OWNER`: **V1_CONFIRMED**
- `PVE_STUN_POLICY`: **V1_CONFIRMED**
- `PVE_DOT_EFFECTS`: **V1_CONFIRMED**
- `PVE_HOT_HEAL_EFFECTS`: **V1_CONFIRMED**
- `PVE_SHIELD_EFFECTS`: **V1_CONFIRMED**
- `PVE_EXTRA_RAGE_EFFECT`: **V1_CONFIRMED**
- `PVE_COMBO_REQUIREMENT`: **V1_CONFIRMED**
- `PVP_ACTION_VALIDATION`: **V1_CONFIRMED**
- `PVP_EFFECTIVE_COST`: **V1_CONFIRMED**
- `PVP_DETERMINISTIC_EXECUTION`: **V1_CONFIRMED**
- `PVP_INTENT_AND_OUTCOME`: **V1_CONFIRMED**
- `PVP_PAYMENT_BEFORE_EFFECT`: **V1_CONFIRMED**
- `SIMULATOR_AVAILABILITY_PARITY`: **V1_CONFIRMED**
- `SIMULATOR_EXECUTION_PARITY`: **V1_CONFIRMED**
- `SIMULATOR_CATALOG_PARITY`: **V1_CONFIRMED**
- `PRESENTATION_IS_CONSUMER`: **V1_CONFIRMED**
- `BOSS_IS_ADJACENT_CONSUMER`: **V1_CONFIRMED**
- `FAILURE_WITHOUT_PARTIAL_MUTATION`: **V1_CONFIRMED**

## Boundary

No implementation is permitted unless every semantic row is resolved. Exact skill identity, validation order, cost payment, cooldown timing, hit routing and effect semantics remain bound to the V1 owner evidence and must be consumed without reinterpretation by the implementation patch.

## Suggested next patch

`resolve exact unresolved semantic rows before implementation`
