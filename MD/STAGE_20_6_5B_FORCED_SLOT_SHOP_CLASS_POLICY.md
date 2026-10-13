# Stage 20.6.5b — Forced-slot and Shop Class Policy

Implemented the approved source-specific policy:

- **Base shop:** item identity and all primary stats, including ring/necklace, are strict class-aware for the buyer. Rogue shop jewelry can contain only DEX/STR/STA.
- **Mob loot:** weapon/off-hand stats follow item subtype, armor stats follow armor type, and dropped jewelry keeps the universal STR/DEX/INT/WIS/STA pool.
- **Forced-slot generation:** `armor_type` is initialized safely. Armor slots use the recipient class canonical armor type; weapon/off-hand/jewelry use an empty armor type.
- **Shoulders:** generate PDEF/MDEF only. They receive no STR/DEX/INT/WIS/STA, including rarity bonus rolls.

Existing items, route/drop suitability chances, equipment restrictions, database schema and stored data are unchanged.

Manual verification is required for Rogue shop ring/amulet, forced-slot armor, defense-only shoulders, identity-aware mob loot and universal dropped jewelry.
