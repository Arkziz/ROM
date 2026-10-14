# Stage 20.6.5 — Identity-aware Generated Equipment Stats

Implemented `IDENTITY_AWARE_PRIMARY_STATS_WITH_WEIGHTED_DROP_SUITABILITY`.

- Main-hand and off-hand primary stats are resolved from item subtype.
- Armor primary stats are resolved from armor type.
- Necklace and ring use an equal-weight universal STR/DEX/INT/WIS/STA pool.
- Recipient class never rewrites stats.
- `class_aware_chance` still controls how often item identity suits the recipient.
- Shop, forced-slot and dropped-equipment generation use the same resolver.
- Unknown identity fails closed before persistence.
- Existing items, drop chances, rarity, budgets, secondary bonuses, equipment restrictions and DB schema remain unchanged.

Manual verification is required with representative weapon, armor and jewelry drops, plus shop preview/purchase parity.
