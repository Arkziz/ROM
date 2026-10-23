# Stage 21.10.7a - Refined Bag Expansion contract

- Status: **PASS**
- Conclusion: **REVIEW_REQUIRED**
- V1-confirmed rows: **13**
- Review-required rows: **6**
- Production changed: **False**
- Database opened: **False**
- Manual game check: **NOT_REQUIRED**

## Authoritative context owners

- `canonical_expansion_owner`: `systems/crystal_bag_expansion_system.py`
- `crystal_wallet`: `systems/crystal_wallet_system.py`
- `crystal_shop_facade`: `systems/crystal_shop_system.py`
- `capacity_source`: `db_modules/inventory.py`
- `presentation`: `handlers/crystal_shop.py`

## Contract matrix

- `CANONICAL_EXPANSION_OWNER`: **V1_CONFIRMED** - V1 centralizes bag expansion purchase in systems/crystal_bag_expansion_system.py.
- `EXPANSION_STATE_OWNER`: **V1_CONFIRMED** - V1 exposes authoritative current and next capacity state.
- `EXPANSION_PREVIEW_OWNER`: **V1_CONFIRMED** - V1 has a dedicated expansion preview before mutation.
- `EXPANSION_HISTORY_OWNER`: **V1_CONFIRMED** - V1 exposes dedicated bag-expansion purchase history.
- `CRYSTAL_WALLET_BALANCE`: **V1_CONFIRMED** - Crystal balance reads are delegated to the canonical wallet.
- `CRYSTAL_WALLET_DEBIT`: **V1_CONFIRMED** - Crystal debit is a wallet dependency rather than expansion ownership.
- `CRYSTAL_COMPENSATION_BOUNDARY`: **V1_CONFIRMED** - V1 exposes compensation for failed downstream crystal purchases.
- `CRYSTAL_SHOP_PREVIEW_BOUNDARY`: **V1_CONFIRMED** - The general Crystal Shop preview remains a facade boundary.
- `CRYSTAL_SHOP_PURCHASE_BOUNDARY`: **V1_CONFIRMED** - The general Crystal Shop purchase path requires explicit delegation policy.
- `CANONICAL_CAPACITY_READ`: **V1_CONFIRMED** - V1 inventory capacity reads use get_bag_capacity.
- `INVENTORY_CAPACITY_ENFORCEMENT`: **V1_CONFIRMED** - Inventory insertion enforces the persisted bag capacity.
- `PRESENTATION_EXPANSION_BOUNDARY`: **V1_CONFIRMED** - Bag expansion rendering remains presentation-only.
- `PRESENTATION_CALLBACK_BOUNDARY`: **V1_CONFIRMED** - Expansion callbacks remain consumers rather than mutation owners.
- `CAPACITY_PATH_AND_PRICES`: **REVIEW_REQUIRED** - Exact 60-to-80 for 75 crystals and 80-to-100 for 150 crystals require stable technical keys and snapshots.
- `SEQUENTIAL_AND_MAXIMUM_POLICY`: **REVIEW_REQUIRED** - No-skip progression and maximum-capacity rejection require explicit normalization.
- `CRYSTAL_DEBIT_CAPACITY_ATOMICITY`: **REVIEW_REQUIRED** - Crystal debit, capacity update and purchase receipt require one Unit-of-Work boundary.
- `IDEMPOTENCY_AND_STALE_CONFIRMATION`: **REVIEW_REQUIRED** - Stable operation keys, replay/conflict and stale current-capacity or price handling require resolution.
- `ACCOUNT_SCOPE_RESET_AND_RESTART`: **REVIEW_REQUIRED** - Account-level user identity, character-reset survival and restart persistence require a precise contract.
- `CONSUMER_ALLOWLIST_AND_SHADOW_OWNERS`: **REVIEW_REQUIRED** - Crystal Shop facades, capacity readers, handlers, direct SQL and duplicate mutation paths require an allowlist.

## Unresolved contracts

- `CAPACITY_PATH_AND_PRICES`
- `SEQUENTIAL_AND_MAXIMUM_POLICY`
- `CRYSTAL_DEBIT_CAPACITY_ATOMICITY`
- `IDEMPOTENCY_AND_STALE_CONFIRMATION`
- `ACCOUNT_SCOPE_RESET_AND_RESTART`
- `CONSUMER_ALLOWLIST_AND_SHADOW_OWNERS`

Implementation remains unauthorized until capacity path/prices, sequential maximum policy, crystal-capacity atomicity, idempotency/stale confirmation, account reset/restart, consumer allowlist and shadow mutation paths are resolved from V1 evidence.
