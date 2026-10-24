# Stage 21.12.1a - Refined Guild Core contract

- Status: **PASS**
- Conclusion: **REVIEW_REQUIRED**
- Refined contracts: **7**
- Remaining unresolved contracts: **7**
- Implementation authorized: **False**
- Manual game check: **NOT_REQUIRED**

## Canonical constants

- Creation cost: **50.00 gold**
- Minimum access level: **3**
- Default member limit: **10**

## Refined unresolved contracts

### NAME_TAG_ICON_IDENTITY_POLICY

Confirmed:

- name and tag pass dedicated normalization and validation functions
- name_norm and tag_norm are persisted unique keys
- icon passes a dedicated single-emoji contract
- creation revalidates normalized identity inside the savepoint before debit

Remaining question: Resolve exact length, Unicode, whitespace, case-folding, reserved-value and validation-reason contracts for typed V2 input.

### MEMBERSHIP_AND_ROLE_INVARIANTS

Confirmed:

- one guild_members row per user is schema-enforced
- creator is inserted as leader
- guilds.leader_user_id and guild_members.role represent leadership together
- roles are leader, officer and member
- member_limit is persisted on the guild

Remaining question: Resolve one aggregate invariant for leader pointer/role consistency, exactly one leader, officer limits, member counting and repair behavior.

### DUPLICATE_GUILD_AND_MEMBERSHIP_POLICY

Confirmed:

- normalized name and tag are unique
- membership user_id is unique
- creation checks existing membership before debit
- identity uniqueness is revalidated transactionally
- database constraint failures remain a final race guard

Remaining question: Resolve canonical typed reasons and idempotency behavior for duplicate name, duplicate tag, existing membership and concurrent creation.

### PERMISSIONS_AND_MANAGEMENT_BOUNDARY

Confirmed:

- application management permits leader and officer
- member role is read-only for management operations
- leader-only and leader-or-officer decisions are spread across Guild Core functions and handler flows
- presentation currently consumes role strings

Remaining question: Resolve a centralized permission matrix for creation, applications, role changes, removal, transfer, leave and dissolution without handler-owned authorization.

### LEAVE_TRANSFER_AND_DISSOLUTION_BOUNDARY

Confirmed:

- leave_guild and transfer_guild_leadership are canonical owner operations
- membership history records departures and join cooldowns
- leadership transfer and leader departure are separate lifecycle concerns
- guild-related rows are persistent and require coordinated mutation

Remaining question: Resolve leader leave preconditions, transfer atomicity, last-member dissolution, target eligibility, cooldown timing and terminal guild lifecycle semantics.

### PERSISTENCE_RESTART_AND_FAILURE_POLICY

Confirmed:

- guild, membership, roles, limits, logs and membership history are SQLite-persisted
- creation uses savepoint rollback and conditional debit
- critical Guild Core state is not RAM-only
- schema constraints survive restart

Remaining question: Resolve the V2 Unit of Work/repository ports, commit boundaries, rollback result contract, restart validation and constraint-error mapping.

### HANDLER_REGISTRATION_AND_CONSUMER_BOUNDARY

Confirmed:

- handlers/guild.py exposes one register_guild_handlers entrypoint
- the handler contains many decorator registrations inside one consumer module
- Guild Resource System consumes Guild Core identity/state
- Guild Core owner currently also returns presentation messages in result dictionaries

Remaining question: Resolve duplicate-registration prevention, one runtime registration path, typed application results and separation of Telegram text from Guild Core.

No production persistence, handler wiring, database mutation or new Guild Core behavior is authorized.

## Next patch

`patch_21_12_1b_resolve_guild_core_parity.py`
