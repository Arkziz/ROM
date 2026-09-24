# Stage 19.21: аудит готовності балансу сюжетних квестів

## Рішення

**BLOCKED_MISSING_QUEST_1_100_CANDIDATE_DATA**

Кількісний баланс 100 квестів зараз неможливо обчислити без вигадування даних. Canonical production registry порожній, а repository не містить погоджених candidate values для квестів 1–100.

## Контрольна точка

- HEAD: `69899044e420044cd6853c11a6b53c62e99162c6`
- Production DB quick_check: `ok`
- Foreign-key violations: `0`
- Production mutation: **ні**
- Production content installed: **ні**

## Що підтверджено

- Definition schema підтримує TALK, KILL_REGION, QUEST_ITEM, TURN_IN і BOSS.
- EXP/gold, target quantity та quest-item drop chance можуть бути перевірені після появи candidate content.
- Канонічні рівні локацій і player EXP progression доступні для моделювання.
- Інтеграції progress, drops, SKIP, RNG boss і guaranteed boss call уже створені.

## Чого бракує

Для кожного з 100 квестів потрібні щонайменше:

- `quest_id`
- `number`
- `quest_type`
- `location_id`
- `unlock_level`
- `target_quantity`
- `reward.exp`
- `reward.gold`

Для `QUEST_ITEM` додатково потрібні `item_key`, `required_quantity`, `drop_chance`; для `BOSS` потрібен `boss_key`.

## Знайдені story-related файли

- `MD/STAGE_17_24_0_PROFILE_TRADE_AND_PVP_HISTORY_READ_ONLY_AUDIT.md`
- `MD/STAGE_18_2_1_AUCTION_HISTORY_AND_SELL_STATE_FIX.md`
- `MD/STAGE_18_3_1A_ADMIN_MENU_CLOSE_AND_HISTORY_PAGINATION.md`
- `MD/STAGE_18_3_1B_ADMIN_HISTORY_TIMEZONE_AND_USER_NOTIFICATIONS.md`
- `MD/STAGE_18_3_1C_ADMIN_HISTORY_INLINE_DETAILS_AND_CHARACTER_NAMES.md`
- `MD/STAGE_19_14_STORY_QUEST_REWARD_OWNER_READ_ONLY_AUDIT.md`
- `MD/STAGE_19_1_STORY_QUEST_ARCHITECTURE_READ_ONLY_AUDIT.md`
- `data/__pycache__/story_quest_content.cpython-314.pyc`
- `data/__pycache__/story_quest_definitions.cpython-314.pyc`
- `data/__pycache__/story_quest_npcs.cpython-314.pyc`
- `data/story_quest_content.py`
- `data/story_quest_definitions.py`
- `data/story_quest_npcs.py`

Schema fixtures не є production balance candidates і не можуть використовуватися для розрахунку нагород.

## Які розрахунки заблоковано

- сумарні EXP і gold по кожному пакету з 10;
- частка quest EXP відносно mob EXP;
- прогноз рівня після кожного квесту;
- ризик передчасного переходу на рівень 6 або 11 і SKIP;
- очікувана кількість hunts для QUEST_ITEM;
- kill counts і тривалість пакетів;
- окрема перевірка boss rewards;
- повна матриця прогресії 1–10.

## Наступний безпечний крок

Надати candidate content для квестів 1–100 або початковий документ із назвами, типами, target values, EXP, gold і drop chance. Після цього виконати окремий імпорт/нормалізацію candidate dataset без production activation, а потім повторити кількісний Stage 19.21.

Рекомендований наступний patch: `patch_19_21a_import_story_quest_balance_candidates.py`.
