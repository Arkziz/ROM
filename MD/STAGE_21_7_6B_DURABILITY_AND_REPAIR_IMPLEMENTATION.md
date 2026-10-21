# Stage 21.7.6b — Durability and repair implementation

- Status: **PASS**
- Evidence: **API_READY**
- Runtime dispatch connected: **False**
- Database opened: **False**
- Manual game check: **NOT_REQUIRED**

## Implemented V1 contracts

- durability is clamped to `0..100`;
- death removes exactly `5` durability from equipped items;
- durability `0` disables base equipment, rune and enhancement contribution;
- repair cost uses `(100 - durability) × rarity multiplier × 0.05`;
- multipliers: common `1.0`, uncommon `2.5`, rare `7.0`, epic `18.0`;
- repair targets the exact owned equipped `inventory_id`;
- reservation fails closed;
- debit and persistent repair are one gateway transaction;
- repair-all is all-or-nothing at the same atomic gateway boundary.

## Boundary

This stage supplies the canonical domain/application API. Telegram/runtime dispatch and a production database adapter are intentionally not connected before their roadmap consumer stage. No V1 database was opened or migrated.
