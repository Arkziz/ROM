# Stage 21.15.2a — DEV data operations contract refinement

- Status: **PASS**
- Decision: **REFINED_PARITY_RESOLUTION_REQUIRED**
- Next action: **GO_TO_PARITY_RESOLUTION**
- Flat domain module: `rom_v2/domain/dev_data_operations.py`
- Production mutation / DEV operation execution: **NO**
- Production SQLite / `.env`: **NOT OPENED**
- Manual in-game verification: **NOT REQUIRED**
- `game.db-wal` / `game.db-shm`: **NOT MANIPULATED**

## Refined contract

### operation_boundary
- Status: **REFINED**
- Contract: Give, Reset and Set are application commands. Telegram handlers and DEV compatibility helpers are adapters, not the V2 invariant-owning boundary.
- Owners: `handlers/dev.py`, `db_modules/dev_compat.py`

### authorization_order
- Status: **REFINED**
- Contract: The Stage 21.15.1 authorization decision must succeed before target lookup, repository mutation, notification or audit append. Disabled or unauthorized paths produce no observable side effect.
- Owners: `rom_v2/domain/dev_authorization.py`, `handlers/dev.py`

### application_service
- Status: **REFINED_WITH_PARITY_REVIEW_REQUIRED**
- Contract: Each operation invokes a typed application-service port and repository/Unit-of-Work abstraction. V1 direct SQL is behavioral evidence only and is not an authorized V2 bypass.
- Owners: `db_modules/dev_compat.py`, `systems/admin_crystal_credit_system.py`

### transaction
- Status: **REFINED**
- Contract: Validation, mutation and required audit/idempotency receipt are one atomic application transaction. Any mandatory failure rolls back the complete operation.
- Owners: `systems/admin_crystal_credit_system.py`, `db_modules/dev_compat.py`

### target_identity
- Status: **REFINED_WITH_PARITY_REVIEW_REQUIRED**
- Contract: Each command declares one canonical target kind: account, user, character, item definition or inventory instance. Identifiers are not interchangeable and must be resolved before mutation.
- Owners: `handlers/dev.py`, `db_modules/dev_compat.py`

### give
- Status: **REFINED_WITH_PARITY_REVIEW_REQUIRED**
- Contract: Give operations validate the authoritative item/currency/resource identity and quantity, then use the canonical service that preserves binding, namespace, stack, capacity, wallet and ledger invariants evidenced by V1.
- Owners: `handlers/dev.py`, `db_modules/dev_compat.py`, `systems/premium_item_policy_system.py`, `systems/admin_crystal_credit_system.py`

### reset
- Status: **REFINED_WITH_PARITY_REVIEW_REQUIRED**
- Contract: Reset uses an explicit field/scope policy. Character-level data may be reset only where V1 proves it; account-level wallets, entitlements, audit ledgers and other preserved data must not be deleted by implication.
- Owners: `handlers/dev.py`, `db_modules/dev_compat.py`

### set
- Status: **REFINED_WITH_PARITY_REVIEW_REQUIRED**
- Contract: Set operations validate exact V1 bounds and derive dependent state through canonical domain/application services. Raw field assignment cannot bypass level, EXP, stats, wallet or inventory invariants.
- Owners: `handlers/dev.py`, `db_modules/dev_compat.py`

### idempotency_and_audit
- Status: **REFINED_WITH_PARITY_REVIEW_REQUIRED**
- Contract: Where V1 proves durable audit or idempotency, V2 preserves it within the transaction. A universal receipt is not invented for operations lacking evidence; parity resolution must decide per command.
- Owners: `systems/admin_crystal_credit_system.py`, `handlers/dev.py`

### result_and_notification
- Status: **REFINED**
- Contract: The application service returns a deterministic result. External notification occurs only after commit and is not part of the domain mutation transaction.
- Owners: `handlers/dev.py`, `systems/admin_crystal_credit_system.py`

### flat_domain_layout
- Status: **REFINED_FINAL**
- Contract: Any Stage 21.15.2c domain contract is implemented in the flat module rom_v2/domain/dev_data_operations.py; rom_v2/domain/dev_data_operations/ is prohibited.
- Owners: `Stage 21.15.1d flat-domain remediation`, `reports/stage_21_15_2_existing_dev_data_operations_audit.json`

## Unresolved for parity resolution

- **effective_operation_inventory**: Exact effective Give/Reset/Set commands must be resolved after Python shadowing and registration order.
- **operation_target_matrix**: Canonical target kind and lookup semantics must be resolved per operation.
- **give_validation_matrix**: Exact item/currency/resource identities, quantities, caps, binding and capacity behavior require V1 owner resolution.
- **reset_scope_matrix**: Exact reset/delete/preserve fields and account-vs-character boundaries require parity resolution.
- **set_bounds_and_derived_state**: Exact bounds and dependent recalculation behavior for level, EXP, gold and other setters require parity resolution.
- **service_repository_mapping**: Each operation must map to an existing V2 service/repository or an explicitly authorized port without direct SQL.
- **audit_idempotency_matrix**: Durable audit and idempotency requirements are not proven uniform across all operations.
- **post_commit_notifications**: Exact notification and history/domain-event behavior must be resolved per operation.

## Superseded interpretations

- A handler or compatibility helper is not the V2 application-service boundary.
- V1 direct SQL is not automatically authorized for V2.
- User, account, character, item definition and inventory instance IDs are not interchangeable.
- Reset does not imply deletion of account-level wallets, entitlements or audit data.
- Set does not imply raw assignment without dependent invariant recalculation.
- Keyword matches outside authoritative owners do not define operation policy.

## Non-goals

- No V1/V2 production mutation.
- No DEV operation execution.
- No production SQLite or .env access.
- No invented operation, quantity, bound, target, reset scope, service mapping, audit field or idempotency rule.
- No runtime, Telegram or production persistence wiring.

Stage 21.15.2b must resolve every listed parity question before implementation authorization.
