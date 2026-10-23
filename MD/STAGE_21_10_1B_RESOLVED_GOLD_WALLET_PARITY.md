# Stage 21.10.2b - Resolved Crystal Wallet/Ledger parity

- Status: **PASS**
- Conclusion: **GO_TO_IMPLEMENTATION**
- Resolved contracts: **6/6**
- Remaining unresolved contracts: **0**
- Production changed: **False**
- Database opened: **False**
- Manual game check: **NOT_REQUIRED**

## Resolutions

### LEDGER_SCHEMA_AND_APPEND_ONLY

Every successful mutation appends one immutable ledger row containing transaction_id, idempotency_key, user_id, direction, amount, balance_before, balance_after, reason_code, source, original_transaction_id and created_at. Existing rows are never updated or deleted.

### IDEMPOTENCY_KEY_CONFLICT_POLICY

Every mutation requires a stable idempotency_key. Same key plus identical canonical payload returns the original transaction; same key with changed payload fails as conflict without mutation.

### COMPENSATION_EXACT_ONCE_POLICY

Compensation is a new opposite-direction ledger transaction linked to exactly one original transaction. Repeating the same compensation key replays; a second distinct compensation for an already compensated original is rejected. Compensation of compensation is forbidden.

### NON_NEGATIVE_AND_CLAMP_POLICY

Canonical debit is fail-closed and never clamps. Administrative removal may calculate a clamped requested amount before issuing one explicit debit command; the wallet itself still rejects insufficient balance and never becomes negative.

### TRANSACTION_AND_COMMIT_OWNERSHIP

CrystalWalletLedgerService mutates wallet and appends ledger through a caller-supplied Unit of Work. The application use case owns exactly one commit; every failure rolls back balance, ledger and consumer mutation together.

### CONSUMER_ALLOWLIST_AND_SHADOW_OWNERS

Production consumers use only CrystalWalletLedgerService. Allowed categories are admin, crystal_shop, bag_expansion, premium_purchase, daily_or_milestone_reward, refund and compensation. Direct SQL/setter mutation, DEV/presentation ownership and a second wallet owner are forbidden.

## Implementation boundary

Only the API-ready V2 domain/application layer is authorized. SQLite, production adapters, runtime and Telegram wiring remain forbidden.

## Next patch

`patch_21_10_2c_implement_crystal_wallet_ledger.py`
