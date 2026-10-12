# Stage 20.6.4a — Identity-aware Equipment Policy

## Decision

**IDENTITY_AWARE_EQUIPMENT_STATS_APPROVED**

This policy supersedes Stage 20.6.4 before any production mutation was applied.

## Core rule

The receiving character class never rewrites item stats. Weapon/off-hand stats follow subtype identity, armor stats follow armor type, and jewelry uses a universal fully random STR/DEX/INT/WIS/STA pool.

## Examples

- Rogue receives `staff_2h` → INT/WIS/STA.
- Mage receives `dagger_1h` → DEX/STR/STA.
- Rogue receives cloth armor → INT/WIS/STA.
- Scout receives leather armor → DEX/STR/STA.
- Any class receives jewelry → fully random universal primary stats.

## class_aware_chance

The chance is preserved and controls only how often the selected identity is wearable by the recipient. It does not rewrite stats after identity selection.

## Safety

- Existing items are unchanged.
- Unknown identity fails closed.
- No database schema change.
- Stage 20.6.5 must implement one canonical identity-aware resolver for shop, loot, event, DEV and simulator paths.
