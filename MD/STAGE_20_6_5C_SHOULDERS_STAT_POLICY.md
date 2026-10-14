# Stage 20.6.5c — Localized Shoulders Stat Policy

The defense-only contract now belongs to the authoritative `shoulders` branch in `generate_dynamic_equipment_stats()`.

- Shoulders assign PDEF and MDEF and return immediately.
- Shoulders never enter the shared rarity primary-stat bonus loop.
- The shared rarity loop is generic again and contains no slot-specific exception.
- Common, uncommon, rare and epic shoulders have zero STR/DEX/INT/WIS/STA.
- Non-shoulder rarity bonuses remain unchanged.

No database, existing item, shop policy, loot identity policy, drop chance or equipment restriction was changed.
