# Stage 21.10.8b - Resolved Admin Crystals parity

- Status: **PASS**
- Conclusion: **GO_TO_IMPLEMENTATION**
- Resolved contracts: **6/6**
- Remaining unresolved contracts: **0**
- Production changed: **False**
- Database opened: **False**
- Manual game check: **NOT_REQUIRED**

## Approved behavior

- Admin-only credit and clamped debit
- Account identity by target_user_id
- Financial commit before recipient notification
- Newest-first permanent history, 10 records per page

## Resolutions

### AUTHORIZATION_AND_TARGET_IDENTITY

AdminCrystalAdjustmentService fails closed unless actor_user_id is authorized by the admin policy port. The target is an account identified only by target_user_id; current character_name is presentation metadata resolved at read time and never a financial identity.

### CREDIT_DEBIT_AND_CLAMP_POLICY

Requested amount must be a positive integer. Credit applies the full requested amount. Debit is clamped to min(requested_amount,current_balance), never produces a negative balance, and records requested_amount and applied_amount separately. A zero applied debit is a valid audited no-op receipt.

### PREVIEW_CONFIRMATION_AND_IDEMPOTENCY

Preview returns an immutable quote containing actor_user_id, target_user_id, adjustment_kind, requested_amount, expected_balance_before and applied_amount. Confirmation requires a stable operation_key. Identical replay returns the original receipt; changed payload conflicts. A changed balance makes the quote stale and rejects before mutation.

### WALLET_LEDGER_ATOMICITY_AND_COMPENSATION

Wallet mutation, canonical Crystal Ledger entry and immutable admin adjustment receipt execute in one caller-owned Unit of Work with one commit. Any pre-commit failure rolls all effects back. Compensation is reserved for an explicitly committed downstream recovery operation and must reference the original transaction.

### NOTIFICATION_ORDERING_AND_FAILURE_POLICY

Financial commit occurs before recipient notification. Notification delivery is a post-commit side effect with its own delivery status and retry key. Delivery failure never rolls back or repeats the crystal adjustment; retry may only resend the notice for the existing receipt.

### HISTORY_DETAIL_AND_CONSUMER_ALLOWLIST

History is newest-first, ten records per page, persistent without expiry, and detail exposes operation key, actor, target, kind, requested/applied amounts, balances and timestamp. Current character_name is resolved when rendering. Only admin presentation and explicit audit/testing adapters may consume the service; direct SQL, handler-owned mutation and duplicate admin adjustment owners are forbidden.

## Implementation boundary

Only the API-ready V2 domain/application layer is authorized. SQLite, production adapters, runtime and Telegram wiring remain forbidden.

## Next patch

`patch_21_10_8c_implement_admin_crystals.py`
