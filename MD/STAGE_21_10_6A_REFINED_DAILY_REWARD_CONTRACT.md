# Stage 21.10.6a - Refined Daily Reward contract

- Status: **PASS**
- Conclusion: **REVIEW_REQUIRED**
- V1-confirmed rows: **13**
- Review-required rows: **6**
- Production changed: **False**
- Database opened: **False**
- Manual game check: **NOT_REQUIRED**

## Authoritative context owners

- `reward_settlement`: `systems/rune_system.py`
- `claim_state`: `db_modules/quests.py`
- `daily_compatibility`: `db_modules/daily_compat.py`
- `presentation`: `handlers/daily.py`
- `inventory`: `db_modules/inventory.py`

## Contract matrix

- `CANONICAL_REWARD_SETTLEMENT_OWNER`: **V1_CONFIRMED** - V1 settles the combined daily reward through the rune system path.
- `CLAIM_STATE_OWNER`: **V1_CONFIRMED** - V1 persists daily quest claim state in the quest subsystem.
- `CLAIM_COMPLETION_OWNER`: **V1_CONFIRMED** - Daily quest completion is checked before claim settlement.
- `DAILY_QUEST_READ_OWNER`: **V1_CONFIRMED** - V1 exposes the current daily quest and claim state.
- `DAILY_RESET_OWNER`: **V1_CONFIRMED** - V1 owns daily reset and period rollover in the quest subsystem.
- `DAILY_PERIOD_COMPATIBILITY`: **V1_CONFIRMED** - The compatibility facade exposes the effective V1 daily period key.
- `REWARD_STACK_PLANNER`: **V1_CONFIRMED** - V1 plans stack additions before applying the potion reward.
- `REWARD_STACK_APPLIER`: **V1_CONFIRMED** - V1 applies the planned potion stack mutation.
- `PHIRIUS_TOKEN_BALANCE_READ`: **V1_CONFIRMED** - V1 exposes Phirius Token quantity through the rune system.
- `INVENTORY_ADD_BOUNDARY`: **V1_CONFIRMED** - Inventory item grants remain an explicit dependency boundary.
- `INVENTORY_COMPACTION_BOUNDARY`: **V1_CONFIRMED** - Potion stack compaction remains an inventory dependency.
- `PRESENTATION_CLAIM_BOUNDARY`: **V1_CONFIRMED** - The daily handler delegates claim mutation and remains presentation-only.
- `PRESENTATION_STATUS_BOUNDARY`: **V1_CONFIRMED** - Daily status rendering remains outside mutation ownership.
- `REWARD_CATALOG_AND_KEYS`: **REVIEW_REQUIRED** - Stable reward keys and the approved exact 3 small HP potions plus 3 Phirius Tokens require explicit normalization.
- `PERIOD_BOUNDARY_AND_ONCE_POLICY`: **REVIEW_REQUIRED** - The exact period boundary, period key and once-per-period semantics require bounded parity resolution.
- `CLAIM_STATE_AND_REWARD_ORDERING`: **REVIEW_REQUIRED** - Completion validation, claim-state mutation and reward settlement ordering require one authoritative boundary.
- `INVENTORY_CAPACITY_AND_STACKS`: **REVIEW_REQUIRED** - Capacity preflight, stack planning and exact potion grant ordering require explicit resolution.
- `ATOMICITY_IDEMPOTENCY_AND_RESTART`: **REVIEW_REQUIRED** - Atomic 3+3 settlement, replay, rollback and restart behavior require one Unit-of-Work contract.
- `CONSUMER_ALLOWLIST_AND_SHADOW_OWNERS`: **REVIEW_REQUIRED** - Quest wrappers, compatibility facade, handlers, simulator paths and direct SQL mutation require an explicit allowlist.

## Unresolved contracts

- `REWARD_CATALOG_AND_KEYS`
- `PERIOD_BOUNDARY_AND_ONCE_POLICY`
- `CLAIM_STATE_AND_REWARD_ORDERING`
- `INVENTORY_CAPACITY_AND_STACKS`
- `ATOMICITY_IDEMPOTENCY_AND_RESTART`
- `CONSUMER_ALLOWLIST_AND_SHADOW_OWNERS`

Implementation remains unauthorized until reward catalog/keys, period once-policy, claim ordering, inventory stacks, atomicity/idempotency/restart, consumer allowlist and shadow mutation paths are resolved from V1 evidence.
