# Stage 21.10.3a - Refined Base Equipment Shop contract

- Status: **PASS**
- Conclusion: **REVIEW_REQUIRED**
- V1-confirmed rows: **16**
- Review-required rows: **6**
- Production changed: **False**
- Database opened: **False**
- Manual game check: **NOT_REQUIRED**

## Authoritative context owners

- `canonical_shop_owner`: `db_modules/shop.py`
- `item_id_allocator`: `systems/item_id_allocator_system.py`
- `presentation_boundary`: `handlers/city.py`
- `generated_equipment`: `db_modules/generated_equipment.py`
- `equipment_compatibility`: `db_modules/equipment.py`

## Contract matrix

- `CANONICAL_SHOP_OWNER`: **V1_CONFIRMED** - V1 centralizes the base equipment offer flow in db_modules/shop.py.
- `CLASS_AWARE_MAIN_HAND_PROFILES`: **V1_CONFIRMED** - Main-hand offers are filtered through explicit class-aware shop profiles.
- `CLASS_AWARE_OFF_HAND_PROFILES`: **V1_CONFIRMED** - Off-hand offers are filtered through explicit class-aware shop profiles.
- `SUBOFFER_OWNER`: **V1_CONFIRMED** - Typed suboffers remain owned by the canonical shop module.
- `PRICE_OWNER`: **V1_CONFIRMED** - V1 has a dedicated base-equipment slot-price owner.
- `PREVIEW_CREATION`: **V1_CONFIRMED** - V1 creates a persisted preview before confirmation.
- `PREVIEW_READ`: **V1_CONFIRMED** - Preview reads are owned by the canonical shop module.
- `PREVIEW_CANCELLATION`: **V1_CONFIRMED** - Cancellation is an explicit preview lifecycle operation.
- `CONFIRMATION_OWNER`: **V1_CONFIRMED** - V1 has a dedicated confirmation boundary before purchase settlement.
- `PURCHASE_OWNER`: **V1_CONFIRMED** - Purchase settlement is owned by the canonical shop module.
- `PREVIEW_ID_ALLOCATOR`: **V1_CONFIRMED** - Preview identity is allocated by the shared item-id allocator.
- `PERMANENT_PROMOTION_OWNER`: **V1_CONFIRMED** - V1 promotes the purchased preview into permanent identity through the allocator.
- `STRANDED_PREVIEW_RECOVERY`: **V1_CONFIRMED** - V1 exposes restart recovery for a stranded preview promotion.
- `CLASS_AWARE_GENERATION`: **V1_CONFIRMED** - Generated shop equipment is class-aware before preview creation.
- `PRESENTATION_SHOP_BOUNDARY`: **V1_CONFIRMED** - The city handler renders shop presentation and is not the mutation owner.
- `PRESENTATION_CONFIRM_BOUNDARY`: **V1_CONFIRMED** - The confirmation handler delegates to the shop domain path.
- `OFFER_AND_SUBOFFER_IDENTITY`: **REVIEW_REQUIRED** - Stable technical offer/suboffer keys and stale-selection behavior require bounded parity resolution.
- `PREVIEW_SNAPSHOT_AND_EXPIRY`: **REVIEW_REQUIRED** - Exact preview snapshot fields, ownership, expiry and cleanup semantics require explicit resolution.
- `PRICE_AND_GOLD_DEBIT_SNAPSHOT`: **REVIEW_REQUIRED** - Price locking, insufficient-gold rejection and debit ownership require one canonical transaction boundary.
- `INVENTORY_CAPACITY_AND_INSERTION`: **REVIEW_REQUIRED** - Inventory capacity checks and exact item insertion order must be fixed before mutation.
- `PROMOTION_ATOMICITY_AND_IDEMPOTENCY`: **REVIEW_REQUIRED** - Preview promotion, permanent ID allocation, purchase replay and rollback require exact-once semantics.
- `CONSUMER_ALLOWLIST_AND_SHADOW_OWNERS`: **REVIEW_REQUIRED** - Presentation wrappers, legacy trader purchase paths and direct SQL mutations require an explicit migration allowlist.

## Unresolved contracts

- `OFFER_AND_SUBOFFER_IDENTITY`
- `PREVIEW_SNAPSHOT_AND_EXPIRY`
- `PRICE_AND_GOLD_DEBIT_SNAPSHOT`
- `INVENTORY_CAPACITY_AND_INSERTION`
- `PROMOTION_ATOMICITY_AND_IDEMPOTENCY`
- `CONSUMER_ALLOWLIST_AND_SHADOW_OWNERS`

Implementation remains unauthorized until offer identity, preview snapshot/expiry, price and gold-debit snapshot, inventory insertion, promotion atomicity/idempotency, consumer allowlist and shadow mutation paths are resolved from V1 evidence.
