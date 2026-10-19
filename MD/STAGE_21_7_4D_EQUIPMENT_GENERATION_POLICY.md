# Stage 21.7.4d — Equipment generation policy

Canonical V2 `EquipmentGenerationService` now owns source-aware orchestration. Identity selection and numeric stat generation remain separate policy ports. `item_level` is the single generation and persisted-level semantic; `required_level` exposes the same value for equip validation. Shop class identity, loot weapon/off-hand identity, armor type, universal dropped jewelry, DEV delegation and simulator delegation are enforced without introducing V2 formulas.

## Manual game check

`NOT_REQUIRED`. Telegram and V1 runtime consumers are not switched by this foundation patch.
