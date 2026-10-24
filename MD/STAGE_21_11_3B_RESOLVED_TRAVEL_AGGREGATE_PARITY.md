# Stage 21.11.3b - Resolved Travel Aggregate parity

- Status: **PASS**
- Conclusion: **GO_TO_IMPLEMENTATION**
- Resolved contracts: **7/7**
- Remaining unresolved contracts: **0**
- Implementation authorized: **True**
- Runtime integration authorized: **False**
- Production persistence authorized: **False**
- Manual game check: **NOT_REQUIRED**

## Resolutions

### START_AND_AVAILABILITY_PIPELINE

StartTravel evaluates busy state first, then opens one Unit of Work. Inside it: load account/current location and level; validate source and destination IDs; validate adjacency; validate destination unlock unless destination is city; reject an existing ACTIVE travel; create ACTIVE revision 1 with started_at=UTC now and arrival_at=now+20 seconds; commit once.

### SINGLE_ACTIVE_AND_BUSY_RESTRICTIONS

BusyStatePort is authoritative for incompatible activity. A truthy busy snapshot rejects before mutation as player_busy. The repository and database unique constraint remain the race-safe final guard for one ACTIVE travel per user; constraint collision maps to already_travelling.

### CANCEL_REVISION_AND_TERMINAL_POLICY

Cancel requires travel existence, ownership, ACTIVE state, not-yet-due ETA and matching expected revision. V2 uses expected_revision as required command concurrency data. Success sets CANCELLED, increments revision once and timestamps cancelled_at/updated_at. Replays are read-only typed rejections.

### COMPLETE_LOCATION_MUTATION_ATOMICITY

Complete claims one due ACTIVE travel in one Unit of Work. It verifies the user's current location still equals from_node. Source drift sets FAILED and increments revision. Successful completion compare-and-sets current_location to to_node and sets ARRIVED with one revision increment in the same commit. Any persistence exception rolls back both changes.

### RESTART_RECOVERY_AND_WORKER_POLICY

Recovery queries persisted due ACTIVE rows ordered by arrival_at then id, bounded to 100 per batch, and invokes the same completion service. Scheduler ownership is application/infrastructure, not entity logic. Multi-process correctness relies on transactional terminal claim. Notification occurs after commit and failure never rolls back travel; durable outbox is deferred because V1 has none.

### FAILURE_REASONS_AND_IDEMPOTENCY

Queries are side-effect free. Start retry after a successful commit returns already_travelling. Cancel and complete terminal replays never mutate or increment revision. Completion races return terminal_claim_lost or the persisted terminal snapshot. All validation failures occur before aggregate mutation; persistence failures raise after rollback.

### CONSUMER_PRESENTATION_AND_NOTIFICATION_BOUNDARY

Domain owns immutable travel state and transitions. Application service owns commands, Unit of Work, World Graph/Location Catalog/BusyState ports and recovery orchestration. Persistence adapter owns storage. Scheduler triggers recovery. Telegram/map adapters render DTOs and send notifications after commit. Presentation text and keyboards never enter domain/application owners.

## Implementation boundary

Only pure aggregate/application logic, ports, in-memory fixtures, tests and smoke verification are authorized. SQLite production persistence, Telegram/runtime wiring, scheduler threads and notification delivery remain forbidden.

## Next patch

`patch_21_11_3c_implement_travel_aggregate.py`
