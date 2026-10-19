# Stage 21.7.1a — Refined item definition and instance contract

## Decision

- Status: `PASS`
- Conclusion: `REVIEW_REQUIRED`
- Explicit production-owner files: `18`
- Parity rows: `17`
- Blocking unresolved rows: `2`

## Canonical V1 model

- `items.id` is definition identity.
- `inventory.id` is the owned inventory-row/item-instance identity.
- `inventory.item_id` references the definition.
- Equipment slots reference exact `inventory_id` values.
- Story quest items use a separate `user_id + quest_id + item_key` identity and are not ordinary inventory instances.
- Generated permanent definitions, shop previews, event items, and story quest items use separate identity/namespace mechanisms.

## Provisional V2 schema decision

Migration `001_v2_baseline` remains immutable. The current `item_instances`, `equipment_slots`, and `item_reservations` contracts remain provisional. The implementation stage must use a new forward migration because the V1 definition/instance split is not represented authoritatively by the provisional single-table item model.

## Mutation gate

Mutation remains blocked until every unresolved parity row below is resolved:
- `DEFINITION_VS_INSTANCE_SEPARATION`
- `QUEST_ITEMS_SEPARATE_FROM_ORDINARY_INVENTORY`

## Required implementation naming

Because `21.7.1a` is a read-only refinement, the mutation patch uses the next suffix:

`patch_21_7_1b_implement_item_definition_and_instance.py`

## Manual game check

`NOT_REQUIRED`. This is a read-only semantic refinement.
