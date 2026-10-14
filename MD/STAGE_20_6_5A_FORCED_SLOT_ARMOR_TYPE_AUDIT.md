# Stage 20.6.5a — Forced-slot armor_type Audit

**FORCED_SLOT_ARMOR_TYPE_ROOT_CAUSE_FOUND**

## Root cause

create_generated_equipment_item_for_slot passes armor_type=armor_type to redistribute_identity_primary_stats, but armor_type is neither a parameter nor a local/direct module-level assignment. Every forced-slot call reaches NameError before allocate_generated_item_id and before items INSERT. Random loot and shop preview define armor_type and are unaffected.

## Scope

- All 10 forced slots are affected before allocation/INSERT.
- Random loot and shop preview are unaffected.

## Stage 20.6.5b

Initialize armor_type before slot branching. Resolve canonical armor identity for armor slots; keep empty armor_type for main-hand, off-hand and jewelry. Preserve item_profile and identity-aware policy.

Required tests:
- all 10 forced slots
- cloth/leather/chain/plate
- main/off-hand subtypes
- necklace/ring universal stats
- invalid identity fail-closed
- no orphan item/ID
- random loot regression
- shop preview/permanent parity

Production code and DB were unchanged. Manual verification is not required.
