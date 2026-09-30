#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Production story content for Початок Шляху quests 21-30."""

QUEST_ROWS: tuple[dict, ...] = ({'definition': {'quest_id': 'start_path_021_search_party',
                 'number': 21,
                 'title': 'Пошуковий загін',
                 'quest_type': 'TALK',
                 'location_id': 'start_path',
                 'unlock_level': 3,
                 'previous_quest_id': 'start_path_020_patrol_knew',
                 'giver_npc_id': 'mercenary_head',
                 'turn_in_npc_id': 'mercenary_head',
                 'target_quantity': 1,
                 'description': 'Голова Найманців формує пошуковий маршрут до печер, старого мосту '
                                'та зарослої стежки.',
                 'objective_text': 'Поговорити з Головою Найманців і отримати маршрут пошуку.',
                 'reward': {'exp': 42, 'gold': 0.65},
                 'navigation': {'location_id': 'start_path',
                                'giver_npc_id': 'mercenary_head',
                                'turn_in_npc_id': 'mercenary_head',
                                'objective_hint': 'Поговорити з Головою Найманців і отримати '
                                                  'маршрут пошуку.',
                                'next_step_hint': '🏙️ Місто → 📜 Гільдія Найманців → ⚔️ Голова '
                                                  'Найманців'},
                 'required_quest_items': []},
  'acceptance_text': 'Староста передав мені записку патруля. Тепер ми знаємо, що вартові '
                     'добровільно вирушили до печер, переслідуючи джерело рунічної аномалії. Я '
                     'розділив пошукову територію на кілька ділянок. Мої люди перевірять дорогу до '
                     'табору, а ти оглянеш печери та старий міст. Шукай особисті речі, уламки '
                     'спорядження або будь-які знаки, за якими можна відновити їхній шлях.',
  'completion_text': 'Голова Найманців позначає на карті печери, старий міст і зарослу стежку, '
                     'якою міг рухатися патруль.',
  'progress_text': '',
  'drop_message': ''},
 {'definition': {'quest_id': 'start_path_022_cave_entrance',
                 'number': 22,
                 'title': 'Вхід до печер',
                 'quest_type': 'KILL_REGION',
                 'location_id': 'start_path',
                 'unlock_level': 3,
                 'previous_quest_id': 'start_path_021_search_party',
                 'giver_npc_id': 'mercenary_head',
                 'turn_in_npc_id': 'mercenary_head',
                 'target_quantity': 8,
                 'description': 'Герой розчищає підступи до печер і знаходить перший особистий '
                                'слід патруля.',
                 'objective_text': 'Перемогти 8 будь-яких істот у локації Початок Шляху.',
                 'reward': {'exp': 42, 'gold': 0.65},
                 'navigation': {'location_id': 'start_path',
                                'giver_npc_id': 'mercenary_head',
                                'turn_in_npc_id': 'mercenary_head',
                                'objective_hint': 'Перемогти 8 будь-яких істот у локації Початок '
                                                  'Шляху.',
                                'next_step_hint': '🏙️ Місто → 📜 Гільдія Найманців → ⚔️ Голова '
                                                  'Найманців'},
                 'required_quest_items': []},
  'acceptance_text': 'Біля входу до печер стало надто небезпечно. Істоти збираються там частіше, '
                     'ніж раніше, а рунічне світіння видно навіть удень. Розчисти підступи. Не '
                     'заходь надто глибоко, доки ми не зрозуміємо, що трапилося з патрулем.',
  'completion_text': 'Підступи до печер очищено. Між камінням видно невеликий металевий предмет із '
                     'міським гербом.',
  'progress_text': 'Вхід до печер: {progress}/8',
  'drop_message': ''},
 {'definition': {'quest_id': 'start_path_023_guards_ring',
                 'number': 23,
                 'title': 'Перстень вартового',
                 'quest_type': 'QUEST_ITEM',
                 'location_id': 'start_path',
                 'unlock_level': 3,
                 'previous_quest_id': 'start_path_022_cave_entrance',
                 'giver_npc_id': 'mercenary_head',
                 'turn_in_npc_id': 'trader',
                 'target_quantity': 1,
                 'description': 'Під час полювання потрібно обшукати стежку до печер і відшукати '
                                'особисту річ, яка могла належати одному зі зниклих вартових.',
                 'objective_text': 'Знайти особистий перстень одного зі зниклих вартових.',
                 'reward': {'exp': 42, 'gold': 0.65},
                 'quest_item': {'item_key': 'start_path_guards_ring',
                                'display_name': 'Перстень вартового',
                                'required_quantity': 1,
                                'drop_chance': 0.15,
                                'consume_on_completion': False},
                 'retain_until_quest_id': 'start_path_030_scene_of_the_attack',
                 'navigation': {'location_id': 'start_path',
                                'giver_npc_id': 'mercenary_head',
                                'turn_in_npc_id': 'trader',
                                'objective_hint': 'Знайти особистий перстень одного зі зниклих '
                                                  'вартових.',
                                'next_step_hint': '🏙️ Місто → 📜 Гільдія Найманців → ⚔️ Голова '
                                                  'Найманців'},
                 'required_quest_items': []},
  'acceptance_text': 'Оглядай каміння й землю біля печер. Особиста річ допоможе встановити, хто '
                     'саме дістався сюди.',
  'completion_text': 'Перстень знайдено. Торговець може впізнати власника за міським клеймом.',
  'progress_text': '',
  'drop_message': '💍 Сюжетна знахідка: Перстень вартового\n'
                  '\n'
                  'На внутрішньому боці персня вигравіювано знак міської варти. Торговець може '
                  'знати, кому належав цей перстень.'},
 {'definition': {'quest_id': 'start_path_024_last_purchase',
                 'number': 24,
                 'title': 'Остання покупка',
                 'quest_type': 'TALK',
                 'location_id': 'start_path',
                 'unlock_level': 3,
                 'previous_quest_id': 'start_path_023_guards_ring',
                 'giver_npc_id': 'trader',
                 'turn_in_npc_id': 'trader',
                 'target_quantity': 1,
                 'description': 'Торговець упізнає перстень і згадує підготовку патрульного до '
                                'небезпечного походу.',
                 'objective_text': 'Показати Торговцю перстень вартового та дізнатися про останню '
                                   'покупку патрульного.',
                 'reward': {'exp': 42, 'gold': 0.65},
                 'required_quest_items': [{'item_key': 'start_path_guards_ring',
                                           'quantity': 1,
                                           'consume': False}],
                 'quest_item_consumption': 'none',
                 'navigation': {'location_id': 'start_path',
                                'giver_npc_id': 'trader',
                                'turn_in_npc_id': 'trader',
                                'objective_hint': 'Показати Торговцю перстень вартового та '
                                                  'дізнатися про останню покупку патрульного.',
                                'next_step_hint': '🏙️ Місто → 🛒 Торговий ряд → 🧙 Торговець'}},
  'acceptance_text': 'Я впізнаю цей перстень. Його власник заходив до мене перед останнім обходом. '
                     'Вартовий купив мотузку, запас олії для ліхтаря і кілька смужок тканини для '
                     'перев’язки. Сказав, що біля старого мосту бачили дивні сліди, схожі на '
                     'вовчі, але значно більші. Перстень залиш собі. Голові Найманців знадобляться '
                     'всі докази разом.',
  'completion_text': 'Торговець підтверджує, що патруль готувався до небезпечного походу й шукав '
                     'великі вовчі сліди.',
  'progress_text': '',
  'drop_message': ''},
 {'definition': {'quest_id': 'start_path_025_tracks_near_the_bridge',
                 'number': 25,
                 'title': 'Сліди біля мосту',
                 'quest_type': 'KILL_REGION',
                 'location_id': 'start_path',
                 'unlock_level': 3,
                 'previous_quest_id': 'start_path_024_last_purchase',
                 'giver_npc_id': 'mercenary_head',
                 'turn_in_npc_id': 'mercenary_head',
                 'target_quantity': 10,
                 'description': 'Голова Найманців просить знову розчистити околиці старого мосту, '
                                'щоб безпечно продовжити пошуки спорядження зниклого патруля.',
                 'objective_text': 'Перемогти 10 будь-яких істот у локації Початок Шляху.',
                 'reward': {'exp': 42, 'gold': 0.65},
                 'navigation': {'location_id': 'start_path',
                                'giver_npc_id': 'mercenary_head',
                                'turn_in_npc_id': 'mercenary_head',
                                'objective_hint': 'Перемогти 10 будь-яких істот у локації Початок '
                                                  'Шляху.',
                                'next_step_hint': '🏙️ Місто → 📜 Гільдія Найманців → ⚔️ Голова '
                                                  'Найманців'},
                 'required_quest_items': []},
  'acceptance_text': 'Якщо патруль ішов за великими вовчими слідами, сутичка могла статися біля '
                     'старого мосту. Але місцевість знову заполонили небезпечні істоти. Розчисти '
                     'околиці, щоб ми могли безпечно продовжити пошуки слідів патруля.',
  'completion_text': 'Біля кам’яної опори мосту видно глибокі борозни. Під уламками деревини '
                     'лежить частина пошкодженого щита.',
  'progress_text': 'Сліди біля мосту: {progress}/10',
  'drop_message': ''},
 {'definition': {'quest_id': 'start_path_026_damaged_guard_shield',
                 'number': 26,
                 'title': 'Розбитий захист',
                 'quest_type': 'QUEST_ITEM',
                 'location_id': 'start_path',
                 'unlock_level': 3,
                 'previous_quest_id': 'start_path_025_tracks_near_the_bridge',
                 'giver_npc_id': 'mercenary_head',
                 'turn_in_npc_id': 'mercenary_head',
                 'target_quantity': 1,
                 'description': 'Після зачистки старого мосту Голова Найманців просить уважно '
                                'обшукати місцевість та знайти спорядження, яке могло належати '
                                'зниклому патрулю.',
                 'objective_text': 'Знайти пошкоджений щит зниклого вартового.',
                 'reward': {'exp': 42, 'gold': 0.65},
                 'quest_item': {'item_key': 'start_path_damaged_guard_shield',
                                'display_name': 'Пошкоджений щит вартового',
                                'required_quantity': 1,
                                'drop_chance': 0.15,
                                'consume_on_completion': False},
                 'retain_until_quest_id': 'start_path_030_scene_of_the_attack',
                 'navigation': {'location_id': 'start_path',
                                'giver_npc_id': 'mercenary_head',
                                'turn_in_npc_id': 'mercenary_head',
                                'objective_hint': 'Знайти пошкоджений щит зниклого вартового.',
                                'next_step_hint': '🏙️ Місто → 📜 Гільдія Найманців → ⚔️ Голова '
                                                  'Найманців'},
                 'required_quest_items': []},
  'acceptance_text': 'Тепер біля старого мосту стало безпечніше. Повернися туди й уважно оглянь '
                     'землю, каміння та зарості. Шукай уламки спорядження або інший доказ, який '
                     'допоможе відновити перебіг сутички.',
  'completion_text': 'Пошкоджений щит знайдено та збережено для фінального зіставлення доказів.',
  'progress_text': '',
  'drop_message': '🛡️ Сюжетна знахідка: Пошкоджений щит вартового\n'
                  '\n'
                  'Дерев’яна основа тріснула, а на металевому ободі видно глибокі паралельні '
                  'подряпини. Схоже, щит пошкодили великі кігті.'},
 {'definition': {'quest_id': 'start_path_027_howling_beyond_the_walls',
                 'number': 27,
                 'title': 'Виття за стінами',
                 'quest_type': 'TALK',
                 'location_id': 'start_path',
                 'unlock_level': 3,
                 'previous_quest_id': 'start_path_026_damaged_guard_shield',
                 'giver_npc_id': 'bartender',
                 'turn_in_npc_id': 'bartender',
                 'target_quantity': 1,
                 'description': 'Бармен передає чутки мисливців про організовану вовчу зграю та '
                                'великого звіра зі світлими відмітками.',
                 'objective_text': 'Розпитати Бармена про чутки щодо вовків.',
                 'reward': {'exp': 42, 'gold': 0.65},
                 'navigation': {'location_id': 'start_path',
                                'giver_npc_id': 'bartender',
                                'turn_in_npc_id': 'bartender',
                                'objective_hint': 'Розпитати Бармена про чутки щодо вовків.',
                                'next_step_hint': '🏙️ Місто → 🍺 Таверна → 🍺 Бармен'},
                 'required_quest_items': []},
  'acceptance_text': 'Мисливці останніми ночами повертаються раніше. Кажуть, біля старого мосту '
                     'чути вовче виття, але воно лунає одразу з кількох боків. Один мандрівник '
                     'бачив у темряві великого вовка зі світлими відмітками на шерсті. Звір ніби '
                     'спостерігав і чекав, поки інші істоти кинуться вперед.',
  'completion_text': 'Бармен підтверджує, що біля мосту діє організована вовча зграя, якою може '
                     'керувати особливо великий звір.',
  'progress_text': '',
  'drop_message': ''},
 {'definition': {'quest_id': 'start_path_028_pursuit_trail',
                 'number': 28,
                 'title': 'Стежка переслідування',
                 'quest_type': 'KILL_REGION',
                 'location_id': 'start_path',
                 'unlock_level': 3,
                 'previous_quest_id': 'start_path_027_howling_beyond_the_walls',
                 'giver_npc_id': 'mercenary_head',
                 'turn_in_npc_id': 'mercenary_head',
                 'target_quantity': 10,
                 'description': 'Герой перевіряє стежку між мостом і печерами та знаходить сліди '
                                'переслідування.',
                 'objective_text': 'Перемогти 10 будь-яких істот у локації Початок Шляху.',
                 'reward': {'exp': 42, 'gold': 0.65},
                 'navigation': {'location_id': 'start_path',
                                'giver_npc_id': 'mercenary_head',
                                'turn_in_npc_id': 'mercenary_head',
                                'objective_hint': 'Перемогти 10 будь-яких істот у локації Початок '
                                                  'Шляху.',
                                'next_step_hint': '🏙️ Місто → 📜 Гільдія Найманців → ⚔️ Голова '
                                                  'Найманців'},
                 'required_quest_items': []},
  'acceptance_text': 'Якщо слова Бармена правдиві, патруль міг не переслідувати вовків. Можливо, '
                     'зграя сама гнала вартових до печер. Перевір зарослу стежку між мостом і '
                     'кам’янистим схилом.',
  'completion_text': 'На колючих кущах залишилися нитки темної тканини. Поруч видно вовчу шерсть і '
                     'старі сліди крові.',
  'progress_text': 'Стежка переслідування: {progress}/10',
  'drop_message': ''},
 {'definition': {'quest_id': 'start_path_029_torn_guard_cloak',
                 'number': 29,
                 'title': 'Подертий плащ',
                 'quest_type': 'QUEST_ITEM',
                 'location_id': 'start_path',
                 'unlock_level': 3,
                 'previous_quest_id': 'start_path_028_pursuit_trail',
                 'giver_npc_id': 'mercenary_head',
                 'turn_in_npc_id': 'mercenary_head',
                 'target_quantity': 1,
                 'description': 'Потрібно перевірити місцевість біля входу до печер і відшукати '
                                'останній доказ, який допоможе відновити шлях зниклого патруля.',
                 'objective_text': 'Знайти подертий клапоть плаща зниклого вартового.',
                 'reward': {'exp': 42, 'gold': 0.65},
                 'quest_item': {'item_key': 'start_path_torn_guard_cloak',
                                'display_name': 'Подертий клапоть плаща',
                                'required_quantity': 1,
                                'drop_chance': 0.15,
                                'consume_on_completion': False},
                 'retain_until_quest_id': 'start_path_030_scene_of_the_attack',
                 'navigation': {'location_id': 'start_path',
                                'giver_npc_id': 'mercenary_head',
                                'turn_in_npc_id': 'mercenary_head',
                                'objective_hint': 'Знайти подертий клапоть плаща зниклого '
                                                  'вартового.',
                                'next_step_hint': '🏙️ Місто → 📜 Гільдія Найманців → ⚔️ Голова '
                                                  'Найманців'},
                 'required_quest_items': []},
  'acceptance_text': 'Оглядай колючі кущі та каміння вздовж стежки. Тканина або шерсть допоможуть '
                     'відновити картину нападу.',
  'completion_text': 'Клапоть плаща знайдено. Тепер доказів достатньо для остаточного висновку.',
  'progress_text': '',
  'drop_message': '🧥 Сюжетна знахідка: Подертий клапоть плаща\n'
                  '\n'
                  'Темна тканина просякнута брудом. У волокнах застрягли жорсткі сірі шерстинки, а '
                  'краї розірвані гострими кігтями.'},
 {'definition': {'quest_id': 'start_path_030_scene_of_the_attack',
                 'number': 30,
                 'title': 'Картина нападу',
                 'quest_type': 'TURN_IN',
                 'location_id': 'start_path',
                 'unlock_level': 3,
                 'previous_quest_id': 'start_path_029_torn_guard_cloak',
                 'giver_npc_id': 'mercenary_head',
                 'turn_in_npc_id': 'mercenary_head',
                 'target_quantity': 1,
                 'description': 'Голова Найманців зіставляє три докази й встановлює, що патруль '
                                'переслідувала організована вовча зграя.',
                 'objective_text': 'Передати Голові Найманців перстень, пошкоджений щит і клапоть '
                                   'плаща.',
                 'reward': {'exp': 42, 'gold': 0.65},
                 'required_quest_items': [{'item_key': 'start_path_guards_ring',
                                           'quantity': 1,
                                           'consume': True},
                                          {'item_key': 'start_path_damaged_guard_shield',
                                           'quantity': 1,
                                           'consume': True},
                                          {'item_key': 'start_path_torn_guard_cloak',
                                           'quantity': 1,
                                           'consume': True}],
                 'quest_item_consumption': 'atomic_exact_once_all_or_nothing',
                 'next_chapter': {'title': 'Вовча загроза',
                                  'quest_range': [31, 40],
                                  'unlock_level': 4,
                                  'first_npc_id': 'mercenary_head'},
                 'navigation': {'location_id': 'start_path',
                                'giver_npc_id': 'mercenary_head',
                                'turn_in_npc_id': 'mercenary_head',
                                'objective_hint': 'Передати Голові Найманців перстень, пошкоджений '
                                                  'щит і клапоть плаща.',
                                'next_step_hint': '🏙️ Місто → 📜 Гільдія Найманців → ⚔️ Голова '
                                                  'Найманців'}},
  'acceptance_text': 'Перстень підтверджує, що патруль дістався печер. Подряпини на щиті залишили '
                     'великі кігті, а в плащі застрягла вовча шерсть. Це не схоже на випадковий '
                     'напад. Зграя переслідувала вартових від мосту до печер, перекриваючи їм шлях '
                     'назад. Потрібно підготувати мисливців, зміцнити спорядження та знайти лігво.',
  'completion_text': '✅ Главу «Слід зниклого патруля» завершено.\n'
                     '\n'
                     'Зібрані докази підтверджують: патруль атакувала організована вовча зграя. Її '
                     'поведінку міг змінити рунічний вплив.',
  'progress_text': '',
  'drop_message': ''})
