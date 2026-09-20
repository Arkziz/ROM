# Stage 18.30.5d

Read-only audit of the canonical refinement lifecycle.

The audit compares simulation chance tables with `systems.refine_system`, derives the exact 50% boundary, and executes deterministic in-memory fixtures for weapon and armor success, failure, degradation, below-threshold attempts, maximum levels, stone consumption, counters, and item selection.

The approved simulator policy is explicit: attempt refinement only while the canonical chance for the next attempt is at least 50%. A chance of exactly 50% is allowed; a chance below 50% is blocked without consuming a stone. Failure-level behavior must also match the canonical production owner.

No production file, simulation implementation, or database file is modified.
