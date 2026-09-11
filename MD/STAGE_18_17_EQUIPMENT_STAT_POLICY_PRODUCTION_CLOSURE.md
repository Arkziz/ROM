# Stage 18.17: Class-aware Equipment Stat Policy Production Closure

**Status:** CLOSED
**Manual acceptance:** PASS
**Production database migration:** none

## Objective

Stage 18.17 makes newly generated equipment class-aware across mob loot and the base equipment shop while preserving armor defense identity, rarity budgets, weapon damage, preview-to-purchase consistency and existing player-owned items.

## Authoritative architecture

- `data/equipment_stat_policy.py` is the single source of class stat rules, allowed armor types, weapon subtypes, off-hand subtypes and weighted primary-stat choices.
- `db_modules/generated_equipment.py` is the canonical calculation and generated-item creation owner.
- `db_modules/shop.py` owns base-shop preview and purchase integration.
- `systems/dynamic_equipment_system.py` is a thin lazy compatibility delegate with no SQL, balance tables, independent RNG logic or item creation.

## Class profiles

- Warrior: STR 60%, STA 30%, DEX 10%.
- Knight: STA 50%, STR 45%, DEX 5%.
- Scout: STR 45%, DEX 45%, STA 10%.
- Rogue: DEX 60%, STR 30%, STA 10%.
- Mage: INT 65%, WIS 25%, STA 10%.
- Priest: INT 50%, WIS 40%, STA 10%.

These percentages are weighted stat-selection probabilities. They are not PATK/MATK coefficients and do not increase the total generated stat budget.

## Equipment rules

- Mage and Priest use cloth.
- Scout and Rogue use leather.
- Warrior uses chain.
- Knight uses plate.
- Knight shield generates only STA and STR, weighted 65% and 35% for shield-specific selection.
- Warrior and Knight swords may receive rare DEX as a secondary class stat.
- Scout keeps both bow and crossbow subtypes.
- Jewelry is class-aware: physical classes use STR/DEX/STA profiles; magical classes use INT/WIS/STA profiles.

## Armor defense identity

The existing armor defense distribution remains unchanged:

- Cloth emphasizes MDEF.
- Leather remains comparatively balanced.
- Chain emphasizes PDEF.
- Plate has the strongest PDEF emphasis.

Class-aware primary-stat redistribution does not alter the already calculated PDEF/MDEF values.

## Generation and shop flow

- Class-aware mob loot applies the target character class only when the class-aware branch is selected.
- Forced-slot generation and new base-shop previews always use the target user's class.
- Preview creation generates the item once.
- Purchase promotes the preview to a permanent generated item and does not reroll stats.
- Existing generated and historical preview items are not migrated or recalculated.

## Legacy route consolidation

The broken legacy class-shop route no longer imports the missing `generate_equipment_item` symbol and no longer inserts a full parallel random shop into `items`. Its public functions remain available as read-only canonical offer descriptors.

## Verification

- Seven maintained Stage 18.17 tests PASS.
- Drop/shop parity: 58 routes and 11,600 deterministic samples PASS.
- Dynamic-equipment behavioral parity: 1,950 fixtures PASS.
- Seventeen compatibility helpers preserve their signatures and delegate to the canonical owner.
- `py_compile`, imports, structural contracts, exception contracts and RNG seed behavior PASS.
- `PRAGMA quick_check`: ok.
- Foreign-key violations: 0.
- `game.db` remained unchanged during closure.
- WAL/SHM were not manipulated.

## Manual acceptance

Manual verification was completed successfully after Stage 18.17.8. The base shop, class-appropriate stats, preview and purchase consistency, inventory, comparison, equip flow, PvE and restart were accepted without runtime traceback.

## Known nuances

- The class-aware policy applies to newly generated class-aware loot and new base-shop previews; existing generated items are not rewritten.
- Unrestricted loot remains unrestricted when class_aware_chance selects the random branch.
- Selection weights guide which primary stats receive existing generated stat chunks; they do not change the total stat budget.
- The legacy class-shop public signatures remain as read-only compatibility catalog adapters and do not populate items or previews.
- systems.dynamic_equipment_system remains import-compatible but delegates calculations to db_modules.generated_equipment.

## Superseded point-in-time audits

Stages 18.17.0, 18.17.4 and 18.17.5 remain historical evidence. Their pre-mutation findings are intentionally superseded by the current production invariants and are not treated as present defects.

## Final decision

Stage 18.17 is closed. No additional implementation patch is required unless a new runtime defect is discovered. Continue with Stage 18.18 according to the current roadmap.
