# Stage 21.10.5a - Refined Premium Shop contract

- Status: **PASS**
- Conclusion: **REVIEW_REQUIRED**
- V1-confirmed rows: **12**
- Review-required rows: **6**
- Production changed: **False**
- Database opened: **False**
- Manual game check: **NOT_REQUIRED**

## Authoritative context owners

- `canonical_premium_owner`: `systems/timed_exp_bonus_system.py`
- `crystal_shop_boundary`: `systems/crystal_shop_system.py`
- `crystal_wallet_boundary`: `systems/crystal_wallet_system.py`
- `premium_presentation`: `handlers/timed_exp_bonus.py`
- `crystal_shop_presentation`: `handlers/crystal_shop.py`

## Contract matrix

- `CANONICAL_PREMIUM_OWNER`: **V1_CONFIRMED** - V1 centralizes Premium activation and extension in systems/timed_exp_bonus_system.py.
- `PREMIUM_STATUS_OWNER`: **V1_CONFIRMED** - V1 exposes account Premium status and expiration through the timed bonus owner.
- `PREMIUM_PURCHASE_PREVIEW`: **V1_CONFIRMED** - V1 has a dedicated Premium purchase preview before mutation.
- `ACCOUNT_SUMMARY_OWNER`: **V1_CONFIRMED** - Premium account summary remains owned by the timed bonus system.
- `CRYSTAL_SHOP_CATALOG_BOUNDARY`: **V1_CONFIRMED** - The general Crystal Shop catalog is a dependency boundary, not a second Premium activation owner.
- `CRYSTAL_SHOP_PREVIEW_BOUNDARY`: **V1_CONFIRMED** - The general Crystal Shop preview remains separate from Premium activation semantics.
- `CRYSTAL_WALLET_BALANCE`: **V1_CONFIRMED** - Crystal balance reads are delegated to the canonical wallet.
- `CRYSTAL_WALLET_DEBIT`: **V1_CONFIRMED** - Crystal debit is a wallet dependency, not Premium ownership.
- `CRYSTAL_COMPENSATION_BOUNDARY`: **V1_CONFIRMED** - V1 exposes a compensation boundary for failed downstream crystal purchases.
- `PREMIUM_PRESENTATION_OWNER`: **V1_CONFIRMED** - Timed Premium presentation remains a consumer of the application contract.
- `PREMIUM_CALLBACK_BOUNDARY`: **V1_CONFIRMED** - Premium callbacks remain presentation dispatch rather than mutation ownership.
- `PREMIUM_EXPIRY_FORMATTER`: **V1_CONFIRMED** - Kyiv display formatting remains outside UTC domain semantics.
- `PLAN_KEYS_AND_PRICES`: **REVIEW_REQUIRED** - Stable plan keys and exact 15-day/100-crystal and 30-day/180-crystal snapshots require bounded parity resolution.
- `ACTIVATION_AND_EXTENSION_BASE`: **REVIEW_REQUIRED** - The exact UTC base for inactive activation and active extension requires explicit normalization.
- `CRYSTAL_DEBIT_AND_PREMIUM_ATOMICITY`: **REVIEW_REQUIRED** - Crystal debit, Premium expiry mutation, history and compensation require one canonical Unit-of-Work boundary.
- `IDEMPOTENCY_AND_STALE_CONFIRMATION`: **REVIEW_REQUIRED** - Stable operation keys, replay/conflict and stale plan/price confirmation require explicit resolution.
- `ACCOUNT_SCOPE_AND_RESTART`: **REVIEW_REQUIRED** - Account-level user identity, character reset survival and restart semantics require a precise V2 contract.
- `CONSUMER_ALLOWLIST_AND_SHADOW_OWNERS`: **REVIEW_REQUIRED** - Crystal Shop wrappers, handlers, direct SQL and duplicate Premium mutation paths require an explicit migration allowlist.

## Unresolved contracts

- `PLAN_KEYS_AND_PRICES`
- `ACTIVATION_AND_EXTENSION_BASE`
- `CRYSTAL_DEBIT_AND_PREMIUM_ATOMICITY`
- `IDEMPOTENCY_AND_STALE_CONFIRMATION`
- `ACCOUNT_SCOPE_AND_RESTART`
- `CONSUMER_ALLOWLIST_AND_SHADOW_OWNERS`

Implementation remains unauthorized until plan keys/prices, activation/extension base, crystal debit atomicity, idempotency/stale confirmation, account restart semantics, consumer allowlist and shadow mutation paths are resolved from V1 evidence.
