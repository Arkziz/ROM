# Stage 20.3.6 — PvP Canonical Mana Policy

## Scope
PvP projected validation and pure round-engine payment use `calculate_mana_skill_cost(skill, max_mp)`. Mana restores use canonical `calculate_mana_restore_amount` and catalog `restore_max_mp_percent`.

## Ordering
`_pay` runs before `_special`, so `Очищення віри` preserves spend-before-restore. Invalid actions do not mutate MP, cooldown or round state. The existing revision/idempotency layer is not changed.

## Unchanged
PvE, simulator, 50% PvE terminal floor, 30% passive regeneration, database persistence and physical-class resources are unchanged.

## Manual check
Required: Mage/Priest PvP costs, insufficient Mana rejection, Arcane Flow restore, Purify spend-before-restore and replay protection.
