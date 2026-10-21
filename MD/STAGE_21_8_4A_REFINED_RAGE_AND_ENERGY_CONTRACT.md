# Stage 21.8.4a — Refined V1 Rage and Energy contract

- Status: **PASS**
- Conclusion: **REVIEW_REQUIRED**
- Explicit owner files: **12**
- Semantic rows: **30**
- Unresolved rows: **1**
- Database opened: **False**
- Production changed: **False**
- Manual game check: **NOT_REQUIRED**

## Authority

- `handlers/combat.py`: authoritative V1 PvE Rage/Energy initialization, gain, regeneration and payment path.
- `data/classes.py` and `systems/character_system.py`: class-to-resource mapping owners/facades.
- `systems/pvp_config.py`, validation, round engine and battle factory define PvP policy constants and consumers requiring parity.
- Rage and Energy require separate typed V2 policies; Mana, presentation, persistence and skill execution remain external boundaries.

## Semantic matrix

- `PVE_RESOURCE_INITIALIZATION_OWNER`: **V1_CONFIRMED**
- `PVE_RESOURCE_REGEN_OWNER`: **V1_CONFIRMED**
- `RAGE_GAIN_ON_ATTACK`: **V1_CONFIRMED**
- `RAGE_GAIN_ON_DAMAGE_TAKEN`: **V1_CONFIRMED**
- `RAGE_EXTRA_SKILL_GAIN`: **V1_CONFIRMED**
- `RAGE_COST_VALIDATION`: **V1_CONFIRMED**
- `ENERGY_REGEN_PER_PLAYER_TURN`: **V1_CONFIRMED**
- `ENERGY_COST_VALIDATION`: **V1_CONFIRMED**
- `PVE_VALIDATE_BEFORE_DEBIT`: **V1_CONFIRMED**
- `PVE_RESOURCE_CLAMP`: **V1_CONFIRMED**
- `CLASS_RESOURCE_MAPPING`: **V1_CONFIRMED**
- `RAGE_CLASS_MAPPING`: **V1_CONFIRMED**
- `ENERGY_CLASS_MAPPING`: **V1_CONFIRMED**
- `PVP_RESOURCE_CONSTANTS`: **V1_CONFIRMED**
- `PVP_VALIDATION_BEFORE_DEBIT`: **V1_CONFIRMED**
- `PVP_EFFECTIVE_SKILL_COST`: **V1_CONFIRMED**
- `PVP_PAYMENT_OWNER`: **V1_CONFIRMED**
- `PVP_RESOURCE_CLAMP`: **V1_CONFIRMED**
- `PVP_SNAPSHOT_RESOURCE_TYPE`: **V1_CONFIRMED**
- `PVP_MODEL_RESOURCE_STATE`: **V1_CONFIRMED**
- `PVE_ACTION_STATE_RESOURCE`: **UNRESOLVED**
- `SIMULATOR_RESOURCE_PARITY`: **V1_CONFIRMED**
- `RAGE_AND_ENERGY_SEPARATE_FROM_MANA`: **V1_CONFIRMED**
- `FAILURE_WITHOUT_PARTIAL_MUTATION`: **V1_CONFIRMED**
- `PRESENTATION_IS_CONSUMER`: **V1_CONFIRMED**
- `RESTART_SNAPSHOT_BOUNDARY`: **V1_CONFIRMED**
- `RAGE_TYPED_POLICY_TARGET`: **V1_CONFIRMED**
- `ENERGY_TYPED_POLICY_TARGET`: **V1_CONFIRMED**
- `NO_PARALLEL_RAGE_OWNER`: **V1_CONFIRMED**
- `NO_PARALLEL_ENERGY_OWNER`: **V1_CONFIRMED**

## Boundary

No implementation is permitted unless every semantic row is resolved. Exact Rage gain, Energy regeneration, maxima, costs, class routing, validation and clamp order remain bound to the V1 owner evidence and must be consumed without reinterpretation by the implementation patch.

## Suggested next patch

`resolve exact unresolved semantic rows before implementation`
