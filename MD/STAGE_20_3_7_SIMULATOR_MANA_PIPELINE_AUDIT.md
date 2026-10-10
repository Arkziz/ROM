# Stage 20.3.7 — Simulator Mana Pipeline Audit

## Статус

- Audit: PASS
- Decision: **GO**
- Production mutation: NONE

## Підтверджена архітектура

- Max MP: canonical `systems.stat_system.calculate_max_mp`.
- Catalog: literal production `CLASS_SKILLS_V1`.
- Current MP: simulator actor підтримує перенесення `current_mp`.

## Parity gaps

1. **SIM-MANA-001 HIGH:** availability/payment використовують legacy `skill["cost"]`.
2. **SIM-MANA-002 HIGH:** restore paths використовують локальний `round()` для 25% і 15%.
3. **SIM-MANA-003 HIGH:** `restore_mp_after_combat()` відновлює MP до Max MP замість canonical 50% floor.

## Наступний mutation scope

Змінювати лише:

- `systems/simulation/pve_battle.py`;
- `systems/simulation/survival_state.py`.

Обов’язкові контракти:

- dynamic cost однаковий у availability і payment;
- restore бере `restore_max_mp_percent` із catalog і `ROUND_HALF_UP`;
- порядок spend-before-restore;
- post-combat floor 50% як `max(current, floor)`, не додавання;
- current MP зберігається між боями;
- PvE, PvP, БД, WAL/SHM не змінюються.

## Висновок

**GO** для Stage 20.3.8: simulator Mana parity mutation.
