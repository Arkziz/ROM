# Stage 21.10.3b - Resolved Base Equipment Shop parity

- Status: **PASS**
- Conclusion: **GO_TO_IMPLEMENTATION**
- Resolved contracts: **6/6**
- Remaining unresolved contracts: **0**
- Production changed: **False**
- Database opened: **False**
- Manual game check: **NOT_REQUIRED**

## Resolutions

### OFFER_AND_SUBOFFER_IDENTITY

Use stable technical offer_key and suboffer_key values derived from canonical slot/profile identifiers. Presentation labels are never identifiers. Unknown, mismatched or stale keys fail closed before mutation.

### PREVIEW_SNAPSHOT_AND_EXPIRY

A preview is an immutable user-owned snapshot containing preview_id, user_id, offer_key, suboffer_key, class_key, generated item snapshot, quoted_price and created_at. Only one active preview per user/offer context is authoritative; cancel, replacement and expiry invalidate it without consuming a permanent ID.

### PRICE_AND_GOLD_DEBIT_SNAPSHOT

Confirmation uses the quoted_price stored in the preview. Sufficient gold is checked before promotion or inventory mutation. Gold debit, promotion, inventory insertion and receipt share one caller-owned Unit of Work and one commit.

### INVENTORY_CAPACITY_AND_INSERTION

Inventory capacity and user ownership are validated before the first mutation. A purchased promoted item is inserted exactly once with the preview's complete equipment snapshot; full inventory fails closed without debit or promotion.

### PROMOTION_ATOMICITY_AND_IDEMPOTENCY

Confirmation requires a stable operation_key. Same key and same preview payload replay the original receipt. Changed payload conflicts. Preview-to-permanent promotion allocates one never-reused permanent ID and commits atomically with debit and insertion; rollback leaves no partial purchase.

### CONSUMER_ALLOWLIST_AND_SHADOW_OWNERS

BaseEquipmentShopService is the sole V2 owner. Allowed consumers are shop presentation and explicit recovery tooling. Legacy direct trader purchase, direct SQL mutation, allocator bypass and presentation-owned mutation are forbidden production paths.

## Implementation boundary

Only the API-ready V2 domain/application layer is authorized. SQLite, production adapters, runtime and Telegram wiring remain forbidden.

## Next patch

`patch_21_10_3c_implement_base_equipment_shop.py`
