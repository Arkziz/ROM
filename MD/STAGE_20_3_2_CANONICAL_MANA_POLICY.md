# Stage 20.3.2 — Canonical Mana Policy

## Статус

Stage 20.3.2 створює pure canonical policy для майбутньої гібридної вартості mana-навичок і явного round-half-up округлення.

## Межа відповідальності

Цей підетап додає:

- `data/mana_policy.py` — pure numeric policy без SQLite, Telegram і runtime owners;
- `tools/smoke_test_canonical_mana_policy.py` — виконувані контрольні вектори;
- цей документ.

Policy **ще не підключена** до PvE, PvP, UI, notifications, potion flow або simulator. Поточна бойова поведінка та фіксовані ціни навичок не змінені.

## Canonical формули

### Вартість mana-навички

```text
round_half_up(flat + Max MP × percent / 100)
```

### Passive regeneration

```text
30% Max MP за кожну повну хвилину поза боєм
```

Значення збережено без зміни.

### Post-combat floor

```text
Current baseline: 30% Max MP
Approved target: 50% Max MP
```

50% target лише оголошено в policy. Перемикання production виконується окремо в Stage 20.3.5.

## Округлення

Policy використовує `Decimal` і `ROUND_HALF_UP`:

```text
12.4 → 12
12.5 → 13
12.6 → 13
```

Python bankers rounding для mana policy не використовується.

## Контрольні профілі

- `mage_fireball`: `8 + 7% Max MP`.
- `mage_thunder_spell`: `15 + 18% Max MP`.
- `mage_arcane_flow`: `0 + 0% Max MP`.
- `priest_holy_ray`: `6 + 4% Max MP`.
- `priest_healing_blessing`: `12 + 10% Max MP`.
- `priest_purify_faith`: `10 + 8% Max MP`.

Профілі поки містяться лише у verifier як acceptance vectors. Їх перенесення до canonical skill catalog належить Stage 20.3.3, щоб не створювати друге authoritative джерело.

## Валідація

Policy fail-closed відхиляє:

- не-mana `cost_type`;
- відсутні hybrid fields;
- від’ємні значення;
- `bool`;
- `None`;
- `NaN` та infinity;
- дробовий `max_mp`;
- нечислові значення.

## Незмінені owners

Усі 22 owners, зафіксовані Stage 20.3.1, перевіряються за SHA-256 до та після mutation. Патч не змінює `game.db`, `game.db-wal`, `game.db-shm` або чинні runtime paths.

## Наступний підетап

Stage 20.3.3 має додати hybrid fields до `CLASS_SKILLS_V1`, використовуючи цю policy як єдиний calculator, але без передчасного перемикання всіх runtime consumers.

## Ручна перевірка

Не потрібна. Новий pure policy module ще не підключений до gameplay.
