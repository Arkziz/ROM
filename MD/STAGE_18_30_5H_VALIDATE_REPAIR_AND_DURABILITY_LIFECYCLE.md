# Stage 18.30.5h

One vertical slice validates and aligns the simulation repair and durability lifecycle.

The simulator now visits maintenance and repairs equipped items when durability is at or below 15%. Durability 16% is not repaired, while 15% is repaired. Death continues to subtract exactly 5 durability from every equipped item, clamps at zero, and ignores unequipped items. Repair cost remains delegated through the canonical `systems.equipment_system.calculate_repair_cost` owner via the existing simulation canonical rule.

The maintained smoke covers the 16/15/14 boundary, canonical cost parity, exact and insufficient gold, deterministic partial repair, zero-durability recovery, breaking semantics, and non-equipped isolation. No gameplay production owner or database file is modified.
