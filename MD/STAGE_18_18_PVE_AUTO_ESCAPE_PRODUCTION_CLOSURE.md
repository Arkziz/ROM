# Stage 18.18: PvE Auto-Escape Production Closure

**Status:** CLOSED
**Manual acceptance:** PASS
**Timeout:** 300 seconds

## Architecture

- `systems/pve_auto_escape_system.py` owns persistence, deadlines, atomic terminal claims, recovery and the worker.
- `handlers/combat.py` registers encounters and claims victory/manual escape.
- `main.py` performs restart recovery and starts the worker.
- `pve_encounters` retains history and permits only one active row per user through a partial unique index.

## Policy

- Deadline is 300 seconds from authoritative encounter start.
- HP and MP remain actual; energy is not refunded.
- No extra durability or death penalty is applied.
- No EXP, gold, loot, quest, contract, boss or event progress is awarded.
- Normal, elite and boss encounters use the same policy.
- First atomic terminal completion wins.

## Restart

Before deadline, runtime mob state is restored without extending the deadline. After deadline, the encounter is completed as auto_escape.

## Verification

- Both maintained smoke tests PASS.
- Manual five-minute timeout, no rewards, stale buttons and repeated hunting PASS.
- Partial unique active index exists; duplicate active users: 0.
- quick_check=ok; FK violations=0; closure performs no DB writes.
- WAL/SHM were not manipulated.

## Final decision

Stage 18.18 is closed. No further implementation patch is required unless a new runtime defect is discovered.
