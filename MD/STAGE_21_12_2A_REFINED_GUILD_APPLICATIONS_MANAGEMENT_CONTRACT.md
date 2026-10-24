# Stage 21.12.2a - Refined Guild Applications/Management contract

- Status: **PASS**
- Conclusion: **REVIEW_REQUIRED**
- Refined contracts: **7**
- Remaining unresolved contracts: **7**
- Implementation authorized: **False**
- Manual game check: **NOT_REQUIRED**

## Application statuses

- `pending`
- `accepted`
- `rejected`
- `cancelled`

## Refined unresolved contracts

### APPLICATION_ACCEPT_ATOMICITY

Confirmed:

- accept_guild_application is a canonical Guild System operation
- acceptance transitions a persisted pending application
- acceptance creates guild membership
- processed_at and processed_by are persisted
- acceptance is a mutation that must coordinate application and membership state

Remaining question: Resolve the exact transaction/savepoint boundary, conditional pending claim, membership insert ordering, log ordering, rollback contract and replay result.

### APPLICATION_REJECT_POLICY

Confirmed:

- reject_guild_application is a canonical Guild System operation
- only a pending application is eligible for rejection
- processed metadata is persisted
- leader/officer application-management permission is reused

Remaining question: Resolve typed not-found, wrong-guild, forbidden, already-processed and replay outcomes, plus whether rejection logging is inside the same commit boundary.

### MEMBER_LIMIT_AND_ELIGIBILITY_RECHECK

Confirmed:

- member_limit is persisted on guilds
- acceptance rechecks capacity rather than trusting list-time state
- applicant membership eligibility can change after application creation
- Guild Core access level and join cooldown are authoritative dependencies

Remaining question: Resolve the complete accept-time recheck order for level, cooldown, existing membership, guild existence, capacity and pending status under concurrency.

### ROLE_PROMOTION_AND_OFFICER_LIMIT

Confirmed:

- promotion uses promote_guild_member_to_officer
- officer count has a canonical query
- target membership and current role are inspected
- leader role is distinct and cannot be produced through officer promotion

Remaining question: Resolve the exact officer limit source, leader-only authorization, self-target behavior, already-officer replay and atomic conditional role update semantics.

### MEMBER_KICK_AND_SELF_PROTECTION

Confirmed:

- kick_guild_member is the canonical removal operation
- departure history and join cooldown infrastructure exist
- leader and ordinary member roles require different protection
- management is actor/target-aware

Remaining question: Resolve leader/officer kick permissions, self-kick prohibition, leader-target prohibition, officer-on-officer rules, departure logging and atomic removal/cooldown behavior.

### MANAGEMENT_PERMISSION_MATRIX

Confirmed:

- can_manage_guild_applications permits leader and officer
- Guild Core parity already centralizes role meanings
- application decisions, promotion and kick do not share identical authorization
- handlers currently pass actor and target identifiers

Remaining question: Resolve one operation-by-role matrix for accept, reject, promote, demote if supported, kick and profile viewing without handler-owned authorization.

### DUPLICATE_HANDLER_REGISTRATION_RISK

Confirmed:

- handlers/guild.py contains six top-level register_guild_handlers definitions
- Python retains only the last top-level definition after module execution
- 32 decorators exist across superseded and final function bodies in source
- duplicate definitions create maintenance and audit ambiguity even when only the final function is called

Remaining question: Resolve the authoritative final registration body, prove one composition-root call, classify superseded definitions, and define safe consolidation without deleting active callbacks.

No production mutation, handler consolidation, runtime wiring or new guild-management rule is authorized.

## Next patch

`patch_21_12_2b_resolve_guild_applications_management_parity.py`
