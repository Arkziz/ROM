# Stage 21.14.1a - Refined Item ID Namespace Contract

- Status: **PASS**
- Conclusion: **GO_TO_PARITY_RESOLUTION**
- Contracts: **12 refined / 0 review required**
- Implementation authorized: **False**

## Refined namespaces

- Static catalog: explicit canonical IDs/bands; all gaps remain `UNASSIGNED_RESERVED`.
- Story quest items: `(user_id, quest_id, item_key)`; no numeric `item_id` or `inventory_id`.
- Event items: `4000-9999`, 25 IDs per immutable block, 240 blocks.
- Generated permanent: `10000-10009999`, persistent never-reuse allocator.
- Shop preview: `10010000-11009999`, temporary preview identity followed by atomic promotion.

## Event block arithmetic

- `4024 - 4000 + 1 = 25`
- `4049 - 4025 + 1 = 25`
- `9999 - 9975 + 1 = 25`
- `(9999 - 4000 + 1) / 25 = 240`

## Next patch

`patch_21_14_1b_resolve_item_id_namespace_parity.py`
