# Stage 21.10.5b - Resolved Premium Shop parity

- Status: **PASS**
- Conclusion: **GO_TO_IMPLEMENTATION**
- Resolved contracts: **6/6**
- Remaining unresolved contracts: **0**
- Production changed: **False**
- Database opened: **False**
- Manual game check: **NOT_REQUIRED**

## Fixed plans

- `premium_15d`: 15 days, 100 crystals
- `premium_30d`: 30 days, 180 crystals

## Resolutions

### PLAN_KEYS_AND_PRICES

Use stable technical plan keys premium_15d and premium_30d. Their immutable catalog values are exactly 15 days / 100 crystals and 30 days / 180 crystals. Presentation labels are not identifiers, and any changed or unknown quote fails closed.

### ACTIVATION_AND_EXTENSION_BASE

All domain timestamps are timezone-aware UTC. If current Premium expiry is absent or not later than now, activation starts at now. If expiry is later than now, extension starts at the existing expiry. The selected plan duration is added exactly once.

### CRYSTAL_DEBIT_AND_PREMIUM_ATOMICITY

PremiumShopService validates account, plan, quote and crystal balance before mutation. Crystal debit, Premium expiry update and immutable purchase receipt execute in one caller-owned Unit of Work with one commit; any failure rolls all effects back.

### IDEMPOTENCY_AND_STALE_CONFIRMATION

Every confirmation requires a stable operation_key. Same key with identical user_id, plan_key and quoted crystal price replays the original receipt. Changed payload conflicts. Unknown plan, changed price, insufficient crystals or changed account state reject without mutation.

### ACCOUNT_SCOPE_AND_RESTART

Premium is account-level by user_id, survives character reset, and persists across restart. Receipts store previous_expiry, base_expiry and new_expiry in UTC so that replay does not extend Premium twice.

### CONSUMER_ALLOWLIST_AND_SHADOW_OWNERS

PremiumShopService is the sole V2 mutation owner. Allowed consumers are timed-Premium presentation, Crystal Shop presentation delegation and explicit recovery/testing adapters. Crystal Wallet remains a dependency. Direct SQL expiry updates, presentation-owned mutation and duplicate Premium owners are forbidden.

## Implementation boundary

Only the API-ready V2 domain/application layer is authorized. SQLite, production adapters, runtime and Telegram wiring remain forbidden.

## Next patch

`patch_21_10_5c_implement_premium_shop.py`
