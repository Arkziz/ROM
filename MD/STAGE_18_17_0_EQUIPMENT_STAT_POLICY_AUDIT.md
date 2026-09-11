# Stage 18.17.0: Equipment Stat Policy Read-only Audit

**Status:** PASS
**Production mutation:** none

## Findings

- Total findings: **16**.
- Severity: `{'HIGH': 15, 'MEDIUM': 1}`.
- Armor class restrictions and PDEF/MDEF identity are already present.
- Primary-stat generation remains partly armor-type, slot and subtype based rather than target-class based.
- Shared cloth and leather profiles do not distinguish Mage/Priest and Scout/Rogue.
- Necklace and ring pools are not class-aware.
- Existing generated items should not be rewritten automatically.

## Approximate plan

1. 18.17.1 canonical class-aware policy and validator.
2. 18.17.2 integrate target_class into new generated equipment.
3. 18.17.3 deterministic class/slot/subtype/rarity regressions.
4. 18.17.4 static catalog and shop/loot/preview/comparison parity.
5. 18.17.5 manual acceptance and closure.

## Database safety

- quick_check: `ok`.
- FK violations: `0`.
- DB unchanged: `True`.
- Generated rows inspected: `32`.
