# Stage 18.30.4b

Propagates equipment `armor_type`, `item_subtype`, and `weapon_hands` into the actual simulation inventory item. Reporting now mirrors the production-facing Ukrainian format: rarity icon, canonical item name, optional armor type in square brackets, level, and optional refine suffix.

Examples: `⚪ Поножі [Шкіра] 5 рівня`, `⚪ Лук 5 рівня`, `🟢 Шолом [Шкіра] 7 рівня +3`.

The simulation continues to produce exactly three transferable report files.
