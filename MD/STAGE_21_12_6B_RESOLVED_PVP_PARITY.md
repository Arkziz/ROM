# Stage 21.12.6b - Resolved PvP parity

- Status: **PASS**
- Conclusion: **GO_TO_IMPLEMENTATION**
- Contract matrix: **4 previously confirmed + 8 resolved = 12/12**
- Remaining unresolved contracts: **0**
- Implementation authorized: **True**
- No copied formulas: **REQUIRED**
- Runtime integration authorized: **False**
- Production persistence authorized: **False**
- Production battle execution authorized: **False**
- Production terminal settlement authorized: **False**
- Production timer authorized: **False**
- Manual game check: **NOT_REQUIRED**

## Resolutions

### AVAILABILITY_AND_ACTIVITY_SESSION_POLICY

Challenge creation rejects self-target and requires both users online, in the same canonical location, free of PvE and other interaction activity, without another pending duel or active battle. Acceptance repeats all checks against the accepted request revision. After immutable snapshots are prepared, both pvp_battle activity sessions are acquired for the same battle_id; failure to acquire either session compensates any acquired session and cancels the created battle.

### ACCEPTED_DUEL_TO_BATTLE_ATOMICITY

The accepted request is the idempotency key for battle creation. One application orchestration prepares both snapshots, creates exactly one battle under BEGIN IMMEDIATE, acquires both activity sessions, and publishes success only after all steps pass. A retry returns the existing battle. Failure before commit creates nothing; failure after battle creation but before both sessions are acquired cancels that battle and releases every acquired session.

### COMBAT_SNAPSHOT_AND_PARTICIPANT_IDENTITY

Each participant is persisted by stable user_id plus immutable side and a battle-start snapshot. The snapshot freezes class, level, max/current HP, attack, defenses, critical, dodge, resource type/value, combo, equipment-derived bonuses and skill availability. Battle-start HP is full canonical max HP; resource initialization follows the shared class resource policy. Durability and equipment changes after acceptance do not refresh an active battle snapshot.

### SHARED_COMBAT_FORMULA_BOUNDARY

PvP orchestration may sequence simultaneous actions, status effects, timeout intents and terminal checks, but it must consume shared canonical damage, defense, critical, dodge, resource-cost, regeneration and skill-effect policies through imports or adapters. Handlers and presentation may not calculate combat values. The Stage 21.12.6c architecture gate must fail on local duplicate formula constants/functions or direct arithmetic implementations outside approved shared adapters. No new PvP-only damage or resource formulas are authorized.

### EVENT_HISTORY_AND_PROFILE_HISTORY

Battle events are append-only and ordered by battle_id, round_number, event sequence and stable event id. Participants may read their own complete battle history; non-participants receive no private battle payload. Only resultful completed battles publish one profile-history entry per participant, keyed by battle_id and user_id. Cancelled or setup-failed battles are excluded. Machine reasons remain stable keys and Ukrainian text is presentation-only.

### TIMEOUT_FORFEIT_AND_ANTI_STALL_POLICY

Each required action uses the persisted round deadline owned by the timer service. Repeated timer ticks are idempotent. If exactly one participant misses the final deadline, that participant forfeits and the opponent wins; if both miss it, the battle ends without a winner using the canonical double-timeout reason. Warnings do not mutate battle state. Maximum-round or no-progress termination uses the existing round-engine terminal policy and never introduces copied damage formulas.

### RESTART_RECOVERY_AND_SESSION_CLEANUP

Restart recovery classifies every non-terminal battle from persisted round, revision, actions, resolution claim and deadline. Unclaimed complete rounds resume resolution with the same seed/revision; partially submitted rounds resume until their reconstructed deadline; stale unresolved claims are released before retry. Terminal battles are never reopened. Missing active sessions are reconciled when safe, while orphan sessions for terminal or absent battles are released. Repeated recovery returns the same typed per-battle outcome without duplicate events or completion.

### PRESENTATION_TIMER_AND_HANDLER_BOUNDARY

One PvP application service owns challenge acceptance, battle creation, action commands, recovery and terminal completion through typed commands/results. The pure round engine owns deterministic resolution; the timer port supplies deadlines and timeout commands. Telegram handlers own callback parsing, keyboards and Ukrainian text, pass battle_id, round_number and expected_revision, and register one canonical route. Handlers, timer adapters and presentation modules may not contain combat formulas.

## Implementation boundary

Stage 21.12.6c may implement pure PvP DTOs, policies, state machines, shared-policy ports, in-memory Unit of Work, tests, smoke verification and a no-copied-formulas gate. It may not connect SQLite, Telegram, runtime timers or execute production battles.

## Next patch

`patch_21_12_6c_implement_pvp.py`
