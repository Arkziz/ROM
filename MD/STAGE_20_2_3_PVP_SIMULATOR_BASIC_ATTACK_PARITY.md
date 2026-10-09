# Stage 20.2.3 — PvP and simulator basic-attack parity

- Status: **PASS**
- Baseline: `5e85116703aa1411c58d740604c96b819f2c9199`

## Canonical parity

PvP snapshot creation, PvP basic-attack fallback, simulator combat snapshots and simulator basic attacks now consume `systems.stat_system.resolve_basic_attack_type()`.

## Class contract

- Warrior, Knight, Scout, Rogue: physical → PATK → PDEF.
- Mage, Priest: magical → MATK → MDEF.
- Basic attack resource cost remains zero.

## Preserved behavior

Skill-specific `attack_type` remains authoritative in PvP and simulator skill branches. Weapon physical/magical ranges, crit routing, penetration, class multipliers, rage gain and energy regeneration remain unchanged. PvE production files are not modified.

## Removed duplicates

- PvP local `mage/priest` fallback.
- Simulator local `MAGIC_CLASSES`.
- Simulator attack-type inference from Mana resource.
- PvP snapshot fallback to physical.

## Verification

- Git baseline, owner AST and exact-count preconditions: PASS.
- Future-source AST and compile: PASS.
- Six-class canonical resolver: PASS.
- PvP skill precedence: PASS.
- PvP basic attack cost zero: PASS.
- Simulator skill precedence: PASS.
- No local class attack-type duplicate: PASS.
- Live DB integrity read-only: PASS.

## Manual verification

**REQUIRED.** Verify one physical and one magical class in PvP, then run simulator smoke for all six classes. Basic attacks must use canonical stat/defense layers and cost zero; skills must retain their own attack types and costs.
