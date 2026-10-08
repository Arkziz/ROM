# Stage 19.34.3: identity contract сюжетних предметів

Сюжетні предмети залишаються virtual items поза звичайним `items`/`inventory`. Canonical identity: `user_id + quest_id + item_key`; числовий `id` має лише семантику локального row ID. `item_id` та `inventory_id` заборонені schema contract, а high AUTOINCREMENT regression підтверджує відсутність перетину namespace.

Наступні обов’язкові аудити:
- фактична матриця KILL_REGION після балансування; квести 2/6/9 залишаються 3/5/6;
- українське відмінювання числівників у всіх quest/UI текстах: `1 перемога`, `2–4 перемоги`, `5–20 перемог`; відповідні форми для істот, монстрів, предметів і разів.

DB migration не потрібна. WAL/SHM не маніпулювалися. Manual verification: NOT REQUIRED.
