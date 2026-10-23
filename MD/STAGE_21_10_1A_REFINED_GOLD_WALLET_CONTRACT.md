# Stage 21.10.1a - Refined gold wallet contract

- Status: **PASS**
- Conclusion: **REVIEW_REQUIRED**
- V1-confirmed rows: **17**
- Review-required rows: **6**
- Production changed: **False**
- Database opened: **False**
- Manual game check: **NOT_REQUIRED**

## Authoritative context owners

- `persisted_wallet_owner`: `systems/player_system.py`
- `db_wrapper`: `db_modules/player.py`
- `auction_consumer`: `systems/auction_house_system.py`
- `trade_consumer`: `systems/player_interaction_system.py`
- `combat_reward_consumer`: `systems/reward_system.py`
- `level_up_reward_consumer`: `systems/level_up_reward_system.py`
- `presentation_formatter`: `db_modules/utils.py`
- `simulation_exclusion`: `systems/simulation/parity_foundation.py`
- `crystal_wallet_exclusion`: `systems/crystal_wallet_system.py`

## Contract matrix

- `PERSISTED_WALLET_READ_OWNER`: **V1_CONFIRMED** - V1 reads the persisted player gold wallet through get_wallet; duplicate definitions are preserved as evidence. No silver token is required because the authoritative function evidence exposes gold only.
- `PERSISTED_GOLD_MUTATION_OWNER`: **V1_CONFIRMED** - V1 mutates persisted player gold through add_gold; duplicate definitions are preserved as evidence.
- `TRANSACTIONAL_GOLD_MUTATION`: **V1_CONFIRMED** - V1 exposes an in-transaction gold mutation helper without taking commit ownership.
- `DB_MODULE_WRAPPER`: **V1_CONFIRMED** - The db_modules function is a compatibility wrapper, not a second authoritative wallet owner.
- `AUCTION_READ_ADAPTER`: **V1_CONFIRMED** - Auction reads gold through a dedicated adapter.
- `AUCTION_WRITE_ADAPTER`: **V1_CONFIRMED** - Auction writes gold through a dedicated adapter that must be classified as a consumer path.
- `AUCTION_PURCHASE_CONSUMER`: **V1_CONFIRMED** - Auction purchase is a transactional gold debit consumer.
- `AUCTION_SALE_CLAIM_CONSUMER`: **V1_CONFIRMED** - Claiming auction proceeds is a deferred gold credit consumer.
- `TRADE_WALLET_STATE`: **V1_CONFIRMED** - Player trade exposes wallet state for offer validation.
- `TRADE_GOLD_OFFER`: **V1_CONFIRMED** - Player trade reserves and validates an offered gold amount before settlement.
- `TRADE_SETTLEMENT_CONSUMER`: **V1_CONFIRMED** - Trade commit is an atomic two-party gold transfer consumer.
- `TRADE_HISTORY_BOUNDARY`: **V1_CONFIRMED** - Trade history records completed exchange details but is not a general gold-wallet ledger. Gold is intentionally not required as a literal token because the helper stores the completed trade payload rather than owning wallet mutation.
- `COMBAT_REWARD_CONSUMER`: **V1_CONFIRMED** - Combat victory settlement is a gold credit source and must not become a second wallet owner.
- `LEVEL_UP_REWARD_CONSUMER`: **V1_CONFIRMED** - Level-up gold is applied inside the caller transaction.
- `GOLD_FORMATTING_BOUNDARY`: **V1_CONFIRMED** - Gold presentation formatting remains outside wallet mutation semantics.
- `SIMULATOR_EXCLUDED`: **V1_CONFIRMED** - Simulator credit/debit helpers are evidence fixtures and are excluded from production wallet ownership.
- `CRYSTAL_WALLET_EXCLUDED`: **V1_CONFIRMED** - Crystal wallet ledger and idempotency belong to Stage 21.10.2 and are excluded from Gold Wallet parity.
- `MONEY_REPRESENTATION`: **REVIEW_REQUIRED** - V1 add_gold evidence confirms float-based mutation, while no literal round call is present in that owner. Stage 21.10.1 forbids float, so exact Decimal-safe parity and quantization require explicit resolution.
- `NON_NEGATIVE_DEBIT_POLICY`: **REVIEW_REQUIRED** - The audit does not establish one canonical insufficient-funds and negative-delta policy across all direct consumers.
- `GENERAL_GOLD_TRANSACTION_HISTORY`: **REVIEW_REQUIRED** - Auction and trade histories exist, but V1 evidence does not establish a general immutable gold-wallet transaction ledger.
- `IDEMPOTENCY_POLICY`: **REVIEW_REQUIRED** - No canonical idempotency key or duplicate-operation policy is established for generic gold mutations.
- `TRANSACTION_OWNERSHIP`: **REVIEW_REQUIRED** - Commit ownership and rollback behavior must be normalized across wallet, shops, auction, trade, repair and reward consumers.
- `DIRECT_MUTATION_CONSUMER_ALLOWLIST`: **REVIEW_REQUIRED** - V1 has distributed gold consumers; the exact migration allowlist and shadow-owner prohibition require a parity decision.

## Unresolved contracts

- `MONEY_REPRESENTATION`
- `NON_NEGATIVE_DEBIT_POLICY`
- `GENERAL_GOLD_TRANSACTION_HISTORY`
- `IDEMPOTENCY_POLICY`
- `TRANSACTION_OWNERSHIP`
- `DIRECT_MUTATION_CONSUMER_ALLOWLIST`

Implementation remains unauthorized until Decimal-safe representation, quantization, non-negative debit policy, transaction ownership, general history/idempotency scope, consumer allowlist and shadow mutation paths are resolved from V1 evidence.
