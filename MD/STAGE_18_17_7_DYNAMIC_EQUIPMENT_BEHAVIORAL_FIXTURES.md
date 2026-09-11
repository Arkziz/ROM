# Stage 18.17.7: Dynamic Equipment Behavioral Fixtures

**Status:** PASS
**Production mutation:** none

## Behavioral parity

The six same-signature but AST-different helper functions were compared deterministically between `db_modules.generated_equipment` and `systems.dynamic_equipment_system`.

- `add_primary_stat_to_stats`: `40` fixtures PASS.
- `apply_armor_type_defense_profile_to_stats`: `700` fixtures PASS.
- `apply_armor_type_primary_stat_profile_to_stats`: `700` fixtures PASS.
- `clear_primary_stat_bonuses`: `5` fixtures PASS.
- `get_existing_primary_stat_budget`: `5` fixtures PASS.
- `pick_weighted_stat`: `500` fixtures PASS.

Total fixtures: **1950**.

## Verified behavior

- Return values, exception contracts and in-place argument mutations are equal.
- Weighted RNG behavior is equal for identical seeds.
- Unknown and empty armor profiles remain behaviorally equal.
- Cloth and plate defense identities remain intact.
- Custom dictionary fields remain preserved equally.

## Consolidation decision

The six previously blocked helpers are behaviorally equivalent and may be replaced by thin compatibility delegates while preserving their current signatures.

## Database safety

- quick_check: `ok`.
- FK violations: `0`.
- DB unchanged: `True`.
