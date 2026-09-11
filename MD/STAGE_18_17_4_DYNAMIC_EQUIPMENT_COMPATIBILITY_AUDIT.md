# Stage 18.17.4: Dynamic Equipment Compatibility Read-only Audit

**Status:** PASS
**Production mutation:** none

## Import surface

- Shared function names: **17**.
- Referenced dynamic symbols: `['apply_armor_type_defense_profile_to_stats', 'generate_dynamic_equipment_stats', 'generate_equipment_item', 'get_dynamic_armor_name', 'get_dynamic_sell_price', 'get_dynamic_weapon_name', 'init_dynamic_equipment_system']`.
- Public `__all__`: `['init_dynamic_equipment_system', 'get_dynamic_weapon_name', 'get_dynamic_armor_name', 'generate_dynamic_equipment_stats', 'apply_armor_type_defense_profile_to_stats', 'get_dynamic_sell_price']`.
- Missing referenced symbols: `['generate_equipment_item']`.
- Missing symbols are audit findings and consolidation blockers, not audit execution failures.

## Consolidation classification

- Byte-equivalent delegate candidates: `['add_stat_value', 'generate_dynamic_equipment_stats', 'get_dynamic_armor_name', 'get_dynamic_sell_price', 'get_dynamic_stat_value', 'get_dynamic_weapon_name', 'get_profile_for_generated_item', 'get_random_main_hand_profile', 'get_random_off_hand_profile', 'init_dynamic_equipment_system', 'normalize_equipment_restriction_value']`.
- Same-signature but behavior-different functions: `['add_primary_stat_to_stats', 'apply_armor_type_defense_profile_to_stats', 'apply_armor_type_primary_stat_profile_to_stats', 'clear_primary_stat_bonuses', 'get_existing_primary_stat_budget', 'pick_weighted_stat']`.
- Signature mismatches: `[]`.

## Decision

- Do not remove compatibility functions by name alone.
- Preserve the current public import surface.
- Add behavioral fixtures before replacing non-equivalent implementations with delegates.
- Resolve or retire the legacy `generate_equipment_item` reference before consolidation.
- Item creation remains owned by `db_modules/generated_equipment.py`.

## Database safety

- quick_check: `ok`.
- FK violations: `0`.
- DB unchanged: `True`.
