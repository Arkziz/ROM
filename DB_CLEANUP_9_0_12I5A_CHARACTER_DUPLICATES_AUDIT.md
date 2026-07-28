# ROM 9.0.12i5a - Character Duplicates Audit

## Scope

Read-only audit. No gameplay code or database rows were changed.

## Cleanup candidates

- `normalize_character_name`: db definitions=2, db lines=[6291, 11473], system definitions=1, public signature=`(name)`, system signature=`(name)`
- `validate_character_name`: db definitions=2, db lines=[6300, 11477], system definitions=1, public signature=`(name)`, system signature=`(name)`
- `get_character_name`: db definitions=2, db lines=[6239, 11481], system definitions=1, public signature=`(user_id)`, system signature=`(user_id)`
- `set_character_name`: db definitions=3, db lines=[6330, 9507, 11485], system definitions=1, public signature=`(user_id, name)`, system signature=`(user_id, name)`
- `get_character_class`: db definitions=2, db lines=[6256, 11489], system definitions=1, public signature=`(user_id)`, system signature=`(user_id)`
- `set_character_class`: db definitions=2, db lines=[6355, 11493], system definitions=1, public signature=`(user_id, class_key)`, system signature=`(user_id, class_key)`
- `get_character_class_display`: db definitions=2, db lines=[6273, 11497], system definitions=1, public signature=`(user_id)`, system signature=`(user_id)`
- `get_character_resource_type`: db definitions=2, db lines=[6282, 11501], system definitions=1, public signature=`(user_id)`, system signature=`(user_id)`
- `get_max_mp`: db definitions=2, db lines=[6397, 11513], system definitions=1, public signature=`(user_id)`, system signature=`(user_id)`
- `get_user_mp`: db definitions=3, db lines=[6476, 6885, 11505], system definitions=2, public signature=`(user_id)`, system signature=`(user_id)`
- `set_user_mp`: db definitions=2, db lines=[6910, 11509], system definitions=1, public signature=`(user_id, mp)`, system signature=`(user_id, amount)`
- `refresh_user_mp`: db definitions=3, db lines=[6419, 6802, 11517], system definitions=1, public signature=`(user_id)`, system signature=`(user_id)`
- `grant_class_change_available`: db definitions=4, db lines=[6513, 6530, 6626, 11521], system definitions=1, public signature=`(user_id, amount=1)`, system signature=`(user_id, amount=1)`
- `consume_class_change_available`: db definitions=3, db lines=[6547, 6643, 11525], system definitions=1, public signature=`(user_id)`, system signature=`(user_id)`
- `has_class_change_available`: db definitions=2, db lines=[6609, 11533], system definitions=1, public signature=`(user_id)`, system signature=`(user_id)`

## Manual review / not part of automatic cleanup

- `get_class_change_available`: only one db wrapper; do not delete.
- Unique helpers are not duplicate db cleanup candidates: `is_character_name_taken`, `needs_character_name`, `needs_character_class`, `get_class_reset_sphere_item_id`.

## Runtime

- Getter comparisons: 40
- Pure-function comparisons: 10
- Mismatches: 0
- Database mutations: 0

## Recommendation

Proceed to 9.0.12i5b with isolated mutation tests for name/class/MP/class-change writes. After equivalence succeeds, i5c may remove only the confirmed earlier db.py definitions while preserving final wrappers and unique helpers.
