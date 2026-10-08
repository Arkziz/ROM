#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Stage 19.34.5 normalized production pack.
QUEST_ROWS = [{'definition': {'quest_id': 'start_path_041_council_before_the_hunt',
                 'number': 41,
                 'title': 'Рада перед походом',
                 'quest_type': 'TALK',
                 'location_id': 'start_path',
                 'unlock_level': 5,
                 'previous_quest_id': 'start_path_040_before_the_final_hunt',
                 'giver_npc_id': 'elder',
                 'turn_in_npc_id': 'elder',
                 'target_quantity': 1,
                 'description': 'Староста скликає останню раду й розподіляє ролі перед вирішальним '
                                'походом до вовчого лігва.',
                 'objective_text': 'Взяти участь у раді Старости перед фінальним походом.',
                 'acceptance_text': 'Староста затверджує фінальний похід проти Ватажка зграї.',
                 'completion_text': 'Староста затверджує похід до лігва та доручає очистити '
                                    'підступи.',
                 'reward': {'exp': 57, 'gold': 1.29},
                 'required_quest_items': [],
                 'navigation': {'location_id': 'start_path',
                                'giver_npc_id': 'elder',
                                'turn_in_npc_id': 'elder',
                                'objective_hint': '🏙️ Місто → 🏛️ Ратуша → 🗣️ Староста',
                                'next_step_hint': '🏙️ Місто → 🏛️ Ратуша → 🗣️ Староста'}},
  'acceptance_text': 'Усі вже зібралися. Мисливці знайшли стежку до лігва, Рунний Майстер '
                     'підтвердив природу впливу, а найманці готують передовий загін. Залишайся на '
                     'раді: кожен має знати свою роль, перш ніж ми рушимо проти Ватажка зграї.',
  'completion_text': 'Рішення ухвалено. Найманці перевірять підступи до лігва, а мисливці '
                     'перекриють зграї шлях до відступу. Вирушай до Голови Найманців: відтепер '
                     'кожен крок наближає вирішальну сутичку.',
  'progress_text': 'Рада ще триває. Вислухай план до кінця, щоб жоден крок походу не став '
                   'несподіванкою.',
  'drop_message': ''},
 {'definition': {'quest_id': 'start_path_042_den_approaches',
                 'number': 42,
                 'title': 'Підступи до лігва',
                 'quest_type': 'KILL_REGION',
                 'location_id': 'start_path',
                 'unlock_level': 5,
                 'previous_quest_id': 'start_path_041_council_before_the_hunt',
                 'giver_npc_id': 'mercenary_head',
                 'turn_in_npc_id': 'mercenary_head',
                 'target_quantity': 8,
                 'description': 'Передовий загін має очистити підступи до лігва, перш ніж основні '
                                'сили залишать безпечні стежки.',
                 'objective_text': 'Перемогти 8 будь-яких істот у локації Початок Шляху.',
                 'acceptance_text': 'Герой послаблює зовнішню оборону лігва.',
                 'completion_text': 'Мисливці займають зовнішній периметр, де знаходять рунічний '
                                    'знак.',
                 'reward': {'exp': 57, 'gold': 1.29},
                 'progress_text': 'Підступи до лігва: {progress}/15',
                 'required_quest_items': [],
                 'navigation': {'location_id': 'start_path',
                                'giver_npc_id': 'mercenary_head',
                                'turn_in_npc_id': 'mercenary_head',
                                'objective_hint': '🏙️ Місто → 📜 Гільдія Найманців → ⚔️ Голова '
                                                  'Найманців',
                                'next_step_hint': '🏙️ Місто → 📜 Гільдія Найманців → ⚔️ Голова '
                                                  'Найманців'}},
  'acceptance_text': 'Розвідники позначили два проходи, але обидва кишать звірами. Якщо загін '
                     'натрапить на них у вузькій ущелині, похід закінчиться ще до лігва. Пройди '
                     'попереду й очисти підступи, поки ми збираємо людей.',
  'completion_text': 'Підступи очищено, і передовий загін уже займає перші позиції. Серед слідів '
                     'розвідники помітили дивні мітки, яких не залишають звичайні вовки.',
  'progress_text': 'Шлях іще небезпечний. Не залишай за спиною зграю, яка зможе вдарити по '
                   'основному загону.',
  'drop_message': ''},
 {'definition': {'quest_id': 'start_path_043_pack_leader_seal',
                 'number': 43,
                 'title': 'Печатка зграї',
                 'quest_type': 'QUEST_ITEM',
                 'location_id': 'start_path',
                 'unlock_level': 5,
                 'previous_quest_id': 'start_path_042_den_approaches',
                 'giver_npc_id': 'mercenary_head',
                 'turn_in_npc_id': 'mercenary_head',
                 'target_quantity': 1,
                 'description': 'На очищеній стежці залишилися сліди влади Ватажка, і найманцям '
                                'потрібен доказ для розвідки лігва.',
                 'objective_text': 'Знайти під час полювання доказ, залишений наближеними Ватажка '
                                   'зграї.',
                 'acceptance_text': 'Герой знаходить печатку, що позначає територію Ватажка.',
                 'completion_text': 'Печатку Ватажка знайдено.',
                 'reward': {'exp': 57, 'gold': 1.29},
                 'quest_item': {'item_key': 'start_path_pack_leader_seal',
                                'display_name': 'Печатка Ватажка зграї',
                                'required_quantity': 1,
                                'drop_chance': 0.15,
                                'consume_on_completion': False},
                 'progress_text': 'Знайти під час полювання рунічний знак, пов’язаний із '
                                  'територією зграї.',
                 'required_quest_items': [],
                 'navigation': {'location_id': 'start_path',
                                'giver_npc_id': 'mercenary_head',
                                'turn_in_npc_id': 'mercenary_head',
                                'objective_hint': '🏙️ Місто → 📜 Гільдія Найманців → ⚔️ Голова '
                                                  'Найманців',
                                'next_step_hint': '🏙️ Місто → 📜 Гільдія Найманців → ⚔️ Голова '
                                                  'Найманців'}},
  'acceptance_text': 'На каменях є подряпини, складені майже в правильне коло. Це не випадковий '
                     'слід і не робота самотнього звіра. Оглядай здобич та місця сутичок, але не '
                     'називай знахідку вголос, доки ми не переконаємося, що вона означає.',
  'completion_text': 'Голова Найманців оглядає доказ і впізнає на ньому той самий знак, що й на '
                     'каменях біля проходу. Мітка належить наближеним Ватажка та допоможе '
                     'визначити, як зграя охороняє лігво.',
  'progress_text': 'Шукай уважно біля стежок до лігва. Потрібний доказ може здаватися звичайним, '
                   'доки не потрапить до досвідчених рук.',
  'drop_message': 'Печатку Ватажка знайдено.'},
 {'definition': {'quest_id': 'start_path_044_mark_of_the_pack_leader',
                 'number': 44,
                 'title': 'Знак Ватажка',
                 'quest_type': 'TURN_IN',
                 'location_id': 'start_path',
                 'unlock_level': 5,
                 'previous_quest_id': 'start_path_043_pack_leader_seal',
                 'giver_npc_id': 'mercenary_head',
                 'turn_in_npc_id': 'mercenary_head',
                 'target_quantity': 1,
                 'description': 'Голова Найманців має дослідити знайдений доказ і встановити, як '
                                'Ватажок керує охороною лігва.',
                 'objective_text': 'Передати знайдений доказ Голові Найманців.',
                 'acceptance_text': 'Голова Найманців приймає печатку та послаблює рунічний '
                                    'зв’язок лігва.',
                 'completion_text': 'Печатку знищено, зовнішній рунічний зв’язок слабшає.',
                 'reward': {'exp': 57, 'gold': 1.29},
                 'required_quest_items': [{'item_key': 'start_path_pack_leader_seal',
                                           'quantity': 1,
                                           'consume': True}],
                 'quest_item_consumption': 'atomic_exact_once',
                 'navigation': {'location_id': 'start_path',
                                'giver_npc_id': 'mercenary_head',
                                'turn_in_npc_id': 'mercenary_head',
                                'objective_hint': '🏙️ Місто → 📜 Гільдія Найманців → ⚔️ Голова '
                                                  'Найманців',
                                'next_step_hint': '🏙️ Місто → 📜 Гільдія Найманців → ⚔️ Голова '
                                                  'Найманців'}},
  'acceptance_text': 'Покажи, що вдалося знайти. Якщо мітка справді належить Ватажкові, вона '
                     'пояснить, чому зграя рухається так злагоджено й завжди встигає закривати '
                     'проходи до лігва.',
  'completion_text': 'Сумнівів немає: це знак Ватажка, яким він позначає наближених і межі своєї '
                     'території. Тепер ми знаємо, де шукати найсильнішу охорону лігва.',
  'progress_text': 'Знахідка має бути при тобі. Без неї я не зможу звірити мітку зі слідами '
                   'розвідників.',
  'drop_message': ''},
 {'definition': {'quest_id': 'start_path_045_guardians_of_the_den',
                 'number': 45,
                 'title': 'Охорона лігва',
                 'quest_type': 'KILL_REGION',
                 'location_id': 'start_path',
                 'unlock_level': 5,
                 'previous_quest_id': 'start_path_044_mark_of_the_pack_leader',
                 'giver_npc_id': 'mercenary_head',
                 'turn_in_npc_id': 'mercenary_head',
                 'target_quantity': 10,
                 'description': 'Вірні Ватажкові звірі стягуються до лігва й можуть зімкнути '
                                'оборону раніше, ніж підійде загін.',
                 'objective_text': 'Перемогти 10 будь-яких істот у локації Початок Шляху.',
                 'acceptance_text': 'Герой відтискає захисників головного входу.',
                 'completion_text': 'Захисників лігва відтиснуто.',
                 'reward': {'exp': 57, 'gold': 1.29},
                 'progress_text': 'Охорона лігва: {progress}/15',
                 'required_quest_items': [],
                 'navigation': {'location_id': 'start_path',
                                'giver_npc_id': 'mercenary_head',
                                'turn_in_npc_id': 'mercenary_head',
                                'objective_hint': '🏙️ Місто → 📜 Гільдія Найманців → ⚔️ Голова '
                                                  'Найманців',
                                'next_step_hint': '🏙️ Місто → 📜 Гільдія Найманців → ⚔️ Голова '
                                                  'Найманців'}},
  'acceptance_text': 'Знак указав на сторожові стежки. Там збираються найагресивніші звірі, і '
                     'кожна сутичка кличе до лігва нових. Розбий охорону поодинці, перш ніж вона '
                     'збереться в єдину зграю.',
  'completion_text': 'Сторожові стежки спорожніли, а виття біля лігва стало рідшим. Ватажок '
                     'утратив зовнішню охорону, проте розвідники помітили ще одну важливу зачіпку.',
  'progress_text': 'Охорона ще тримає кілька стежок. Не дозволяй їй зімкнути кільце навколо лігва.',
  'drop_message': ''},
 {'definition': {'quest_id': 'start_path_046_pack_leader_fur',
                 'number': 46,
                 'title': 'Шерсть Ватажка',
                 'quest_type': 'QUEST_ITEM',
                 'location_id': 'start_path',
                 'unlock_level': 5,
                 'previous_quest_id': 'start_path_045_guardians_of_the_den',
                 'giver_npc_id': 'mercenary_head',
                 'turn_in_npc_id': 'mercenary_head',
                 'target_quantity': 1,
                 'description': 'Голова Найманців чекає на доказ, що зберіг слід сили Ватажка, '
                                'перш ніж передати знахідку майстрові.',
                 'objective_text': 'Знайти під час полювання матеріал зі слідом сили Ватажка зграї '
                                   'та доповісти Голові Найманців.',
                 'acceptance_text': 'Герой знаходить шерсть Ватажка для перевірки спорядження.',
                 'completion_text': 'Клоччя шерсті Ватажка знайдено.',
                 'reward': {'exp': 57, 'gold': 1.29},
                 'quest_item': {'item_key': 'start_path_pack_leader_fur',
                                'display_name': 'Клоччя шерсті Ватажка',
                                'required_quantity': 1,
                                'drop_chance': 0.15,
                                'consume_on_completion': False},
                 'progress_text': 'Знайти біля входу до лігва біологічний слід для перевірки '
                                  'спорядження.',
                 'required_quest_items': [],
                 'navigation': {'location_id': 'start_path',
                                'giver_npc_id': 'mercenary_head',
                                'turn_in_npc_id': 'mercenary_head',
                                'objective_hint': '🏙️ Місто → 📜 Гільдія Найманців → ⚔️ Голова '
                                                  'Найманців',
                                'next_step_hint': '🏙️ Місто → 📜 Гільдія Найманців → ⚔️ Голова '
                                                  'Найманців'}},
  'acceptance_text': 'Коваль зможе використати лише справжній слід сили Ватажка, але спочатку я '
                     'маю переконатися, що знахідка походить із лігва. Шукай біля місць сутичок і '
                     'повертайся до мене, щойно помітиш щось незвичайне.',
  'completion_text': 'Так, це саме той слід, про який попереджав Рунний Майстер. Я позначу '
                     'знахідку печаткою загону, але забирати її не буду. Віднеси матеріал '
                     'Ковалеві: тепер він знатиме, що перед ним справжній доказ із лігва.',
  'progress_text': 'Потрібний матеріал трапляється рідко. Продовжуй полювання біля лігва, а після '
                   'знахідки повернися з доповіддю до Голови Найманців.',
  'drop_message': 'Клоччя шерсті Ватажка знайдено.'},
 {'definition': {'quest_id': 'start_path_047_final_equipment_check',
                 'number': 47,
                 'title': 'Остання перевірка',
                 'quest_type': 'TURN_IN',
                 'location_id': 'start_path',
                 'unlock_level': 5,
                 'previous_quest_id': 'start_path_046_pack_leader_fur',
                 'giver_npc_id': 'blacksmith',
                 'turn_in_npc_id': 'blacksmith',
                 'target_quantity': 1,
                 'description': 'Коваль огляне позначений матеріал, прийме його та завершить '
                                'підготовку спорядження для походу.',
                 'objective_text': 'Показати Ковалеві позначений матеріал і передати його для '
                                   'підготовки спорядження.',
                 'acceptance_text': 'Коваль досліджує шерсть і завершує перевірку спорядження.',
                 'completion_text': 'Коваль завершує перевірку та попереджає про бойове шаленство '
                                    'Ватажка.',
                 'reward': {'exp': 57, 'gold': 1.29},
                 'required_quest_items': [{'item_key': 'start_path_pack_leader_fur',
                                           'quantity': 1,
                                           'consume': True}],
                 'quest_item_consumption': 'atomic_exact_once',
                 'navigation': {'location_id': 'start_path',
                                'giver_npc_id': 'blacksmith',
                                'turn_in_npc_id': 'blacksmith',
                                'objective_hint': '🏙️ Місто → ⚒️ Ремісничий квартал → ⚒️ Коваль',
                                'next_step_hint': '🏙️ Місто → ⚒️ Ремісничий квартал → ⚒️ Коваль'}},
  'acceptance_text': 'Бачу печатку загону, отже Голова Найманців уже перевірив знахідку. Поклади '
                     'матеріал на камінь: я огляну рунічний слід, прийму його до роботи й одразу '
                     'завершу останню підготовку спорядження.',
  'completion_text': 'Матеріал прийнято й використано під час гартування. Сталь витримає перший '
                     'удар Ватажка, а спорядження загону готове до походу. Повертайся до Голови '
                     'Найманців.',
  'progress_text': 'Покажи позначений матеріал і передай його мені. Без цієї знахідки я не зможу '
                   'перевірити реакцію сталі та завершити підготовку загону.',
  'drop_message': ''},
 {'definition': {'quest_id': 'start_path_048_final_perimeter',
                 'number': 48,
                 'title': 'Останній периметр',
                 'quest_type': 'KILL_REGION',
                 'location_id': 'start_path',
                 'unlock_level': 5,
                 'previous_quest_id': 'start_path_047_final_equipment_check',
                 'giver_npc_id': 'mercenary_head',
                 'turn_in_npc_id': 'mercenary_head',
                 'target_quantity': 10,
                 'description': 'Перед викликом Ватажка необхідно знищити останні групи зграї та '
                                'замкнути периметр навколо лігва.',
                 'objective_text': 'Перемогти 10 будь-яких істот у локації Початок Шляху.',
                 'acceptance_text': 'Герой очищає останній периметр і відрізає Ватажка від зграї.',
                 'completion_text': 'Оборону біля входу зламано.',
                 'reward': {'exp': 57, 'gold': 1.29},
                 'progress_text': 'Останній периметр: {progress}/10',
                 'required_quest_items': [],
                 'navigation': {'location_id': 'start_path',
                                'giver_npc_id': 'mercenary_head',
                                'turn_in_npc_id': 'mercenary_head',
                                'objective_hint': '🏙️ Місто → 📜 Гільдія Найманців → ⚔️ Голова '
                                                  'Найманців',
                                'next_step_hint': '🏙️ Місто → 📜 Гільдія Найманців → ⚔️ Голова '
                                                  'Найманців'}},
  'acceptance_text': 'Спорядження готове, але навколо лігва ще блукають розрізнені групи. Вони '
                     'можуть ударити в спину, щойно з’явиться Ватажок. Замкни останній периметр і '
                     'залиш йому лише один шлях назовні.',
  'completion_text': 'Кільце навколо лігва замкнулося. Зграя більше не прикриває відступ, а '
                     'Ватажкові доведеться вийти на підготовлене місце. Час вирішальної сутички '
                     'настав.',
  'progress_text': 'Периметр іще не замкнений. Перевір бічні стежки й прибери тих, хто може '
                   'прорвати оточення.',
  'drop_message': ''},
 {'definition': {'quest_id': 'start_path_049_pack_leader',
                 'number': 49,
                 'title': 'Ватажок зграї',
                 'quest_type': 'BOSS',
                 'location_id': 'start_path',
                 'unlock_level': 5,
                 'previous_quest_id': 'start_path_048_final_perimeter',
                 'giver_npc_id': 'mercenary_head',
                 'turn_in_npc_id': None,
                 'target_quantity': 1,
                 'description': 'Після довгої підготовки загін готовий виманити Ватажка з лігва та '
                                'покласти край владі зграї.',
                 'objective_text': 'Викликати Ватажка Зграї, перемогти його та доповісти Голові '
                                   'Найманців.',
                 'acceptance_text': 'Ватажок тримається біля лігва. Вирушай у «Початок Шляху» та '
                                    'натисни «👀 Роззирнутися». Там Ватажка можна викликати на бій. '
                                    'Також він може зустрітися випадково під час звичайного '
                                    'полювання. Якщо ще не готовий до бою, продовжуй полювання та '
                                    'повернися до виклику пізніше.',
                 'completion_text': 'Голова Найманців вислуховує доповідь про перемогу над '
                                    'Ватажком. Зграя втратила провідника, а шлях біля лігва став '
                                    'безпечнішим. Підготовка загону була недаремною. Тепер '
                                    'Староста має почути, чим завершився вирішальний похід. '
                                    'Повернися до Ратуші та доповідь Старості.',
                 'reward': {'exp': 95, 'gold': 2.15},
                 'boss_key': 'pack_leader',
                 'encounter_paths': ['rng_hunt', 'guaranteed_story_call'],
                 'guaranteed_call_after_success': 'blocked',
                 'retry_after_defeat_or_escape': 'allowed',
                 'boss_combat_reward_is_separate': True,
                 'progress_text': 'Перемогти Ватажка зграї: {progress}/1. Після перемоги '
                                  'повернутися до Голови Найманців.',
                 'required_quest_items': [],
                 'navigation': {'location_id': 'start_path',
                                'giver_npc_id': 'mercenary_head',
                                'turn_in_npc_id': None,
                                'objective_hint': '🏙️ Місто → 📜 Гільдія Найманців → ⚔️ Голова '
                                                  'Найманців',
                                'next_step_hint': '🏙️ Місто → 📜 Гільдія Найманців → ⚔️ Голова '
                                                  'Найманців'}},
  'acceptance_text': 'Усі стежки перекриті, спорядження перевірене, а зовнішня охорона розбита. Я '
                     'подам умовний сигнал і виманю Ватажка з лігва. Після перемоги не поспішай '
                     'святкувати: повернися до мене з доповіддю, щоб ми переконалися, що зграя '
                     'справді втратила провідника.',
  'completion_text': 'Ватажок упав, а зграя розсіялася без єдиного наказу. Розвідники вже '
                     'підтвердили, що лігво спорожніло. Твоя перемога врятувала Початок Шляху, але '
                     'останнє слово має почути Староста.',
  'progress_text': 'Ватажок ще не переможений або доповідь не завершена. Скористайся підготовленим '
                   'викликом, а після бою повернися до Голови Найманців.',
  'drop_message': ''},
 {'definition': {'quest_id': 'start_path_050_road_ahead',
                 'number': 50,
                 'title': 'Дорога далі',
                 'quest_type': 'TURN_IN',
                 'location_id': 'start_path',
                 'unlock_level': 5,
                 'previous_quest_id': 'start_path_049_pack_leader',
                 'giver_npc_id': 'elder',
                 'turn_in_npc_id': 'elder',
                 'target_quantity': 1,
                 'description': 'Перемога над Ватажком завершує загрозу для Початку Шляху, і '
                                'Староста чекає на остаточну доповідь.',
                 'objective_text': 'Доповісти Старості про перемогу над Ватажком зграї та '
                                   'завершення походу.',
                 'acceptance_text': 'Староста чекає остаточної доповіді про Ватажка, стан зграї та '
                                    'безпеку шляху біля лігва.',
                 'completion_text': 'Староста вислуховує доповідь про перемогу над Ватажком. Без '
                                    'провідника зграя відступає від табору, а дорога через '
                                    '«Початок Шляху» знову відкрита для мандрівників. Рада дякує '
                                    'за підготовку загону та вирішальний бій.\n'
                                    '\n'
                                    '✅ Розділ «Вирішальний похід» завершено.\n'
                                    '✅ Історію «Початок Шляху» завершено.',
                 'reward': {'exp': 57, 'gold': 1.29},
                 'next_campaign_hint': {'location_id': 'dark_forest',
                                        'canonical_unlock_level': 6,
                                        'story_completion_does_not_unlock_location': True},
                 'progress_text': 'Доповісти Старості про перемогу над Ватажком і завершення '
                                  'вирішального походу.',
                 'itemless_turn_in_policy': {'available_action': '📖 Почати розмову',
                                             'active_action': '🗣️ Доповісти Старості',
                                             'conclusion': 'completion_only'},
                 'required_quest_items': [],
                 'navigation': {'location_id': 'start_path',
                                'giver_npc_id': 'elder',
                                'turn_in_npc_id': 'elder',
                                'objective_hint': '🏙️ Місто → 🏛️ Ратуша → 🗣️ Староста',
                                'next_step_hint': '🏙️ Місто → 🏛️ Ратуша → 🗣️ Староста'}},
  'acceptance_text': 'Я вже чув, що виття біля старого схилу стихло, але хочу почути все від того, '
                     'хто стояв перед Ватажком. Розкажи, як завершився похід і чи справді зграя '
                     'більше не загрожує Початку Шляху.',
  'completion_text': 'Початок Шляху вистояв. Від першої тривоги на околиці до бою біля лігва кожен '
                     'твій крок повертав людям упевненість. Сьогодні ми закриваємо цей розділ, але '
                     'за безпечними стежками вже починається нова дорога. Коли настане час, вона '
                     'чекатиме на тебе.',
  'progress_text': 'Староста чекає на повну доповідь про бій, стан лігва та долю розсіяної зграї.',
  'drop_message': ''}]
