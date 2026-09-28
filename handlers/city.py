from telebot import types
from data.locations import LOCATIONS
from data.mobs import get_mobs_for_location
from db import EQUIPMENT_SLOTS, get_current_location, get_player_stats, get_current_hp, get_max_hp, get_user_energy, get_inventory_used_slots, get_bag_capacity, get_contract_status, sell_all_trash, buy_item_for_gold, get_equipped_items_for_repair, get_total_repair_cost, repair_all_equipped, repair_equipped_item, get_wallet, format_gold, get_common_equipment_shop_offer, get_common_equipment_shop_suboffers, create_common_equipment_shop_preview, get_shop_preview_item, get_shop_preview_weapon_damage_text, confirm_common_equipment_shop_preview, cancel_common_equipment_shop_preview, get_sellable_equipment_items, sell_inventory_item_to_trader, get_item_by_inventory_id_full, get_armor_type_label, get_item_subtype_label, is_armor_slot, process_passive_regeneration
from keyboards import city_kb, trader_kb, craft_kb, guild_kb, townhall_kb, tavern_kb, alchemist_kb, blacksmith_kb, main_kb
from systems.potion_system import POTIONS, ALCHEMIST_SHOP, get_alchemist_potion_stock_17_19_3, buy_alchemist_potion_17_19_3, sell_alchemist_potion_17_19_3


def _format_registration_date_kyiv_18_31_4a(value):
    """Render canonical UTC registration time in Europe/Kyiv."""
    from datetime import datetime, timezone
    from zoneinfo import ZoneInfo
    raw = str(value or "").strip()
    if not raw or raw == "не зафіксована":
        return "не зафіксована"
    moment = None
    try:
        moment = datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except Exception:
        try:
            moment = datetime.strptime(raw.removesuffix(" UTC"), "%d.%m.%Y %H:%M")
            moment = moment.replace(tzinfo=timezone.utc)
        except Exception:
            return "не зафіксована"
    if moment.tzinfo is None:
        moment = moment.replace(tzinfo=timezone.utc)
    return moment.astimezone(ZoneInfo("Europe/Kyiv")).strftime("%d.%m.%Y %H:%M за Києвом")
SELL_EQUIPMENT_ITEMS_PER_PAGE = 10
TRADE_DISTRICT_BACK_BUTTON_17_11_1 = '🔙 Торговий ряд'
TRADE_DISTRICT_CITY_BUTTON_17_11_1 = '⬅️ Місто'

def build_city_text(user_id):
    location_id = get_current_location(user_id)
    location = LOCATIONS.get(location_id, LOCATIONS['start_path'])
    return f"🏙️ Місто\n\n📍 Регіон:\n{location['name']}\n\nТи стоїш на центральній площі табору мандрівників. Навколо чути дзвін ковадла, запах трав від лавки алхіміка та гомін найманців біля дошки контрактів.\n\nКуди підеш?\n\n• 🛒 Торговий ряд — купівля та продаж\n• ⚒️ Ремісничий квартал — коваль і алхімік\n• 📜 Гільдія Найманців — щоденні контракти\n• 🏛️ Ратуша — щоденні й майбутні міські доручення\n• 🍺 Таверна — відпочинок і чутки"

def build_trade_district_text(user_id):
    gold = get_wallet(user_id)
    return f'🛒 Торговий ряд\n\n💰 Золото: {float(gold):.2f}\n\nВузька вулиця заставлена возами, ящиками та прилавками. Торговці скуповують сірий лут, непотрібне спорядження і продають прості речі для мандрівників.'

def build_craft_district_text(user_id):
    gold = get_wallet(user_id)
    return f'⚒️ Ремісничий квартал\n\n💰 Золото: {float(gold):.2f}\n\nТут пахне вугіллям, розпеченим металом і настоями трав. Коваль лагодить спорядження, а алхімік продає зілля для тих, хто збирається повернутися на полювання.\n\nДоступні місця:\n• ⚒️ Коваль — ремонт спорядження\n• 🧪 Алхімік — купівля зілля'

def build_guild_district_text(user_id):
    status = get_contract_status(user_id)
    text = f'📜 Гільдія Найманців\n\nНа старій дошці висять замовлення від варти, торговців і мандрівників. Тут беруть роботу ті, хто не боїться вийти за межі табору.\n\n'
    if not status['exists']:
        text += '❌ Персонажа не знайдено.'
        return text
    if not status['unlocked']:
        text += f"🔒 Контракти відкриються з 5 рівня.\n👤 Твій рівень: {status['level']}\n"
        return text
    text += f"📆 Сьогодні здано контрактів: {status['completed_today']}/{status['daily_limit']}\n"
    active = status['active_contract']
    if active:
        if active.get('completed'):
            text += f"\n✅ Виконаний контракт очікує здачі:\n🎯 Ціль: {active['target_mob_name']}\n📈 Прогрес: {active['current_kills']}/{active['target_kills']}\n✨ Нагорода: {active['reward_exp']} EXP\n\nЗайди до дошки контрактів, щоб здати його."
        else:
            text += f"\n📌 Активний контракт:\n🎯 Ціль: {active['target_mob_name']}\n📈 Прогрес: {active['current_kills']}/{active['target_kills']}\n✨ Нагорода після здачі: {active['reward_exp']} EXP\n"
    else:
        text += '\n✅ Можна переглянути дошку контрактів.'
    return text

def build_townhall_text():
    return f'🏛️ Ратуша\n\nУсередині тихо. На стінах висять старі карти околиць, а за великим столом лежать списки податків, звіти варти та прохання мешканців.\n\nТут можна отримати щоденне завдання від місцевих жителів.\n\nДоступні дії:\n• 📆 Щоденне завдання'

def build_tavern_text():
    return f'🍺 Таверна\n\nУсередині тепло, пахне юшкою, свіжим хлібом і димом від каміна. Мандрівники обмінюються чутками про небезпечних істот, елітних ворогів і старі руїни за межами табору.\n\nПоки що тут можна відпочити від подорожей і послухати розмови мандрівників.\n\nℹ️ Пізніше тут можна буде додати:\n• 🛏️ Відпочинок для прискорення відновлення HP\n• 🍲 Їжу з тимчасовими бонусами\n• 🗣️ Чутки про елітних мобів або босів'

def get_nearby_mobs_for_level(player_level, location_id):
    mobs = get_mobs_for_location(location_id)
    available = []
    for mob in mobs:
        mob_level = int(mob.get('level', 1))
        min_player_level = int(mob.get('min_player_level', 1))
        if min_player_level <= player_level and player_level - 1 <= mob_level <= player_level + 1:
            available.append(mob)
    if not available:
        for mob in mobs:
            if int(mob.get('min_player_level', 1)) <= player_level:
                available.append(mob)
    return available

def build_contracts_short_status(user_id):
    status = get_contract_status(user_id)
    if not status['exists']:
        return '📜 Контракти: недоступно\n'
    if not status['unlocked']:
        return '📜 Контракти: 🔒 з 5 рівня\n'
    completed = status['completed_today']
    daily_limit = status['daily_limit']
    active = status['active_contract']
    text = f'📜 Контракти: {completed}/{daily_limit}\n'
    if active:
        if active.get('completed'):
            text += f"✅ Контракт виконано: {active['target_mob_name']} {active['current_kills']}/{active['target_kills']} — здати в Гільдії\n"
        else:
            text += f"📌 Активний контракт: {active['target_mob_name']} {active['current_kills']}/{active['target_kills']}\n"
    return text

def build_main_menu_text(user_id):
    process_passive_regeneration(user_id)
    location_id = get_current_location(user_id)
    location = LOCATIONS.get(location_id, LOCATIONS['start_path'])
    stats = get_player_stats(user_id)
    if stats:
        _, _, _, _, _, lvl = stats
    else:
        lvl = 1
    current_hp = get_current_hp(user_id)
    max_hp = get_max_hp(user_id)
    energy_data = get_user_energy(user_id)
    energy = energy_data['energy']
    max_energy = energy_data['max_energy']
    used_slots = get_inventory_used_slots(user_id)
    capacity = get_bag_capacity(user_id)
    contracts_text = build_contracts_short_status(user_id)
    nearby_mobs = get_nearby_mobs_for_level(lvl, location_id)
    mobs_text = ''
    if nearby_mobs:
        for mob in nearby_mobs:
            attack_icon = '⚔️' if mob.get('attack_type') == 'physical' else '🔮'
            mobs_text += f"• {attack_icon} {mob['name']} — рівень {mob['level']}\n"
    else:
        mobs_text = '• Навколо поки тихо...\n'
    text = f"🏕️ Табір мандрівників\n\n📍 Поточна зона:\n{location['name']}\n\n📖 {location['description']}\n\nПід ногами волога земля, поруч потріскує багаття, а за межами табору вже чути рух диких звірів. Тут шукачі пригод готуються до наступного полювання.\n\n👤 Твій рівень: {lvl}\n❤️ Здоров’я: {current_hp}/{max_hp}\n😴 Втома: {energy}/{max_energy}\n🎒 Сумка: {used_slots}/{capacity}\n{contracts_text}\n👀 Поблизу твого рівня можна зустріти:\n{mobs_text}\nДоступні дії:\n🔎 Полювання — вийти за межі табору\n🗺️ Мапа — переглянути напрямки та місто\n👤 Профіль — персонаж, інвентар і спорядження\n👀 Роззирнутися — оновити стан персонажа"
    return text
_ALCHEMIST_INPUT_17_19_3 = {}

def alchemist_reply_kb_17_19_3_1():
    """Persistent Alchemist navigation: two actions in one row, return below."""
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    kb.row('🛒 Купити зілля', '💰 Продати зілля')
    kb.row('🔙 Ремісничий квартал')
    return kb

def build_alchemist_root_17_19_3(user_id):
    gold = get_wallet(user_id)
    kb = types.InlineKeyboardMarkup(row_width=1)
    kb.add(types.InlineKeyboardButton('🛒 Купити зілля', callback_data='alchemist:buy'))
    kb.add(types.InlineKeyboardButton('💰 Продати зілля', callback_data='alchemist:sell'))
    return (
        f'🧪 Алхімік\n\n'
        f'Алхімік готує та продає зілля для відновлення сил у бою. '
        f'Непотрібні зілля можна продати назад.\n\n'
        f'Доступні дії:\n'
        f'• 🛒 Купити зілля;\n'
        f'• 💰 Продати зілля.\n\n'
        f'💰 Золото: {float(gold):.2f}',
        kb,
    )

def build_alchemist_buy_list_17_19_3(user_id):
    gold = get_wallet(user_id)
    kb = types.InlineKeyboardMarkup(row_width=1)
    text = f'🛒 Купівля зіль\n\n💰 Золото: {float(gold):.2f}\n\nОберіть зілля для перегляду покупки:\n\n'
    for item_id in ALCHEMIST_SHOP:
        potion = POTIONS[item_id]
        effect = f"+{potion['restore']} {('HP' if potion['type'] == 'hp' else 'MP')}"
        text += f"{potion['name']}\nЕфект: {effect}\nЦіна: {format_gold(potion['buy_price'])}\nМаксимум у стаку: {potion['max_stack']}\n\n"
        kb.add(types.InlineKeyboardButton(text=f"{potion['name']} — {format_gold(potion['buy_price'])}", callback_data=f'alchemist:buyitem:{item_id}'))
    return (text, kb)

def build_alchemist_buy_preview_17_19_3(user_id, item_id, quantity=1):
    potion = POTIONS.get(int(item_id))
    quantity = max(1, min(999, int(quantity)))
    if not potion:
        return ('❌ Зілля не знайдено.', types.InlineKeyboardMarkup())
    total = round(float(potion['buy_price']) * quantity, 2)
    gold = get_wallet(user_id)
    effect = f"+{potion['restore']} {('HP' if potion['type'] == 'hp' else 'MP')}"
    text = f"🛒 Купівля зілля\n\n{float(potion['name']):.2f}\nЕфект: {float(effect):.2f}\nЦіна за одне: {float(potion['buy_price']):.2f}\n📦 Кількість: {float(quantity):.2f}\n💳 Загальна вартість: {float(total):.2f}\n💰 Золото: {float(gold):.2f}"
    kb = types.InlineKeyboardMarkup(row_width=3)
    kb.row(types.InlineKeyboardButton('➖', callback_data=f'alchemist:buyset:{item_id}:{max(1, quantity - 1)}'), types.InlineKeyboardButton(f'×{quantity}', callback_data=f'alchemist:buyqty:{item_id}'), types.InlineKeyboardButton('➕', callback_data=f'alchemist:buyset:{item_id}:{min(999, quantity + 1)}'))
    kb.add(types.InlineKeyboardButton('✏️ Вказати кількість', callback_data=f'alchemist:buyqty:{item_id}'))
    kb.add(types.InlineKeyboardButton(f'✅ Купити за {format_gold(total)}', callback_data=f'alchemist:buydo:{item_id}:{quantity}'))
    kb.add(types.InlineKeyboardButton('🔙 До зіль', callback_data='alchemist:buy'))
    return (text, kb)

def build_alchemist_sell_list_17_19_3(user_id):
    rows = get_alchemist_potion_stock_17_19_3(user_id)
    kb = types.InlineKeyboardMarkup(row_width=1)
    text = f'💰 Продаж зіль\n\n💰 Золото: {float(get_wallet(user_id)):.2f}\n\n'
    available = [r for r in rows if r['available'] > 0]
    if not available:
        text += 'У тебе немає доступних зіль для продажу.'
    else:
        text += 'Оберіть зілля:\n'
        for r in available:
            kb.add(types.InlineKeyboardButton(f"{r['name']} ×{r['available']} — {format_gold(r['sell_price'])}/шт.", callback_data=f"alchemist:sellitem:{r['item_id']}"))
    return (text, kb)

def build_alchemist_sell_preview_17_19_3(user_id, item_id, quantity=1):
    potion = POTIONS.get(int(item_id))
    stock = next((row for row in get_alchemist_potion_stock_17_19_3(user_id) if row['item_id'] == int(item_id)), None)
    available = int((stock or {}).get('available', 0))
    if not potion or available <= 0:
        return build_alchemist_sell_list_17_19_3(user_id)
    quantity = max(1, min(available, int(quantity)))
    total = round(float(potion['sell_price']) * quantity, 2)
    text = f"💰 Продаж зілля\n\n{potion['name']}\n🎒 Доступно: {available}\n🔒 Зарезервовано: {int((stock or {}).get('reserved', 0))}\nЦіна за одне: {format_gold(potion['sell_price'])}\n📦 Кількість: {quantity}\n💰 Отримаєш: {format_gold(total)}"
    kb = types.InlineKeyboardMarkup(row_width=3)
    kb.row(types.InlineKeyboardButton('➖', callback_data=f'alchemist:sellset:{item_id}:{max(1, quantity - 1)}'), types.InlineKeyboardButton(f'×{quantity}', callback_data=f'alchemist:sellqty:{item_id}'), types.InlineKeyboardButton('➕', callback_data=f'alchemist:sellset:{item_id}:{min(available, quantity + 1)}'))
    kb.add(types.InlineKeyboardButton(f'📦 Продати все ×{available}', callback_data=f'alchemist:sellset:{item_id}:{available}'))
    kb.add(types.InlineKeyboardButton('✏️ Вказати кількість', callback_data=f'alchemist:sellqty:{item_id}'))
    kb.add(types.InlineKeyboardButton(f'✅ Продати за {format_gold(total)}', callback_data=f'alchemist:sellconfirm:{item_id}:{quantity}'))
    kb.add(types.InlineKeyboardButton('🔙 До списку', callback_data='alchemist:sell'))
    return (text, kb)

def build_alchemist_sell_confirm_17_19_3(user_id, item_id, quantity):
    potion = POTIONS.get(int(item_id))
    quantity = int(quantity)
    total = round(float(potion['sell_price']) * quantity, 2)
    kb = types.InlineKeyboardMarkup(row_width=1)
    kb.add(types.InlineKeyboardButton('✅ Продати', callback_data=f'alchemist:selldo:{item_id}:{quantity}'))
    kb.add(types.InlineKeyboardButton('❌ Скасувати', callback_data=f'alchemist:sellitem:{item_id}'))
    return (f"Продати {potion['name']} ×{quantity}?\n\nЦіна за одне: {format_gold(potion['sell_price'])}\nОтримаєш: {format_gold(total)}", kb)

def build_alchemist_catalog(user_id):
    gold = get_wallet(user_id)
    kb = types.InlineKeyboardMarkup()
    text = f'🧪 Алхімік\n\n💰 Золото: {float(gold):.2f}\n\nАлхімік продає зілля для виживання в бою.\n\nАсортимент:\n\n'
    for item_id in ALCHEMIST_SHOP:
        potion = POTIONS[item_id]
        if potion['type'] == 'hp':
            effect = f"+{potion['restore']} HP"
        else:
            effect = f"+{potion['restore']} MP"
        text += f"{potion['name']}\nЕфект: {effect}\nЦіна: {format_gold(potion['buy_price'])}\nМаксимум у стаку: {potion['max_stack']}\n\n"
        kb.add(types.InlineKeyboardButton(text=f"Купити: {potion['name']} — {format_gold(potion['buy_price'])}", callback_data=f'buy_potion_{item_id}'))
    text += f'⚠️ Мана ще не реалізована, тому сині зілля можна купити на майбутнє, але використати поки не можна.'
    return (text, kb)

def build_blacksmith_text(user_id):
    gold = get_wallet(user_id)
    return f'⚒️ Коваль\n\nБіля розпеченого горна працює досвідчений коваль. Він може полагодити твоє спорядження або посилити його за допомогою каменів заточки.\n\nДоступні дії:\n• 🛠️ Ремонт спорядження\n• ✨ Заточка спорядження\n\n💰 Золото: {float(gold):.2f}'

def build_blacksmith_repair_text(user_id):
    equipped_items = get_equipped_items_for_repair(user_id)
    total_cost = get_total_repair_cost(user_id)
    gold = get_wallet(user_id)
    text = f'🛠️ Ремонт спорядження\n\n💰 Золото: {float(gold):.2f}\n\n📦 Стан спорядження:\n\n'
    kb = types.InlineKeyboardMarkup()
    damaged_count = 0
    for item in equipped_items:
        slot = item['slot']
        name = item['name']
        durability = item['durability']
        repair_cost = item['repair_cost']
        is_broken = item['is_broken']
        inventory_id = item['inventory_id']
        if inventory_id is None:
            text += f'{slot}: порожньо\n\n'
            continue
        broken_text = ' ⚠️ [ЗЛАМАНО]' if is_broken else ''
        text += f'{slot}: {name}\n🛠️ Міцність: {durability}/100{broken_text}\n💰 Ремонт: {format_gold(repair_cost)}\n\n'
        if repair_cost > 0:
            damaged_count += 1
            kb.add(types.InlineKeyboardButton(text=f'🛠️ Ремонт: {name} — {format_gold(repair_cost)}', callback_data=f'repair_prompt_one_v3_{inventory_id}'))
    text += f'💳 Вартість повного ремонту: {float(total_cost):.2f}\n💰 Золото: {float(gold):.2f}\n\n'
    if damaged_count <= 0:
        text += '✅ Усе спорядження вже в ідеальному стані.'
    elif gold < total_cost:
        text += '❌ Недостатньо золота для повного ремонту.\nℹ️ Можеш відремонтувати окрему річ, якщо вистачає золота.'
    else:
        text += '👇 Можна полагодити все або окрему річ.'
    if total_cost > 0:
        kb.add(types.InlineKeyboardButton(text=f'🛠️ Полагодити все за {format_gold(total_cost)}', callback_data='repair_prompt_all_v3'))
    return (text, kb)

def build_common_equipment_shop_text(user_id):
    offers = get_common_equipment_shop_offer(user_id)
    gold = get_wallet(user_id)
    text = f'⚪ Базове спорядження\n\n💰 Золото: {float(gold):.2f}\n\nТорговець продає прості білі речі поточного рівня персонажа.\nПеред купівлею ти побачиш точні характеристики предмета.\n\nОдяг поки має універсальний тип, але для зброї та другої руки можна вибрати конкретний вид предмета.\n\nОберіть слот:'
    kb = types.InlineKeyboardMarkup(row_width=1)
    for offer in offers:
        slot_key = offer['slot_key']
        if slot_key in ['main_hand', 'off_hand']:
            callback_data = f'common_equipment_slot:{slot_key}'
        else:
            callback_data = f'buy_common_equipment:{slot_key}:'
        kb.add(types.InlineKeyboardButton(text=f"{offer['slot_name']} — {format_gold(offer['price'])} (рівень {offer['item_level']})", callback_data=callback_data))
    return (text, kb)

def build_common_equipment_slot_choice_text(user_id, slot_key):
    offers = get_common_equipment_shop_suboffers(user_id, slot_key)
    gold = get_wallet(user_id)
    if slot_key == 'main_hand':
        title = '🗡️ Вибір зброї'
        description = 'Обери тип базової зброї для свого стилю бою.\n\n⚔️ Фізична зброя посилює фізичні атаки та найкраще підходить персонажам, які розвивають Силу або Спритність.\n\n🔮 Магічна зброя посилює магічні атаки та найкраще підходить персонажам, які розвивають Інтелект або Мудрість.\n\n👐 Дворучна зброя займає обидві руки, тому разом із нею не можна використовувати щит, талісман або зброю для другої руки.'
    elif slot_key == 'off_hand':
        title = '🛡️ Вибір другої руки'
        description = 'Обери предмет для другої руки відповідно до свого стилю бою.\n\n🛡️ Щит підвищує фізичний захист і Витривалість. Найкраще підходить для персонажів, яким важливо витримувати фізичні атаки.\n\n🔮 Магічний талісман підвищує магічний захист і Мудрість. Допомагає протистояти магічним атакам.\n\n🗡️ Зброя для другої руки підвищує атакувальні характеристики та підходить для більш агресивного стилю бою, але не дає захисту щита.\n\nℹ️ Предмет для другої руки не можна використовувати разом із дворучною зброєю.'
    else:
        title = '⚪ Базове спорядження'
        description = 'Оберіть предмет.'
    text = f'{float(title):.2f}\n\n💰 Золото: {float(gold):.2f}\n\n{float(description):.2f}\n\nДоступні варіанти:'
    kb = types.InlineKeyboardMarkup(row_width=1)
    for offer in offers:
        hands_text = ''
        if slot_key == 'main_hand':
            if offer['hands'] == 2:
                hands_text = ' — дворучна'
            else:
                hands_text = ' — одноручна'
        kb.add(types.InlineKeyboardButton(text=f"{offer['name']}{hands_text} — {format_gold(offer['price'])} (рівень {offer['item_level']})", callback_data=f"buy_common_equipment:{slot_key}:{offer['profile_key']}"))
    kb.add(types.InlineKeyboardButton(text='⬅️ Назад до слотів', callback_data='common_equipment_back_to_slots'))
    return (text, kb)

def format_shop_preview_bonuses(b_str, b_dex, b_int, b_wis, b_sta, pdef, mdef):
    bonuses = []
    if b_str:
        bonuses.append(f'💪 Сила +{b_str}')
    if b_dex:
        bonuses.append(f'🎯 Спритність +{b_dex}')
    if b_int:
        bonuses.append(f'🔮 Інтелект +{b_int}')
    if b_wis:
        bonuses.append(f'🦉 Мудрість +{b_wis}')
    if b_sta:
        bonuses.append(f'🛡 Витривалість +{b_sta}')
    if pdef:
        bonuses.append(f'🛡 Фіз. захист +{pdef}')
    if mdef:
        bonuses.append(f'🔮 Маг. захист +{mdef}')
    return bonuses

def build_shop_preview_display_name(name, slot_key, armor_type):
    """
    Повертає красиву назву preview-предмета.

    Для броні додає тип у дужках:
    Чоботи 5 рівня -> Чоботи [Тканина] 5 рівня

    Для зброї / off-hand тип у дужках не додається,
    бо назва вже зазвичай містить сам тип:
    Жезл 5 рівня
    Кинджал 5 рівня
    Щит 5 рівня
    """
    if not is_armor_slot(slot_key):
        return name
    if not armor_type:
        return name
    armor_label = get_armor_type_label(armor_type)
    if not armor_label:
        return name
    if f'[{armor_label}]' in name:
        return name
    marker = ' рівня'
    if marker in name:
        index = name.rfind(marker)
        before_level = name[:index]
        after_level = name[index:]
        parts = before_level.rsplit(' ', 1)
        if len(parts) == 2 and parts[1].isdigit():
            return f'{parts[0]} [{armor_label}] {parts[1]}{after_level}'
    return f'{name} [{armor_label}]'

def build_base_equipment_return_view_17_11_1_1(user_id, slot_key=None):
    """Return to the closest valid base-equipment list after preview completion."""
    if slot_key in ('main_hand', 'off_hand'):
        return build_common_equipment_slot_choice_text(user_id, slot_key)
    return build_common_equipment_shop_text(user_id)

def get_base_equipment_preview_slot_17_11_1_1(user_id, item_id):
    """Read preview context before confirm/cancel can remove the temporary item."""
    preview = get_shop_preview_item(item_id, user_id)
    if not preview or len(preview) <= 5:
        return None
    return preview[5]

def build_common_shop_preview_text(user_id, item_id):
    preview = get_shop_preview_item(item_id, user_id)
    if not preview:
        text = '❌ Попередній перегляд предмета не знайдено або застарів.'
        kb = types.InlineKeyboardMarkup()
        kb.add(types.InlineKeyboardButton(text='⬅️ Назад до базового спорядження', callback_data='common_equipment_back_to_slots'))
        return (text, kb)
    item_id, name, type_, rarity, category, slot_key, weapon_hands, max_stack, sell_price, b_str, b_dex, b_int, b_wis, b_sta, pdef, mdef, item_level, item_subtype, weapon_min_damage, weapon_max_damage, weapon_min_magic_damage, weapon_max_magic_damage, weapon_attack_type, armor_type, price = preview
    gold = get_wallet(user_id)
    slot_name = EQUIPMENT_SLOTS.get(slot_key, slot_key)
    display_name = build_shop_preview_display_name(name=name, slot_key=slot_key, armor_type=armor_type)
    text = f'🛒 Перегляд покупки\n\n📦 {display_name}\n\n🧰 Тип: спорядження\n🎯 Слот: {slot_name}\n🏷 Рівень предмета: {item_level}\n'
    if is_armor_slot(slot_key):
        text += f'🧵 Тип броні: {get_armor_type_label(armor_type)}\n🧭 Класова сумісність: ✅ Підходить твоєму класу\n'
    elif slot_key in ['main_hand', 'off_hand']:
        text += f'⚔️ Тип предмета: {get_item_subtype_label(item_subtype)}\n🧭 Класова сумісність: ✅ Підходить твоєму класу\n'
    if slot_key == 'main_hand':
        if weapon_hands == 2:
            text += '👐 Тип зброї: дворучна\n'
            text += '⚠️ Дворучна зброя блокує другу руку.\n'
        else:
            text += '✋ Тип зброї: одноручна\n'
        weapon_text = get_shop_preview_weapon_damage_text(item_id)
        if weapon_text:
            text += f'{weapon_text}\n'
    text += '🧱 Міцність: 100/100\n'
    bonuses = format_shop_preview_bonuses(b_str, b_dex, b_int, b_wis, b_sta, pdef, mdef)
    if bonuses:
        text += '\n📊 Бонуси:\n'
        for bonus in bonuses:
            text += f'• {bonus}\n'
    else:
        text += '\n📊 Бонуси: немає\n'
    text += f'\n💳 Ціна: {float(price):.2f}\n💰 Золото: {float(gold):.2f}\n\nКупити цей предмет?'
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton(text=f'✅ Купити за {format_gold(price)}', callback_data=f'common_shop_confirm:{item_id}'))
    kb.add(types.InlineKeyboardButton(text='❌ Скасувати', callback_data=f'common_shop_cancel:{item_id}'))
    return (text, kb)

def build_sell_equipment_list_text(user_id, page=0):
    items = get_sellable_equipment_items(user_id)
    gold = get_wallet(user_id)
    if not items:
        text = f'🧰 Продаж спорядження\n\n💰 Золото: {float(gold):.2f}\n\nУ тебе немає невдягненого спорядження для продажу.\n\nℹ️ Вдягнені речі не показуються у цьому списку.'
        kb = types.InlineKeyboardMarkup()
        return (text, kb)
    total_items = len(items)
    total_pages = max(1, (total_items + SELL_EQUIPMENT_ITEMS_PER_PAGE - 1) // SELL_EQUIPMENT_ITEMS_PER_PAGE)
    if page < 0:
        page = 0
    if page >= total_pages:
        page = total_pages - 1
    start = page * SELL_EQUIPMENT_ITEMS_PER_PAGE
    end = start + SELL_EQUIPMENT_ITEMS_PER_PAGE
    page_items = items[start:end]
    text = f'🧰 Продаж спорядження\n\n💰 Золото: {float(gold):.2f}\n\nТорговець готовий купити невдягнені речі з твого інвентаря.\nВдягнене спорядження продавати не можна.\n\n📄 Сторінка: {float(page + 1):.2f}/{float(total_pages):.2f}\n\nОберіть предмет:'
    kb = types.InlineKeyboardMarkup()
    for item in page_items:
        inv_id, item_id, name, type_, rarity, category, slot_key, weapon_hands, quantity, max_stack, durability, b_str, b_dex, b_int, b_wis, b_sta, pdef, mdef, sell_price = item
        quantity = quantity or 1
        sell_price = sell_price or 0
        total_price = round(quantity * sell_price, 2)
        durability_text = ''
        if durability is not None:
            durability_text = f' [{durability}/100]'
        kb.add(types.InlineKeyboardButton(text=f'{name}{durability_text} — {format_gold(total_price)}', callback_data=f'sell_eq_confirm:{inv_id}:{page}'))
    nav_buttons = []
    if page > 0:
        nav_buttons.append(types.InlineKeyboardButton(text='⬅️ Назад', callback_data=f'sell_eq_page:{page - 1}'))
    if page < total_pages - 1:
        nav_buttons.append(types.InlineKeyboardButton(text='➡️ Далі', callback_data=f'sell_eq_page:{page + 1}'))
    if nav_buttons:
        kb.add(*nav_buttons)
    return (text, kb)

def build_sell_equipment_confirm_text(user_id, inventory_id, page=0):
    item = get_item_by_inventory_id_full(inventory_id)
    if not item:
        text = '❌ Предмет не знайдено.'
        kb = types.InlineKeyboardMarkup()
        kb.add(types.InlineKeyboardButton(text='⬅️ Назад', callback_data=f'sell_eq_page:{page}'))
        return (text, kb)
    inv_id, item_id, name, type_, rarity, category, slot_key, weapon_hands, quantity, max_stack, durability, b_str, b_dex, b_int, b_wis, b_sta, pdef, mdef, sell_price = item
    quantity = quantity or 1
    sell_price = sell_price or 0
    total_price = round(quantity * sell_price, 2)
    text = f'💰 Підтвердження продажу\n\nТи точно хочеш продати цей предмет торговцю?\n\n📦 {name} ×{quantity}\n💰 Ціна: {format_gold(total_price)}\n'
    if durability is not None:
        text += f'🛠️ Міцність: {durability}/100\n'
    text += '\n⚠️ Після продажу предмет зникне з інвентаря.'
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton(text=f'✅ Продати за {format_gold(total_price)}', callback_data=f'sell_eq_do:{inventory_id}:{page}'))
    kb.add(types.InlineKeyboardButton(text='❌ Назад', callback_data=f'sell_eq_page:{page}'))
    return (text, kb)

def trade_district_submenu_kb_17_11_1():
    """Reply navigation used inside Trade District sell/buy submenus."""
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
    kb.add(TRADE_DISTRICT_BACK_BUTTON_17_11_1)
    kb.add(TRADE_DISTRICT_CITY_BUTTON_17_11_1)
    return kb

def send_trade_district_submenu_17_11_1(bot, chat_id):
    """Replace persistent Trade District actions with contextual navigation."""
    bot.send_message(chat_id, 'Оберіть дію зі списку нижче.', reply_markup=trade_district_submenu_kb_17_11_1())

def register_city_handlers(bot):

    @bot.message_handler(func=lambda m: m.text == '🏙️ Місто')
    def show_city(message):
        user_id = message.from_user.id
        bot.send_message(message.chat.id, build_city_text(user_id), reply_markup=city_kb())

    @bot.message_handler(func=lambda m: m.text == '👀 Роззирнутися')
    def look_around(message):
        user_id = message.from_user.id
        from systems.location_context_system import get_location_context_kind
        if get_location_context_kind(user_id) == 'city':
            bot.send_message(message.chat.id, build_city_text(user_id), reply_markup=city_kb())
            return
        bot.send_message(message.chat.id, build_main_menu_text(user_id), reply_markup=main_kb())

    @bot.message_handler(func=lambda m: m.text in ('🔙 Місто', '⬅️ Місто'))
    def back_to_city(message):
        user_id = message.from_user.id
        bot.send_message(message.chat.id, build_city_text(user_id), reply_markup=city_kb())

    @bot.message_handler(func=lambda m: m.text == '🛒 Торговий ряд')
    def show_trade_district(message):
        user_id = message.from_user.id
        bot.send_message(message.chat.id, build_trade_district_text(user_id), reply_markup=trader_kb())

    @bot.message_handler(func=lambda m: m.text == '⚒️ Ремісничий квартал')
    def show_craft_district(message):
        user_id = message.from_user.id
        bot.send_message(message.chat.id, build_craft_district_text(user_id), reply_markup=craft_kb())

    @bot.message_handler(func=lambda m: m.text == '📜 Гільдія Найманців')
    def show_guild_district(message):
        user_id = message.from_user.id
        bot.send_message(message.chat.id, build_guild_district_text(user_id), reply_markup=guild_kb())

    @bot.message_handler(func=lambda m: m.text == '🏛️ Ратуша')
    def show_townhall(message):
        bot.send_message(message.chat.id, build_townhall_text(), reply_markup=townhall_kb())

    @bot.message_handler(func=lambda m: m.text == '🍺 Таверна')
    def show_tavern(message):
        bot.send_message(message.chat.id, build_tavern_text(), reply_markup=tavern_kb())

    @bot.message_handler(func=lambda m: m.text == '🔙 Торговий ряд')
    def back_to_trade_district_message(message):
        user_id = message.from_user.id
        bot.send_message(message.chat.id, build_trade_district_text(user_id), reply_markup=trader_kb())

    @bot.message_handler(func=lambda m: m.text == '🔙 Ремісничий квартал')
    def back_to_craft_district_message(message):
        user_id = message.from_user.id
        _ALCHEMIST_INPUT_17_19_3.pop(int(user_id), None)
        bot.send_message(message.chat.id, build_craft_district_text(user_id), reply_markup=craft_kb())

    @bot.message_handler(func=lambda m: m.text == '🔙 Гільдія Найманців')
    def back_to_guild_district_message(message):
        user_id = message.from_user.id
        bot.send_message(message.chat.id, build_guild_district_text(user_id), reply_markup=guild_kb())

    @bot.message_handler(func=lambda m: m.text == '🪙 Продати весь мотлох')
    def sell_trash(message):
        user_id = message.from_user.id
        result = sell_all_trash(user_id)
        if result['sold_items_count'] == 0:
            bot.send_message(message.chat.id, '💰 У тебе немає сірого луту для продажу.', reply_markup=trader_kb())
            return
        text = '💰 Продаж сірого луту\n\n'
        for line in result['details']:
            text += f'• {line}\n'
        text += f"\n✅ Отримано золота: {format_gold(result['gold_earned'])}\n🎒 Звільнено слотів: {result['freed_slots']}"
        bot.send_message(message.chat.id, text, reply_markup=trader_kb())

    @bot.message_handler(func=lambda m: m.text == '🧰 Продати спорядження')
    def show_sell_equipment(message):
        user_id = message.from_user.id
        text, kb = build_sell_equipment_list_text(user_id, page=0)
        send_trade_district_submenu_17_11_1(bot, message.chat.id)
        bot.send_message(message.chat.id, text, reply_markup=kb)

    @bot.callback_query_handler(func=lambda call: call.data.startswith('sell_eq_page:'))
    def sell_equipment_page(call):
        user_id = call.from_user.id
        page = int(call.data.split(':')[1])
        text, kb = build_sell_equipment_list_text(user_id, page=page)
        bot.answer_callback_query(call.id)
        bot.send_message(call.message.chat.id, text, reply_markup=kb)

    @bot.callback_query_handler(func=lambda call: call.data.startswith('sell_eq_confirm:'))
    def sell_equipment_confirm(call):
        user_id = call.from_user.id
        parts = call.data.split(':')
        inventory_id = int(parts[1])
        page = int(parts[2]) if len(parts) > 2 else 0
        text, kb = build_sell_equipment_confirm_text(user_id=user_id, inventory_id=inventory_id, page=page)
        bot.answer_callback_query(call.id)
        bot.send_message(call.message.chat.id, text, reply_markup=kb)

    @bot.callback_query_handler(func=lambda call: call.data.startswith('sell_eq_do:'))
    def sell_equipment_do(call):
        user_id = call.from_user.id
        parts = call.data.split(':')
        inventory_id = int(parts[1])
        page = int(parts[2]) if len(parts) > 2 else 0
        result = sell_inventory_item_to_trader(user_id=user_id, inventory_id=inventory_id)
        bot.answer_callback_query(call.id)
        bot.send_message(call.message.chat.id, result['message'], reply_markup=trade_district_submenu_kb_17_11_1())
        text, kb = build_sell_equipment_list_text(user_id, page=page)
        bot.send_message(call.message.chat.id, text, reply_markup=kb)

    @bot.message_handler(func=lambda m: m.text == '⚪ Базове спорядження')
    def show_common_equipment_shop(message):
        user_id = message.from_user.id
        text, kb = build_common_equipment_shop_text(user_id)
        send_trade_district_submenu_17_11_1(bot, message.chat.id)
        bot.send_message(message.chat.id, text, reply_markup=kb)

    @bot.callback_query_handler(func=lambda call: call.data == 'common_equipment_back_to_slots')
    def common_equipment_back_to_slots(call):
        user_id = call.from_user.id
        text, kb = build_common_equipment_shop_text(user_id)
        bot.answer_callback_query(call.id)
        bot.send_message(call.message.chat.id, text, reply_markup=kb)

    @bot.callback_query_handler(func=lambda call: call.data.startswith('common_equipment_slot:'))
    def common_equipment_slot_choice(call):
        user_id = call.from_user.id
        slot_key = call.data.split(':')[1]
        text, kb = build_common_equipment_slot_choice_text(user_id, slot_key)
        bot.answer_callback_query(call.id)
        bot.send_message(call.message.chat.id, text, reply_markup=kb)

    @bot.callback_query_handler(func=lambda call: call.data.startswith('buy_common_equipment:'))
    def preview_common_equipment(call):
        user_id = call.from_user.id
        parts = call.data.split(':')
        slot_key = parts[1]
        item_profile = parts[2] if len(parts) > 2 and parts[2] else None
        result = create_common_equipment_shop_preview(user_id=user_id, slot_key=slot_key, item_profile=item_profile)
        bot.answer_callback_query(call.id)
        if not result.get('success'):
            bot.send_message(call.message.chat.id, result['message'], reply_markup=trade_district_submenu_kb_17_11_1())
            return
        text, kb = build_common_shop_preview_text(user_id=user_id, item_id=result['item_id'])
        bot.send_message(call.message.chat.id, text, reply_markup=kb)

    @bot.callback_query_handler(func=lambda call: call.data.startswith('common_shop_confirm:'))
    def confirm_common_shop_purchase(call):
        user_id = call.from_user.id
        item_id = int(call.data.split(':')[1])
        slot_key = get_base_equipment_preview_slot_17_11_1_1(user_id, item_id)
        result = confirm_common_equipment_shop_preview(user_id=user_id, item_id=item_id)
        bot.answer_callback_query(call.id)
        bot.send_message(call.message.chat.id, result['message'], reply_markup=trade_district_submenu_kb_17_11_1())
        text, kb = build_base_equipment_return_view_17_11_1_1(user_id, slot_key)
        bot.send_message(call.message.chat.id, text, reply_markup=kb)

    @bot.callback_query_handler(func=lambda call: call.data.startswith('common_shop_cancel:'))
    def cancel_common_shop_purchase(call):
        user_id = call.from_user.id
        item_id = int(call.data.split(':')[1])
        slot_key = get_base_equipment_preview_slot_17_11_1_1(user_id, item_id)
        result = cancel_common_equipment_shop_preview(user_id=user_id, item_id=item_id)
        bot.answer_callback_query(call.id)
        bot.send_message(call.message.chat.id, result['message'], reply_markup=trade_district_submenu_kb_17_11_1())
        text, kb = build_base_equipment_return_view_17_11_1_1(user_id, slot_key)
        bot.send_message(call.message.chat.id, text, reply_markup=kb)

    @bot.callback_query_handler(func=lambda call: call.data == 'back_to_trade_district')
    def back_to_trade_district(call):
        user_id = call.from_user.id
        bot.answer_callback_query(call.id)
        bot.send_message(call.message.chat.id, build_trade_district_text(user_id), reply_markup=trader_kb())

    @bot.callback_query_handler(func=lambda call: call.data == 'back_to_trader')
    def back_to_trader_callback(call):
        user_id = call.from_user.id
        bot.answer_callback_query(call.id)
        bot.send_message(call.message.chat.id, build_trade_district_text(user_id), reply_markup=trader_kb())

    @bot.message_handler(func=lambda m: m.text == '🧪 Алхімік')
    def show_alchemist(message):
        user_id = int(message.from_user.id)
        _ALCHEMIST_INPUT_17_19_3.pop(user_id, None)
        text, _ = build_alchemist_root_17_19_3(user_id)
        bot.send_message(message.chat.id, text, reply_markup=alchemist_reply_kb_17_19_3_1())

    @bot.callback_query_handler(func=lambda call: str(call.data).startswith('alchemist:'))
    def alchemist_trade_17_19_3(call):
        user_id = int(call.from_user.id)
        data = str(call.data)
        parts = data.split(':')
        try:
            bot.answer_callback_query(call.id)
        except Exception:
            pass
        if data == 'alchemist:root':
            text, kb = build_alchemist_root_17_19_3(user_id)
        elif data == 'alchemist:buy':
            text, kb = build_alchemist_buy_list_17_19_3(user_id)
        elif data == 'alchemist:sell':
            text, kb = build_alchemist_sell_list_17_19_3(user_id)
        elif parts[1] == 'buyitem':
            text, kb = build_alchemist_buy_preview_17_19_3(user_id, int(parts[2]), 1)
        elif parts[1] == 'buyset':
            text, kb = build_alchemist_buy_preview_17_19_3(user_id, int(parts[2]), int(parts[3]))
        elif parts[1] == 'buyqty':
            _ALCHEMIST_INPUT_17_19_3[user_id] = {'mode': 'buy', 'item_id': int(parts[2]), 'chat_id': call.message.chat.id}
            bot.send_message(call.message.chat.id, 'Введи кількість зіль для купівлі, від 1 до 999.')
            return
        elif parts[1] == 'buydo':
            result = buy_alchemist_potion_17_19_3(user_id, int(parts[2]), int(parts[3]))
            bot.send_message(call.message.chat.id, result['message'], reply_markup=alchemist_reply_kb_17_19_3_1())
            if result.get('success'):
                text, kb = build_alchemist_buy_list_17_19_3(user_id)
            else:
                text, kb = build_alchemist_buy_preview_17_19_3(user_id, int(parts[2]), int(parts[3]))
        elif parts[1] == 'sellitem':
            text, kb = build_alchemist_sell_preview_17_19_3(user_id, int(parts[2]), 1)
        elif parts[1] == 'sellset':
            text, kb = build_alchemist_sell_preview_17_19_3(user_id, int(parts[2]), int(parts[3]))
        elif parts[1] == 'sellqty':
            _ALCHEMIST_INPUT_17_19_3[user_id] = {'mode': 'sell', 'item_id': int(parts[2]), 'chat_id': call.message.chat.id}
            bot.send_message(call.message.chat.id, 'Введи кількість зіль для продажу.')
            return
        elif parts[1] == 'sellconfirm':
            text, kb = build_alchemist_sell_confirm_17_19_3(user_id, int(parts[2]), int(parts[3]))
        elif parts[1] == 'selldo':
            result = sell_alchemist_potion_17_19_3(user_id, int(parts[2]), int(parts[3]))
            bot.send_message(call.message.chat.id, result['message'], reply_markup=alchemist_reply_kb_17_19_3_1())
            text, kb = build_alchemist_sell_list_17_19_3(user_id)
        else:
            return
        bot.send_message(call.message.chat.id, text, reply_markup=kb)

    @bot.message_handler(func=lambda m: m.text == '🛒 Купити зілля')
    def alchemist_buy_message_17_19_3_1(message):
        user_id = int(message.from_user.id)
        _ALCHEMIST_INPUT_17_19_3.pop(user_id, None)
        text, kb = build_alchemist_buy_list_17_19_3(user_id)
        bot.send_message(message.chat.id, text, reply_markup=kb)

    @bot.message_handler(func=lambda m: m.text == '💰 Продати зілля')
    def alchemist_sell_message_17_19_3_1(message):
        user_id = int(message.from_user.id)
        _ALCHEMIST_INPUT_17_19_3.pop(user_id, None)
        text, kb = build_alchemist_sell_list_17_19_3(user_id)
        bot.send_message(message.chat.id, text, reply_markup=kb)

    @bot.message_handler(func=lambda m: int(getattr(m.from_user, 'id', 0)) in _ALCHEMIST_INPUT_17_19_3)
    def alchemist_exact_quantity_17_19_3(message):
        user_id = int(message.from_user.id)
        state = _ALCHEMIST_INPUT_17_19_3.pop(user_id, None)
        try:
            quantity = int(str(message.text).strip())
        except Exception:
            bot.send_message(message.chat.id, '❌ Введи ціле число.')
            return
        if quantity < 1:
            bot.send_message(message.chat.id, '❌ Кількість має бути більшою за нуль.')
            return
        if state['mode'] == 'buy':
            text, kb = build_alchemist_buy_preview_17_19_3(user_id, state['item_id'], quantity)
        else:
            stock = next((r for r in get_alchemist_potion_stock_17_19_3(user_id) if r['item_id'] == state['item_id']), None)
            available = int((stock or {}).get('available', 0))
            if quantity > available:
                bot.send_message(message.chat.id, f'❌ Доступно для продажу лише {available}.')
                return
            text, kb = build_alchemist_sell_confirm_17_19_3(user_id, state['item_id'], quantity)
        bot.send_message(message.chat.id, text, reply_markup=kb)

    @bot.message_handler(func=lambda m: m.text == '⚒️ Коваль')
    def show_blacksmith(message):
        user_id = message.from_user.id
        if has_story_npc_if_present(message, 'blacksmith'):
            # Story interaction must not hide the Blacksmith's canonical services.
            text, kb = build_blacksmith_text(user_id)
            bot.send_message(message.chat.id, text, reply_markup=kb)
            send_story_npc_if_present(bot, message, 'blacksmith')
            return
        bot.send_message(message.chat.id, '⚒️ Ти підійшов до Коваля.', reply_markup=blacksmith_kb())
        text, kb = build_blacksmith_text(user_id)
        bot.send_message(message.chat.id, text, reply_markup=kb)

    @bot.callback_query_handler(func=lambda call: call.data == 'repair_all_equipped')
    def repair_all(call):
        user_id = call.from_user.id
        result = repair_all_equipped(user_id)
        bot.answer_callback_query(call.id)
        bot.send_message(call.message.chat.id, result['message'], reply_markup=blacksmith_kb())
        text, kb = build_blacksmith_text(user_id)
        bot.send_message(call.message.chat.id, text, reply_markup=kb)

    @bot.callback_query_handler(func=lambda call: call.data.startswith('repair_one_'))
    def repair_one(call):
        user_id = call.from_user.id
        inventory_id = int(call.data.split('_')[2])
        result = repair_equipped_item(user_id, inventory_id)
        bot.answer_callback_query(call.id)
        bot.send_message(call.message.chat.id, result['message'], reply_markup=blacksmith_kb())
        text, kb = build_blacksmith_text(user_id)
        bot.send_message(call.message.chat.id, text, reply_markup=kb)

    @bot.message_handler(func=lambda m: m.text == '🔙 Назад')
    def back_to_main(message):
        user_id = message.from_user.id
        bot.send_message(message.chat.id, build_main_menu_text(user_id), reply_markup=main_kb())

def register_blacksmith_repair_button_v2(bot):

    @bot.message_handler(func=lambda message: message.text == '🛠️ Ремонт')
    def blacksmith_repair_button_v2(message):
        bot.send_message(message.chat.id, build_blacksmith_repair_text(message.from_user.id), reply_markup=blacksmith_kb())

def build_blacksmith_text(user_id):
    gold = get_wallet(user_id)
    return (
        f'⚒️ Коваль\n\n'
        f'Коваль ремонтує пошкоджене спорядження та посилює його за допомогою Каменів Посилення.\n\n'
        f'Доступні дії:\n'
        f'• 🛠️ Ремонт спорядження;\n'
        f'• ✨ Заточка спорядження.\n\n'
        f'💰 Золото: {float(gold):.2f}'
    )

def _normalize_text_kb_result(result, fallback_kb=None):
    """
    Допоміжна функція для старих build_* функцій:
    - якщо функція повертає (text, kb), залишаємо як є;
    - якщо повертає тільки text, додаємо fallback_kb.
    """
    if isinstance(result, tuple):
        if len(result) >= 2:
            return (result[0], result[1])
        if len(result) == 1:
            return (result[0], fallback_kb)
    return (result, fallback_kb)

def register_blacksmith_repair_button_v2(bot):

    @bot.message_handler(func=lambda message: message.text == '🛠️ Ремонт')
    def blacksmith_repair_button_v2(message):
        result = build_blacksmith_repair_text(message.from_user.id)
        text, kb = _normalize_text_kb_result(result, blacksmith_kb())
        bot.send_message(message.chat.id, text, reply_markup=kb)
try:
    _base_city_get_sellable_equipment_items_before_refine_display_v1 = get_sellable_equipment_items
except Exception:
    _base_city_get_sellable_equipment_items_before_refine_display_v1 = None
try:
    _base_city_get_item_by_inventory_id_full_before_refine_display_v1 = get_item_by_inventory_id_full
except Exception:
    _base_city_get_item_by_inventory_id_full_before_refine_display_v1 = None

def _city_find_sellable_name_index(row):
    """
    Намагається знайти індекс назви у tuple/list sellable item.
    Різні версії db.py можуть повертати різний формат.
    """
    if not isinstance(row, (tuple, list)):
        return None
    preferred_indexes = [1, 2]
    for index in preferred_indexes:
        if index < len(row) and isinstance(row[index], str):
            value = row[index]
            if value and value not in ['equipment', 'weapon', 'armor', 'common', 'uncommon', 'rare', 'epic']:
                return index
    for index, value in enumerate(row):
        if not isinstance(value, str):
            continue
        if ' рівня' in value:
            return index
        if any((marker in value for marker in ['⚪', '🟢', '🔵', '🟣', 'Посох', 'Меч', 'Кинджал', 'Обладунок', 'Шолом', 'Поножі', 'Рукавиці', 'Чоботи'])):
            return index
    return None

def _city_refine_display_for_row(row):
    """
    Додає [+N] у назву row, не змінюючи структуру row.
    """
    try:
        if isinstance(row, dict):
            inventory_id = row.get('inventory_id') or row.get('id')
            name = row.get('name')
            if not inventory_id or not name:
                return row
            updated = dict(row)
            updated['name'] = get_inventory_refined_display_name(inventory_id, name)
            return updated
        if isinstance(row, (tuple, list)):
            if not row:
                return row
            inventory_id = row[0]
            name_index = _city_find_sellable_name_index(row)
            if name_index is None:
                return row
            values = list(row)
            values[name_index] = get_inventory_refined_display_name(inventory_id, values[name_index])
            if isinstance(row, tuple):
                return tuple(values)
            return values
    except Exception:
        return row
    return row

def get_sellable_equipment_items(user_id):
    """
    FINAL OVERRIDE:
    Список продажу спорядження з назвами [+N].
    """
    if _base_city_get_sellable_equipment_items_before_refine_display_v1 is None:
        return []
    rows = _base_city_get_sellable_equipment_items_before_refine_display_v1(user_id)
    if not rows:
        return rows
    return [_city_refine_display_for_row(row) for row in rows]

def get_item_by_inventory_id_full(inventory_id):
    """
    FINAL OVERRIDE:
    Підтвердження продажу та інші city-деталі показують назву з [+N].
    """
    if _base_city_get_item_by_inventory_id_full_before_refine_display_v1 is None:
        return None
    row = _base_city_get_item_by_inventory_id_full_before_refine_display_v1(inventory_id)
    if not row:
        return row
    try:
        if isinstance(row, dict):
            if 'name' in row:
                updated = dict(row)
                updated['name'] = get_inventory_refined_display_name(inventory_id, updated.get('name'))
                return updated
            return row
        if isinstance(row, (tuple, list)):
            values = list(row)
            if len(values) > 2 and isinstance(values[2], str):
                values[2] = get_inventory_refined_display_name(inventory_id, values[2])
            else:
                name_index = _city_find_sellable_name_index(values)
                if name_index is not None:
                    values[name_index] = get_inventory_refined_display_name(inventory_id, values[name_index])
            if isinstance(row, tuple):
                return tuple(values)
            return values
    except Exception:
        return row
    return row
try:
    _base_city_get_sellable_equipment_items_before_refine_display_v2 = get_sellable_equipment_items
except Exception:
    _base_city_get_sellable_equipment_items_before_refine_display_v2 = None
try:
    _base_city_get_item_by_inventory_id_full_before_refine_display_v2 = get_item_by_inventory_id_full
except Exception:
    _base_city_get_item_by_inventory_id_full_before_refine_display_v2 = None

def _city_get_refined_name_v2(inventory_id, name):
    try:
        from db import get_inventory_refined_display_name
        return get_inventory_refined_display_name(inventory_id, name)
    except Exception:
        return name

def _city_string_looks_like_item_name_v2(value):
    if not isinstance(value, str):
        return False
    if not value:
        return False
    if ' рівня' in value:
        return True
    item_markers = ['⚪', '🟢', '🔵', '🟣', 'Посох', 'Жезл', 'Меч', 'Кинджал', 'Лук', 'Арбалет', 'Щит', 'Обладунок', 'Шолом', 'Поножі', 'Рукавиці', 'Чоботи', 'Каптур', 'Капелюх', 'Амулет', 'Кільце', 'Талісман']
    return any((marker in value for marker in item_markers))

def _city_refine_display_for_sell_row_v2(row):
    try:
        if isinstance(row, dict):
            inventory_id = row.get('inventory_id') or row.get('id')
            if not inventory_id:
                return row
            updated = dict(row)
            for key in ['name', 'item_name', 'display_name', 'label']:
                if key in updated and isinstance(updated[key], str):
                    updated[key] = _city_get_refined_name_v2(inventory_id, updated[key])
            return updated
        if isinstance(row, (tuple, list)):
            if not row:
                return row
            inventory_id = row[0]
            values = list(row)
            changed = False
            for index, value in enumerate(values):
                if _city_string_looks_like_item_name_v2(value):
                    values[index] = _city_get_refined_name_v2(inventory_id, value)
                    changed = True
            if not changed:
                for index in [1, 2]:
                    if index < len(values) and isinstance(values[index], str):
                        values[index] = _city_get_refined_name_v2(inventory_id, values[index])
                        changed = True
                        break
            if isinstance(row, tuple):
                return tuple(values)
            return values
    except Exception:
        return row
    return row

def get_sellable_equipment_items(user_id):
    """
    FINAL OVERRIDE V2:
    Список продажу спорядження з назвами [+N].
    """
    if _base_city_get_sellable_equipment_items_before_refine_display_v2 is None:
        return []
    rows = _base_city_get_sellable_equipment_items_before_refine_display_v2(user_id)
    if not rows:
        return rows
    return [_city_refine_display_for_sell_row_v2(row) for row in rows]

def get_item_by_inventory_id_full(inventory_id):
    """
    FINAL OVERRIDE V2:
    Підтвердження продажу показує назву з [+N].
    """
    if _base_city_get_item_by_inventory_id_full_before_refine_display_v2 is None:
        return None
    row = _base_city_get_item_by_inventory_id_full_before_refine_display_v2(inventory_id)
    if not row:
        return row
    try:
        if isinstance(row, dict):
            updated = dict(row)
            for key in ['name', 'item_name', 'display_name', 'label']:
                if key in updated and isinstance(updated[key], str):
                    updated[key] = _city_get_refined_name_v2(inventory_id, updated[key])
            return updated
        if isinstance(row, (tuple, list)):
            values = list(row)
            for index, value in enumerate(values):
                if _city_string_looks_like_item_name_v2(value):
                    values[index] = _city_get_refined_name_v2(inventory_id, value)
            if isinstance(row, tuple):
                return tuple(values)
            return values
    except Exception:
        return row
    return row
_CITY_SELLABLE_BEFORE_TYPE_DISPLAY_11_4_1 = get_sellable_equipment_items
_CITY_ITEM_FULL_BEFORE_TYPE_DISPLAY_11_4_1 = get_item_by_inventory_id_full

def _city_equipment_typed_name_11_4_1(inventory_id, name):
    """Apply the same [armor type] label used by inventory and loot UI."""
    from db import get_item_classification_by_inventory_id, get_armor_type_label, is_armor_slot
    display_name = str(name or 'Предмет')
    try:
        classification = get_item_classification_by_inventory_id(int(inventory_id)) or {}
        slot_key = classification.get('slot_key', '')
        armor_type = classification.get('armor_type', '')
        if not is_armor_slot(slot_key) or not armor_type:
            return display_name
        label = get_armor_type_label(armor_type)
        if not label or f'[{label}]' in display_name:
            return display_name
        marker = ' рівня'
        if marker in display_name:
            index = display_name.rfind(marker)
            before = display_name[:index]
            after = display_name[index:]
            parts = before.rsplit(' ', 1)
            if len(parts) == 2 and parts[1].isdigit():
                return f'{parts[0]} [{label}] {parts[1]}{after}'
        return f'{display_name} [{label}]'
    except Exception:
        return display_name

def get_sellable_equipment_items(user_id):
    rows = _CITY_SELLABLE_BEFORE_TYPE_DISPLAY_11_4_1(user_id)
    updated_rows = []
    for row in rows or []:
        try:
            values = list(row)
            values[2] = _city_equipment_typed_name_11_4_1(values[0], values[2])
            updated_rows.append(tuple(values) if isinstance(row, tuple) else values)
        except Exception:
            updated_rows.append(row)
    return updated_rows

def get_item_by_inventory_id_full(inventory_id):
    row = _CITY_ITEM_FULL_BEFORE_TYPE_DISPLAY_11_4_1(inventory_id)
    if not row:
        return row
    try:
        if isinstance(row, dict):
            updated = dict(row)
            for key in ('name', 'item_name', 'display_name', 'label'):
                if key in updated and updated[key]:
                    updated[key] = _city_equipment_typed_name_11_4_1(inventory_id, updated[key])
                    break
            return updated
        values = list(row)
        for index in (1, 2):
            if index < len(values) and isinstance(values[index], str):
                values[index] = _city_equipment_typed_name_11_4_1(inventory_id, values[index])
                break
        return tuple(values) if isinstance(row, tuple) else values
    except Exception:
        return row
_BASE_BUILD_MAIN_MENU_TEXT_17_11_2 = build_main_menu_text
_BASE_BUILD_TOWNHALL_TEXT_17_11_2 = build_townhall_text
_BASE_BUILD_BLACKSMITH_TEXT_17_11_2 = build_blacksmith_text
_BASE_REGISTER_CITY_HANDLERS_17_11_2 = register_city_handlers

def _remove_static_actions_block_17_11_2(text, stop_marker=None):
    marker = '\n\nДоступні дії:\n'
    if marker not in text:
        marker = 'Доступні дії:\n'
    if marker not in text:
        return text
    start = text.index(marker)
    if stop_marker and stop_marker in text[start:]:
        end = text.index(stop_marker, start)
        return (text[:start].rstrip() + '\n\n' + text[end:].lstrip()).strip()
    return text[:start].rstrip()

def build_main_menu_text(user_id, show_location_description=False):
    text = _BASE_BUILD_MAIN_MENU_TEXT_17_11_2(user_id)
    location_id = get_current_location(user_id)
    location = LOCATIONS.get(location_id, LOCATIONS['start_path'])
    description_line = f"📖 {location['description']}\n\n"
    text = text.replace(description_line, '', 1)
    text = _remove_static_actions_block_17_11_2(text)
    if show_location_description:
        anchor = f"{location['name']}\n\n"
        if anchor in text:
            text = text.replace(anchor, anchor + description_line, 1)
    return text.strip()

def build_townhall_text(*args, **kwargs):
    return _remove_static_actions_block_17_11_2(_BASE_BUILD_TOWNHALL_TEXT_17_11_2(*args, **kwargs))

def build_blacksmith_text(*args, **kwargs):
    return _normalize_text_kb_result(
        _BASE_BUILD_BLACKSMITH_TEXT_17_11_2(*args, **kwargs),
        blacksmith_kb(),
    )

def location_description_kb_17_11_2(expanded=False):
    kb = types.InlineKeyboardMarkup(row_width=1)
    if expanded:
        kb.add(types.InlineKeyboardButton(text='🔙 Сховати опис', callback_data='location_desc:hide'))
    else:
        kb.add(types.InlineKeyboardButton(text='📖 Опис локації', callback_data='location_desc:show'))
    return kb

def register_city_handlers(bot):
    _BASE_REGISTER_CITY_HANDLERS_17_11_2(bot)

    @bot.callback_query_handler(func=lambda call: call.data in ('location_desc:show', 'location_desc:hide'))
    def location_description_toggle_17_11_2(call):
        expanded = call.data == 'location_desc:show'
        user_id = call.from_user.id
        try:
            bot.edit_message_text(build_main_menu_text(user_id, show_location_description=expanded), chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=location_description_kb_17_11_2(expanded))
        except Exception:
            pass
        finally:
            try:
                bot.answer_callback_query(call.id)
            except Exception:
                pass
_BASE_BUILD_CITY_TEXT_17_11_2_1 = build_city_text
_BASE_BUILD_CRAFT_DISTRICT_TEXT_17_11_2_1 = build_craft_district_text
_BASE_BUILD_TAVERN_TEXT_17_11_2_1 = build_tavern_text

def build_city_text(user_id):
    text = f'🏙️ Місто\n\nПеред тобою центральна площа табору мандрівників, де сходяться дороги торговців, ремісників і шукачів пригод. З майстерень долинає дзенькіт металу, торговці закликають оглянути товари, а біля дошок оголошень збираються найманці. Тут можна підготуватися до нової подорожі, поповнити припаси та дізнатися останні новини.'
    return text + '\n\n' + _online_presence_block_18_22_7(user_id, city=True)

def build_craft_district_text(user_id):
    gold = get_wallet(user_id)
    return (
        f'⚒️ Ремісничий квартал\n\n'
        f'Тут пахне вугіллям, розпеченим металом і настоями трав. '
        f'У кварталі працюють майстри, які допомагають підготуватися до наступного полювання.\n\n'
        f'Доступні місця:\n'
        f'• ⚒️ Коваль — ремонт і заточка спорядження;\n'
        f'• 🧪 Алхімік — купівля та продаж зіль;\n'
        f'• 💠 Рунний Майстер — руни та Екстрактори.\n\n'
        f'💰 Золото: {float(gold):.2f}'
    )

def build_tavern_text():
    text = _BASE_BUILD_TAVERN_TEXT_17_11_2_1()
    marker = '\n\nℹ️ Пізніше тут можна буде додати:\n'
    if marker in text:
        text = text.split(marker, 1)[0]
    return text.rstrip()
_BUILD_MAIN_MENU_TEXT_BEFORE_EXP_BONUS_STATUS_17_30_1_1 = build_main_menu_text

def _format_account_utc_17_30_1_1(value):
    if not value:
        return 'не зафіксована'
    try:
        from datetime import datetime, timezone
        parsed = datetime.fromisoformat(str(value).replace('Z', '+00:00'))
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(timezone.utc).strftime('%d.%m.%Y %H:%M UTC')
    except Exception:
        return 'не зафіксована'

def build_main_menu_text(user_id, show_location_description=False):
    text = _BUILD_MAIN_MENU_TEXT_BEFORE_EXP_BONUS_STATUS_17_30_1_1(user_id, show_location_description=show_location_description)
    from systems.timed_exp_bonus_system import get_exp_bonus_account_summary
    summary = get_exp_bonus_account_summary(user_id)
    lines = [f'🆔 ID: {int(user_id)}', f"📅 Дата реєстрації: {_format_registration_date_kyiv_18_31_4a(_format_account_utc_17_30_1_1(summary.get('registered_at')))}"]
    if summary.get('active'):
        lines.extend(['💎 Premium: активний', '📈 Бонус за вбивство мобів: +25% EXP', f"⏳ Діє до: {_format_account_utc_17_30_1_1(summary.get('expires_at'))}"])
    else:
        lines.append('💎 Premium: неактивний')
    block = '\n'.join(lines)
    title = '📋 Меню'
    if title in text:
        return text.replace(title, title + '\n\n' + block, 1)
    return title + '\n\n' + block + '\n\n' + text
_REGISTER_CITY_HANDLERS_BEFORE_MAIN_MENU_RECOVERY_17_30_1_3 = register_city_handlers

from keyboards import elder_kb, mercenary_head_kb, bartender_kb
from data.story_quest_npcs import get_story_quest_npc
from handlers.story_quest_npc_runtime import send_story_npc_if_present, has_story_npc_if_present


def _build_story_npc_placeholder_text(npc_id, description):
    """Build an informational NPC screen before production quest content exists."""
    npc = get_story_quest_npc(npc_id)
    return (
        f"{npc.button_label}\n\n{description}\n\n"
        "📜 Нових сюжетних доручень зараз немає. "
        "Перевір журнал квестів або повернися пізніше."
    )


def build_story_elder_text():
    """Render the Elder in Town Hall without duplicating quest lifecycle logic."""
    return _build_story_npc_placeholder_text(
        "elder",
        "Староста переглядає звіти варти, прохання мешканців і карти околиць.",
    )


def build_story_mercenary_head_text():
    """Render the Mercenary Head in the Guild without enabling boss calls yet."""
    return _build_story_npc_placeholder_text(
        "mercenary_head",
        "Голова Найманців стежить за контрактами та небезпеками навколо міста.",
    )


def build_story_bartender_text():
    """Render the Bartender in the Tavern without enabling quest acceptance yet."""
    return _build_story_npc_placeholder_text(
        "bartender",
        "Бармен слухає розмови мандрівників і збирає чутки з навколишніх земель.",
    )


def register_city_handlers(bot):
    @bot.message_handler(func=lambda m: getattr(m, "text", None) == "🗣️ Староста")
    def show_story_elder(message):
        if send_story_npc_if_present(bot, message, 'elder'):
            return
        bot.send_message(
            message.chat.id,
            build_story_elder_text(),
            reply_markup=elder_kb(),
        )

    @bot.message_handler(func=lambda m: getattr(m, "text", None) == "⚔️ Голова Найманців")
    def show_story_mercenary_head(message):
        if has_story_npc_if_present(message, 'mercenary_head'):
            # Keep contracts and the City return route visible beside story UI.
            bot.send_message(
                message.chat.id,
                '⚔️ Інші справи Гільдії Найманців:',
                reply_markup=mercenary_head_kb(message.from_user.id),
            )
            send_story_npc_if_present(bot, message, 'mercenary_head')
            return
        bot.send_message(
            message.chat.id,
            build_story_mercenary_head_text(),
            reply_markup=mercenary_head_kb(message.from_user.id),
        )

    @bot.message_handler(func=lambda m: getattr(m, "text", None) == "🍺 Бармен")
    def show_story_bartender(message):
        bot.send_message(
            message.chat.id,
            build_story_bartender_text(),
            reply_markup=bartender_kb(),
        )

    @bot.message_handler(func=lambda m: getattr(m, "text", None) == "🔙 Ратуша")
    def back_to_story_townhall(message):
        bot.send_message(message.chat.id, build_townhall_text(), reply_markup=townhall_kb())

    @bot.message_handler(func=lambda m: getattr(m, "text", None) == "🔙 Гільдія Найманців")
    def back_to_story_mercenary_guild(message):
        bot.send_message(
            message.chat.id,
            build_guild_district_text(message.from_user.id),
            reply_markup=guild_kb(),
        )

    @bot.message_handler(func=lambda m: getattr(m, "text", None) == "🔙 Таверна")
    def back_to_story_tavern(message):
        bot.send_message(message.chat.id, build_tavern_text(), reply_markup=tavern_kb())

    _REGISTER_CITY_HANDLERS_BEFORE_MAIN_MENU_RECOVERY_17_30_1_3(bot)

    @bot.message_handler(func=lambda message: str(getattr(message, 'text', '') or '') == '📋 Меню')
    def open_main_menu_17_30_1_3(message):
        try:
            from handlers.crystal_shop import _close_shop_session
            _close_shop_session(bot, message.from_user.id)
        except Exception:
            pass
        bot.send_message(message.chat.id, build_account_menu_text_17_30_1_4(message.from_user.id), reply_markup=account_menu_kb_17_30_1_4())

def build_account_menu_text_17_30_1_4(user_id):
    from systems.timed_exp_bonus_system import get_exp_bonus_account_summary
    summary = get_exp_bonus_account_summary(user_id)
    lines = ['📋 Меню', '', f'🆔 ID: {int(user_id)}', f"📅 Дата реєстрації: {_format_registration_date_kyiv_18_31_4a(_format_account_utc_17_30_1_1(summary.get('registered_at')))}"]
    if summary.get('active'):
        lines.extend(['💎 Premium: активний', '📈 Бонус за вбивство мобів: +25% EXP', f"⏳ Діє до: {_format_account_utc_17_30_1_1(summary.get('expires_at'))}"])
    else:
        lines.append('💎 Premium: неактивний')
    lines.extend(['', 'Оберіть розділ:'])
    return '\n'.join(lines)

def account_menu_kb_17_30_1_4():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row('💎 Магазин кристалів', '🏆 Рейтинг')
    kb.row('📖 Про гру', '🔗 Корисні посилання')
    # ROM_STAGE_18_29_4D_EVENT_MENU_ROW
    kb.row('📜 Хроніки світу', '🎉 Івенти')
    kb.add('🔙 Назад')
    return kb

def _online_presence_block_18_22_7(user_id, *, city=False):
    from systems.player_interaction_system import get_online_player_counts
    result = get_online_player_counts(user_id)
    if not result.get('success'):
        return '👥 Гравці:\n🟢 Дані про онлайн тимчасово недоступні'
    location_label = 'У Місті' if city else 'У цій локації'
    return f"👥 Гравці:\n🟢 Усього онлайн: {int(result.get('online_total') or 0)}\n📍 {location_label}: {int(result.get('online_here') or 0)}"

def build_main_menu_text(user_id, show_location_description=False):
    text = _BUILD_MAIN_MENU_TEXT_BEFORE_EXP_BONUS_STATUS_17_30_1_1(user_id, show_location_description=show_location_description)
    return text.rstrip() + '\n\n' + _online_presence_block_18_22_7(user_id, city=False)
