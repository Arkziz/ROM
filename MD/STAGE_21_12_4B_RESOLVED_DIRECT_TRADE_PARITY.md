# Stage 21.12.4b - Resolved Direct Trade parity

- Status: **PASS**
- Conclusion: **GO_TO_IMPLEMENTATION**
- Normalized contract matrix: **2 previously confirmed + 8 resolved = 10/10**
- Remaining unresolved contracts: **0**
- Implementation authorized: **True**
- Runtime integration authorized: **False**
- Production persistence authorized: **False**
- Production settlement authorized: **False**
- Manual game check: **NOT_REQUIRED**

## Resolutions

### SAME_LOCATION_ONLINE_AND_BUSY_POLICY

Trade creation requires an accepted trade request between two different users who are online, in the same canonical location, not busy in another activity and not already in an active trade. The same participant, active-trade and activity-session invariants are rechecked before ready and final settlement; a location or availability change returns a typed rejection before transfer. Eligibility belongs to the application service, not Telegram handlers.

### TRADEABLE_ITEM_POLICY

One canonical item-policy service is used by inventory browsing, reservation and settlement. It rejects equipped items, auction-reserved items, gray loot, Firius Tokens, Rune of Success, Perfect Extractor, Sphere of the New Path, quest/DEV/premium-bound items and any item with tradeable=False; Simple Extractor remains permitted. Offers reference exact inventory_id, quantity and immutable snapshot, preserving generated-equipment identity.

### OFFER_REVISION_AND_EDITING_POLICY

Every effective item or gold offer mutation increments trade revision and clears both participants' ready and confirmed flags. expected_revision mismatch returns stale_revision without mutation. An idempotent no-change request reports unchanged and does not increment revision. Returning to editing is allowed for either participant before completion, increments revision once and clears all readiness/confirmation state.

### TWO_PHASE_CONFIRMATION

The canonical state flow is editing -> ready -> final confirmation -> completed. Both participants independently mark ready against the same revision; only when both are ready may either confirm. Each participant confirms once; the first confirmation is non-terminal, the second triggers settlement. Replays return already_ready or already_confirmed without duplicate mutation. Any offer edit or return-to-editing invalidates all confirmations.

### ATOMIC_ITEM_AND_GOLD_SETTLEMENT

The second final confirmation opens one BEGIN IMMEDIATE Unit of Work. It reloads trade and revision, verifies both ready/confirmed flags, participants, reservations, exact quantities, item policy, snapshots, wallet balances and recipient bag capacity, then transfers items and gold, writes terminal status/history, releases reservations and activity sessions, and commits once. Any failure rolls back every transfer and leaves the trade non-completed; retry uses persisted terminal status to prevent double settlement.

### CANCEL_EXPIRY_AND_RELEASE_POLICY

Either participant may cancel an active non-terminal trade. Expiry is a system action for stale active trades. Cancel and expiry atomically set one terminal status/reason, append history, release every trade reservation and release matching activity sessions. Replays against the same terminal trade are idempotent and perform no second release. Completed trades cannot be cancelled or expired.

### RESTART_RECOVERY_POLICY

Restart recovery scans persisted active trades. Expired or structurally invalid trades are terminally expired/cancelled with atomic reservation and session release. Valid unexpired trades preserve offers and reservations, clear transient ready/confirmed state when V1 evidence requires it, and restore or reconcile matching activity sessions. Completed/cancelled/expired trades are never reopened or settled again. Repeated recovery returns a typed per-trade report and is idempotent.

### PRESENTATION_AND_HANDLER_BOUNDARY

A single Direct Trade application service owns commands, lifecycle, policy and typed results. Domain/application code does not import Telegram. Handlers own keyboards, localized text, editor page state and callback parsing, pass trade_id plus expected_revision, and map typed reasons to Ukrainian presentation. Compatibility wrappers delegate only and never become a second production owner.

## Implementation boundary

Stage 21.12.4c may implement pure Direct Trade DTOs, policies, state machine, in-memory Unit of Work, tests and smoke verification. It may not connect SQLite/Telegram/runtime or mutate real inventory and gold.

## Next patch

`patch_21_12_4c_implement_direct_trade.py`
