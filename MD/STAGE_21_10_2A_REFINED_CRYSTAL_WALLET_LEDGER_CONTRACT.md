# Stage 21.10.2a - Refined Crystal Wallet/Ledger contract

- Status: **PASS**
- Conclusion: **REVIEW_REQUIRED**
- V1-confirmed rows: **14**
- Review-required rows: **6**
- Production changed: **False**
- Database opened: **False**
- Manual game check: **NOT_REQUIRED**

## Authoritative context owners

- `canonical_wallet_owner`: `systems/crystal_wallet_system.py`
- `admin_consumer`: `systems/admin_crystal_credit_system.py`
- `shop_consumer`: `systems/crystal_shop_system.py`
- `bag_expansion_consumer`: `systems/crystal_bag_expansion_system.py`
- `premium_item_boundary`: `systems/premium_item_policy_system.py`
- `dev_presentation_boundary`: `handlers/dev.py`

## Contract matrix

- `CANONICAL_WALLET_OWNER`: **V1_CONFIRMED** - V1 centralizes account-level crystal mutation in the shared _apply function.
- `ACCOUNT_LEVEL_IDENTITY`: **V1_CONFIRMED** - The wallet is addressed by user_id and is independent from character lifecycle.
- `ZERO_WALLET_CREATION`: **V1_CONFIRMED** - V1 ensures a zero-balance wallet exists before reads and mutation.
- `BALANCE_READ_OWNER`: **V1_CONFIRMED** - Canonical balance reads are provided by the wallet system.
- `CREDIT_API`: **V1_CONFIRMED** - Credit is a named wrapper over the canonical mutation path.
- `DEBIT_API`: **V1_CONFIRMED** - Debit is a named wrapper over the canonical mutation path.
- `TRANSACTION_HISTORY_API`: **V1_CONFIRMED** - V1 exposes persistent crystal transaction history.
- `COMPENSATION_API`: **V1_CONFIRMED** - V1 exposes explicit compensation of a prior crystal transaction.
- `ADMIN_CONSUMER`: **V1_CONFIRMED** - Administrative grant and debit are wallet consumers, not a second owner.
- `SHOP_CONSUMER`: **V1_CONFIRMED** - Crystal shop purchase is an atomic debit consumer.
- `BAG_EXPANSION_CONSUMER`: **V1_CONFIRMED** - Bag expansion is an atomic debit consumer.
- `PREMIUM_ITEM_BOUNDARY`: **V1_CONFIRMED** - Premium item grant policy remains separate from wallet ownership.
- `DEV_CREDIT_BOUNDARY`: **V1_CONFIRMED** - DEV credit command is a presentation/test consumer of the wallet API.
- `DEV_DEBIT_BOUNDARY`: **V1_CONFIRMED** - DEV debit command is a presentation/test consumer of the wallet API.
- `LEDGER_SCHEMA_AND_APPEND_ONLY`: **REVIEW_REQUIRED** - Exact immutable ledger fields, ordering and append-only constraints require bounded parity resolution.
- `IDEMPOTENCY_KEY_CONFLICT_POLICY`: **REVIEW_REQUIRED** - Exact same-key replay and changed-payload conflict behavior require explicit normalization.
- `COMPENSATION_EXACT_ONCE_POLICY`: **REVIEW_REQUIRED** - Compensation linkage, repeat behavior and compensation-of-compensation policy require explicit resolution.
- `NON_NEGATIVE_AND_CLAMP_POLICY`: **REVIEW_REQUIRED** - Insufficient-funds and administrative clamped-debit boundaries must be separated precisely.
- `TRANSACTION_AND_COMMIT_OWNERSHIP`: **REVIEW_REQUIRED** - Commit/rollback ownership across wallet and purchase consumers requires one canonical V2 boundary.
- `CONSUMER_ALLOWLIST_AND_SHADOW_OWNERS`: **REVIEW_REQUIRED** - Direct SQL mutation, wrappers, DEV commands and domain consumers require an explicit migration allowlist.

## Unresolved contracts

- `LEDGER_SCHEMA_AND_APPEND_ONLY`
- `IDEMPOTENCY_KEY_CONFLICT_POLICY`
- `COMPENSATION_EXACT_ONCE_POLICY`
- `NON_NEGATIVE_AND_CLAMP_POLICY`
- `TRANSACTION_AND_COMMIT_OWNERSHIP`
- `CONSUMER_ALLOWLIST_AND_SHADOW_OWNERS`

Implementation remains unauthorized until ledger schema, idempotency conflict policy, exact-once compensation, debit/clamp policy, transaction ownership, consumer allowlist and shadow mutation paths are resolved from V1 evidence.
