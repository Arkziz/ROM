# ROM 9.0.12i6c - Equipment Write Repair Trader Audit

## Scope

Structural audit plus protected missing-ID runtime checks. No real user rows were changed.

## Cleanup candidates

- `equip_inventory_item`: db definitions=3, db lines=[831, 7049, 10523], system definitions=2, public signature=`(*args, **kwargs)`, final system signature=`(user_id, inventory_id)`
- `unequip_inventory_item`: db definitions=2, db lines=[905, 10526], system definitions=2, public signature=`(*args, **kwargs)`, final system signature=`(user_id, inventory_id)`
- `unequip_incompatible_items_after_class_change`: db definitions=3, db lines=[7133, 8429, 10529], system definitions=2, public signature=`(*args, **kwargs)`, final system signature=`(user_id)`
- `calculate_repair_cost`: db definitions=2, db lines=[1211, 10553], system definitions=2, public signature=`(*args, **kwargs)`, final system signature=`(durability, rarity)`
- `repair_equipped_item`: db definitions=3, db lines=[1312, 4907, 10547], system definitions=2, public signature=`(*args, **kwargs)`, final system signature=`(user_id, inventory_id)`
- `repair_all_equipped`: db definitions=3, db lines=[1419, 5018, 10550], system definitions=2, public signature=`(*args, **kwargs)`, final system signature=`(user_id)`
- `damage_equipped_items_on_death`: db definitions=2, db lines=[1498, 10556], system definitions=3, public signature=`(*args, **kwargs)`, final system signature=`(user_id, amount=5)`
- `sell_inventory_item_to_trader`: db definitions=3, db lines=[2355, 4737, 10559], system definitions=2, public signature=`(*args, **kwargs)`, final system signature=`(user_id, inventory_id)`
- `buy_item_for_gold`: db definitions=3, db lines=[1126, 4656, 10565], system definitions=2, public signature=`(*args, **kwargs)`, final system signature=`(user_id, item_id, price, quantity=1)`
- `buy_common_equipment_from_trader`: db definitions=4, db lines=[2284, 4336, 4815, 10562], system definitions=2, public signature=`(*args, **kwargs)`, final system signature=`(user_id, slot_key, item_profile=None)`

## Runtime

- Repair-cost equivalence cases: 40
- Protected missing-ID comparisons: 9
- Mismatches: 0
- Final system implementations using `_call_legacy`: 0
- Rows created by protected checks: 0

## Existing isolated contract suites

- `smoke_test_equipment_write_contracts.py`
- `smoke_test_equipment_durability_contracts.py`
- `smoke_test_equipment_trader_contracts.py`

## Recommendation

Proceed to 9.0.12i6d. Remove all earlier db.py definitions for these 10 APIs, retain only final wrappers, and rerun write, class compatibility, durability, trader, read-only, player-stat, core, import, and readiness checks.
