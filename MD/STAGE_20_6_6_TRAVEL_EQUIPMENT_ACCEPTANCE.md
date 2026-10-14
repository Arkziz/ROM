# Stage 20.6.6 — Travel and Equipment Generation Acceptance

## Decision

**STAGE 20.6 ACCEPTED**

Final accepted behavior:

- travel has canonical localized preview, active and arrival text for all four directions;
- City map is informative, unknown location IDs fail closed, duration remains 20 seconds;
- base shop identity and primary stats are strict buyer-class-aware, including jewelry;
- mob-loot weapon/off-hand and armor stats follow item identity; dropped jewelry uses the universal five-stat pool;
- forced-slot generation has a valid armor identity and no undefined `armor_type`;
- shoulders have PDEF/MDEF plus primary stats for common, uncommon, rare and epic rarities;
- Stage 20.6.4 STRICT-recipient decision was superseded by 20.6.4a identity-aware loot policy;
- Stage 20.6.5c defense-only shoulders interpretation was superseded by 20.6.5d.

Production code and database were not changed by acceptance. No additional manual verification is required.
