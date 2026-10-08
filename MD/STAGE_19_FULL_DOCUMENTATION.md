# Stage 19: повна документація сюжетної системи

Generated: 2026-10-08T21:49:16.558062+00:00

## 1. Підсумок

Stage 19 реалізує 100 сюжетних квестів у двох історіях: `start_path` (50) і `dark_forest` (50). Registry, hierarchy, persistence, quest items, boss flow, overlevel SKIP і журнал прийняті regression-рішенням GO.

## 2. Архітектура

- `data/story_quest_definitions.py`: immutable schema, objective enums, validation, derived statuses.
- `data/story_quest_content.py`: authoritative registry 1–100 і presentation text.
- `data/story_quests/*.py`: production packs по 10 квестів.
- `data/story_quest_hierarchy.py`: історії та розділи; canonical термін у UI — «розділ».
- `db_modules/story_quests.py`: persistent lifecycle і journal queries.
- `systems/story_quest_system.py`: canonical orchestration API.
- `systems/story_quest_combat_progress_system.py`: KILL_REGION progress.
- `systems/story_quest_item_drop_system.py`: isolated quest-item drops.
- `systems/story_quest_boss_call_system.py` і `story_quest_boss_completion_system.py`: boss 49/99.
- `systems/story_quest_overlevel_system.py`: location-wide SKIP.
- `handlers/story_quests.py` і `story_quest_hierarchy_ui.py`: journal і Telegram navigation.

## 3. Історії та розділи
- **start_path / Розділ 1. Тривога на околиці**: level 1, quests 1–10, sort 10
- **start_path / Розділ 2. Рунічна аномалія**: level 2, quests 11–20, sort 20
- **start_path / Розділ 3. Зниклий патруль**: level 3, quests 21–30, sort 30
- **start_path / Розділ 4. Вовча загроза**: level 4, quests 31–40, sort 40
- **start_path / Розділ 5. Вирішальний похід**: level 5, quests 41–50, sort 50
- **dark_forest / Розділ 1. Тінь за Темним Бором**: level 6, quests 51–60, sort 60
- **dark_forest / Розділ 2. Гоблінські дозори**: level 7, quests 61–70, sort 70
- **dark_forest / Розділ 3. Слід рунічного культу**: level 8, quests 71–80, sort 80
- **dark_forest / Розділ 4. Осквернені землі**: level 9, quests 81–90, sort 90
- **dark_forest / Розділ 5. Король Гоблінів**: level 10, quests 91–100, sort 100

## 4. Доступ і strict chain

Кожен пакет із 10 квестів має власний unlock level. Для availability одночасно потрібні відповідний рівень, завершений predecessor і відсутність іншого ACTIVE-квесту. Persistent statuses: ACTIVE, COMPLETED, SKIPPED. Derived statuses: AVAILABLE, LOCKED.

- Level 1: quests 1–10
- Level 2: quests 11–20
- Level 3: quests 21–30
- Level 4: quests 31–40
- Level 5: quests 41–50
- Level 6: quests 51–60
- Level 7: quests 61–70
- Level 8: quests 71–80
- Level 9: quests 81–90
- Level 10: quests 91–100

## 5. Objective families

Розподіл: `{'TALK': 26, 'KILL_REGION': 25, 'QUEST_ITEM': 21, 'TURN_IN': 26, 'BOSS': 2}`.

- TALK: розмова та exact-once completion через NPC.
- KILL_REGION: progress від перемог у required location.
- QUEST_ITEM: chance 15%, required quantity 1, isolated virtual storage.
- TURN_IN: здача й optional exact-once consumption accumulated items.
- BOSS: canonical forced encounter/identity, victory progress, deferred NPC turn-in.

## 6. Rewards

Звичайні квести пакетів використовують затверджені story rewards, калібровані як 3× canonical expected reward normal mob відповідного рівня. Boss 49 має 5× story reward, окремо від бойової boss reward. Reward adapter атомарний; `reward_claimed` захищає exact-once. SKIPPED ніколи не отримує reward.

## 7. QUEST_ITEM lifecycle

Production QUEST_ITEM definitions: 21. Canonical identity: `user_id + quest_id + item_key`; local numeric row ID не є `items.id`. Колонки `item_id` і `inventory_id` заборонені. Предмети не займають bag slots, не продаються, не передаються й не потрапляють на auction. Drop chance для production quest items: 0.15. Cleanup виконується під час completion/consumption або SKIP.

## 8. Boss flow

- Quest 49: boss_key `pack_leader`, target 1, turn-in `None`.
- Quest 99: boss_key `goblin_king`, target 1, turn-in `mercenary_head`.

Boss encounter не має окремої кнопки полювання; виклик інтегрований у canonical combat flow. Після перемоги objective готовий, але story reward видається лише через deferred NPC turn-in.

## 9. Overlevel SKIP

Location ceilings: Початок Шляху 5, Темний Бір 10. Після переходу вище ceiling система атомарно зберігає COMPLETED, матеріалізує решту незавершених квестів як SKIPPED, не видає rewards, очищує isolated items і формує summary. Boundary 5→6 перевірено вручну, 10→11 — isolated production-code evidence. Повторний виклик idempotent.

## 10. Level-up integration

Combat pipeline спочатку показує victory/reward, потім canonical level-up message/rewards, після цього overlevel SKIP summary. Attribute points і special rewards не дублюються.

## 11. Journal

Hierarchy: історія → розділ → квест → detail. Icons: ✅ completed, 📖 active, ✨ available, 🔒 locked, ⏭️ skipped. Finalized COMPLETED+SKIPPED section має ⏭️, але progress рахує тільки COMPLETED. Root повертається через canonical `story_quest:profile`. Pagination не потрібна за section size 10.

## 12. KILL_REGION balance

- Quest 2: 3
- Quest 6: 5
- Quest 9: 6
- Quest 12: 8
- Quest 17: 10
- Quest 22: 8
- Quest 25: 10
- Quest 28: 10
- Quest 32: 8
- Quest 36: 10
- Quest 39: 10
- Quest 42: 8
- Quest 45: 10
- Quest 48: 10
- Quest 52: 8
- Quest 56: 10
- Quest 59: 10
- Quest 62: 8
- Quest 67: 10
- Quest 72: 8
- Quest 77: 10
- Quest 82: 8
- Quest 87: 10
- Quest 92: 8
- Quest 97: 10

Intro exceptions 2/6/9 = 3/5/6. Інші пакети використовують 8/10[/10]. Objective text має нормативну форму `N будь-яких істот`.

## 13. Persistence і migrations

Migration 053 створює `user_story_quests` і `user_story_quest_items`, partial unique index одного ACTIVE на user та journal index. Migration 054 reconciles лише ACTIVE targets для 12/17/32/36/39/42/45, clamped progress, без auto-completion і rewards.
Live DB: integrity `ok`, FK errors 0, statuses `{'ACTIVE': 1, 'COMPLETED': 106, 'SKIPPED': 50}`, migrations `['050_event_kill_statistics.py', '051_event_shop_exchange.py', '052_registration_date_pipeline.py', '053_story_quest_persistence_schema.py', '054_story_quest_kill_target_normalization.py']`.

## 14. Verification і acceptance

- `tools/verify_stage_19_33_6_boss_call_quest_identity.py`: PASS
- `tools/verify_stage_19_34_2_atomic_location_story_skip.py`: PASS
- `tools/verify_stage_19_34_2a_level_up_notification.py`: PASS
- `tools/verify_stage_19_34_3_story_quest_item_identity.py`: PASS
- `tools/verify_stage_19_34_5_routes_and_kill_targets.py`: PASS
- `tools/verify_stage_19_36_2_story_quest_journal.py`: PASS

Manual evidence: повні проходження 1–50 і 51–100; boss 49/99; finale 100; SKIP 5→6; level-up ordering; startup after Migration 054; journal navigation. Full regression: GO, closure gaps 0.

## 15. Known limitations

- Production gameplay level cap може залишатися нижчим за майбутній content roadmap; Stage 19 охоплює story levels 1–10.
- Third story location не активована; quest 101 відсутній.
- Journal pagination не реалізована, бо canonical section має 10 квестів.
- AVAILABLE і LOCKED не persist, а derive at runtime.

## 16. Повний quest catalog
- 1. **Патруль не повернувся** | `TALK` | level 1 | target 1 | giver `elder` | turn-in `elder` | reward 30 EXP / 0.27 gold
- 2. **Перевірка стежки** | `KILL_REGION` | level 1 | target 3 | giver `mercenary_head` | turn-in `mercenary_head` | reward 30 EXP / 0.27 gold
- 3. **Останній слід** | `TALK` | level 1 | target 1 | giver `mercenary_head` | turn-in `mercenary_head` | reward 30 EXP / 0.27 gold
- 4. **Клапоть форми** | `QUEST_ITEM` | level 1 | target 1 | giver `mercenary_head` | turn-in `mercenary_head` | reward 30 EXP / 0.27 gold
- 5. **Доказ із хащі** | `TURN_IN` | level 1 | target 1 | giver `elder` | turn-in `elder` | reward 30 EXP / 0.27 gold
- 6. **Старий міст** | `KILL_REGION` | level 1 | target 5 | giver `mercenary_head` | turn-in `mercenary_head` | reward 30 EXP / 0.27 gold
- 7. **Згаслий ліхтар** | `QUEST_ITEM` | level 1 | target 1 | giver `mercenary_head` | turn-in `mercenary_head` | reward 30 EXP / 0.27 gold
- 8. **Сліди на металі** | `TURN_IN` | level 1 | target 1 | giver `blacksmith` | turn-in `blacksmith` | reward 30 EXP / 0.27 gold
- 9. **Шлях до печер** | `KILL_REGION` | level 1 | target 6 | giver `mercenary_head` | turn-in `mercenary_head` | reward 30 EXP / 0.27 gold
- 10. **Розслідування починається** | `TURN_IN` | level 1 | target 1 | giver `elder` | turn-in `elder` | reward 30 EXP / 0.27 gold
- 11. **Неспокійне світіння** | `TALK` | level 2 | target 1 | giver `rune_master` | turn-in `rune_master` | reward 36 EXP / 0.43 gold
- 12. **Осередки аномалії** | `KILL_REGION` | level 2 | target 8 | giver `rune_master` | turn-in `rune_master` | reward 36 EXP / 0.43 gold
- 13. **Уламок аномалії** | `QUEST_ITEM` | level 2 | target 1 | giver `rune_master` | turn-in `rune_master` | reward 36 EXP / 0.43 gold
- 14. **Кристал під склом** | `TURN_IN` | level 2 | target 1 | giver `alchemist` | turn-in `alchemist` | reward 36 EXP / 0.43 gold
- 15. **Рунічний пил** | `QUEST_ITEM` | level 2 | target 1 | giver `alchemist` | turn-in `alchemist` | reward 36 EXP / 0.43 gold
- 16. **Неприродний слід** | `TURN_IN` | level 2 | target 1 | giver `alchemist` | turn-in `alchemist` | reward 36 EXP / 0.43 gold
- 17. **Заражені стежки** | `KILL_REGION` | level 2 | target 10 | giver `rune_master` | turn-in `rune_master` | reward 36 EXP / 0.43 gold
- 18. **Світло після заходу** | `TALK` | level 2 | target 1 | giver `rune_master` | turn-in `rune_master` | reward 36 EXP / 0.43 gold
- 19. **Записка при світлі рун** | `QUEST_ITEM` | level 2 | target 1 | giver `rune_master` | turn-in `rune_master` | reward 36 EXP / 0.43 gold
- 20. **Патруль знав** | `TURN_IN` | level 2 | target 1 | giver `elder` | turn-in `elder` | reward 36 EXP / 0.43 gold
- 21. **Пошуковий загін** | `TALK` | level 3 | target 1 | giver `mercenary_head` | turn-in `mercenary_head` | reward 42 EXP / 0.65 gold
- 22. **Вхід до печер** | `KILL_REGION` | level 3 | target 8 | giver `mercenary_head` | turn-in `mercenary_head` | reward 42 EXP / 0.65 gold
- 23. **Перстень вартового** | `QUEST_ITEM` | level 3 | target 1 | giver `mercenary_head` | turn-in `trader` | reward 42 EXP / 0.65 gold
- 24. **Остання покупка** | `TALK` | level 3 | target 1 | giver `trader` | turn-in `trader` | reward 42 EXP / 0.65 gold
- 25. **Сліди біля мосту** | `KILL_REGION` | level 3 | target 10 | giver `mercenary_head` | turn-in `mercenary_head` | reward 42 EXP / 0.65 gold
- 26. **Розбитий захист** | `QUEST_ITEM` | level 3 | target 1 | giver `mercenary_head` | turn-in `mercenary_head` | reward 42 EXP / 0.65 gold
- 27. **Виття за стінами** | `TALK` | level 3 | target 1 | giver `bartender` | turn-in `bartender` | reward 42 EXP / 0.65 gold
- 28. **Стежка переслідування** | `KILL_REGION` | level 3 | target 10 | giver `mercenary_head` | turn-in `mercenary_head` | reward 42 EXP / 0.65 gold
- 29. **Подертий плащ** | `QUEST_ITEM` | level 3 | target 1 | giver `mercenary_head` | turn-in `mercenary_head` | reward 42 EXP / 0.65 gold
- 30. **Картина нападу** | `TURN_IN` | level 3 | target 1 | giver `mercenary_head` | turn-in `mercenary_head` | reward 42 EXP / 0.65 gold
- 31. **Зграя на підступах** | `TALK` | level 4 | target 1 | giver `mercenary_head` | turn-in `mercenary_head` | reward 48 EXP / 0.89 gold
- 32. **Перша лінія оборони** | `KILL_REGION` | level 4 | target 8 | giver `mercenary_head` | turn-in `mercenary_head` | reward 48 EXP / 0.89 gold
- 33. **Захист для мисливців** | `TALK` | level 4 | target 1 | giver `blacksmith` | turn-in `blacksmith` | reward 48 EXP / 0.89 gold
- 34. **Хутро зі слідами рун** | `QUEST_ITEM` | level 4 | target 1 | giver `blacksmith` | turn-in `blacksmith` | reward 48 EXP / 0.89 gold
- 35. **Посилення загону** | `TURN_IN` | level 4 | target 1 | giver `blacksmith` | turn-in `blacksmith` | reward 48 EXP / 0.89 gold
- 36. **За межею безпечних стежок** | `KILL_REGION` | level 4 | target 10 | giver `mercenary_head` | turn-in `mercenary_head` | reward 48 EXP / 0.89 gold
- 37. **Слід до лігва** | `QUEST_ITEM` | level 4 | target 1 | giver `mercenary_head` | turn-in `rune_master` | reward 48 EXP / 0.89 gold
- 38. **Серце впливу** | `TURN_IN` | level 4 | target 1 | giver `rune_master` | turn-in `rune_master` | reward 48 EXP / 0.89 gold
- 39. **Дорога до лігва** | `KILL_REGION` | level 4 | target 10 | giver `mercenary_head` | turn-in `mercenary_head` | reward 48 EXP / 0.89 gold
- 40. **Перед вирішальним походом** | `TURN_IN` | level 4 | target 1 | giver `elder` | turn-in `elder` | reward 48 EXP / 0.89 gold
- 41. **Рада перед походом** | `TALK` | level 5 | target 1 | giver `elder` | turn-in `elder` | reward 57 EXP / 1.29 gold
- 42. **Підступи до лігва** | `KILL_REGION` | level 5 | target 8 | giver `mercenary_head` | turn-in `mercenary_head` | reward 57 EXP / 1.29 gold
- 43. **Печатка зграї** | `QUEST_ITEM` | level 5 | target 1 | giver `mercenary_head` | turn-in `mercenary_head` | reward 57 EXP / 1.29 gold
- 44. **Знак Ватажка** | `TURN_IN` | level 5 | target 1 | giver `mercenary_head` | turn-in `mercenary_head` | reward 57 EXP / 1.29 gold
- 45. **Охорона лігва** | `KILL_REGION` | level 5 | target 10 | giver `mercenary_head` | turn-in `mercenary_head` | reward 57 EXP / 1.29 gold
- 46. **Шерсть Ватажка** | `QUEST_ITEM` | level 5 | target 1 | giver `mercenary_head` | turn-in `mercenary_head` | reward 57 EXP / 1.29 gold
- 47. **Остання перевірка** | `TURN_IN` | level 5 | target 1 | giver `blacksmith` | turn-in `blacksmith` | reward 57 EXP / 1.29 gold
- 48. **Останній периметр** | `KILL_REGION` | level 5 | target 10 | giver `mercenary_head` | turn-in `mercenary_head` | reward 57 EXP / 1.29 gold
- 49. **Ватажок зграї** | `BOSS` | level 5 | target 1 | giver `mercenary_head` | turn-in `mercenary_head` | reward 95 EXP / 2.15 gold
- 50. **Дорога далі** | `TURN_IN` | level 5 | target 1 | giver `elder` | turn-in `elder` | reward 57 EXP / 1.29 gold
- 51. **Тінь за межею** | `TALK` | level 6 | target 1 | giver `elder` | turn-in `elder` | reward 66 EXP / 1.84 gold
- 52. **Межа Темного Бору** | `KILL_REGION` | level 6 | target 8 | giver `mercenary_head` | turn-in `mercenary_head` | reward 66 EXP / 1.84 gold
- 53. **Не випадковий дозор** | `TALK` | level 6 | target 1 | giver `mercenary_head` | turn-in `mercenary_head` | reward 66 EXP / 1.84 gold
- 54. **Знак на старому шляху** | `QUEST_ITEM` | level 6 | target 1 | giver `mercenary_head` | turn-in `mercenary_head` | reward 66 EXP / 1.84 gold
- 55. **Межа, якої не було** | `TURN_IN` | level 6 | target 1 | giver `elder` | turn-in `elder` | reward 66 EXP / 1.84 gold
- 56. **Табір біля дороги** | `KILL_REGION` | level 6 | target 10 | giver `mercenary_head` | turn-in `mercenary_head` | reward 66 EXP / 1.84 gold
- 57. **Рунічний слід** | `QUEST_ITEM` | level 6 | target 1 | giver `mercenary_head` | turn-in `mercenary_head` | reward 66 EXP / 1.84 gold
- 58. **Знайома руна** | `TURN_IN` | level 6 | target 1 | giver `rune_master` | turn-in `rune_master` | reward 66 EXP / 1.84 gold
- 59. **Дорога вглиб** | `KILL_REGION` | level 6 | target 10 | giver `mercenary_head` | turn-in `mercenary_head` | reward 66 EXP / 1.84 gold
- 60. **Загроза з глибини** | `TURN_IN` | level 6 | target 1 | giver `elder` | turn-in `elder` | reward 66 EXP / 1.84 gold
- 61. **Наказ про вилазки** | `TALK` | level 7 | target 1 | giver `mercenary_head` | turn-in `mercenary_head` | reward 75 EXP / 2.36 gold
- 62. **Зміна варти** | `KILL_REGION` | level 7 | target 8 | giver `mercenary_head` | turn-in `mercenary_head` | reward 75 EXP / 2.36 gold
- 63. **Відповідь із лісу** | `TALK` | level 7 | target 1 | giver `mercenary_head` | turn-in `mercenary_head` | reward 75 EXP / 2.36 gold
- 64. **Голос дозору** | `QUEST_ITEM` | level 7 | target 1 | giver `mercenary_head` | turn-in `mercenary_head` | reward 75 EXP / 2.36 gold
- 65. **Насічки на обручі** | `TURN_IN` | level 7 | target 1 | giver `blacksmith` | turn-in `blacksmith` | reward 75 EXP / 2.36 gold
- 66. **Знак із трьома зубцями** | `TALK` | level 7 | target 1 | giver `trader` | turn-in `trader` | reward 75 EXP / 2.36 gold
- 67. **Перерізати постачання** | `KILL_REGION` | level 7 | target 10 | giver `mercenary_head` | turn-in `mercenary_head` | reward 75 EXP / 2.36 gold
- 68. **Важкий жетон** | `QUEST_ITEM` | level 7 | target 1 | giver `mercenary_head` | turn-in `mercenary_head` | reward 75 EXP / 2.36 gold
- 69. **Сім зарубок** | `TALK` | level 7 | target 1 | giver `trader` | turn-in `trader` | reward 75 EXP / 2.36 gold
- 70. **Сьома стоянка** | `TURN_IN` | level 7 | target 1 | giver `mercenary_head` | turn-in `mercenary_head` | reward 75 EXP / 2.36 gold
- 71. **Шлях до сьомої стоянки** | `TALK` | level 8 | target 1 | giver `mercenary_head` | turn-in `mercenary_head` | reward 87 EXP / 3.23 gold
- 72. **Підступи до яру** | `KILL_REGION` | level 8 | target 8 | giver `mercenary_head` | turn-in `mercenary_head` | reward 87 EXP / 3.23 gold
- 73. **Не військовий табір** | `TALK` | level 8 | target 1 | giver `mercenary_head` | turn-in `mercenary_head` | reward 87 EXP / 3.23 gold
- 74. **Знаки біля кам’яного яру** | `QUEST_ITEM` | level 8 | target 1 | giver `mercenary_head` | turn-in `mercenary_head` | reward 87 EXP / 3.23 gold
- 75. **Розімкнене коло** | `TURN_IN` | level 8 | target 1 | giver `rune_master` | turn-in `rune_master` | reward 87 EXP / 3.23 gold
- 76. **Домішка в рунічному порошку** | `TALK` | level 8 | target 1 | giver `alchemist` | turn-in `alchemist` | reward 87 EXP / 3.23 gold
- 77. **Погасити ритуальні вогні** | `KILL_REGION` | level 8 | target 10 | giver `alchemist` | turn-in `alchemist` | reward 87 EXP / 3.23 gold
- 78. **Залишки обряду** | `QUEST_ITEM` | level 8 | target 1 | giver `alchemist` | turn-in `alchemist` | reward 87 EXP / 3.23 gold
- 79. **Ціна обряду** | `TURN_IN` | level 8 | target 1 | giver `alchemist` | turn-in `alchemist` | reward 87 EXP / 3.23 gold
- 80. **Слід рунічного культу** | `TURN_IN` | level 8 | target 1 | giver `elder` | turn-in `elder` | reward 87 EXP / 3.23 gold
- 81. **Слід за кам’яним яром** | `TALK` | level 9 | target 1 | giver `mercenary_head` | turn-in `mercenary_head` | reward 99 EXP / 4.13 gold
- 82. **Прихована стежка** | `KILL_REGION` | level 9 | target 8 | giver `mercenary_head` | turn-in `mercenary_head` | reward 99 EXP / 4.13 gold
- 83. **Земля без слідів** | `TALK` | level 9 | target 1 | giver `mercenary_head` | turn-in `mercenary_head` | reward 99 EXP / 4.13 gold
- 84. **Темний ґрунт** | `QUEST_ITEM` | level 9 | target 1 | giver `mercenary_head` | turn-in `mercenary_head` | reward 99 EXP / 4.13 gold
- 85. **Коріння осквернення** | `TURN_IN` | level 9 | target 1 | giver `alchemist` | turn-in `alchemist` | reward 99 EXP / 4.13 gold
- 86. **Межа осквернення** | `TALK` | level 9 | target 1 | giver `alchemist` | turn-in `alchemist` | reward 99 EXP / 4.13 gold
- 87. **Крізь чорне коріння** | `KILL_REGION` | level 9 | target 10 | giver `alchemist` | turn-in `alchemist` | reward 99 EXP / 4.13 gold
- 88. **Сліди серед коріння** | `QUEST_ITEM` | level 9 | target 1 | giver `alchemist` | turn-in `alchemist` | reward 99 EXP / 4.13 gold
- 89. **Печатка без імені** | `TURN_IN` | level 9 | target 1 | giver `rune_master` | turn-in `rune_master` | reward 99 EXP / 4.13 gold
- 90. **Осквернені землі** | `TURN_IN` | level 9 | target 1 | giver `elder` | turn-in `elder` | reward 99 EXP / 4.13 gold
- 91. **Непрочитані рядки** | `TALK` | level 10 | target 1 | giver `rune_master` | turn-in `rune_master` | reward 114 EXP / 5.29 gold
- 92. **Дорога до руїн** | `KILL_REGION` | level 10 | target 8 | giver `mercenary_head` | turn-in `mercenary_head` | reward 114 EXP / 5.29 gold
- 93. **Знак над брамою** | `TALK` | level 10 | target 1 | giver `mercenary_head` | turn-in `mercenary_head` | reward 114 EXP / 5.29 gold
- 94. **Символ старих руїн** | `QUEST_ITEM` | level 10 | target 1 | giver `mercenary_head` | turn-in `mercenary_head` | reward 114 EXP / 5.29 gold
- 95. **Корона і три зубці** | `TURN_IN` | level 10 | target 1 | giver `rune_master` | turn-in `rune_master` | reward 114 EXP / 5.29 gold
- 96. **Той, кому служать дозори** | `TALK` | level 10 | target 1 | giver `mercenary_head` | turn-in `mercenary_head` | reward 114 EXP / 5.29 gold
- 97. **Зовнішня охорона** | `KILL_REGION` | level 10 | target 10 | giver `mercenary_head` | turn-in `mercenary_head` | reward 114 EXP / 5.29 gold
- 98. **Перед вирішальним походом** | `TALK` | level 10 | target 1 | giver `mercenary_head` | turn-in `mercenary_head` | reward 114 EXP / 5.29 gold
- 99. **Король Гоблінів** | `BOSS` | level 10 | target 1 | giver `mercenary_head` | turn-in `mercenary_head` | reward 190 EXP / 8.81 gold
- 100. **Завершення Темного Бору** | `TURN_IN` | level 10 | target 1 | giver `elder` | turn-in `elder` | reward 114 EXP / 5.29 gold

## 17. Operation rules

Не видаляти й не маніпулювати `game.db-wal`/`game.db-shm`. Для mutation patch: backup, exact staging, py_compile/verifier/regression, automatic rollback on FAIL, recovery report, manual scenario list. `ROM_FULL_DUMP.txt` дозволений dirty-файл і не staging-иться.
