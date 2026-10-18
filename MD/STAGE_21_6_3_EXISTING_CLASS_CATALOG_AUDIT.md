# Stage 21.6.3 — Existing V1 class catalog audit

## Scope

Read-only AST audit of the existing V1 class and equipment owners. No V1 module was imported, no database was opened, and no V2 production implementation was created.

## Authoritative sources

- `data/classes.py`
- `data/equipment_profiles.py`
- `data/equipment_stat_policy.py`
- `data/equipment_identity_stat_policy.py`

## Class parity matrix

### `warrior`

- resource: `rage`
- explicit attack type: `None`
- armor types: `chain`
- main-hand subtypes: `['sword_1h', 'sword_2h']`
- off-hand subtypes: `['warrior_shield']`

### `knight`

- resource: `rage`
- explicit attack type: `None`
- armor types: `plate`
- main-hand subtypes: `['sword_1h']`
- off-hand subtypes: `['shield']`

### `scout`

- resource: `combat_energy`
- explicit attack type: `None`
- armor types: `leather`
- main-hand subtypes: `['bow_2h', 'crossbow_2h']`
- off-hand subtypes: `[]`

### `rogue`

- resource: `combat_energy_combo`
- explicit attack type: `None`
- armor types: `leather`
- main-hand subtypes: `['dagger_1h']`
- off-hand subtypes: `['dagger']`

### `mage`

- resource: `mana`
- explicit attack type: `None`
- armor types: `cloth`
- main-hand subtypes: `['wand_1h', 'staff_2h']`
- off-hand subtypes: `['talisman']`

### `priest`

- resource: `mana`
- explicit attack type: `None`
- armor types: `cloth`
- main-hand subtypes: `['wand_1h', 'staff_2h']`
- off-hand subtypes: `['talisman']`

## Decision

Conclusion: `GO`
Blockers: `[]`

A V2 mutation patch is permitted only when this report is PASS/GO. The implementation must be named `patch_21_6_3a_implement_class_catalog.py` and must reproduce this evidence without adding equipment, resources, formulas, or rules.

## Manual game check

Not required. This audit is static and read-only.
