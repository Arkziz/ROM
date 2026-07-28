# ROM 9.0.12i6a - Equipment Read-only Duplicates Audit

## Scope

Read-only audit. No gameplay code or database rows were changed.

## Cleanup candidates

- `ensure_equipment_slots`: db definitions=2, db lines=[314, 11239], system definitions=2, public signature=`(*args, **kwargs)`, final system signature=`(user_id)`
- `get_all_equipped_items`: db definitions=2, db lines=[449, 11242], system definitions=5, public signature=`(*args, **kwargs)`, final system signature=`(user_id)`
- `get_inventory_detailed`: db definitions=3, db lines=[748, 9856, 11248], system definitions=2, public signature=`(*args, **kwargs)`, final system signature=`(user_id)`
- `get_inventory_entry`: db definitions=3, db lines=[835, 9909, 11251], system definitions=2, public signature=`(*args, **kwargs)`, final system signature=`(user_id, inventory_id)`
- `get_item_by_inventory_id`: db definitions=3, db lines=[777, 9879, 11254], system definitions=2, public signature=`(*args, **kwargs)`, final system signature=`(inventory_id)`
- `get_item_by_inventory_id_full`: db definitions=3, db lines=[805, 9894, 11257], system definitions=2, public signature=`(*args, **kwargs)`, final system signature=`(inventory_id)`
- `get_item_bonuses`: db definitions=2, db lines=[1065, 11260], system definitions=2, public signature=`(*args, **kwargs)`, final system signature=`(user_id)`
- `get_equipped_item_defenses`: db definitions=2, db lines=[1114, 11263], system definitions=2, public signature=`(*args, **kwargs)`, final system signature=`(user_id)`
- `get_sellable_equipment_items`: db definitions=3, db lines=[2569, 9924, 11266], system definitions=2, public signature=`(*args, **kwargs)`, final system signature=`(user_id)`
- `get_inventory_refine_level`: db definitions=2, db lines=[9272, 11281], system definitions=2, public signature=`(*args, **kwargs)`, final system signature=`(inventory_id)`
- `get_inventory_refined_display_name`: db definitions=2, db lines=[9772, 11284], system definitions=2, public signature=`(*args, **kwargs)`, final system signature=`(inventory_id, name=None)`
- `format_refined_item_name`: db definitions=2, db lines=[9753, 11287], system definitions=2, public signature=`(*args, **kwargs)`, final system signature=`(name, refine_level)`
- `init_weapon_damage_system`: db definitions=3, db lines=[3709, 4166, 11269], system definitions=2, public signature=`(*args, **kwargs)`, final system signature=`()`
- `calculate_weapon_damage_by_values`: db definitions=3, db lines=[3758, 4385, 11272], system definitions=2, public signature=`(*args, **kwargs)`, final system signature=`(item_level, rarity, weapon_hands=1)`
- `get_weapon_damage_by_inventory_id`: db definitions=5, db lines=[3792, 4451, 9511, 9676, 11275], system definitions=2, public signature=`(*args, **kwargs)`, final system signature=`(inventory_id)`
- `get_inventory_weapon_damage_display`: db definitions=2, db lines=[3978, 11278], system definitions=2, public signature=`(*args, **kwargs)`, final system signature=`(inventory_id)`

## Runtime

- Public/system read-only comparisons: 179
- Pure API comparisons: 2
- Mismatches: 0
- Final system implementations using `_call_legacy`: 0
- Database mutations: 0

## Recommendation

Proceed to 9.0.12i6b. Remove all earlier db.py definitions for these 16 APIs, preserve only final facade wrappers, and rerun the existing equipment readonly, inventory/refine, weapon-damage, trader, player-stat, core, and import tests.
