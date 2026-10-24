# Stage 21.11.3 - Existing V1 Travel Aggregate audit

- Status: **PASS**
- Conclusion: **GO_TO_SEMANTIC_REFINEMENT**
- Implementation authorized: **False**
- Production changed: **False**
- Database opened: **False**
- Manual game check: **NOT_REQUIRED**

## Canonical V1 evidence

- Owner: `systems/travel_system.py`
- Persisted table: `location_travels`
- Lifecycle: `active -> arrived | cancelled | failed`
- One active travel per user: partial unique index
- ETA: UTC second precision plus canonical 20 seconds
- Start/cancel/complete: `BEGIN IMMEDIATE` transaction paths
- Restart: due active rows are recovered from persistence
- Critical travel state stored only in RAM: **False**

## Contract matrix

- `TRAVEL_AGGREGATE_OWNER_AND_SCHEMA`: **V1_CONFIRMED** - systems/travel_system.py owns persisted location_travels state, ACTIVE/terminal lifecycle and revisioned rows.
- `START_AND_AVAILABILITY_PIPELINE`: **REVIEW_REQUIRED** - V1 validates user, target, adjacency, unlock, optional busy state and existing active travel before insert; exact ordering and result contract require refinement.
- `ETA_TIME_AND_UTC_POLICY`: **V1_CONFIRMED** - UTC second-precision timestamps and TRAVEL_SECONDS define started_at and arrival_at.
- `SINGLE_ACTIVE_AND_BUSY_RESTRICTIONS`: **REVIEW_REQUIRED** - A partial unique index enforces one active travel; optional busy_checker behavior and exhaustive busy reasons require refinement.
- `CANCEL_REVISION_AND_TERMINAL_POLICY`: **REVIEW_REQUIRED** - Cancellation is allowed only for owned active not-yet-due travel and optionally checks expected_revision; exact stale/idempotency semantics require refinement.
- `COMPLETE_LOCATION_MUTATION_ATOMICITY`: **REVIEW_REQUIRED** - Completion verifies due/active/source state and updates users.location with terminal arrival in one transaction; exact claim and retry semantics require refinement.
- `RESTART_RECOVERY_AND_WORKER_POLICY`: **REVIEW_REQUIRED** - Due persisted travel is recovered after restart; worker ownership, ordering, limits and notification failure policy require refinement.
- `FAILURE_REASONS_AND_IDEMPOTENCY`: **REVIEW_REQUIRED** - Machine-readable V1 reasons were discovered; retry and terminal replay behavior require an explicit parity matrix.
- `PERSISTENCE_TRANSACTION_AND_ROLLBACK`: **V1_CONFIRMED** - V1 uses SQLite, BEGIN IMMEDIATE, commit and rollback; critical travel state is not RAM-only.
- `CONSUMER_PRESENTATION_AND_NOTIFICATION_BOUNDARY`: **REVIEW_REQUIRED** - Map and restart notification consumers exist; exact domain/application/presentation boundary requires refinement.

## Unresolved contracts

- `START_AND_AVAILABILITY_PIPELINE`
- `SINGLE_ACTIVE_AND_BUSY_RESTRICTIONS`
- `CANCEL_REVISION_AND_TERMINAL_POLICY`
- `COMPLETE_LOCATION_MUTATION_ATOMICITY`
- `RESTART_RECOVERY_AND_WORKER_POLICY`
- `FAILURE_REASONS_AND_IDEMPOTENCY`
- `CONSUMER_PRESENTATION_AND_NOTIFICATION_BOUNDARY`

No migration, SQLite mutation, runtime connection or new travel behavior is authorized by this audit.

## Next patch

`patch_21_11_3a_refine_travel_aggregate_contract.py`
