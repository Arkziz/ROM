# Stage 21.6.5c — Canonical full stat snapshot

Implemented one source-separated snapshot owner for base, allocated, active equipment, runes, and precomputed enhancement outputs. Broken and unequipped items are excluded. Profile, combat, and simulator application entrypoints delegate to the same domain builder. Item generation, rune-level, and refinement formulas remain with their audited owning subsystems and are not redefined here.
