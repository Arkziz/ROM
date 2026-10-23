# Stage 21.10.6b - Resolved Daily Reward parity

- Status: **PASS**
- Conclusion: **GO_TO_IMPLEMENTATION**
- Resolved contracts: **6/6**
- Remaining unresolved contracts: **0**
- Production changed: **False**
- Database opened: **False**
- Manual game check: **NOT_REQUIRED**

## Approved reward

- 3 small HP potions
- 3 Phirius Tokens
- The superseded 5-token value is forbidden for V2 parity.

## Resolutions

### REWARD_CATALOG_AND_KEYS

Use stable reward_key daily_reward_3hp_3firius and typed item/currency keys small_hp_potion and phirius_token. The exact immutable reward is 3 small HP potions and 3 Phirius Tokens. The previous 5-token value is superseded and forbidden for V2 parity.

### PERIOD_BOUNDARY_AND_ONCE_POLICY

A claim is account-level by user_id and unique for a stable daily period_key produced by the canonical period provider. One successful claim is allowed per user_id plus period_key. Repeated claims for the same period fail closed or replay the original receipt when the operation_key matches.

### CLAIM_STATE_AND_REWARD_ORDERING

DailyRewardService validates quest existence, completion, matching period and unclaimed state before mutation. It then validates reward capacity, builds reward plans, grants both reward components, marks the claim state and writes one receipt inside the same Unit of Work.

### INVENTORY_CAPACITY_AND_STACKS

The service builds and validates the small-HP stack plan for exactly 3 units before the first mutation. Capacity failure rejects the whole claim. Stack application and optional compaction occur inside the claim transaction; rejected claims never normalize inventory.

### ATOMICITY_IDEMPOTENCY_AND_RESTART

Every claim requires a stable operation_key. Same key with identical user_id, period_key and reward_key replays one immutable receipt. Changed payload conflicts. Potion grant, 3-token credit, claim-state update and receipt use one caller-owned commit; any failure rolls all effects back. Persisted receipt and claim state prevent duplicate rewards after restart.

### CONSUMER_ALLOWLIST_AND_SHADOW_OWNERS

DailyRewardService is the sole V2 mutation owner. Allowed consumers are daily presentation and explicit recovery/testing adapters. Quest state, inventory and token wallet are dependencies. Compatibility wrappers may delegate only. Direct SQL grants, presentation-owned mutation, simulator grants and duplicate reward owners are forbidden.

## Implementation boundary

Only the API-ready V2 domain/application layer is authorized. SQLite, production adapters, runtime and Telegram wiring remain forbidden.

## Next patch

`patch_21_10_6c_implement_daily_reward.py`
