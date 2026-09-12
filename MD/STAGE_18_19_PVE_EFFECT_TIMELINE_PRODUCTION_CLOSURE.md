# Stage 18.19: PvE Effect Timeline Production Closure

**Status:** CLOSED
**Manual acceptance:** PASS
**Production mutation in closure:** none

## Authoritative implementation

- `handlers/combat.py` remains the canonical PvE combat and effect-timeline owner.
- `add_enemy_effect` owns same-key replace and refresh policy.
- `process_enemy_turn_start_effects` skips newly applied effects once, then performs periodic ticks and duration decrement.
- `set_skill_cooldown` stores the internal offset needed for exactly N blocked subsequent player actions.
- Existing immediate stun and shield routes remain canonical.
- PvP production was not modified or imported into PvE.

## Accepted semantics

- New DOT and HOT effects do not tick during application.
- New enemy effects do not lose duration during application.
- Bleed and poison tick from the next action and retain all configured ticks.
- Same-key effects do not stack damage; stronger replaces weaker and equal strength may refresh a longer duration.
- Cooldown N blocks exactly N subsequent owner actions.
- Stun skips exactly the nearest enemy action.
- Shields apply immediately.

## Manual verification

Telegram combat logs confirmed bleed, poison, stun, HOT, shield, cooldown progression, ordinary PvE completion and repeated hunting. No traceback was observed.

## Automated verification

- Stage 18.19.1 deterministic timing smoke: PASS.
- Stage 18.18 auto-escape regression: PASS.
- Stage 18.18 encounter-history regression: PASS.
- Python compilation and owner-aware structural contracts: PASS.
- `quick_check=ok`, FK violations=0, database unchanged.
- WAL/SHM were not manipulated.

## Accepted limitations

- Lethal DOT, same-key reapplication and elite/boss parity were accepted from deterministic contracts and shared canonical routing rather than additional manual reproduction.
- A direct press of a disabled cooldown skill cannot be performed through the current Telegram keyboard; cooldown validation remains covered automatically.

## Final decision

Stage 18.19 is closed. Further changes require a separately identified runtime defect.
