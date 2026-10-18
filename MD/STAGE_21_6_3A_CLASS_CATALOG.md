# Stage 21.6.3a — Source-faithful V2 class catalog

Implemented solely from the accepted Stage 21.6.3 V1 parity audit. The canonical owner is `rom_v2.domain.class_catalog.DEFAULT_CLASS_CATALOG`. It reproduces the six audited keys, existing display names and descriptions, exact resource keys, armor types, and main/off-hand subtype compatibility. No class-level attack type, initial stat values, HP/MP formulas, or new equipment has been added. `CharacterService` rejects unknown keys before opening a Unit of Work. Manual game verification is not required.
