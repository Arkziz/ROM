# Stage 21.10.7b - Resolved Bag Expansion parity

- Status: **PASS**
- Conclusion: **GO_TO_IMPLEMENTATION**
- Resolved contracts: **6/6**
- Remaining unresolved contracts: **0**
- Production changed: **False**
- Database opened: **False**
- Manual game check: **NOT_REQUIRED**

## Approved capacity path

- `bag_60_to_80`: 60 to 80 for 75 crystals
- `bag_80_to_100`: 80 to 100 for 150 crystals
- Maximum capacity: 100

## Resolutions

### CAPACITY_PATH_AND_PRICES

Use stable expansion keys bag_60_to_80 and bag_80_to_100. Their immutable transitions and prices are exactly 60 to 80 for 75 crystals and 80 to 100 for 150 crystals. Presentation labels are never identifiers; unknown or changed quotes fail closed.

### SEQUENTIAL_AND_MAXIMUM_POLICY

Only the transition matching the account's current capacity is valid. Capacity 60 permits only bag_60_to_80; capacity 80 permits only bag_80_to_100; capacity 100 is terminal and returns maximum_capacity. Skipping, downgrading or repeating a completed transition is forbidden.

### CRYSTAL_DEBIT_CAPACITY_ATOMICITY

BagExpansionService validates user, current capacity, target capacity, quote and crystal balance before mutation. Crystal debit, account-level capacity update and immutable purchase receipt execute in one caller-owned Unit of Work with one commit; any failure rolls all effects back.

### IDEMPOTENCY_AND_STALE_CONFIRMATION

Every confirmation requires a stable operation_key. Same key with identical user_id, expansion_key, current capacity, target capacity and quoted price replays the original receipt. Changed payload conflicts. Stale capacity, stale price, insufficient crystals or maximum capacity reject without mutation.

### ACCOUNT_SCOPE_RESET_AND_RESTART

Bag capacity is account-level by user_id, survives character reset and persists across restart. Receipts store previous_capacity, target_capacity and price so replay cannot expand or debit twice.

### CONSUMER_ALLOWLIST_AND_SHADOW_OWNERS

BagExpansionService is the sole V2 mutation owner. Allowed consumers are Crystal Shop presentation delegation, canonical inventory capacity readers and explicit recovery/testing adapters. Crystal Wallet remains a dependency. Direct SQL capacity updates, presentation-owned mutation and duplicate expansion owners are forbidden.

## Implementation boundary

Only the API-ready V2 domain/application layer is authorized. SQLite, production adapters, runtime and Telegram wiring remain forbidden.

## Next patch

`patch_21_10_7c_implement_bag_expansion.py`
