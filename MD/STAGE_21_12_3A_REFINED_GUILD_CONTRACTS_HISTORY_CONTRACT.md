# Stage 21.12.3a - Refined Guild Contracts/History contract

- Status: **PASS**
- Conclusion: **REVIEW_REQUIRED**
- Refined contracts: **7**
- Remaining unresolved contracts: **7**
- Implementation authorized: **False**
- Manual game check: **NOT_REQUIRED**

## Refined unresolved contracts

### CONTRACT_TARGET_NAME_PROPAGATION

Confirmed:

- award_guild_contract_completion accepts contract payload
- target name resolution checks target_mob_name, name, title and contract_name in order
- generic контракт is the final fallback
- contract completion caller can pass either a structured payload or a string

Remaining question: Resolve one typed completion DTO and authoritative target_name field, legacy alias handling, missing-name result and the exact boundary that prevents generic fallback when canonical target metadata exists.

### GUILD_PROGRESS_AND_REWARD_ATOMICITY

Confirmed:

- contract completion delegates to add_user_guild_progress
- guild EXP, resource, contract counter and member contribution are coordinated by Guild System
- history reason is derived before progress mutation
- non-member completion returns without guild progress

Remaining question: Resolve one Unit of Work for guild totals, member contribution and history append, including rollback and result mapping when any write fails.

### LOCALIZED_GUILD_LOG_POLICY

Confirmed:

- contract reason uses GUILD_CONTRACT_SCORE_REASON
- resolved contract_name and optional actor character name are embedded in the reason
- handler formats persisted log text for Ukrainian presentation
- user_id leakage has separate character-name compatibility work

Remaining question: Resolve typed event payload versus persisted localized text, punctuation, unknown actor/target fallbacks and a hard rule that available target metadata must render the localized mob name rather than контракт.

### GUILD_LOG_RETENTION_POLICY

Confirmed:

- guild_logs are persisted and countable
- reader clamps page size to 1..100
- reader pagination does not itself delete rows
- audit found no canonical retention cleanup in the verified owner path

Remaining question: Resolve whether V2 preserves unbounded persisted history or adopts the separately approved last-100 event policy, and define cleanup ownership without silently deleting V1 data.

### CONTRACT_COMPLETION_IDEMPOTENCY

Confirmed:

- award entrypoint accepts no explicit idempotency key
- progress and history are produced from completion flow
- repeated calls can be operationally distinct unless caller state prevents replay
- contract system owns completion state

Remaining question: Resolve the completion identity key, exactly-once claim location, duplicate result, crash-after-commit recovery and whether Guild System trusts a pre-claimed completion.

### HISTORY_PERMISSION_AND_VISIBILITY

Confirmed:

- history is scoped by guild_id
- presentation enters through the current user's guild context
- pagination exposes count and page navigation
- history is a read-only guild feature

Remaining question: Resolve member-only visibility, behavior after leaving or dissolution, actor-name privacy, empty/out-of-range pages and authorization ownership outside Telegram handlers.

### PRESENTATION_AND_HANDLER_BOUNDARY

Confirmed:

- Guild System owns persisted log rows and counts
- handlers/guild.py owns text, dates, keyboards and page state
- contract system initiates reward after completion
- presentation consumes already persisted reason text

Remaining question: Resolve typed history DTOs, event-to-text localization, one application query service and handler registration boundary without importing Telegram into domain/application code.

No production mutation, retention cleanup, runtime wiring or new guild-contract rule is authorized.

## Next patch

`patch_21_12_3b_resolve_guild_contracts_history_parity.py`
