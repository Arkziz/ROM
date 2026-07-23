# ✅ ROM REFACTOR SAFETY AUDIT TOOLS V1
# ROM Architecture Refactor 9.0

## Стартовий етап

`9.0.0 — Refactor safety audit tools`

Цей етап нічого не змінює у gameplay-коді.
Він додає інструменти для безпечного аудиту перед підчищенням `db.py`.

## Погоджені правила

1. Один patch = один домен.
2. Перед перенесенням логіки створюємо safety baseline.
3. `db.py` спочатку залишається compatibility facade.
4. Нові системи створюються у `systems/*`.
5. Дані/баланс поступово виносяться у `data/*`.
6. Після кожного етапу виконуються smoke-tests.

## Рекомендований порядок

```text
9.0.0 — audit/safety tools
9.0.1 — systems/character_system.py
9.0.2 — systems/player_system.py
9.0.3 — systems/contract_system.py
9.0.4 — systems/energy_system.py
9.0.5 — systems/regen_system.py
9.0.6 — systems/equipment_system.py read-only helpers
9.0.7 — systems/equipment_system.py equip/unequip/compatibility
9.0.8 — systems/equipment_system.py repair/durability/sell
9.0.9 — data/classes.py and data/equipment_profiles.py
9.0.10 — data/balance.py
9.0.11 — migrations foundation
9.0.12 — final db.py cleanup
```
