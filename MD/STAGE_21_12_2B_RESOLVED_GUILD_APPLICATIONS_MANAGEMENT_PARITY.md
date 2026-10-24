# Stage 21.12.2b - Resolved Guild Applications/Management parity

- Status: **PASS**
- Conclusion: **GO_TO_IMPLEMENTATION**
- Resolved contracts: **7/7**
- Remaining unresolved contracts: **0**
- Implementation authorized: **True**
- Runtime integration authorized: **False**
- Handler consolidation authorized: **False**
- Manual game check: **NOT_REQUIRED**

## Resolutions

### APPLICATION_ACCEPT_ATOMICITY

Accept is one Unit of Work. It loads the application and actor membership, requires PENDING status and leader/officer permission, then rechecks applicant eligibility and capacity. It conditionally claims the pending row, inserts member role=member, records processed_at/processed_by and the V1-confirmed log effects, then commits once. Any failure rolls back all changes. Replays return already_processed and never add a second membership.

### APPLICATION_REJECT_POLICY

Reject requires an existing PENDING application in the actor's guild and leader/officer application-management permission. It conditionally changes status to REJECTED with processed metadata in one commit. Missing, forbidden and already-processed outcomes are typed and read-only; replay never changes processed metadata.

### MEMBER_LIMIT_AND_ELIGIBILITY_RECHECK

Accept-time order is: application exists, actor permission, pending status, target guild exists, applicant is not already in any guild, minimum level 3 is still met, join cooldown permits entry, current member count is below persisted member_limit, then conditional claim and membership insert. List-time state never authorizes acceptance. Constraint races map to typed rejection after rollback.

### ROLE_PROMOTION_AND_OFFICER_LIMIT

Only the leader may promote a same-guild MEMBER to OFFICER. The target may not be the actor or leader. Officer capacity is rechecked immediately before a conditional role update using the canonical V1 officer-limit owner. already_officer is an idempotent read-only result. No demotion command is introduced because this stage cannot invent behavior not confirmed in V1.

### MEMBER_KICK_AND_SELF_PROTECTION

Kick requires an authorized same-guild actor and target. Self-kick and leader-target kick are forbidden. Officer authority is limited to V1-confirmed targets and may not override leader-only protections. Successful kick atomically removes membership, records departure/history and cooldown, and writes the V1-confirmed log effects. Failure leaves membership and cooldown unchanged.

### MANAGEMENT_PERMISSION_MATRIX

Leader and officer may accept/reject applications. Promotion is leader-only. Kick authorization follows the exact V1 actor/target role checks, with self and leader protection enforced centrally. Profile viewing remains a read-only adapter action and is not a Guild Core mutation. Handlers pass IDs only and never decide authorization.

### DUPLICATE_HANDLER_REGISTRATION_RISK

For V2, exactly one composition-root registration path and one authoritative Guild Applications/Management handler owner are allowed. The final V1 register_guild_handlers definition is the behavioral evidence source; earlier definitions are classified as superseded source, not additional runtime owners. Stage 21.12.2c may implement pure APIs only and must not edit or consolidate handlers/guild.py. Any later handler consolidation requires a separate mutation stage with callback inventory and regression fixtures.

## Implementation boundary

Stage 21.12.2c may implement pure application/domain APIs, typed results, in-memory fixtures, tests and smoke verification. It may not edit `handlers/guild.py`, connect SQLite/runtime, or invent demotion, limits, cooldowns or notifications.

## Next patch

`patch_21_12_2c_implement_guild_applications_management.py`
