# Stage 21.11.3a - Refined Travel Aggregate contract

- Status: **PASS**
- Conclusion: **REVIEW_REQUIRED**
- Refined contracts: **7**
- Remaining unresolved contracts: **7**
- Implementation authorized: **False**
- Production changed: **False**
- Database opened: **False**
- Manual game check: **NOT_REQUIRED**

## Confirmed ownership

- Persisted aggregate and transactions: `systems/travel_system.py`
- Static nodes, adjacency and 20-second duration: World Graph
- Destination unlock: Location Catalog
- Route/arrival prose: `data/travel_presentation.py`
- Telegram map consumer: `handlers/map.py`
- Travelling context consumer: `systems/location_context_system.py`

## Refined unresolved contracts

### START_AND_AVAILABILITY_PIPELINE

Confirmed:

- busy_checker executes before the SQLite transaction
- inside BEGIN IMMEDIATE V1 loads the user and derives source from current_location or city
- availability checks source identity, destination identity, adjacency and destination unlock
- existing active travel is rejected before insertion
- arrival_at equals UTC now plus canonical TRAVEL_SECONDS

Remaining question: Resolve the V2 command/port split, exact check ordering, and whether busy-state evaluation must be repeated transactionally before save.

### SINGLE_ACTIVE_AND_BUSY_RESTRICTIONS

Confirmed:

- partial unique index guarantees at most one ACTIVE row per user
- explicit already_travelling rejection exists before insert
- SQLite IntegrityError is mapped to already_travelling
- truthy busy_checker output maps to player_busy and may carry a dict payload

Remaining question: Resolve the canonical busy port, accepted busy categories, check timing, and race-safe interaction with the unique constraint.

### CANCEL_REVISION_AND_TERMINAL_POLICY

Confirmed:

- cancel requires matching user, ACTIVE status and arrival_at greater than now
- expected_revision is optional and participates in the conditional UPDATE when supplied
- successful cancel increments revision and writes cancelled_at/updated_at
- all zero-row outcomes currently collapse to not_cancellable with the current row returned

Remaining question: Resolve typed stale-revision, already-terminal, already-due, wrong-owner and replay semantics instead of one collapsed rejection.

### COMPLETE_LOCATION_MUTATION_ATOMICITY

Confirmed:

- complete requires existing ACTIVE due travel
- source drift marks travel FAILED and increments revision
- terminal arrival claim and users.current_location compare-and-set occur in one transaction
- location changes only on successful completion, never at start
- lost terminal claim returns terminal_claim_lost

Remaining question: Resolve the V2 Unit of Work ports, claim ordering, source-drift result, rollback contract and retry/idempotency result shapes.

### RESTART_RECOVERY_AND_WORKER_POLICY

Confirmed:

- due ACTIVE rows are ordered by arrival_at then id and processed with a bounded limit
- restart recovery calls the same complete_travel path
- arrival notification is attempted only after successful completion
- notification failure does not roll back the already committed travel completion
- a process-local flag prevents duplicate worker startup only within one process

Remaining question: Resolve V2 scheduler ownership, batch limit, multi-process safety, retry cadence and durable notification/outbox policy.

### FAILURE_REASONS_AND_IDEMPOTENCY

Confirmed:

- already_terminal
- already_travelling
- invalid_current_node
- location_locked
- not_adjacent
- not_cancellable
- not_due
- player_busy
- source_changed
- terminal_claim_lost
- travel_not_found
- unknown_destination
- user_not_found

Remaining question: Resolve one operation-by-operation matrix for validation failures, stale/replay outcomes, terminal replays, transient persistence failures and safe retries.

### CONSUMER_PRESENTATION_AND_NOTIFICATION_BOUNDARY

Confirmed:

- handlers/map.py owns Telegram command/callback presentation and calls travel queries/commands
- systems/location_context_system.py consumes only travelling state
- data/travel_presentation.py owns route and arrival prose
- systems/travel_system.py currently also contains Telegram keyboard/message helpers and worker code

Remaining question: Resolve extraction of domain/application behavior from Telegram notification, keyboard, worker and presentation concerns without creating a second command path.

No migration, SQLite mutation, runtime connection, scheduler or notification implementation is authorized.

## Next patch

`patch_21_11_3b_resolve_travel_aggregate_parity.py`
