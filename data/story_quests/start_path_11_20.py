#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Stage 19.34.5 normalized production pack.
QUEST_ROWS = ({'definition': {'quest_id': 'start_path_011_unstable_glow',
                 'number': 11,
                 'title': 'Неспокійне світіння',
                 'quest_type': 'TALK',
                 'location_id': 'start_path',
                 'unlock_level': 2,
                 'previous_quest_id': 'start_path_010_investigation_begins',
                 'giver_npc_id': 'rune_master',
                 'turn_in_npc_id': 'rune_master',
                 'description': 'Поговорити з Рунним Майстром про рунічне світіння, помічене на '
                                'старих стежках біля маршруту зниклого патруля.',
                 'objective_text': 'Поговорити з Рунним Майстром про аномальне світіння.',
                 'target_quantity': 1,
                 'boss_key': None,
                 'quest_item': None,
                 'required_quest_items': [],
                 'quest_item_consumption': 'default',
                 'reward': {'exp': 36, 'gold': 0.43, 'item_keys': []},
                 'navigation': {'location_id': 'start_path',
                                'giver_npc_id': 'rune_master',
                                'turn_in_npc_id': 'rune_master',
                                'objective_hint': 'Поговорити з Рунним Майстром про аномальне '
                                                  'світіння.',
                                'next_step_hint': '🏙️ Місто → ⚒️ Ремісничий квартал → 💠 Рунний '
                                                  'Майстер'}},
  'acceptance_text': 'Староста розповів про сліди патруля біля печер. Це збігається з іншими '
                     'повідомленнями. На старих стежках з’явилося слабке рунічне світіння. '
                     'Спочатку воно було помітне лише на рослинах, але тепер світяться каміння, '
                     'слиз і навіть сліди деяких істот. Потрібно визначити, наскільки далеко '
                     'поширилася аномалія. Почни з місцевості навколо рунічних плям.',
  'completion_text': 'Рунний Майстер позначає на карті кілька місць, де рунічне світіння '
                     'проявляється найсильніше.',
  'progress_text': '',
  'drop_message': ''},
 {'definition': {'quest_id': 'start_path_012_anomaly_sites',
                 'number': 12,
                 'title': 'Осередки аномалії',
                 'quest_type': 'KILL_REGION',
                 'location_id': 'start_path',
                 'unlock_level': 2,
                 'previous_quest_id': 'start_path_011_unstable_glow',
                 'giver_npc_id': 'rune_master',
                 'turn_in_npc_id': 'rune_master',
                 'description': 'Рунний Майстер просить перевірити позначені осередки аномалії та '
                                'стримати істот, які збираються біля рунічних плям.',
                 'objective_text': 'Перемогти 8 будь-яких істот у локації Початок Шляху.',
                 'target_quantity': 8,
                 'boss_key': None,
                 'quest_item': None,
                 'required_quest_items': [],
                 'quest_item_consumption': 'default',
                 'reward': {'exp': 36, 'gold': 0.43, 'item_keys': []},
                 'navigation': {'location_id': 'start_path',
                                'giver_npc_id': 'rune_master',
                                'turn_in_npc_id': 'rune_master',
                                'objective_hint': 'Перемогти 8 будь-яких істот у локації Початок '
                                                  'Шляху.',
                                'next_step_hint': '🏙️ Місто → ⚒️ Ремісничий квартал → 💠 Рунний '
                                                  'Майстер'},
                 'acceptance_text': None,
                 'completion_text': None},
  'acceptance_text': 'Рунічне світіння накопичується там, де часто проходять істоти. Я не знаю, чи '
                     'вони розносять аномалію, чи лише реагують на неї. Перевір позначені ділянки '
                     'та стримай істот навколо них. Після кількох сутичок стане зрозуміло, чи '
                     'залишаються на місці придатні для дослідження сліди.',
  'completion_text': 'Після боїв світіння на землі слабшає, але серед каміння залишається гострий '
                     'уламок, що пульсує блідим світлом.',
  'progress_text': 'Осередки аномалії: {progress}/8',
  'drop_message': ''},
 {'definition': {'quest_id': 'start_path_013_runic_crystal_fragment',
                 'number': 13,
                 'title': 'Уламок аномалії',
                 'quest_type': 'QUEST_ITEM',
                 'location_id': 'start_path',
                 'unlock_level': 2,
                 'previous_quest_id': 'start_path_012_anomaly_sites',
                 'giver_npc_id': 'rune_master',
                 'turn_in_npc_id': 'rune_master',
                 'description': 'Рунний Майстер просить продовжити пошуки біля ослаблених рунічних '
                                'плям і знайти матеріальний слід аномалії.',
                 'objective_text': 'Шукати під час полювання нестабільний матеріальний слід '
                                   'рунічної аномалії.',
                 'target_quantity': 1,
                 'boss_key': None,
                 'quest_item': {'item_key': 'start_path_runic_crystal_fragment',
                                'display_name': 'Уламок рунічного кристала',
                                'required_quantity': 1,
                                'drop_chance': 0.15,
                                'consume_on_completion': False},
                 'required_quest_items': [],
                 'quest_item_consumption': 'default',
                 'reward': {'exp': 36, 'gold': 0.43, 'item_keys': []},
                 'navigation': {'location_id': 'start_path',
                                'giver_npc_id': 'rune_master',
                                'turn_in_npc_id': 'rune_master',
                                'objective_hint': 'Шукати під час полювання нестабільний '
                                                  'матеріальний слід рунічної аномалії.',
                                'next_step_hint': '🏙️ Місто → ⚒️ Ремісничий квартал → 💠 Рунний '
                                                  'Майстер'}},
  'acceptance_text': 'Після сутичок світіння слабшає, але частина енергії могла залишитися в '
                     'камінні чи уламках навколо осередків. Обшукай місцевість під час полювання. '
                     'Не торкайся підозрілих знахідок голими руками й принеси звістку про '
                     'будь-який матеріальний слід аномалії.',
  'completion_text': 'Рунний Майстер оглядає знайдений уламок і радить передати його Алхіміку в '
                     'захисному контейнері для безпечного дослідження.',
  'progress_text': '',
  'drop_message': '💠 Сюжетна знахідка: Уламок рунічного кристала\n'
                  '\n'
                  'Кристал випромінює слабке пульсуюче світло, а його поверхня вкрита дрібними '
                  'тріщинами. Про знахідку потрібно доповісти Рунному Майстру.'},
 {'definition': {'quest_id': 'start_path_014_crystal_under_glass',
                 'number': 14,
                 'title': 'Кристал під склом',
                 'quest_type': 'TURN_IN',
                 'location_id': 'start_path',
                 'unlock_level': 2,
                 'previous_quest_id': 'start_path_013_runic_crystal_fragment',
                 'giver_npc_id': 'alchemist',
                 'turn_in_npc_id': 'alchemist',
                 'description': 'Показати Алхіміку знайдений уламок рунічного кристала та передати '
                                'його для безпечного дослідження.',
                 'objective_text': 'Передати Алхіміку уламок рунічного кристала.',
                 'target_quantity': 1,
                 'boss_key': None,
                 'quest_item': None,
                 'required_quest_items': [{'item_key': 'start_path_runic_crystal_fragment',
                                           'quantity': 1,
                                           'consume': True}],
                 'quest_item_consumption': 'default',
                 'reward': {'exp': 36, 'gold': 0.43, 'item_keys': []},
                 'navigation': {'location_id': 'start_path',
                                'giver_npc_id': 'alchemist',
                                'turn_in_npc_id': 'alchemist',
                                'objective_hint': 'Передати Алхіміку уламок рунічного кристала.',
                                'next_step_hint': '🏙️ Місто → ⚒️ Ремісничий квартал → 🧪 Алхімік'}},
  'acceptance_text': 'Обережніше. Поклади уламок у цей контейнер. Кристал не схожий на природне '
                     'рунічне утворення. У ньому є домішки крові, рослинного соку та дрібного '
                     'кам’яного пилу. Енергія ніби проходила крізь живу істоту, а потім '
                     'затверділа. Одного зразка недостатньо. Мені потрібен рунічний пил із тієї '
                     'самої місцевості. Він покаже, чи аномалія виникла природно, чи її хтось '
                     'поширює.',
  'completion_text': 'Алхімік ізолює уламок у захисному контейнері та просить знайти пробу '
                     'рунічного пилу.',
  'progress_text': '',
  'drop_message': ''},
 {'definition': {'quest_id': 'start_path_015_runic_dust_sample',
                 'number': 15,
                 'title': 'Рунічний пил',
                 'quest_type': 'QUEST_ITEM',
                 'location_id': 'start_path',
                 'unlock_level': 2,
                 'previous_quest_id': 'start_path_014_crystal_under_glass',
                 'giver_npc_id': 'alchemist',
                 'turn_in_npc_id': 'alchemist',
                 'description': 'Алхімік просить знайти біля рунічних осередків другий зразок, '
                                'який можна порівняти з уламком кристала.',
                 'objective_text': 'Шукати під час полювання пробу рунічного пилу біля осередків '
                                   'аномалії.',
                 'target_quantity': 1,
                 'boss_key': None,
                 'quest_item': {'item_key': 'start_path_runic_dust_sample',
                                'display_name': 'Проба рунічного пилу',
                                'required_quantity': 1,
                                'drop_chance': 0.15,
                                'consume_on_completion': False},
                 'required_quest_items': [],
                 'quest_item_consumption': 'default',
                 'reward': {'exp': 36, 'gold': 0.43, 'item_keys': []},
                 'navigation': {'location_id': 'start_path',
                                'giver_npc_id': 'alchemist',
                                'turn_in_npc_id': 'alchemist',
                                'objective_hint': 'Шукати під час полювання пробу рунічного пилу '
                                                  'біля осередків аномалії.',
                                'next_step_hint': '🏙️ Місто → ⚒️ Ремісничий квартал → 🧪 Алхімік'}},
  'acceptance_text': 'Шукай місця, де світіння осідає на камінні або шерсті істот. Пил може бути '
                     'майже непомітним, але в темряві він відбиває синювате світло. Не торкайся '
                     'його голими руками. Збери пробу в цю посудину.',
  'completion_text': 'Алхімік готує захисну камеру для порівняння проби пилу з раніше переданим '
                     'уламком і просить передати посудину, не відкриваючи її.',
  'progress_text': '',
  'drop_message': '✨ Сюжетна знахідка: Проба рунічного пилу\n'
                  '\n'
                  'На дні посудини мерехтить дрібний синюватий пил. Світіння стає яскравішим біля '
                  'залишків рунічної енергії. Про зібрану пробу потрібно повідомити Алхіміку.'},
 {'definition': {'quest_id': 'start_path_016_unnatural_trace',
                 'number': 16,
                 'title': 'Неприродний слід',
                 'quest_type': 'TURN_IN',
                 'location_id': 'start_path',
                 'unlock_level': 2,
                 'previous_quest_id': 'start_path_015_runic_dust_sample',
                 'giver_npc_id': 'alchemist',
                 'turn_in_npc_id': 'alchemist',
                 'description': 'Передати Алхіміку запечатану пробу рунічного пилу та отримати '
                                'результати порівняння з уламком кристала.',
                 'objective_text': 'Передати Алхіміку пробу рунічного пилу та отримати результати '
                                   'дослідження.',
                 'target_quantity': 1,
                 'boss_key': None,
                 'quest_item': None,
                 'required_quest_items': [{'item_key': 'start_path_runic_dust_sample',
                                           'quantity': 1,
                                           'consume': True}],
                 'quest_item_consumption': 'default',
                 'reward': {'exp': 36, 'gold': 0.43, 'item_keys': []},
                 'navigation': {'location_id': 'start_path',
                                'giver_npc_id': 'alchemist',
                                'turn_in_npc_id': 'alchemist',
                                'objective_hint': 'Передати Алхіміку пробу рунічного пилу та '
                                                  'отримати результати дослідження.',
                                'next_step_hint': '🏙️ Місто → ⚒️ Ремісничий квартал → 🧪 Алхімік'}},
  'acceptance_text': 'Постав посудину в захисну камеру. Я порівняю пил із уламком, який ти передав '
                     'раніше. Світіння обох зразків збігається в одному ритмі. Це не випадкове '
                     'накопичення енергії. Хтось або щось розносить один і той самий рунічний '
                     'вплив різними ділянками околиць. Найсильніше забруднення видно на органічних '
                     'рештках. Істоти не просто проходять крізь аномалію. Вона змінює їх і робить '
                     'агресивнішими. Передай висновок Рунному Майстру.',
  'completion_text': 'Алхімік підтверджує спільне неприродне походження уламка й пилу та передає '
                     'висновок для Рунного Майстра.',
  'progress_text': '',
  'drop_message': ''},
 {'definition': {'quest_id': 'start_path_017_tainted_paths',
                 'number': 17,
                 'title': 'Заражені стежки',
                 'quest_type': 'KILL_REGION',
                 'location_id': 'start_path',
                 'unlock_level': 2,
                 'previous_quest_id': 'start_path_016_unnatural_trace',
                 'giver_npc_id': 'rune_master',
                 'turn_in_npc_id': 'rune_master',
                 'description': 'Рунний Майстер просить очистити стежки біля найяскравіших '
                                'рунічних плям і стримати поширення впливу через заражених істот.',
                 'objective_text': 'Перемогти 10 будь-яких істот у локації Початок Шляху.',
                 'target_quantity': 10,
                 'boss_key': None,
                 'quest_item': None,
                 'required_quest_items': [],
                 'quest_item_consumption': 'default',
                 'reward': {'exp': 36, 'gold': 0.43, 'item_keys': []},
                 'navigation': {'location_id': 'start_path',
                                'giver_npc_id': 'rune_master',
                                'turn_in_npc_id': 'rune_master',
                                'objective_hint': 'Перемогти 10 будь-яких істот у локації Початок '
                                                  'Шляху.',
                                'next_step_hint': '🏙️ Місто → ⚒️ Ремісничий квартал → 💠 Рунний '
                                                  'Майстер'},
                 'acceptance_text': None,
                 'completion_text': None},
  'acceptance_text': 'Висновок Алхіміка підтверджує мої побоювання. Рунічний вплив переходить від '
                     'одного носія до іншого, а заражені істоти розносять його далі. Повністю '
                     'знищити аномалію ми поки не можемо, але здатні стримати її поширення. Очисти '
                     'стежки навколо найяскравіших плям.',
  'completion_text': 'Кількість заражених істот зменшилася, але із заходом сонця рунічне світіння '
                     'починає посилюватися.',
  'progress_text': 'Заражені стежки: {progress}/10',
  'drop_message': ''},
 {'definition': {'quest_id': 'start_path_018_glow_after_sunset',
                 'number': 18,
                 'title': 'Світло після заходу',
                 'quest_type': 'TALK',
                 'location_id': 'start_path',
                 'unlock_level': 2,
                 'previous_quest_id': 'start_path_017_tainted_paths',
                 'giver_npc_id': 'rune_master',
                 'turn_in_npc_id': 'rune_master',
                 'description': 'Поговорити з Рунним Майстром про нічні зміни аномалії та '
                                'перевірити, чи перетинається її карта з маршрутом зниклого '
                                'патруля.',
                 'objective_text': 'Отримати від Рунного Майстра результати спостережень за '
                                   'аномалією.',
                 'target_quantity': 1,
                 'boss_key': None,
                 'quest_item': None,
                 'required_quest_items': [],
                 'quest_item_consumption': 'default',
                 'reward': {'exp': 36, 'gold': 0.43, 'item_keys': []},
                 'navigation': {'location_id': 'start_path',
                                'giver_npc_id': 'rune_master',
                                'turn_in_npc_id': 'rune_master',
                                'objective_hint': 'Отримати від Рунного Майстра результати '
                                                  'спостережень за аномалією.',
                                'next_step_hint': '🏙️ Місто → ⚒️ Ремісничий квартал → 💠 Рунний '
                                                  'Майстер'}},
  'acceptance_text': 'Ти стримав поширення, але аномалія не зникла. Уночі рунічні плями світяться '
                     'сильніше, наче отримують енергію з іншого джерела. Я порівняв карту світіння '
                     'з маршрутом зниклого патруля. Вартові проходили просто через одну з '
                     'найактивніших ділянок. Пошукай там сліди їхньої присутності.',
  'completion_text': 'На карті позначено ділянку, де маршрут патруля перетинається з найсильнішим '
                     'осередком рунічної енергії.',
  'progress_text': '',
  'drop_message': ''},
 {'definition': {'quest_id': 'start_path_019_guards_note',
                 'number': 19,
                 'title': 'Записка при світлі рун',
                 'quest_type': 'QUEST_ITEM',
                 'location_id': 'start_path',
                 'unlock_level': 2,
                 'previous_quest_id': 'start_path_018_glow_after_sunset',
                 'giver_npc_id': 'rune_master',
                 'turn_in_npc_id': 'rune_master',
                 'description': 'Рунний Майстер просить обшукати ділянку, де маршрут патруля '
                                'перетинається з найсильнішим рунічним осередком.',
                 'objective_text': 'Шукати під час полювання сліди зниклого патруля біля '
                                   'найсильнішого рунічного осередку.',
                 'target_quantity': 1,
                 'boss_key': None,
                 'quest_item': {'item_key': 'start_path_guard_note',
                                'display_name': 'Записка вартового',
                                'required_quantity': 1,
                                'drop_chance': 0.15,
                                'consume_on_completion': False},
                 'required_quest_items': [],
                 'quest_item_consumption': 'default',
                 'reward': {'exp': 36, 'gold': 0.43, 'item_keys': []},
                 'navigation': {'location_id': 'start_path',
                                'giver_npc_id': 'rune_master',
                                'turn_in_npc_id': 'rune_master',
                                'objective_hint': 'Шукати під час полювання сліди зниклого патруля '
                                                  'біля найсильнішого рунічного осередку.',
                                'next_step_hint': '🏙️ Місто → ⚒️ Ремісничий квартал → 💠 Рунний '
                                                  'Майстер'}},
  'acceptance_text': 'На цій ділянці світіння посилюється після заходу сонця, а маршрут патруля '
                     'проходить просто через осередок. Обшукай землю, каміння та покинуті речі. '
                     'Шукай будь-який слід, який підтвердить, що вартові дісталися сюди.',
  'completion_text': 'Рунний Майстер упізнає позначки міської варти на знайденій записці й просить '
                     'негайно передати її Старості.',
  'progress_text': '',
  'drop_message': '📜 Сюжетна знахідка: Записка вартового\n'
                  '\n'
                  'Частина тексту розмита, але окремі рядки ще можна прочитати: «Світіння веде до '
                  'мосту… істоти поводяться неприродно… ми продовжимо пошук до печер…» Про '
                  'знахідку потрібно доповісти Рунному Майстру.'},
 {'definition': {'quest_id': 'start_path_020_patrol_knew',
                 'number': 20,
                 'title': 'Патруль знав',
                 'quest_type': 'TURN_IN',
                 'location_id': 'start_path',
                 'unlock_level': 2,
                 'previous_quest_id': 'start_path_019_guards_note',
                 'giver_npc_id': 'elder',
                 'turn_in_npc_id': 'elder',
                 'description': 'Показати Старості записку зниклого вартового й передати її як '
                                'доказ того, що патруль самостійно розслідував аномалію.',
                 'objective_text': 'Передати Старості записку зниклого вартового.',
                 'target_quantity': 1,
                 'boss_key': None,
                 'quest_item': None,
                 'required_quest_items': [{'item_key': 'start_path_guard_note',
                                           'quantity': 1,
                                           'consume': True}],
                 'quest_item_consumption': 'default',
                 'reward': {'exp': 36, 'gold': 0.43, 'item_keys': []},
                 'navigation': {'location_id': 'start_path',
                                'giver_npc_id': 'elder',
                                'turn_in_npc_id': 'elder',
                                'objective_hint': 'Передати Старості записку зниклого вартового.',
                                'next_step_hint': '🏙️ Місто → 🏛️ Ратуша → 🗣️ Староста'}},
  'acceptance_text': 'Це почерк одного зі зниклих вартових. Патруль помітив рунічне світіння ще до '
                     'того, як про нього почали говорити в таборі. У записці сказано, що істоти '
                     'ставали агресивнішими ближче до старого мосту. Вартові вирішили простежити '
                     'за ними до печер, але не встигли повернутися. Тепер ми знаємо, що патруль не '
                     'заблукав. Вони проводили власне розслідування і натрапили на щось '
                     'небезпечне.',
  'completion_text': '✅ Розділ «Рунічна аномалія» завершено.\n'
                     '\n'
                     'Патруль розслідував неприродну агресію істот і вирушив до печер. Наступний '
                     'етап пошуку очолить Голова Найманців.',
  'progress_text': '',
  'drop_message': ''})
