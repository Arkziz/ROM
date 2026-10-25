# Stage 21.12.5a - Refined Auction contract

- Status: **PASS**
- Conclusion: **REVIEW_REQUIRED**
- Contract matrix: **3 confirmed / 8 review-required / 11 total**
- Implementation authorized: **False**
- Manual game check: **NOT_REQUIRED**

## Refined unresolved contracts

### PRICE_CATEGORY_AND_LIMIT_POLICY

Confirmed:

- 7-day active lifetime
- maximum 20 active lots per seller
- price range 1.00..999999.00 gold
- price quantized to 0.01 with ROUND_DOWN

Remaining question: Resolve category normalization, price input failures, exact active-count boundary and whether limits are rechecked inside listing transaction.

### LISTING_RESERVATION_AND_REMOVAL_ATOMICITY

Confirmed:

- equipment and stack listing use separate entrypoints
- listing captures an immutable snapshot
- listing uses BEGIN IMMEDIATE
- equipment is removed and stack quantity reduced while lot becomes ACTIVE

Remaining question: Resolve exact write order, rollback restoration, rune snapshot identity, partial-stack handling and duplicate listing prevention.

### PUBLIC_BROWSE_AND_SELF_PURCHASE_POLICY

Confirmed:

- public browse returns ACTIVE lots
- seller's own lots are excluded in query
- buy path rejects buyer equal to seller
- category/search/sort pagination exists

Remaining question: Resolve filter normalization, ordering/tie-breakers, stale listing visibility and typed self-purchase/replay results.

### BUYER_GOLD_BAG_AND_ITEM_TRANSFER

Confirmed:

- buyer gold is checked in purchase transaction
- recipient inventory capacity is checked
- stack merge and new-slot paths exist
- lot snapshot is transfer authority

Remaining question: Resolve exact bag-slot calculation, stack merge limits, generated equipment identity, gold rounding and failure mapping.

### SELLER_PROCEEDS_AND_UNCLAIMED_ASSETS

Confirmed:

- purchase transitions to SOLD_UNCLAIMED
- seller identity and price remain on lot
- unclaimed sold and expired assets have separate states
- claim-oriented user queries exist

Remaining question: Resolve when seller gold is credited, what remains claimable, exact-once claim identity and terminal transition to claimed states.

### CANCEL_EXPIRY_AND_CLAIM_POLICY

Confirmed:

- seller can cancel ACTIVE lot
- expiry converts stale ACTIVE lots to EXPIRED_UNCLAIMED
- cancel/expiry return the snapshot through canonical paths
- claimed and unclaimed terminal states are distinct

Remaining question: Resolve authorization, terminal idempotency, restore ordering, bag-full claim behavior and concurrent cancel/buy/expiry precedence.

### HISTORY_IDEMPOTENCY_AND_RESTART_RECOVERY

Confirmed:

- auction history records status transitions
- purchase ACTIVE guard prevents double settlement
- expiry scans persisted ACTIVE rows
- lot status persists restart state

Remaining question: Resolve event identity, duplicate history suppression, crash-after-commit recovery, repeated expiry/claim reports and startup recovery owner.

### PRESENTATION_AND_HANDLER_BOUNDARY

Confirmed:

- Auction System owns mutations
- auction_house handler owns Telegram UI
- systems_wrappers is compatibility facade
- public/detail builders currently mix presentation support with system data

Remaining question: Resolve typed command/result DTOs, application query service, localization boundary and one handler registration path without a second production owner.

No production mutation, auction settlement, claim, database access or runtime wiring is authorized.

## Next patch

`patch_21_12_5b_resolve_auction_parity.py`
