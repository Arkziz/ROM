# Stage 21.7.6a — Refined V1 durability and repair contract

- Status: **PASS**
- Conclusion: **GO_TO_IMPLEMENTATION**
- Explicit owner files: **14**
- Semantic rows: **19**
- Unresolved rows: **0**
- Database opened: **False**
- Production changed: **False**
- Manual game check: **NOT_REQUIRED**

## Authority

- `systems/equipment_system.py`: canonical runtime mutation and formulas.
- `db_modules/equipment.py`: persistence facade, not a second policy owner.
- `handlers/blacksmith.py`: presentation/orchestration consumer.
- rune, enhancement, simulator and DEV paths: consumers of the canonical durability policy.

## Semantic matrix

- `AUTHORITATIVE_MUTATION_OWNER`: **V1_CONFIRMED**
- `PERSISTENCE_FACADE_ONLY`: **V1_CONFIRMED**
- `DURABILITY_RANGE_AND_CLAMP`: **V1_CONFIRMED**
- `EXACT_INVENTORY_IDENTITY`: **V1_CONFIRMED**
- `EQUIPPED_ONLY_DAMAGE`: **V1_CONFIRMED**
- `DEATH_PENALTY`: **V1_CONFIRMED**
- `ZERO_DURABILITY_BASE_STAT_GATE`: **V1_CONFIRMED**
- `ZERO_DURABILITY_RUNE_GATE`: **V1_CONFIRMED**
- `ZERO_DURABILITY_ENHANCEMENT_GATE`: **V1_CONFIRMED**
- `REPAIR_COST_OWNER`: **V1_CONFIRMED**
- `REPAIR_FORMULA_INPUTS`: **V1_CONFIRMED**
- `RARITY_MULTIPLIERS`: **V1_CONFIRMED**
- `REPAIR_ONE_ATOMICITY`: **V1_CONFIRMED**
- `REPAIR_ALL_ATOMICITY`: **V1_CONFIRMED**
- `INSUFFICIENT_FUNDS_NO_MUTATION`: **V1_CONFIRMED**
- `RESERVATION_BOUNDARY`: **V1_CONFIRMED**
- `PERSISTENCE_AND_RESTART`: **V1_CONFIRMED**
- `CONSUMER_BOUNDARIES`: **V1_CONFIRMED**
- `FAILURE_TAXONOMY`: **V1_CONFIRMED**

## Boundary

No implementation is permitted unless every semantic row is resolved. Exact constants and formula bodies remain in the machine report and must be consumed without reinterpretation by the implementation patch.

## Suggested next patch

`patch_21_7_6b_implement_durability_and_repair.py`
