# Stage 20.3.7 — Integrate Mana Parity into Simulator

## Roadmap identity
Це mutation-підетап `20.3.7 Integrate mana parity into simulator` із затвердженого checklist. Попередній read-only audit був підготовчою контрольною точкою і не переносить mutation на 20.3.8. Stage 20.3.8 залишається `Consolidate legacy mana paths`.

## Реалізація
- `_can_use` та `_pay` використовують один canonical effective cost.
- Mana cost: `calculate_mana_skill_cost(skill, actor.max_resource)`.
- Restore: `calculate_mana_restore_amount(max_resource, restore_max_mp_percent)`.
- `Магічний потік`: 25% із `ROUND_HALF_UP`.
- `Очищення віри`: spend-before-restore, 15% із `ROUND_HALF_UP`.
- Після бою: `apply_post_combat_mp_floor_value(current, max)` із floor 50%, не full restore.

## Scope
Змінено лише `systems/simulation/pve_battle.py` і `systems/simulation/survival_state.py`. Production PvE/PvP, БД, WAL/SHM не змінені.

## Manual check
Не потрібна безпосередньо у грі. Потрібен simulator regression/acceptance у наступних підетапах консолідації та приймання.
