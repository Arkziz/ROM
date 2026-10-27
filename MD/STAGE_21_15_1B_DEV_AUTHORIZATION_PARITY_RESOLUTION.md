# Stage 21.15.1b — DEV authorization parity resolution

- Status: **PASS**
- Decision: **PARITY_RESOLVED_IMPLEMENTATION_AUTHORIZED**
- Production mutation: **NO**
- Production SQLite / `.env`: **NOT OPENED**
- Manual in-game verification: **NOT REQUIRED**
- `game.db-wal` / `game.db-shm`: **NOT MANIPULATED**

## Resolutions

### canonical_dev_identity_policy
- Status: **RESOLVED**
- Resolution: Preserve V1 separation. DEV_MODE is a capability gate, not proof of caller identity. Commands that V1 intentionally exposes only through DEV handler registration remain DEV-capability operations; administrative production operations retain their authoritative allowlist guard. V2 must represent both inputs explicitly and must not invent developer IDs.
- Implementation rule: Authorization input = capability_enabled plus operation policy. Identity is required only where the authoritative V1 operation owner requires it; identity values are injected by configuration and never embedded.
- Owners: `handlers/dev.py`, `config.py`, `systems/admin_crystal_credit_system.py`

### effective_register_dev_handlers_chain
- Status: **RESOLVED**
- Resolution: Python last-definition semantics select the final top-level register_dev_handlers definition in handlers/dev.py. main.py invokes that exported name. Earlier same-name definitions are shadow evidence, not parallel runtime owners.
- Owners: `handlers/dev.py`, `main.py`

### command_inventory_and_risk_class
- Status: **RESOLVED_AS_CLASSIFICATION_CONTRACT**
- Resolution: V2 must register only explicitly declared command specifications. Each specification requires one of READ_ONLY, CONTROLLED_MUTATION, DESTRUCTIVE_RESET, or ADMIN_PRODUCTION. db_modules/dev_compat.py helpers cannot authorize or self-register commands. Exact Telegram command names remain transport metadata and are not implemented in the API-ready domain stage.
- Owners: `handlers/dev.py`, `db_modules/dev_compat.py`

### audit_requirements_per_command
- Status: **RESOLVED**
- Resolution: Preserve operation-specific V1 guarantees. ADMIN_PRODUCTION operations that already have durable audit/idempotency must require those capabilities. DEV operations without proven V1 durable audit must not receive an invented ledger; their API contract exposes audit_required and idempotency_required flags for fail-closed adapter validation.
- Owners: `systems/admin_crystal_credit_system.py`, `handlers/dev.py`

### separate_auction_admin_policy
- Status: **RESOLVED**
- Resolution: Auction administrator authorization remains a separate authoritative policy. It must not be merged into ROM_ADMIN_USER_IDS or the DEV capability gate by Stage 21.15.1 implementation.
- Owners: `handlers/auction_house.py`, `config.py`

## Implementation authorization

- `decision_function`: A single pure guard evaluates capability, identity requirement, allowed caller IDs, command risk class, and required adapter guarantees before execution.
- `default_behavior`: FAIL_CLOSED
- `disabled_behavior`: DENY_BEFORE_SIDE_EFFECT
- `unknown_command_behavior`: DENY_BEFORE_SIDE_EFFECT
- `unauthorized_behavior`: DENY_BEFORE_SIDE_EFFECT
- `risk_classes`: ['READ_ONLY', 'CONTROLLED_MUTATION', 'DESTRUCTIVE_RESET', 'ADMIN_PRODUCTION']
- `identity_values`: CONFIGURATION_INJECTED_ONLY
- `audit_policy`: DECLARED_PER_OPERATION_FROM_V1_EVIDENCE
- `idempotency_policy`: DECLARED_PER_OPERATION_FROM_V1_EVIDENCE
- `runtime_registration`: OUT_OF_SCOPE
- `telegram_transport`: OUT_OF_SCOPE
- `production_persistence`: OUT_OF_SCOPE

## Prohibitions

- Do not hard-code developer or administrator IDs.
- Do not merge auction administrator policy with ROM administrator or DEV policy.
- Do not invent audit rows or idempotency guarantees absent from V1.
- Do not register Telegram handlers, start main.py, open production SQLite, read .env, or wire production persistence.
- Do not execute any DEV or administrator operation during implementation tests.

Stage 21.15.1c is authorized to implement only the pure API-ready authorization domain described above.
