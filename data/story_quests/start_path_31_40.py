"""Authoritative production story content for Start Path quests 31-40.

Generated from the reviewed canonical candidate by Stage 19.26.3. Keep this module readable and preserve presentation/runtime schema separation.
"""
from __future__ import annotations

QUEST_ROWS: tuple[dict, ...] = ({'definition': {'quest_id': 'start_path_031_pack_at_the_outskirts',
                 'number': 31,
                 'title': 'Зграя на підступах',
                 'quest_type': 'TALK',
                 'location_id': 'start_path',
                 'unlock_level': 4,
                 'previous_quest_id': 'start_path_030_scene_of_the_attack',
                 'giver_npc_id': 'mercenary_head',
                 'turn_in_npc_id': 'mercenary_head',
                 'target_quantity': 1,
                 'description': 'Голова Найманців підтверджує загрозу організованої вовчої зграї '
                                'та готує першу лінію оборони.',
                 'objective_text': 'Поговорити з Головою Найманців про вовчу загрозу.',
                 'reward': {'exp': 48, 'gold': 0.89},
                 'required_quest_items': [],
                 'navigation': {'location_id': 'start_path',
                                'giver_npc_id': 'mercenary_head',
                                'turn_in_npc_id': 'mercenary_head',
                                'objective_hint': '🏙️ Місто → 📜 Гільдія Найманців → ⚔️ Голова '
                                                  'Найманців',
                                'next_step_hint': '🏙️ Місто → 📜 Гільдія Найманців → ⚔️ Голова '
                                                  'Найманців'}},
  'acceptance_text': 'Ми перевірили зібрані докази. Сумнівів більше немає: патруль переслідувала '
                     'велика вовча зграя. Звичайні вовки не діють так злагоджено. Вони не '
                     'перекривають шлях до відступу й не заганяють озброєних вартових у вузьку '
                     'ущелину без причини. Мої розвідники помітили нові сліди зовсім близько до '
                     'міських стежок. Перш ніж шукати лігво, потрібно відтіснити зграю від '
                     'околиць.',
  'completion_text': 'Голова Найманців визначає першу лінію оборони та доручає стримати істот на '
                     'підступах до міста.',
  'progress_text': 'Поговорити з Головою Найманців про вовчу загрозу.',
  'drop_message': ''},
 {'definition': {'quest_id': 'start_path_032_first_line_of_defense',
                 'number': 32,
                 'title': 'Перша лінія оборони',
                 'quest_type': 'KILL_REGION',
                 'location_id': 'start_path',
                 'unlock_level': 4,
                 'previous_quest_id': 'start_path_031_pack_at_the_outskirts',
                 'giver_npc_id': 'mercenary_head',
                 'turn_in_npc_id': 'mercenary_head',
                 'target_quantity': 10,
                 'description': 'Герой стримує істот на підступах і дає мисливцям час укріпити '
                                'табір.',
                 'objective_text': 'Перемогти 10 будь-яких істот у локації Початок Шляху.',
                 'reward': {'exp': 48, 'gold': 0.89},
                 'required_quest_items': [],
                 'navigation': {'location_id': 'start_path',
                                'giver_npc_id': 'mercenary_head',
                                'turn_in_npc_id': 'mercenary_head',
                                'objective_hint': '🏙️ Місто → 📜 Гільдія Найманців → ⚔️ Голова '
                                                  'Найманців',
                                'next_step_hint': '🏙️ Місто → 📜 Гільдія Найманців → ⚔️ Голова '
                                                  'Найманців'}},
  'acceptance_text': 'Зграя рухається вздовж стежок, але разом із вовками активізувалися й інші '
                     'істоти. Рунічний вплив міг охопити всю місцевість. Стримай загрозу на '
                     'підступах. Десяти перемог вистачить, щоб розірвати їхню лінію та дати '
                     'мисливцям час укріпити табір.',
  'completion_text': 'Напади на стежках слабшають. Під час огляду місцевості мисливці знаходять '
                     'шматки незвично щільної вовчої шерсті.',
  'progress_text': 'Перша лінія оборони: {progress}/10',
  'drop_message': ''},
 {'definition': {'quest_id': 'start_path_033_protection_for_hunters',
                 'number': 33,
                 'title': 'Захист для мисливців',
                 'quest_type': 'TALK',
                 'location_id': 'start_path',
                 'unlock_level': 4,
                 'previous_quest_id': 'start_path_032_first_line_of_defense',
                 'giver_npc_id': 'blacksmith',
                 'turn_in_npc_id': 'blacksmith',
                 'target_quantity': 1,
                 'description': 'Коваль просить знайти міцне вовче хутро для захисного спорядження '
                                'мисливців.',
                 'objective_text': 'Отримати від Коваля завдання на пошук міцного вовчого хутра.',
                 'reward': {'exp': 48, 'gold': 0.89},
                 'required_quest_items': [],
                 'navigation': {'location_id': 'start_path',
                                'giver_npc_id': 'blacksmith',
                                'turn_in_npc_id': 'blacksmith',
                                'objective_hint': '🏙️ Місто → ⚒️ Ремісничий квартал → ⚒️ Коваль',
                                'next_step_hint': '🏙️ Місто → ⚒️ Ремісничий квартал → ⚒️ Коваль'}},
  'acceptance_text': 'Подряпини на щиті вартового були надто глибокими. Якщо мисливці підуть до '
                     'лігва зі звичайними ременями та підкладкою, спорядження довго не витримає. '
                     'Мені потрібне міцне вовче хутро, щільний шматок із густим підшерстям. Я '
                     'зроблю з нього захисні накладки для рук і шиї. Проти великих кігтів це може '
                     'врятувати життя.',
  'completion_text': 'Коваль передає вимоги до матеріалу та просить принести придатний зразок.',
  'progress_text': 'Отримати від Коваля завдання на пошук міцного вовчого хутра.',
  'drop_message': ''},
 {'definition': {'quest_id': 'start_path_034_runemarked_wolf_pelt',
                 'number': 34,
                 'title': 'Хутро зі слідами рун',
                 'quest_type': 'QUEST_ITEM',
                 'location_id': 'start_path',
                 'unlock_level': 4,
                 'previous_quest_id': 'start_path_033_protection_for_hunters',
                 'giver_npc_id': 'blacksmith',
                 'turn_in_npc_id': 'blacksmith',
                 'target_quantity': 1,
                 'description': 'Герой знаходить щільне вовче хутро, змінене рунічною енергією.',
                 'objective_text': 'Знайти під час полювання придатний матеріал для захисного '
                                   'спорядження мисливців.',
                 'reward': {'exp': 48, 'gold': 0.89},
                 'quest_item': {'item_key': 'start_path_runemarked_wolf_pelt',
                                'display_name': 'Вовче хутро підвищеної якості',
                                'required_quantity': 1,
                                'drop_chance': 0.15},
                 'required_quest_items': [],
                 'navigation': {'location_id': 'start_path',
                                'giver_npc_id': 'blacksmith',
                                'turn_in_npc_id': 'blacksmith',
                                'objective_hint': '🏙️ Місто → ⚒️ Ремісничий квартал → ⚒️ Коваль',
                                'next_step_hint': '🏙️ Місто → ⚒️ Ремісничий квартал → ⚒️ Коваль'}},
  'acceptance_text': 'Шукай щільне хутро з густим підшерстям. Воно має витримати удари кігтів і '
                     'бути придатним для захисних накладок.',
  'completion_text': 'Вовче хутро підвищеної якості знайдено. Матеріал потрібно передати Ковалю.',
  'progress_text': 'Знайти під час полювання придатний матеріал для захисного спорядження '
                   'мисливців.',
  'drop_message': '🐺 Сюжетна знахідка: Вовче хутро підвищеної якості\n'
                  '\n'
                  'Хутро надзвичайно щільне, а біля коренів шерсті помітне слабке синювате '
                  'світіння. Коваль зможе використати його для спорядження мисливців.'},
 {'definition': {'quest_id': 'start_path_035_reinforce_the_hunting_party',
                 'number': 35,
                 'title': 'Посилення загону',
                 'quest_type': 'TURN_IN',
                 'location_id': 'start_path',
                 'unlock_level': 4,
                 'previous_quest_id': 'start_path_034_runemarked_wolf_pelt',
                 'giver_npc_id': 'blacksmith',
                 'turn_in_npc_id': 'blacksmith',
                 'target_quantity': 1,
                 'description': 'Коваль приймає рунічно змінене хутро та виготовляє захисні '
                                'накладки для загону.',
                 'objective_text': 'Передати Ковалю вовче хутро підвищеної якості.',
                 'reward': {'exp': 48, 'gold': 0.89},
                 'required_quest_items': [{'item_key': 'start_path_runemarked_wolf_pelt',
                                           'quantity': 1,
                                           'consume': True}],
                 'quest_item_consumption': 'atomic_exact_once',
                 'navigation': {'location_id': 'start_path',
                                'giver_npc_id': 'blacksmith',
                                'turn_in_npc_id': 'blacksmith',
                                'objective_hint': '🏙️ Місто → ⚒️ Ремісничий квартал → ⚒️ Коваль',
                                'next_step_hint': '🏙️ Місто → ⚒️ Ремісничий квартал → ⚒️ Коваль'}},
  'acceptance_text': 'Саме те, що потрібно. Поглянь на ці сині прожилки між шерстинками. Рунічна '
                     'енергія змінила не лише поведінку звірів, а й саме їхнє тіло. Я очищу '
                     'матеріал і зроблю накладки для загону. Вони не зупинять прямий удар великого '
                     'звіра, але захистять мисливців від дрібніших вовків. Поки я працюю, '
                     'повернися до Голови Найманців.',
  'completion_text': 'Коваль починає виготовляти захисні накладки для мисливського загону.',
  'progress_text': 'Передати Ковалю вовче хутро підвищеної якості.',
  'drop_message': ''},
 {'definition': {'quest_id': 'start_path_036_beyond_safe_paths',
                 'number': 36,
                 'title': 'За межею безпечних стежок',
                 'quest_type': 'KILL_REGION',
                 'location_id': 'start_path',
                 'unlock_level': 4,
                 'previous_quest_id': 'start_path_035_reinforce_the_hunting_party',
                 'giver_npc_id': 'mercenary_head',
                 'turn_in_npc_id': 'mercenary_head',
                 'target_quantity': 12,
                 'description': 'Герой проводить розвідку за кам’янистим схилом і знаходить прохід '
                                'у територію зграї.',
                 'objective_text': 'Перемогти 12 будь-яких істот у локації Початок Шляху.',
                 'reward': {'exp': 48, 'gold': 0.89},
                 'required_quest_items': [],
                 'navigation': {'location_id': 'start_path',
                                'giver_npc_id': 'mercenary_head',
                                'turn_in_npc_id': 'mercenary_head',
                                'objective_hint': '🏙️ Місто → 📜 Гільдія Найманців → ⚔️ Голова '
                                                  'Найманців',
                                'next_step_hint': '🏙️ Місто → 📜 Гільдія Найманців → ⚔️ Голова '
                                                  'Найманців'}},
  'acceptance_text': 'Коваль майже завершив спорядження. Тепер потрібно з’ясувати, звідки '
                     'приходить зграя. За кам’янистим схилом є стара мисливська стежка. Мої люди '
                     'не можуть пройти нею непомітно, тому ти підеш попереду. Очисти територію та '
                     'звертай увагу на подряпини на деревах, витоптану траву й залишки здобичі.',
  'completion_text': 'За кам’янистим схилом знайдено вузький прохід. На деревах залишилися свіжі '
                     'подряпини, а земля вкрита слідами великої зграї.',
  'progress_text': 'За межею безпечних стежок: {progress}/12',
  'drop_message': ''},
 {'definition': {'quest_id': 'start_path_037_trail_to_the_den',
                 'number': 37,
                 'title': 'Слід до лігва',
                 'quest_type': 'QUEST_ITEM',
                 'location_id': 'start_path',
                 'unlock_level': 4,
                 'previous_quest_id': 'start_path_036_beyond_safe_paths',
                 'giver_npc_id': 'mercenary_head',
                 'turn_in_npc_id': 'rune_master',
                 'target_quantity': 1,
                 'description': 'Герой знаходить фізичний доказ із району лігва, насичений '
                                'рунічною енергією.',
                 'objective_text': 'Знайти під час полювання доказ, який указує на шлях до вовчого '
                                   'лігва.',
                 'reward': {'exp': 48, 'gold': 0.89},
                 'quest_item': {'item_key': 'start_path_runemarked_den_token',
                                'display_name': 'Рунічно позначений уламок із лігва',
                                'required_quantity': 1,
                                'drop_chance': 0.15},
                 'required_quest_items': [],
                 'navigation': {'location_id': 'start_path',
                                'giver_npc_id': 'mercenary_head',
                                'turn_in_npc_id': 'rune_master',
                                'objective_hint': '🏙️ Місто → 📜 Гільдія Найманців → ⚔️ Голова '
                                                  'Найманців',
                                'next_step_hint': '🏙️ Місто → ⚒️ Ремісничий квартал → 💠 Рунний '
                                                  'Майстер'}},
  'acceptance_text': 'Оглядай вузький прохід, каміння й місця, де зграя залишала здобич. Нам '
                     'потрібен доказ, який можна показати Рунному Майстру.',
  'completion_text': 'Рунічно позначений уламок знайдено. Його потрібно передати Рунному Майстру.',
  'progress_text': 'Знайти під час полювання доказ, який указує на шлях до вовчого лігва.',
  'drop_message': '🪨 Сюжетна знахідка: Рунічно позначений уламок із лігва\n'
                  '\n'
                  'Темний камінь укритий вовчою шерстю та глибокими слідами кігтів. Усередині '
                  'тріщин пульсує знайоме синювате світіння.'},
 {'definition': {'quest_id': 'start_path_038_heart_of_the_influence',
                 'number': 38,
                 'title': 'Серце впливу',
                 'quest_type': 'TURN_IN',
                 'location_id': 'start_path',
                 'unlock_level': 4,
                 'previous_quest_id': 'start_path_037_trail_to_the_den',
                 'giver_npc_id': 'rune_master',
                 'turn_in_npc_id': 'rune_master',
                 'target_quantity': 1,
                 'description': 'Рунний Майстер досліджує уламок і підтверджує, що лігво є центром '
                                'рунічного впливу.',
                 'objective_text': 'Передати Рунному Майстру рунічно позначений уламок.',
                 'reward': {'exp': 48, 'gold': 0.89},
                 'required_quest_items': [{'item_key': 'start_path_runemarked_den_token',
                                           'quantity': 1,
                                           'consume': True}],
                 'quest_item_consumption': 'atomic_exact_once',
                 'navigation': {'location_id': 'start_path',
                                'giver_npc_id': 'rune_master',
                                'turn_in_npc_id': 'rune_master',
                                'objective_hint': '🏙️ Місто → ⚒️ Ремісничий квартал → 💠 Рунний '
                                                  'Майстер',
                                'next_step_hint': '🏙️ Місто → ⚒️ Ремісничий квартал → 💠 Рунний '
                                                  'Майстер'}},
  'acceptance_text': 'Цей камінь не з поверхні. Такі породи трапляються лише в глибоких печерах '
                     'під старим схилом. Рунічний відбиток значно сильніший, ніж на попередніх '
                     'зразках. Енергія проходила крізь нього багато разів. Сліди кігтів також '
                     'незвичайні. Великий звір постійно торкався цього уламка або лежав поруч із '
                     'ним. Лігво і є центром впливу, а ватажок зграї, найімовірніше, став головним '
                     'носієм аномалії.',
  'completion_text': 'Рунний Майстер підтверджує, що джерело найсильнішого рунічного впливу '
                     'розташоване у вовчому лігві.',
  'progress_text': 'Передати Рунному Майстру рунічно позначений уламок.',
  'drop_message': ''},
 {'definition': {'quest_id': 'start_path_039_road_to_the_den',
                 'number': 39,
                 'title': 'Дорога до лігва',
                 'quest_type': 'KILL_REGION',
                 'location_id': 'start_path',
                 'unlock_level': 4,
                 'previous_quest_id': 'start_path_038_heart_of_the_influence',
                 'giver_npc_id': 'mercenary_head',
                 'turn_in_npc_id': 'mercenary_head',
                 'target_quantity': 12,
                 'description': 'Герой розчищає вузький прохід до лігва, щоб мисливці могли '
                                'зайняти позиції.',
                 'objective_text': 'Перемогти 12 будь-яких істот у локації Початок Шляху.',
                 'reward': {'exp': 48, 'gold': 0.89},
                 'required_quest_items': [],
                 'navigation': {'location_id': 'start_path',
                                'giver_npc_id': 'mercenary_head',
                                'turn_in_npc_id': 'mercenary_head',
                                'objective_hint': '🏙️ Місто → 📜 Гільдія Найманців → ⚔️ Голова '
                                                  'Найманців',
                                'next_step_hint': '🏙️ Місто → 📜 Гільдія Найманців → ⚔️ Голова '
                                                  'Найманців'}},
  'acceptance_text': 'Рунний Майстер підтвердив місце. Лігво розташоване за вузьким проходом під '
                     'кам’янистим схилом. Зграя стягнула туди майже всіх сильних звірів. Якщо ми '
                     'поведемо загін зараз, нас затиснуть у проході. Розчисти дорогу до лігва.',
  'completion_text': 'Прохід до лігва очищено. Мисливці закріплюються біля входу та чекають '
                     'рішення Старости.',
  'progress_text': 'Дорога до лігва: {progress}/12',
  'drop_message': ''},
 {'definition': {'quest_id': 'start_path_040_before_the_final_hunt',
                 'number': 40,
                 'title': 'Перед вирішальним походом',
                 'quest_type': 'TURN_IN',
                 'location_id': 'start_path',
                 'unlock_level': 4,
                 'previous_quest_id': 'start_path_039_road_to_the_den',
                 'giver_npc_id': 'elder',
                 'turn_in_npc_id': 'elder',
                 'target_quantity': 1,
                 'description': 'Герой доповідає Старості про відкритий шлях до лігва й завершує '
                                'підготовчий розділ.',
                 'objective_text': 'Доповісти Старості, що шлях до вовчого лігва відкрито.',
                 'reward': {'exp': 48, 'gold': 0.89},
                 'next_chapter': {'title': 'Ватажок зграї',
                                  'quest_range': [41, 50],
                                  'unlock_level': 5,
                                  'first_npc_id': 'elder'},
                 'required_quest_items': [],
                 'navigation': {'location_id': 'start_path',
                                'giver_npc_id': 'elder',
                                'turn_in_npc_id': 'elder',
                                'objective_hint': '🏙️ Місто → 🏛️ Ратуша → 🗣️ Староста',
                                'next_step_hint': '🏙️ Місто → 🏛️ Ратуша → 🗣️ Староста'}},
  'acceptance_text': 'Отже, лігво знайдено, шлях очищено, а мисливці готові. Ми втратили патруль, '
                     'бо не знали, з чим маємо справу. Цього разу загін виступить підготовленим. '
                     'Але нападати негайно не можна. Голова Найманців має розставити людей, Коваль '
                     'завершити спорядження, а Рунний Майстер підготувати захист від рунічного '
                     'впливу. Я скличу раду. Після неї почнеться останній етап походу.',
  'completion_text': '✅ Розділ «Вовча загроза» завершено.\n'
                     '\n'
                     'Лігво знайдено, мисливський загін підготовлено, а джерело рунічного впливу '
                     'пов’язано з Ватажком зграї.',
  'progress_text': 'Доповісти Старості, що шлях до вовчого лігва відкрито.',
  'drop_message': ''})
