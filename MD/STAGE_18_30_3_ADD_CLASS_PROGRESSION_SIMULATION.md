# ROM Stage 18.30.3: Add Class Progression Simulation

## Scope

- Validated class/target-level/seed request contract.
- Direct operator CLI with ROM root insertion into `sys.path`.
- Reuse of the existing `WorldProgressionSimulator`, production-shaped progression provider and exact PvE engine.
- Canonical result preserved under `canonical_result` with a concise operator summary.
- Deterministic 1 to 2 smoke scenario.
- Activity profile fixed to the approved 09:00-23:00 `hardcore` profile.

## Current acceptance boundary

This stage exposes the existing progression route for a minimal deterministic run. Detailed encounter-type totals, extended defeat/escape contracts, complete resource reporting and equipment economy remain follow-up integration work after runtime evidence from the minimal simulation.

## Minimal operator test

`python .\tools\run_class_progression_simulation.py --class scout --target-level 2 --seed 1`

## Manual verification

**REQUIRED OUTSIDE THE GAME.** Run the minimal CLI command and review its JSON output. Telegram gameplay verification is not required.
