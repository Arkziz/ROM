# Stage 21.10.4a - Refined Potion Trading contract

- Status: **PASS**
- Conclusion: **REVIEW_REQUIRED**
- V1-confirmed rows: **14**
- Review-required rows: **6**
- Production changed: **False**
- Database opened: **False**
- Manual game check: **NOT_REQUIRED**

## Authoritative context owners

- `canonical_trading_owner`: `systems/potion_system.py`
- `alchemist_presentation`: `handlers/city.py`
- `reservation_boundary`: `systems/player_interaction_system.py`

## Contract matrix

- `CANONICAL_TRADING_OWNER`: **V1_CONFIRMED** - V1 centralizes Alchemist potion purchase in systems/potion_system.py.
- `SELL_OWNER`: **V1_CONFIRMED** - V1 centralizes Alchemist potion sale in the same authoritative module.
- `CATALOG_STOCK_OWNER`: **V1_CONFIRMED** - V1 exposes the accepted potion catalog and price-bearing stock rows.
- `STACK_PLAN_OWNER`: **V1_CONFIRMED** - V1 builds a deterministic stack-normalization plan before applying inventory changes.
- `STACK_NORMALIZATION_OWNER`: **V1_CONFIRMED** - V1 exposes a dedicated normalization operation for potion stacks.
- `BUY_PRESENTATION_LIST`: **V1_CONFIRMED** - The city handler renders buy choices and remains a presentation consumer.
- `BUY_PRESENTATION_PREVIEW`: **V1_CONFIRMED** - The buy preview is presentation-only and must not own mutation.
- `SELL_PRESENTATION_LIST`: **V1_CONFIRMED** - The city handler renders sellable potion choices.
- `SELL_PRESENTATION_PREVIEW`: **V1_CONFIRMED** - The sell preview remains outside the mutation owner.
- `SELL_CONFIRM_PRESENTATION`: **V1_CONFIRMED** - V1 has a separate sell confirmation presentation boundary.
- `EXACT_QUANTITY_PRESENTATION`: **V1_CONFIRMED** - V1 accepts an explicit quantity through the Alchemist presentation flow.
- `TRADE_DISPATCH_PRESENTATION`: **V1_CONFIRMED** - The city handler dispatches trading actions but is not the canonical owner.
- `RESERVED_QUANTITY_OWNER`: **V1_CONFIRMED** - V1 has an authoritative inventory reservation quantity query.
- `AVAILABLE_QUANTITY_OWNER`: **V1_CONFIRMED** - V1 computes inventory availability after reservations.
- `BUY_QUANTITY_AND_PRICE_SNAPSHOT`: **REVIEW_REQUIRED** - Exact quantity validation, accepted buy price snapshot and stale-confirmation behavior require bounded parity resolution.
- `SELL_QUANTITY_RESERVATION_AND_PRICE`: **REVIEW_REQUIRED** - Reservation-aware sell quantity, accepted sell price and sell-all semantics require explicit resolution.
- `STACK_PLAN_APPLICATION_ORDER`: **REVIEW_REQUIRED** - The exact order for validating and applying stack normalization relative to gold mutation requires one canonical boundary.
- `ATOMIC_BUY_AND_SELL`: **REVIEW_REQUIRED** - Gold and inventory changes for both directions require one caller-owned Unit of Work and rollback policy.
- `IDEMPOTENCY_AND_STALE_CONFIRMATION`: **REVIEW_REQUIRED** - Operation keys, exact replay, changed payload conflicts and stale inventory/price handling require explicit resolution.
- `CONSUMER_ALLOWLIST_AND_SHADOW_OWNERS`: **REVIEW_REQUIRED** - Presentation wrappers, player-trade reservations, simulator paths and direct SQL mutation require a precise migration allowlist.

## Unresolved contracts

- `BUY_QUANTITY_AND_PRICE_SNAPSHOT`
- `SELL_QUANTITY_RESERVATION_AND_PRICE`
- `STACK_PLAN_APPLICATION_ORDER`
- `ATOMIC_BUY_AND_SELL`
- `IDEMPOTENCY_AND_STALE_CONFIRMATION`
- `CONSUMER_ALLOWLIST_AND_SHADOW_OWNERS`

Implementation remains unauthorized until buy quantity/price snapshot, reservation-aware sell quantity, stack application order, atomic buy/sell, idempotency/stale confirmation, consumer allowlist and shadow mutation paths are resolved from V1 evidence.
