# Stage 18.17.3: Equipment Drop and Shop Parity

**Status:** PASS
**Production mutation:** none

## Verified contract

- Class-aware mob drops, forced-slot generation and base-shop previews use the same canonical policy.
- Purchase promotion does not regenerate or reroll the preview snapshot.
- All six classes, armor, weapon, jewelry and supported off-hand routes are covered deterministically.
- Primary-stat budget and PDEF/MDEF are preserved.
- Existing generated items and game.db are unchanged.

## Compatibility decision

- Item creation remains owned by `db_modules/generated_equipment.py`.
- `systems/dynamic_equipment_system.py` does not create items.
- Duplicate calculation helpers remain and require a separate import-surface audit before consolidation.

## Database safety

- quick_check: `ok`.
- FK violations: `0`.
- DB unchanged: `True`.
