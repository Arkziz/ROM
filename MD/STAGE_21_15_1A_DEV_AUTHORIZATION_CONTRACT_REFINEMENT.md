# Stage 21.15.1a — DEV authorization contract refinement

- Status: **PASS**
- Decision: **REFINED_PARITY_RESOLUTION_REQUIRED**
- Next action: **GO_TO_PARITY_RESOLUTION**
- Production mutation: **NO**
- Production SQLite / `.env`: **NOT OPENED**
- Manual in-game verification: **NOT REQUIRED**
- `game.db-wal` / `game.db-shm`: **NOT MANIPULATED**

## Refined contract

### dev_mode
- Status: **REFINED**
- Contract: DEV_MODE is an environment-controlled capability gate. Disabled DEV_MODE must prevent DEV handler registration or fail closed before any DEV side effect, according to the authoritative V1 registration path.
- Owners: `handlers/dev.py`, `main.py`

### identity
- Status: **REFINED_WITH_PARITY_REVIEW_REQUIRED**
- Contract: DEV_MODE and administrator identity are distinct dimensions. ROM_ADMIN_USER_IDS is evidence for administrative authorization; auction-specific identity sources are separate V1 policy and must not be silently merged without parity resolution.
- Owners: `config.py`, `systems/admin_crystal_credit_system.py`, `handlers/auction_house.py`

### single_guard
- Status: **TARGET_CONTRACT_REQUIRES_PARITY_RESOLUTION**
- Contract: V2 requires one explicit authorization decision before command execution: capability enabled, caller authorized for the operation class, and command classified as allowed. Existing V1 local checks remain evidence, not automatically canonical duplicates.
- Owners: `handlers/dev.py`, `handlers/fatigue_artifact.py`, `handlers/guild.py`, `systems/premium_item_policy_system.py`

### registration
- Status: **REFINED_WITH_SHADOW_REVIEW_REQUIRED**
- Contract: The effective register_dev_handlers definition and main.py invocation chain must be identified by Python last-definition semantics. Earlier duplicate definitions are shadow candidates and cannot be treated as simultaneous canonical owners.
- Owners: `handlers/dev.py`, `main.py`

### command_classes
- Status: **REFINED**
- Contract: Commands must be classified as read-only diagnostics, controlled reversible mutation, destructive reset, or administrative production operation. Test helpers in db_modules/dev_compat.py are not Telegram authorization policy by themselves.
- Owners: `handlers/dev.py`, `db_modules/dev_compat.py`, `systems/admin_crystal_credit_system.py`

### guard_order
- Status: **REFINED**
- Contract: Authorization must complete before database writes, item grants, currency changes, resets, notifications, or other observable side effects. Unauthorized and disabled paths must not partially mutate state.
- Owners: `handlers/dev.py`, `systems/admin_crystal_credit_system.py`, `handlers/auction_house.py`

### audit_and_idempotency
- Status: **REFINED_WITH_PARITY_REVIEW_REQUIRED**
- Contract: Where V1 provides durable audit or idempotency, V2 must preserve it. The audit must not invent a universal ledger for commands whose V1 owner has none; gaps require explicit parity resolution.
- Owners: `systems/admin_crystal_credit_system.py`, `handlers/dev.py`

### configuration_secrecy
- Status: **REFINED**
- Contract: Configuration variable names may be modeled, but .env values and identity lists must never be copied into reports, tests, documentation, or source defaults.
- Owners: `config.py`, `handlers/dev.py`, `handlers/auction_house.py`

## Unresolved for parity resolution

- **canonical_dev_identity_policy**: Audit evidence shows DEV_MODE gating and separate administrator allowlists; parity resolution must decide which V1 commands are intentionally DEV_MODE-only and which require identity authorization.
- **effective_register_dev_handlers_chain**: Duplicate or extended register_dev_handlers definitions require exact last-definition and invocation-order resolution.
- **command_inventory_and_risk_class**: Each effective command must be mapped to read-only, controlled mutation, destructive reset, or administrative production operation from authoritative V1 code.
- **audit_requirements_per_command**: Durable audit and idempotency exist for some administrative operations but are not proven universal for all DEV commands.
- **separate_auction_admin_policy**: Auction administrator environment variables appear separate from ROM_ADMIN_USER_IDS and cannot be merged by refinement alone.

## Superseded interpretations

- Keyword matches outside authoritative owners are not DEV authorization policy.
- db_modules/dev_compat.py mutation helpers do not independently authorize callers.
- A DEV_MODE check alone must not be assumed equivalent to an administrator identity check.
- Earlier duplicate register_dev_handlers definitions are shadow candidates until exact resolution.

## Non-goals

- No V1/V2 production mutation.
- No new developer/admin identity values.
- No command execution, Telegram connection, production SQLite connection, migration, or runtime registration.
- No reading or reporting of .env values.

Stage 21.15.1b must resolve the listed V1 parity questions before implementation authorization.
