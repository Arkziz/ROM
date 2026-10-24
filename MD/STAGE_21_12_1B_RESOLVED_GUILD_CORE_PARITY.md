# Stage 21.12.1b - Resolved Guild Core parity

- Status: **PASS**
- Conclusion: **GO_TO_IMPLEMENTATION**
- Resolved contracts: **7/7**
- Remaining unresolved contracts: **0**
- Implementation authorized: **True**
- Runtime integration authorized: **False**
- Production persistence authorized: **False**
- Manual game check: **NOT_REQUIRED**

## Canonical constants

- Creation cost: **50.00 gold**
- Minimum access level: **3**
- Default member limit: **10**
- Roles: `leader`, `officer`, `member`

## Resolutions

### NAME_TAG_ICON_IDENTITY_POLICY

Guild creation accepts a validated display name, tag and one canonical emoji icon. Name and tag are whitespace-normalized and compared only through persisted normalized keys. Empty, malformed or out-of-contract values fail before debit. Database uniqueness remains the final concurrency guard. V2 must preserve the exact V1 validators and typed reasons discovered from those validators; presentation text is not an identifier.

### MEMBERSHIP_AND_ROLE_INVARIANTS

A user has at most one guild membership. Every guild has exactly one leader membership, and guild.leader_user_id must equal that member's user_id. Allowed roles are leader, officer and member. The creator becomes leader. member_limit counts all membership rows, including the leader. Any load or mutation that would produce zero leaders, multiple leaders, pointer/role drift or an unknown role fails closed.

### DUPLICATE_GUILD_AND_MEMBERSHIP_POLICY

Normalized guild name, normalized tag and member user_id are independent unique keys. Creation rejects duplicate_name, duplicate_tag and already_in_guild before gold mutation when observable. Constraint races map to the same typed results after rollback. A retry after a successful creation returns already_in_guild and never charges gold again.

### PERMISSIONS_AND_MANAGEMENT_BOUNDARY

Guild Core owns one permission matrix. Leader may transfer leadership, manage roles and members, manage applications and perform leader-only lifecycle operations. Officer may manage applications and only the V1-confirmed delegated operations, never alter leadership. Member has read-only core access. Handlers supply actor and target IDs but never authorize operations themselves.

### LEAVE_TRANSFER_AND_DISSOLUTION_BOUNDARY

A non-leader may leave atomically, recording membership history and applicable cooldown. A leader cannot leave while another member exists until leadership is transferred to an eligible member of the same guild. Transfer atomically demotes the old leader, promotes the target and updates leader_user_id. If the leader is the final member, leave dissolves the guild and removes coordinated guild-owned rows according to the V1 owner path. Failed transfer, leave or dissolution leaves all state unchanged.

### PERSISTENCE_RESTART_AND_FAILURE_POLICY

Guild, membership, roles, limits, logs and membership history are persisted through one Guild Unit of Work. Creation uses one atomic boundary for conditional 50.00-gold debit, guild insert, leader membership and creation log. Leave, transfer and dissolution each use one commit boundary. Any exception rolls back; schema constraints survive restart; repository load validates leader/member invariants before returning an aggregate.

### HANDLER_REGISTRATION_AND_CONSUMER_BOUNDARY

One composition-root call may register handlers.guild.register_guild_handlers exactly once. Guild Core returns typed status/reason/data only. Telegram text and keyboards remain adapter concerns. Guild Resource System consumes guild identity and membership through query ports. No second production command path or duplicate decorator registration is authorized.

## Implementation boundary

Only pure aggregate/application logic, validators, ports, in-memory fixtures, tests and smoke verification are authorized. Production SQLite, migrations, Telegram/runtime wiring and new guild rules remain forbidden.

## Next patch

`patch_21_12_1c_implement_guild_core.py`
