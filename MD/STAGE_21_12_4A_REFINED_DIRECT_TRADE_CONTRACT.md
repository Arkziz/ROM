# Stage 21.12.4a - Refined Direct Trade contract

- Status: **PASS**
- Conclusion: **REVIEW_REQUIRED**
- Source matrix normalized: **2 confirmed / 8 review-required / 10 total**
- Refined contracts: **8**
- Remaining unresolved contracts: **8**
- Implementation authorized: **False**
- Manual game check: **NOT_REQUIRED**

## Refined unresolved contracts

### SAME_LOCATION_ONLINE_AND_BUSY_POLICY

Confirmed:

- trade creation originates from an accepted interaction request
- player presence has a canonical online predicate
- activity sessions provide a canonical busy predicate
- location metadata participates in interaction eligibility

Remaining question: Resolve the exact create-time and confirm-time recheck order for same location, online status, busy state, self-target, active trade and accepted request under concurrent changes.

### TRADEABLE_ITEM_POLICY

Confirmed:

- trade offers use inventory_id and immutable item snapshots
- policy rejects equipped, reserved and non-tradeable inventory
- premium, quest, DEV and other bound categories participate in policy checks
- gold is offered through a separate wallet path

Remaining question: Resolve the complete V1 rejection matrix, snapshot fields, stack quantities, generated-equipment identity and the single policy owner shared by editor and final settlement.

### OFFER_REVISION_AND_EDITING_POLICY

Confirmed:

- trade state carries a revision
- mutations accept expected_revision
- offer changes invalidate readiness and confirmations
- ready trades can return to editing

Remaining question: Resolve every revision increment, stale-revision result, which mutations clear one or both ready/confirmed flags, and idempotent no-change behavior.

### TWO_PHASE_CONFIRMATION

Confirmed:

- each participant has an independent ready flag
- final confirmation is stored independently for initiator and recipient
- final settlement requires both ready and both confirmed
- repeated confirmation detects already-confirmed state

Remaining question: Resolve the exact state machine editing to ready to confirming to completed, participant-specific replay results, offer immutability after ready and behavior when either side returns to editing.

### ATOMIC_ITEM_AND_GOLD_SETTLEMENT

Confirmed:

- final confirmation uses BEGIN IMMEDIATE
- _commit_player_trade is the authoritative settlement owner
- reservations and current inventory quantities are revalidated
- items, stacks, gold, terminal status, history and activity release are coordinated

Remaining question: Resolve the exact settlement write order, bag-capacity and wallet checks, generated equipment transfer identity, rollback guarantees, retry mapping and crash-after-commit result.

### CANCEL_EXPIRY_AND_RELEASE_POLICY

Confirmed:

- participants can cancel active trade
- stale trades expire through a dedicated operation
- reservation release is a canonical operation
- terminal history and activity-session cleanup exist

Remaining question: Resolve cancellable statuses, actor authorization, cancellation/expiry idempotency, reservation release ordering, event/history reason and behavior when release finds drift or missing rows.

### RESTART_RECOVERY_POLICY

Confirmed:

- recover_active_player_trades_after_restart is canonical V1 behavior
- recovery inspects active trades and activity sessions
- expiry and orphan-session cleanup are available
- terminal trades must not be settled again after restart

Remaining question: Resolve which active statuses survive restart, which are cancelled or expired, how reservations are reconciled, how sessions are reacquired/released, and the exact idempotent recovery report.

### PRESENTATION_AND_HANDLER_BOUNDARY

Confirmed:

- systems/player_interaction_system.py owns trade mutations
- handlers/player_interaction.py owns Telegram interaction and editor state
- db_modules/systems_wrappers.py is a compatibility facade
- machine-readable results already cross the handler boundary

Remaining question: Resolve typed command/result DTOs, one application service owner, error-to-text mapping, callback revision tokens and a single handler registration path without Telegram imports in domain/application code.

No production mutation, settlement execution, database access or runtime wiring is authorized.

## Next patch

`patch_21_12_4b_resolve_direct_trade_parity.py`
