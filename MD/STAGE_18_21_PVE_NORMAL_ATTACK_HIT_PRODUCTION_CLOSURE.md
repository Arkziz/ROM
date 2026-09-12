# Stage 18.21: PvE Normal Attack Hit Production Closure

## Closure status

**CLOSED**

Manual acceptance: **PASS**.

## Final production contract

- Physical PvE normal attack uses effective player DEX against mob DEX.
- Hit chance is `95 + (player DEX - mob DEX) × 0.5`, clamped to `50–99%`.
- A miss deals zero damage, cannot crit, and does not stop the enemy turn.
- Existing rage, periodic-effect, cooldown, escape, victory and reward contracts remain active.
- Magical normal attacks temporarily remain guaranteed-hit.
- PvE damaging skills temporarily remain guaranteed-hit.
- Support and no-damage skills do not use a hit roll.
- PvP is unchanged.

## Deferred dependency

Magical normal-attack accuracy and PvE skill hit/miss are deferred until after Stage 18.27. Stage 18.27 must add canonical mob INT/WIS generation and scaling for normal, elite and boss encounters. The approved future magical axis is effective player INT versus canonical mob WIS.

## Manual acceptance

Physical normal-attack misses were observed in live PvE. Mob HP remained unchanged on miss, crit did not occur, the enemy completed the turn, rage behavior remained correct, later attacks and victory worked, and no traceback occurred. Physical and magical class checks after the scope guard passed.

## Automated verification

- `tools/smoke_test_pve_normal_attack_hit_18_21_1.py`: PASS
- `tools/smoke_test_pve_physical_normal_attack_scope_18_21_3.py`: PASS
- `tools/smoke_test_pve_effect_timeline_18_19_1.py`: PASS
- `tools/smoke_test_pve_auto_escape_18_18_1.py`: PASS
- `tools/smoke_test_pve_encounter_history_recovery_18_18_1a.py`: PASS

## Database safety

- `quick_check`: `ok`.
- Foreign-key violations: `0`.
- Production database unchanged: `true`.
- WAL/SHM were not manipulated.
