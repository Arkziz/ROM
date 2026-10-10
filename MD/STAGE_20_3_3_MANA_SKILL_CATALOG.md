# Stage 20.3.3 — Mana Skill Catalog

## Статус

Stage 20.3.3 розширює canonical `CLASS_SKILLS_V1` hybrid metadata для шести mana-навичок Мага і Жреця.

## Межа підетапу

Змінено лише metadata каталогу. Поля `cost` збережені з попередніми значеннями як тимчасова compatibility layer для ще не переведених consumers.

Поточні PvE, PvP, UI та simulator paths продовжують читати legacy `cost`, тому gameplay у цьому підетапі не змінюється.

## Hybrid profiles

- `mage_fireball`: `8 + 7% Max MP`, legacy `20`.
- `mage_thunder_spell`: `15 + 18% Max MP`, legacy `45`.
- `mage_arcane_flow`: `0 + 0% Max MP`, restore `25%`, legacy `0`.
- `priest_holy_ray`: `6 + 4% Max MP`, legacy `12`.
- `priest_healing_blessing`: `12 + 10% Max MP`, legacy `30`.
- `priest_purify_faith`: `10 + 8% Max MP`, restore `15%`, legacy `20`.

## Authoritative contract

Hybrid розрахунок виконується тільки через `data.mana_policy.calculate_mana_skill_cost`. Каталог є authoritative джерелом профілів, а policy є authoritative calculator.

Legacy `cost` не є новою формулою. Воно видаляється або перестає використовуватися лише після завершення поетапної інтеграції consumers.

## Перевірки

`tools/smoke_test_mana_skill_catalog.py` перевіряє:

- один literal `CLASS_SKILLS_V1`;
- 6 класів і 18 навичок;
- рівно 3 навички Мага та 3 навички Жреця;
- точні hybrid profiles;
- 24 контрольні cost-вектори;
- незмінність legacy cost;
- restore metadata лише для `mage_arcane_flow` та `priest_purify_faith`;
- відсутність mana metadata у фізичних класів.

## Наступний підетап

Stage 20.3.4 переводить PvE presentation, availability, stale-callback validation і фактичне списання на canonical calculator.

## Ручна перевірка

Не потрібна. Поточні runtime consumers ще використовують незмінний legacy `cost`, тому gameplay не змінено.
