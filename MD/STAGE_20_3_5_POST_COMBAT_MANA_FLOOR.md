# Stage 20.3.5 — 50% Post-Combat Mana Floor

## Canonical policy
Після завершення PvE-бою поточна мана гарантується на рівні не менше 50% Max MP:

```text
new_mp = max(current_mp, round_half_up(Max MP × 50%))
```

Це floor, а не додавання 50%. Якщо поточна мана вища, вона не зменшується.

## Terminal paths
У `handlers/combat.py` збережено п’ять runtime call sites спільної authoritative функції. Вони охоплюють штатні завершення бою, зокрема перемогу, поразку/смерть і втечу. Audit count `6` включав також definition/import evidence.

## Regen clock
Після terminal flow `mp_regen_paused` скидається, а `last_mp_regen_update` встановлюється на актуальний час. Бойовий час не перетворюється на приховані позабойові ticks.

## Незмінені системи
Passive regeneration залишається 30% за повну хвилину. PvP, simulator, skill costs, restore effects, potions і Max MP не змінені.

## Ручна перевірка
Потрібна: перевірити перемогу нижче/вище 50%, поразку та ручну втечу. Для 170 Max MP floor дорівнює 85 MP.
