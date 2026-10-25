# Stage 21.12.6a - Refined PvP contract

- Status: **PASS**
- Conclusion: **REVIEW_REQUIRED**
- Contract matrix: **4 confirmed / 8 review-required / 12 total**
- Implementation authorized: **False**
- Manual game check: **NOT_REQUIRED**

## AVAILABILITY_AND_ACTIVITY_SESSION_POLICY

Exact availability check order and concurrent activity-session acquisition.

## ACCEPTED_DUEL_TO_BATTLE_ATOMICITY

Unit of Work boundary across request acceptance, snapshots, battle creation and two sessions.

## COMBAT_SNAPSHOT_AND_PARTICIPANT_IDENTITY

Immutable snapshot fields, resource initialization and refresh prohibition during battle.

## SHARED_COMBAT_FORMULA_BOUNDARY

Permitted shared policy adapters and executable no-copied-formulas architecture gate.

## EVENT_HISTORY_AND_PROFILE_HISTORY

Event order, retention, profile visibility and exact-once history publication.

## TIMEOUT_FORFEIT_AND_ANTI_STALL_POLICY

Deadlines, warnings, one/two-sided timeout, forfeit and anti-stall semantics.

## RESTART_RECOVERY_AND_SESSION_CLEANUP

Resume/cancel rules, timer reconstruction, claim recovery and session cleanup.

## PRESENTATION_TIMER_AND_HANDLER_BOUNDARY

Typed commands/results, timer ports, callback revisions and single handler registration.

No production mutation, battle execution, timer execution, database access or runtime wiring is authorized.

Next: `patch_21_12_6b_resolve_pvp_parity.py`
