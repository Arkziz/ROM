# Stage 20.1.2 — аудит економіки золота рівнів 1–10

- Статус: **PASS**
- Рішення: **CONDITIONAL_GO**
- Час: `2026-10-09T21:39:55+03:00`
- Git HEAD до commit: `cb59b0b844cdbbba5c85fd511b2ce54a5b0c0349`

## Гарантії виконання

- Production-файли не змінювалися.
- `game.db` відкривався лише через SQLite URI `mode=ro`.
- `game.db-wal` і `game.db-shm` не маніпулювалися.
- Аудит не змінює gold values, prices, reward multipliers або player balances.

## Canonical owners

- `data/mobs.py`
- `data/balance.py`
- `data/story_quest_content.py`
- `data/story_quest_definitions.py`
- `data/player_progression.py`
- `systems/combat_system.py`
- `systems/boss_system.py`
- `systems/drop_system.py`
- `systems/equipment_system.py`
- `systems/dynamic_equipment_system.py`
- `systems/guild_system.py`
- `systems/crystal_shop_system.py`
- `systems/premium_item_policy_system.py`
- `handlers/city.py`
- `handlers/blacksmith.py`
- `db_modules/generated_equipment.py`
- `db_modules/shop.py`

## Матриця рівнів 1–10

| Рівень | Мобів | Normal avg | Elite avg | Boss avg | Story quests | Story gold | Cumulative story gold |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | 2 | 0.09 | 0.27 | 0.45 | 10 | 2.70 | 2.70 |
| 2 | 2 | 0.14 | 0.43 | 0.71 | 10 | 4.30 | 7.00 |
| 3 | 2 | 0.21 | 0.65 | 1.07 | 10 | 6.50 | 13.50 |
| 4 | 2 | 0.29 | 0.89 | 1.48 | 10 | 8.90 | 22.40 |
| 5 | 2 | 0.43 | 1.29 | 2.15 | 10 | 13.76 | 36.16 |
| 6 | 2 | 0.61 | 1.84 | 3.06 | 10 | 18.40 | 54.56 |
| 7 | 2 | 0.79 | 2.36 | 3.94 | 10 | 23.60 | 78.16 |
| 8 | 2 | 1.07 | 3.23 | 5.38 | 10 | 32.30 | 110.46 |
| 9 | 2 | 1.38 | 4.12 | 6.88 | 10 | 41.30 | 151.76 |
| 10 | 2 | 1.76 | 5.29 | 8.81 | 10 | 56.42 | 208.18 |

## Encounter multipliers

- Selected elite gold multiplier: `3.0`
- Selected boss gold multiplier: `5.0`

## Gold sources

- Normal, elite and boss combat gold are captured in the level matrix.
- Story reward gold is aggregated by unlock level.
- Equipment/trash sale and other sources are inventoried as call sites; no synthetic drop-rate model is invented in this audit.

## Gold sinks

### ELITE_GOLD_MULTIPLIER
- `systems/combat_system.py` → `3.0`

### GUILD_CREATE_COST_GOLD
- `systems/guild_system.py` → `100.0`

### RARITY_REPAIR_MULTIPLIERS
- `data/balance.py` → `{'common': 1.0, 'uncommon': 2.5, 'rare': 7.0, 'epic': 18.0}`

## Live DB read-only evidence

- `quick_check`: `['ok']`
- Gold distribution: `{'users': 3, 'min_gold': 2.5700000000000003, 'max_gold': 763.8799999999999, 'avg_gold': 271.55999999999995, 'total_gold': 814.6799999999998}`
- Priced items captured: `86`

## Findings

### AFFORDABILITY_REQUIRES_COMBAT_SIMULATION
- Severity: **HIGH**
- Static gold sources and sinks are mapped, but consumable/repair affordability requires observed kill rates, losses and potion usage from later parity stages.
- Next stage: `20.4.3`

### GUILD_COST_REQUIRES_LEVEL5_REVIEW
- Severity: **MEDIUM**
- Guild creation is a 100-gold level-3+ sink and must be compared with cumulative level-5 income after economy changes.
- Next stage: `20.4.5`

### PREMIUM_GOLD_MODIFIER_SEPARATE_POLICY
- Severity: **MEDIUM**
- Premium combat-gold modification is not part of the base level 1-10 economy baseline and remains owned by Stage 20.5.1-20.5.2.
- Next stage: `20.5.1`

## Audit decision

**CONDITIONAL_GO**

Canonical level 1-10 gold sources and key sinks are mapped. No balance values are changed. Affordability changes remain gated by later mana, potion, guild and premium audits.

## Наступний порядок

1. Stage 20.2.1 — class-aware basic attack audit.
2. Stage 20.4.3 — potion affordability after mana policy is known.
3. Stage 20.4.5 — level-3 guild affordability after final source/sink decisions.
4. Stage 20.5.1 — premium EXP/gold modifier audit.

## Ручна перевірка

**Не потрібна.** Це read-only economy audit; жодне значення балансу не змінюється.

