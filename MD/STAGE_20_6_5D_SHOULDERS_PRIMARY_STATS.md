# Stage 20.6.5d — Restore Shoulders Primary Stats

Corrected the misinterpreted shoulders requirement.

Shoulders now generate:

- base PDEF and MDEF;
- a base primary-stat chunk for common rarity;
- normal additional primary-stat chunks for uncommon, rare and epic rarity.

The raw shoulders pool is `STA / STR`. The existing source-specific resolver then applies the final policy:

- base shop: buyer-class primary stats;
- mob loot: armor-type identity primary stats.

The early defense-only return introduced by Stage 20.6.5c was removed. Forced-slot armor routing, shop jewelry class policy, mob-loot identity policy, existing items and database schema are unchanged.
