# Stage 21.12.3b - Resolved Guild Contracts/History parity

- Status: **PASS**
- Conclusion: **GO_TO_IMPLEMENTATION**
- Resolved contracts: **7/7**
- Remaining unresolved contracts: **0**
- Implementation authorized: **True**
- Runtime integration authorized: **False**
- Production persistence authorized: **False**
- Retention cleanup authorized: **False**
- Manual game check: **NOT_REQUIRED**

## Resolutions

### CONTRACT_TARGET_NAME_PROPAGATION

V2 accepts one immutable GuildContractCompletion DTO with completion_key, user_id and canonical target_name. The adapter may map legacy V1 aliases in order target_mob_name, name, title, contract_name, but the domain receives only normalized target_name. Blank or absent names return missing_target_name before any mutation. The literal контракт is permitted only when the legacy caller truly supplies the string контракт; it is never substituted when canonical target metadata exists.

### GUILD_PROGRESS_AND_REWARD_ATOMICITY

One Unit of Work atomically applies guild EXP, guild resource, guild contract counter, member contribution and one typed history event. Membership is checked before mutation. Any failed write rolls back all counters and the history append. The result exposes applied deltas and event identity, not presentation text.

### LOCALIZED_GUILD_LOG_POLICY

Persistence stores a typed event code and payload containing target_name and optional actor_name. Ukrainian text is rendered by presentation as Виконання контракту: <target_name>. with the V1-confirmed actor suffix when available. Technical user IDs are never substituted into visible text. Unknown actor may be omitted; missing target_name is a command failure, not a generic visible fallback.

### GUILD_LOG_RETENTION_POLICY

API-ready V2 preserves V1 semantics: guild history is persisted without automatic deletion or last-100 cleanup. Readers remain newest-first by monotonic event identity, clamp page size to 1..100 and support count plus offset pagination. Any future retention cap requires a separate approved migration and must not be introduced in Stage 21.12.3c.

### CONTRACT_COMPLETION_IDEMPOTENCY

completion_key is the stable identity of one claimed Contract System completion. Guild reward application atomically claims that key in the same Unit of Work as counters and history. First application returns applied; replay returns already_applied with the original result and performs no writes. Crash-after-commit retries resolve through the persisted claim. A blank completion_key fails before mutation.

### HISTORY_PERMISSION_AND_VISIBILITY

Guild history queries require current membership in the requested guild. Former members and unrelated users receive permission_denied; dissolved or missing guilds return guild_not_found. Empty and out-of-range pages return an empty page with canonical count metadata. Authorization belongs to the application query service, not Telegram handlers.

### PRESENTATION_AND_HANDLER_BOUNDARY

Guild History application services expose typed event/page DTOs only. Domain and application modules do not import Telegram or build Ukrainian prose. The Telegram adapter owns date formatting, localized event text, keyboards and page state. Stage 21.12.3c implements pure APIs, in-memory fixtures, tests and smoke verification only; production persistence and handler wiring remain disconnected.

## Implementation boundary

Stage 21.12.3c may implement pure completion/history DTOs, application services, idempotency and query ports, in-memory fixtures, tests and smoke verification. It may not connect SQLite/Telegram/runtime, delete historical rows or alter reward values.

## Next patch

`patch_21_12_3c_implement_guild_contracts_history.py`
