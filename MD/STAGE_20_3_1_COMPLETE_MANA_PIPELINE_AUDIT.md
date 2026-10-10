# Stage 20.3.1 — повний read-only аудит mana pipeline

- Статус: **PASS**
- Рішення: **GO**
- Git HEAD: `ee1151dbecf3dc948379f841c99cbb8a52502de0`
- Час: `2026-10-10T22:50:02+03:00`

## Гарантії виконання

- Production-файли не змінювалися.
- `game.db` відкривався тільки через SQLite URI `mode=ro`.
- `game.db-wal` і `game.db-shm` не видалялися, не копіювалися, не перейменовувалися і не використовувалися для rollback.
- Patch створює лише JSON у `reports/` і Markdown у `MD/`; commit містить тільки Markdown-звіт.
- Балансні значення, current MP і Max MP не змінювалися.

## Поточний canonical baseline

- Max MP: чинний production resolver через effective INT/WIS; формула Stage 20 не змінюється.
- Passive regeneration: `30% Max MP` за повну хвилину поза боєм.
- Passive regeneration у бою призупинена.
- Post-combat floor до Stage 20.3.5: `30% Max MP`.
- Ціль Stage 20.3.5: floor `50% Max MP`, не додавання 50%.
- Basic attack Mage/Priest залишається безкоштовною і не є mana skill cost path.

## Поточні навички та затверджена майбутня policy

- `mage_fireball` / 🔥 Вогняна куля: зараз `20 MP`; майбутня формула `8 + 7% Max MP`; cooldown `0`.
- `mage_thunder_spell` / ⚡ Грозове заклинання: зараз `45 MP`; майбутня формула `15 + 18% Max MP`; cooldown `4`.
- `mage_arcane_flow` / 🔮 Магічний потік: зараз `0 MP`; майбутня формула `0 + 0% Max MP`; cooldown `5`.
- `priest_holy_ray` / ✨ Святий промінь: зараз `12 MP`; майбутня формула `6 + 4% Max MP`; cooldown `0`.
- `priest_healing_blessing` / 🌿 Благословення зцілення: зараз `30 MP`; майбутня формула `12 + 10% Max MP`; cooldown `4`.
- `priest_purify_faith` / 🛡️ Очищення віри: зараз `20 MP`; майбутня формула `10 + 8% Max MP`; cooldown `4`.

## Карта pipeline

- `max_mp`: 32 файлів, 160 evidence points.
- `current_mp`: 8 файлів, 40 evidence points.
- `regeneration`: 4 файлів, 37 evidence points.
- `skill_cost`: 15 файлів, 91 evidence points.
- `restore`: 15 файлів, 65 evidence points.
- `terminal`: 53 файлів, 303 evidence points.
- `presentation`: 25 файлів, 58 evidence points.

## Direct fixed-cost consumers

- `handlers/combat.py:1123` [presentation_or_pve_runtime] — `cost = int(skill.get("cost", 0))`
- `handlers/profile.py:745` [presentation_or_pve_runtime] — `if skill.get("cost"):`
- `handlers/profile.py:749` [presentation_or_pve_runtime] — `text += f"💥 Вартість: {skill['cost']} Люті\n"`
- `handlers/profile.py:753` [presentation_or_pve_runtime] — `text += f"💥 Вартість: {skill['cost']} Енергії\n"`
- `handlers/profile.py:757` [presentation_or_pve_runtime] — `text += f"💧 Вартість: {skill['cost']} Мани\n"`
- `handlers/start.py:518` [presentation_or_pve_runtime] — `cost = int(skill.get("cost", 0) or 0)`
- `systems/pve_skill_action_state.py:70` [runtime] — `cost = max(0, int(skill.get("cost", 0) or 0))`
- `systems/pvp_action_validation.py:57` [pvp_runtime_or_audit] — `cost = max(0, int(skill.get("cost") or 0))`
- `systems/pvp_knight_judgement_terminal_audit.py:28` [pvp_runtime_or_audit] — `valid=skill_valid(knight,skill); resource_ok=knight.resource>=int(skill.get("cost") or 0); cooldown=int(knight.cooldowns.get("knight_judgement",0) or 0)`
- `systems/pvp_policy_metrics_audit.py:25` [pvp_runtime_or_audit] — `cost = int(skill.get("cost") or 0)`
- `systems/pvp_policy_metrics_audit.py:42` [pvp_runtime_or_audit] — `cost = int(skill.get("cost") or 0)`
- `systems/pvp_real_actor_root_cause_audit.py:70` [pvp_runtime_or_audit] — `cost_type = str(skill.get("cost_type") or ""); cost = int(skill.get("cost") or 0)`
- `systems/pvp_round_engine.py:129` [pvp_runtime_or_audit] — `cost = max(0, int(skill.get("cost") or 0))`
- `systems/simulation/pve_battle.py:49` [simulator] — `typ=skill["cost_type"]; cost=int(skill.get("cost",0))`
- `systems/simulation/pve_battle.py:83` [simulator] — `typ=skill["cost_type"]; cost=int(skill.get("cost",0)); spent={"rage":0,"combo":0}`

## MP API definitions

- `apply_lazy_mp_regeneration_17_15_1`: `systems/character_system.py:812`
- `apply_post_combat_mp_floor_17_15_1`: `systems/character_system.py:934`
- `begin_mp_combat_pause_17_15_1`: `systems/character_system.py:800`
- `get_max_mp`: `db_modules/character.py:227`, `systems/character_system.py:233`, `systems/character_system.py:537`
- `get_user_mp`: `db_modules/character.py:120`, `systems/character_system.py:299`, `systems/character_system.py:501`
- `refresh_user_mp`: `db_modules/character.py:231`, `systems/character_system.py:257`
- `reset_mp_regen_clock_17_15_1`: `systems/character_system.py:766`
- `restore_user_mp_to_full`: `db_modules/character.py:183`
- `set_user_mp`: `db_modules/character.py:124`, `systems/character_system.py:315`
- `spend_user_mp`: `db_modules/character.py:128`

## Regeneration and floor constants

- `MP_REGEN_PERCENT_PER_MINUTE_17_15_1` = `0.3` at `systems/character_system.py:730`
- `MP_POST_COMBAT_FLOOR_PERCENT_17_15_1` = `0.3` at `systems/character_system.py:732`
- `MP_REGEN_PERCENT_PER_MINUTE_17_15_1` = `0.3` at `systems/notifications.py:834`

## Terminal paths

- `handlers/combat.py:221` — labels: `victory, defeat_or_death`
- `handlers/combat.py:1835` — labels: `victory`
- `handlers/combat.py:2519` — labels: `defeat_or_death`
- `handlers/combat.py:2929` — labels: `defeat_or_death`
- `handlers/combat.py:3459` — labels: `defeat_or_death`
- `handlers/combat.py:3752` — labels: `escape`

## SQLite read-only evidence

- Mode: `READ_ONLY_URI`
- quick_check: `['ok']`
- Missing required columns: `[]`
- Legacy columns: `['last_regen_at']`
- Users: `4`; MP range: `0..170`; Max MP range: `0..170`

## Findings

### DUPLICATE_MP_API_DEFINITIONS

- Severity: **HIGH**
- Multiple definitions exist for MP APIs: get_max_mp, get_user_mp, refresh_user_mp, set_user_mp
- Наступний підетап: `20.3.2/20.3.8`

### DUPLICATE_REGEN_POLICY

- Severity: **HIGH**
- Passive MP regeneration constants/logic are distributed across multiple owners.
- Наступний підетап: `20.3.2/20.3.8`

### FIXED_MANA_COST_CONSUMERS

- Severity: **HIGH**
- Found 15 direct skill cost reads requiring classification and staged parity migration.
- Наступний підетап: `20.3.3-20.3.7`

### DIRECT_MP_SQL_MUTATIONS

- Severity: **HIGH**
- Found 15 direct SQL MP mutation sites outside one canonical runtime API.
- Наступний підетап: `20.3.2/20.3.8`

## Точний порядок наступних mutation-патчів

1. `20.3.2` — створити pure canonical mana policy та round-half-up calculator.
2. `20.3.3` — додати hybrid fields до canonical skill catalog без другого authoritative cost path.
3. `20.3.4` — перевести PvE presentation, availability, stale-callback validation і spending.
4. `20.3.5` — перевести всі доведені terminal paths на 50% floor.
5. `20.3.6` — перевести PvP snapshot, projected validation, spend, restore і replay parity.
6. `20.3.7` — перевести exact PvE simulator та додати mana metrics.
7. `20.3.8` — прибрати безпечні duplicate/legacy paths після виконуваних parity checks.
8. `20.3.9` — automated regression і ручне приймання.

## Audit decision

**GO**

Canonical owners, duplicate paths, fixed-cost consumers, terminal branches and parity surfaces mapped. Stage 20.3.2 may proceed without production mutation in this audit.

## Ручна перевірка

**Не потрібна.** Це read-only audit patch.
