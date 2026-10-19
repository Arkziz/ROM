# Stage 21.7.1b - Item identity separation resolution

## Decision

- Status: `PASS`
- Conclusion: `GO_WITH_FORWARD_MIGRATION_REQUIRED`
- Unresolved before: `2`
- Unresolved after: `0`

## Resolved contracts

- `DEFINITION_VS_INSTANCE_SEPARATION`: `V1_CONFIRMED`
- `QUEST_ITEMS_SEPARATE_FROM_ORDINARY_INVENTORY`: `V1_CONFIRMED`

## Canonical result

V1 separates `items.id` definition identity from `inventory.id` owned instance identity, with `inventory.item_id` referencing the definition and equipment using exact `inventory_id`. Story quest items use separate `user_id + quest_id + item_key` identity and are not ordinary inventory instances.

Migration `001_v2_baseline` remains immutable. A forward migration is required for Stage 21.7.1 implementation.

## Manual game check

`NOT_REQUIRED`. This resolver is read-only.
