# Stage 21.12.5b - Resolved Auction parity

- Status: **PASS**
- Conclusion: **GO_TO_IMPLEMENTATION**
- Contract matrix: **3 previously confirmed + 8 resolved = 11/11**
- Remaining unresolved contracts: **0**
- Implementation authorized: **True**
- Runtime integration authorized: **False**
- Production persistence authorized: **False**
- Production settlement authorized: **False**
- Production claim authorized: **False**
- Manual game check: **NOT_REQUIRED**

## Resolutions

### PRICE_CATEGORY_AND_LIMIT_POLICY

Auction prices are Decimal values quantized down to 0.01 gold, with an inclusive range of 1.00 through 999999.00. A seller may own at most 20 ACTIVE lots, and the limit is rechecked inside the listing Unit of Work. ACTIVE lots expire after 7 days. Category input is normalized through the canonical category resolver; invalid price or category fails before snapshot removal.

### LISTING_RESERVATION_AND_REMOVAL_ATOMICITY

One BEGIN IMMEDIATE Unit of Work validates seller ownership, active-lot limit, sellability, quantity and immutable snapshot, then creates exactly one ACTIVE lot and removes equipment or decrements the listed stack. Equipment snapshot preserves permanent identity, durability, refinement and inserted runes; a partial stack preserves the remainder. Any failure rolls back lot creation and inventory mutation. Reusing the same consumed inventory state cannot create a duplicate lot.

### PUBLIC_BROWSE_AND_SELF_PURCHASE_POLICY

Public browse returns only currently ACTIVE, unexpired lots and excludes seller-owned lots for the requesting buyer. Category, search, sort, limit and offset are normalized before the query; stable lot_id is the final tie-breaker. The purchase command independently rejects buyer_user_id equal to seller_user_id. A stale or terminal lot returns a typed unavailable result and never replays settlement.

### BUYER_GOLD_BAG_AND_ITEM_TRANSFER

Purchase rechecks the buyer gold balance and recipient inventory capacity in the same transaction. Stackable items merge into an existing compatible stack when V1 identity permits; otherwise one free bag slot is required. Equipment is restored from the immutable lot snapshot as one permanent identity with runes, refinement and durability preserved. Gold uses canonical Decimal 0.01 precision, and any wallet, capacity, snapshot or insert failure aborts the entire purchase.

### SELLER_PROCEEDS_AND_UNCLAIMED_ASSETS

A successful purchase debits buyer gold and credits seller gold atomically before the lot transitions from ACTIVE to SOLD_UNCLAIMED. SOLD_UNCLAIMED represents the seller's unacknowledged sale record, not unpaid proceeds. Seller acknowledgement is exact-once and transitions to SOLD_CLAIMED without another gold credit. EXPIRED_UNCLAIMED represents the returned item awaiting seller claim; its item claim is exact-once and transitions to EXPIRED_CLAIMED.

### CANCEL_EXPIRY_AND_CLAIM_POLICY

Only the seller may cancel an ACTIVE lot. Concurrent buy, cancel and expiry serialize under the same ACTIVE status guard, so exactly one terminal transition wins. Cancellation atomically restores the snapshot and records CANCELLED. Expiry moves ACTIVE to EXPIRED_UNCLAIMED without duplicating the item; the item is restored only by the canonical expiry-claim operation. Bag-full claim fails without changing status. Replays of cancel, expiry or claim return typed already-terminal/already-claimed results and perform no second transfer.

### HISTORY_IDEMPOTENCY_AND_RESTART_RECOVERY

Every effective lot transition writes one typed history event in the same Unit of Work, keyed by lot identity plus transition so retries cannot duplicate the semantic event. Restart recovery first expires eligible ACTIVE lots using the guarded expiry operation and then reports persisted terminal/unclaimed states without reopening them. Crash-after-commit retries observe the terminal status and return the original outcome without repeating item or gold settlement.

### PRESENTATION_AND_HANDLER_BOUNDARY

A single Auction application service owns listing, browse, purchase, cancel, expiry and claim commands plus typed results. Domain/application code does not import Telegram or emit localized prose. Handlers own keyboards, pagination state, Ukrainian text and callback parsing. Compatibility wrappers delegate to the service and do not register a second handler or settlement path; public/detail builders become presentation adapters over typed lot DTOs.

## Implementation boundary

Stage 21.12.5c may implement pure Auction DTOs, policies, state machine, in-memory Unit of Work, tests and smoke verification. It may not connect SQLite, Telegram or runtime, and may not mutate real inventory or gold.

## Next patch

`patch_21_12_5c_implement_auction.py`
