# Stage 21.8.3a — Refined V1 mana engine contract

- Status: **PASS**
- Conclusion: **REVIEW_REQUIRED**
- Explicit owner files: **13**
- Semantic rows: **26**
- Unresolved rows: **2**
- Database opened: **False**
- Production changed: **False**
- Manual game check: **NOT_REQUIRED**

## Authority

- `data/mana_policy.py`: authoritative V1 mana cost, restore, post-combat floor and passive regeneration policy owner.
- `systems/stat_system.py`: authoritative Max MP formula owner; `systems/character_system.py`: persistent current-MP lifecycle owner.
- PvE and PvP handlers/engines are payment consumers; potion, simulator, profile and snapshot modules are adjacent consumers requiring parity.
- Mana remains separate from Rage, Energy and Combo; damage, rewards and presentation remain outside the mana-policy owner.

## Semantic matrix

- `CANONICAL_MANA_POLICY_OWNER`: **V1_CONFIRMED**
- `CANONICAL_MAX_MP_FORMULA_OWNER`: **V1_CONFIRMED**
- `MAX_MP_BASE_TERM`: **UNRESOLVED**
- `MAX_MP_LEVEL_TERM`: **UNRESOLVED**
- `MAX_MP_INT_TERM`: **V1_CONFIRMED**
- `MAX_MP_WIS_TERM`: **V1_CONFIRMED**
- `PERSISTENT_CURRENT_MP_OWNER`: **V1_CONFIRMED**
- `CURRENT_MP_CLAMP`: **V1_CONFIRMED**
- `MAX_MP_CHANGE_SEMANTICS`: **V1_CONFIRMED**
- `SKILL_COST_VALIDATION`: **V1_CONFIRMED**
- `MANA_COST_ROUNDING`: **V1_CONFIRMED**
- `PVE_VALIDATE_BEFORE_DEBIT`: **V1_CONFIRMED**
- `PVP_VALIDATE_BEFORE_DEBIT`: **V1_CONFIRMED**
- `INSUFFICIENT_MANA_NO_MUTATION`: **V1_CONFIRMED**
- `PVE_ATOMIC_DEBIT_BOUNDARY`: **V1_CONFIRMED**
- `PVP_ROUND_DEBIT_BOUNDARY`: **V1_CONFIRMED**
- `PASSIVE_REGEN_POLICY`: **V1_CONFIRMED**
- `COMBAT_REGEN_PAUSE`: **V1_CONFIRMED**
- `POST_COMBAT_MP_FLOOR`: **V1_CONFIRMED**
- `MANA_RESTORE_POLICY`: **V1_CONFIRMED**
- `POTION_RESTORE_BOUNDARY`: **V1_CONFIRMED**
- `CLASS_RESOURCE_SEPARATION`: **V1_CONFIRMED**
- `SIMULATOR_PARITY_REQUIRED`: **V1_CONFIRMED**
- `PVP_SNAPSHOT_CURRENT_MP`: **V1_CONFIRMED**
- `PRESENTATION_IS_CONSUMER`: **V1_CONFIRMED**
- `NO_PARALLEL_MANA_POLICY_OWNER`: **V1_CONFIRMED**

## Boundary

No implementation is permitted unless every semantic row is resolved. Exact Max MP terms, mana costs, rounding, regeneration, floor and current-MP lifecycle semantics remain bound to the V1 owner evidence and must be consumed without reinterpretation by the implementation patch.

## Suggested next patch

`resolve exact unresolved semantic rows before implementation`
