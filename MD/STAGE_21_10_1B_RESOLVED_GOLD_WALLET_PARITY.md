# Stage 21.10.4b - Resolved Potion Trading parity

- Status: **PASS**
- Conclusion: **GO_TO_IMPLEMENTATION**
- Resolved contracts: **6/6**
- Remaining unresolved contracts: **0**
- Production changed: **False**
- Database opened: **False**
- Manual game check: **NOT_REQUIRED**

## Resolutions

### BUY_QUANTITY_AND_PRICE_SNAPSHOT

Buy quantity must be a positive integer and may not exceed the quantity affordable from the accepted catalog price. Confirmation uses a typed potion_key and an immutable quoted unit buy price from the preview; changed or unavailable catalog data fails closed before mutation.

### SELL_QUANTITY_RESERVATION_AND_PRICE

Sell quantity must be a positive integer and may not exceed inventory quantity after subtracting active reservations. Sell-all means all currently available, non-reserved units. Confirmation uses the accepted quoted unit sell price and rejects stale availability or a changed quote.

### STACK_PLAN_APPLICATION_ORDER

Validate potion allowlist, quantity, price, gold and reservation-aware availability first. Build and validate the deterministic stack plan before the first mutation. Apply inventory normalization inside the same Unit of Work as the trade; never normalize on a rejected transaction.

### ATOMIC_BUY_AND_SELL

PotionTradingService owns one application transaction. Buy atomically debits gold, adds quantity, normalizes stacks and writes a receipt. Sell atomically removes only available quantity, credits gold, normalizes stacks and writes a receipt. One caller-owned commit finalizes all effects; failure rolls all effects back.

### IDEMPOTENCY_AND_STALE_CONFIRMATION

Every confirmed trade requires a stable operation_key. Same key with the same canonical direction, potion_key, quantity and quoted unit price replays the original receipt. Changed payload conflicts. Stale price, insufficient gold, changed inventory availability or changed reservations reject without mutation.

### CONSUMER_ALLOWLIST_AND_SHADOW_OWNERS

PotionTradingService is the sole V2 owner. Allowed consumers are Alchemist presentation and explicit recovery/testing adapters. Player-trade reservation queries are read-only dependencies. Simulator paths, direct SQL mutation, presentation-owned mutation and a second potion-trading owner are forbidden.

## Implementation boundary

Only the API-ready V2 domain/application layer is authorized. SQLite, production adapters, runtime and Telegram wiring remain forbidden.

## Next patch

`patch_21_10_4c_implement_potion_trading.py`
