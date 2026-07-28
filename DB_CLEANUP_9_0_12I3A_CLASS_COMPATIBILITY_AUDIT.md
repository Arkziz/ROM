# ROM 9.0.12i3a — Class Compatibility Audit

## Scope

Read-only audit. No legacy code or captures were removed.

## Structural results

- `can_equip_item_by_class`: db.py definitions=2; equipment_system.py definitions=1; final db wrapper delegates to equipment_system.
- `can_equip_inventory_item_by_class`: db.py definitions=2; equipment_system.py definitions=1; final db wrapper delegates to equipment_system.
- `is_inventory_item_class_compatible`: db.py definitions=2; equipment_system.py definitions=1; final db wrapper delegates to equipment_system.

## Legacy captures

- `_legacy_equipment_ro_v1_can_equip_item_by_class`: present and callable; API `can_equip_item_by_class`.
- `_legacy_equipment_ro_v1_can_equip_inventory_item_by_class`: present and callable; API `can_equip_inventory_item_by_class`.
- `_legacy_equipment_ro_v1_is_inventory_item_class_compatible`: present and callable; API `is_inventory_item_class_compatible`.

## Runtime contracts

- Result for missing item is `dict` with `success` and `message`.
- Non-equipment synthetic item is accepted.
- Boolean helper contract passed: True.
- Existing read-only public/legacy/system comparisons: 27.
- Mismatches: 0.

## Conclusion

The three captures remain required because equipment_system still delegates these APIs through `_call_legacy`. Physical removal is not part of i3a.

If the boolean helper contract is false, this confirms a recursive legacy/public delegation risk that must be removed by direct implementation in equipment_system before capture cleanup.

Next safe step: implement these three functions directly in systems/equipment_system.py, then repeat equivalence tests before removing captures.
