# Stage 21.7.4a — Refined V1 equipment-generation contract

- Status: `PASS`
- Conclusion: `REVIEW_REQUIRED`
- Explicit owner files: `15`
- Semantic rows: `18`
- Unresolved rows: `1`
- Duplicate symbols: `54`

## Semantic matrix

- `AUTHORITATIVE_GENERATION_CORE`: `V1_CONFIRMED`
- `PUBLIC_FACADE_DELEGATION`: `V1_CONFIRMED`
- `IDENTITY_STATS_SEPARATION`: `V1_CONFIRMED`
- `SHOP_SOURCE_CONTEXT`: `V1_CONFIRMED`
- `SHOP_CLASS_IDENTITY`: `V1_CONFIRMED`
- `LOOT_SOURCE_CONTEXT`: `V1_CONFIRMED`
- `DROPPED_WEAPON_OFFHAND_IDENTITY`: `V1_CONFIRMED`
- `ARMOR_TYPE_POLICY`: `V1_CONFIRMED`
- `UNIVERSAL_DROPPED_JEWELRY`: `V1_CONFIRMED`
- `RARITY_POLICY`: `V1_CONFIRMED`
- `LEVEL_POLICY`: `UNRESOLVED`
- `SLOT_HAND_POLICY`: `V1_CONFIRMED`
- `STAT_BUDGET_REDISTRIBUTION`: `V1_CONFIRMED`
- `PREVIEW_PERMANENT_PROMOTION`: `V1_CONFIRMED`
- `RNG_BOUNDARY`: `V1_CONFIRMED`
- `DEV_IS_CONSUMER_NOT_OWNER`: `V1_CONFIRMED`
- `SIMULATOR_IS_CONSUMER_NOT_OWNER`: `V1_CONFIRMED`
- `FAIL_CLOSED_VALIDATION`: `V1_CONFIRMED`

## Ownership decision

- Generation core: `db_modules/generated_equipment.py`.
- Public facade: `systems/dynamic_equipment_system.py`.
- Shop, loot, DEV and simulator remain source contexts/consumers, not parallel formula owners.
- Identity policy and numeric stat policy remain separate authoritative layers.
- Preview identity promotion remains owned by the item-ID allocator and shop transaction path.

## Manual game check

`NOT_REQUIRED`. This is a read-only refinement.
