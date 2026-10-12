# Stage 20.5.1 — Premium Modifiers Audit

## Decision
`GO_EXACT_SCOPE_RECORDED_COMBAT_GOLD_GAP`. Current Premium is exactly `+25% EXP` for normal, elite and boss kills. It does not modify combat gold or loot.

## Current commercial contract
- 15 days: 70 crystals.
- 30 days: 120 crystals.
- Active purchases extend from the later of current expiration or current UTC time.
- Integer EXP bonus uses floor division: `floor(base EXP × 25 / 100)`.

## Isolation
Quest, sale, auction, admin, refund and guild gold have no Premium modifier path. Because Premium gold is absent entirely, Stage 20.5.2 must add one canonical modifier only after the percent is approved, and only in the combat-gold owner. Premium loot is currently absent; its future addition is UNDECIDED and must not be implemented without separate approval.

Production code and production database were not changed.
