# Stage 21.7.8a — Refined V1 presentation DTO contract

- Status: **PASS**
- Conclusion: **GO_TO_IMPLEMENTATION**
- Explicit owner files: **14**
- Semantic rows: **24**
- Unresolved rows: **0**
- Database opened: **False**
- Production changed: **False**
- Manual game check: **NOT_REQUIRED**

## Authority

- `handlers/inventory.py`: authoritative V1 item description/comparison presentation path.
- `systems/equipment_system.py` and `db_modules/equipment.py`: display-name/data facades, not DTO owners.
- auction, trade, profile, shop, rune and refine paths: presentation consumers or compatibility formatters.
- business formulas and mutations remain outside the DTO boundary.

## Semantic matrix

- `AUTHORITATIVE_DESCRIPTION_OWNER`: **V1_CONFIRMED**
- `AUTHORITATIVE_COMPARISON_OWNER`: **V1_CONFIRMED**
- `DISPLAY_NAME_BOUNDARY`: **V1_CONFIRMED**
- `BUTTON_LABEL_BOUNDARY`: **V1_CONFIRMED**
- `EXACT_OWNED_IDENTITY`: **V1_CONFIRMED**
- `NO_TEXT_AS_TECHNICAL_ID`: **V1_CONFIRMED**
- `SELECTED_ITEM_COMPARISON`: **V1_CONFIRMED**
- `RUNE_BLOCK_BOUNDARY`: **V1_CONFIRMED**
- `ENHANCEMENT_FIELD_BOUNDARY`: **V1_CONFIRMED**
- `DURABILITY_FIELD_BOUNDARY`: **V1_CONFIRMED**
- `PRIMARY_STATS_FIELDS`: **V1_CONFIRMED**
- `DEFENSE_FIELDS`: **V1_CONFIRMED**
- `DAMAGE_FIELDS`: **V1_CONFIRMED**
- `RARITY_AND_LEVEL_FIELDS`: **V1_CONFIRMED**
- `DETERMINISTIC_FIELD_ORDER`: **V1_CONFIRMED**
- `OPTIONAL_MISSING_FIELDS`: **V1_CONFIRMED**
- `TELEGRAM_IS_CONSUMER`: **V1_CONFIRMED**
- `AUCTION_CONSUMER_PARITY`: **V1_CONFIRMED**
- `TRADE_CONSUMER_PARITY`: **V1_CONFIRMED**
- `PROFILE_CONSUMER_PARITY`: **V1_CONFIRMED**
- `SHOP_CONSUMER_PARITY`: **V1_CONFIRMED**
- `PRESENTATION_NO_MUTATION_OWNER`: **V1_CONFIRMED**
- `BUSINESS_FORMULAS_STAY_OUTSIDE`: **V1_CONFIRMED**
- `DUPLICATE_PATHS_CLASSIFIED`: **V1_CONFIRMED**

## Boundary

No implementation is permitted unless every semantic row is resolved. Exact constants and formula bodies remain bound to the V1 owner evidence and must be consumed without reinterpretation by the implementation patch.

## Suggested next patch

`patch_21_7_8b_implement_presentation_dto.py`
