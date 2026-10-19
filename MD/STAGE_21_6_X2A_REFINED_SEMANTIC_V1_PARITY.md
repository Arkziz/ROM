# Stage 21.6.X2a — Refined semantic V1 parity review

## Decision

- Status: `PASS`
- Conclusion: `RECONCILIATION_REQUIRED`
- Semantic findings: `14`
- Blocking findings: `2`

The broad Stage 21.6.X2 substring inventory was not accepted as proof of semantic parity. This refinement resolves the known unproven constants, validates accepted Stage 21.6 audit/reconciliation chains, and explicitly identifies remaining schema and integration gaps.

## Classification summary

- `OVERSTATED_INTEGRATION`: 1
- `RECONCILED`: 1
- `UNPROVEN_PERSISTENT_CONTRACT`: 1
- `USER_APPROVED_V2_DESIGN`: 5
- `V1_CONFIRMED`: 5
- `V1_CONFIRMED_OR_RECONCILED`: 1

## Blocking findings

### PERSIST-FUTURE-GAMEPLAY-TABLES — item_instances, equipment_slots, item_reservations, quest_progress, quest_item_balances

- Stage: `21.5.1-21.5.2`
- Owner: `rom_v2/infrastructure/persistence/migrations/v001_v2_baseline.py`
- Classification: `UNPROVEN_PERSISTENT_CONTRACT`
- Severity: `HIGH`
- Rationale: The baseline reserves gameplay persistence semantics for future domains before their required V1 audits. The tables may be directionally correct, but columns, constraints and lifecycle actions are not yet authoritative V1 parity.
- Required action: Before the first corresponding domain mutation, audit V1 and either reconcile the existing table contract through a new migration or explicitly approve it. Do not treat the current schema as authoritative gameplay parity.

### INTEGRATION-SNAPSHOT-CONSUMERS — Profile, combat and simulator use one snapshot owner

- Stage: `21.6.5c/21.6.6b`
- Owner: `rom_v2/application/full_stat_snapshot_service.py`
- Classification: `OVERSTATED_INTEGRATION`
- Severity: `MEDIUM`
- Rationale: The one-owner API is implemented and tested, but concrete feature adapters and end-to-end runtime flows are deferred. API_READY is not equivalent to RUNTIME_DISPATCH_VERIFIED.
- Required action: Correct closure/current-state wording to API_READY and require concrete wiring verification in the later profile, combat and simulator roadmap stages.

## Resolved findings

- `TECH-SQLITE-BUSY-TIMEOUT`: `USER_APPROVED_V2_DESIGN` — DEFAULT_BUSY_TIMEOUT_MS
- `TECH-SQLITE-MMAP`: `USER_APPROVED_V2_DESIGN` — DEFAULT_MMAP_SIZE_BYTES
- `TECH-UOW-BEGIN`: `USER_APPROVED_V2_DESIGN` — _BEGIN_SQL
- `TECH-CALLBACK-LIMIT`: `USER_APPROVED_V2_DESIGN` — MAX_CALLBACK_BYTES
- `GAME-PRIMARY-KEYS`: `V1_CONFIRMED` — PRIMARY_KEYS=('str', 'dex', 'int', 'wis', 'sta')
- `RECON-ACCOUNT-CHARACTER`: `RECONCILED` — Account and character lifecycle after parity reconciliation
- `GAME-CLASS-CATALOG`: `V1_CONFIRMED` — Six-class resource, armor and equipment compatibility matrix
- `GAME-PRIMARY-STATS`: `V1_CONFIRMED` — Primary stat base, earned-points, allocation and respec contracts
- `GAME-DERIVED-STATS`: `V1_CONFIRMED` — Derived formulas and source-separated full stat snapshot
- `GAME-RESOURCE-LIFECYCLE`: `V1_CONFIRMED` — HP/MP initialization, maximum synchronization, bounded restore and defeat policy
- `PERSIST-IMPLEMENTED-DOMAINS`: `V1_CONFIRMED_OR_RECONCILED` — accounts, characters, character_primary_stats, gold_wallets, crystal_wallets, crystal_ledger
- `PERSIST-V2-TECHNICAL-TABLES`: `USER_APPROVED_V2_DESIGN` — schema_migrations, operation_records, domain_events, outbox_messages

## Required next step

Create `patch_21_6_X2b_reconcile_retrospective_parity_findings.py` only for the explicit blocking findings above. The reconciliation must not invent inventory, equipment or quest persistence rules. For future-domain tables it should downgrade current contracts to provisional/reserved status in documentation and require a new migration after each domain audit. For snapshot integration it should correct the evidence level to `API_READY`.

## Manual game check

`NOT_REQUIRED` for this read-only refinement. Any later production mutation must declare its own game-verification scenarios.
