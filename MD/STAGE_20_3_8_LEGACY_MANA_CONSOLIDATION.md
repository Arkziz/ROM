# Stage 20.3.8 — Consolidate Legacy Mana Paths

## Roadmap identity
Official checklist stage: `20.3.8 Consolidate legacy mana paths`.

## Consolidation
The remaining local passive-regeneration percentage in `systems/character_system.py` is removed. Runtime regeneration now calls `calculate_passive_mp_regen_per_full_minute(maximum)` from `data.mana_policy`.

The following canonical ownership is enforced by regression:

- skill cost: `calculate_mana_skill_cost` in PvE, PvP and simulator;
- percent restore: `calculate_mana_restore_amount` in PvP and simulator;
- passive regeneration: `calculate_passive_mp_regen_per_full_minute`;
- post-combat floor: `apply_post_combat_mp_floor_value` in production and simulator;
- Max MP: existing canonical stat pipeline.

## Compatibility
Literal `cost` and old Ukrainian description text remain compatibility metadata for AST loaders and non-Mana classes, not authoritative Mana arithmetic. Historical function names with version suffixes remain public compatibility entrypoints and delegate to canonical policy.

## Scope
Production mutation is restricted to `systems/character_system.py`. PvE, PvP, simulator battle logic, catalog, database, WAL and SHM are not changed.

## Manual check
No new in-game scenario is required. Existing PvE/PvP manual acceptance plus executable cross-owner regressions cover this consolidation.
