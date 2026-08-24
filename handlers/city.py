# ROM 17.11.2.1 CITY CRAFT TAVERN TEXT CLEANUP
# ROM 17.11.2 COMPACT TEXT LOCATION DESCRIPTION
# ROM 17.11.1.2 TRADE SUBMENU CITY BUTTON RECOVERY
# ROM 17.11.1.1 BASE EQUIPMENT CONTEXT NAVIGATION RECOVERY
# ROM 17.11.1 TRADE DISTRICT TEXT NAVIGATION
# ROM 17.10.1 ITEM QUANTITY DISPLAY FORMAT
from telebot import types

from data.locations import LOCATIONS
from data.mobs import get_mobs_for_location

from db import (
    EQUIPMENT_SLOTS,

    get_current_location,
    get_player_stats,
    get_current_hp,
    get_max_hp,
    get_user_energy,
    get_inventory_used_slots,
    get_bag_capacity,

    get_contract_status,

    sell_all_trash,
    buy_item_for_gold,

    get_equipped_items_for_repair,
    get_total_repair_cost,
    repair_all_equipped,
    repair_equipped_item,
    get_wallet,
    format_gold,

    get_common_equipment_shop_offer,
    get_common_equipment_shop_suboffers,

    create_common_equipment_shop_preview,
    get_shop_preview_item,
    get_shop_preview_weapon_damage_text,
    confirm_common_equipment_shop_preview,
    cancel_common_equipment_shop_preview,

    get_sellable_equipment_items,
    sell_inventory_item_to_trader,
    get_item_by_inventory_id_full,
    get_armor_type_label,
    get_item_subtype_label,
    is_armor_slot,
    process_passive_regeneration,)

from keyboards import (
    city_kb,
    trader_kb,
    craft_kb,
    guild_kb,
    townhall_kb,
    tavern_kb,
    alchemist_kb,
    blacksmith_kb,
    main_kb
)

from systems.potion_system import (
    POTIONS,
    ALCHEMIST_SHOP,
    get_alchemist_potion_stock_17_19_3,
    buy_alchemist_potion_17_19_3,
    sell_alchemist_potion_17_19_3
)


SELL_EQUIPMENT_ITEMS_PER_PAGE = 10
TRADE_DISTRICT_BACK_BUTTON_17_11_1 = "🔙 Торговий ряд"
TRADE_DISTRICT_CITY_BUTTON_17_11_1 = "⬅️ Місто"


# ==============================
# HELPERS: CITY TEXTS
# ==============================

def build_city_text(user_id):
    location_id = get_current_location(user_id)
    location = LOCATIONS.get(location_id, LOCATIONS["start_path"])

    return (
        f"🏙️ Місто\n\n"
        f"📍 Регіон:\n"
        f"{location['name']}\n\n"
        f"Ти стоїш на центральній площі табору мандрівників. "
        f"Навколо чути дзвін ковадла, запах трав від лавки алхіміка "
        f"та гомін найманців біля дошки контрактів.\n\n"
        f"Куди підеш?\n\n"
        f"• 🛒 Торговий ряд — купівля та продаж\n"
        f"• ⚒️ Ремісничий квартал — коваль і алхімік\n"
        f"• 📜 Гільдія Найманців — щоденні контракти\n"
        f"• 🏛️ Ратуша — щоденні й майбутні міські доручення\n"
        f"• 🍺 Таверна — відпочинок і чутки"
    )


def build_trade_district_text(user_id):
    gold = get_wallet(user_id)

    return (
        f"🛒 Торговий ряд\n\n"
        f"💰 Твоє золото: {format_gold(gold)}\n\n"
        f"Вузька вулиця заставлена возами, ящиками та прилавками. "
        f"Торговці скуповують сірий лут, непотрібне спорядження "
        f"і продають прості речі для мандрівників."
    )


def build_craft_district_text(user_id):
    gold = get_wallet(user_id)

    return (
        f"⚒️ Ремісничий квартал\n\n"
        f"💰 Твоє золото: {format_gold(gold)}\n\n"
        f"Тут пахне вугіллям, розпеченим металом і настоями трав. "
        f"Коваль лагодить спорядження, а алхімік продає зілля "
        f"для тих, хто збирається повернутися на полювання.\n\n"
        f"Доступні місця:\n"
        f"• ⚒️ Коваль — ремонт спорядження\n"
        f"• 🧪 Алхімік — купівля зілля"
    )


def build_guild_district_text(user_id):
    status = get_contract_status(user_id)

    text = (
        f"📜 Гільдія Найманців\n\n"
        f"На старій дошці висять замовлення від варти, торговців "
        f"і мандрівників. Тут беруть роботу ті, хто не боїться "
        f"вийти за межі табору.\n\n"
    )

    if not status["exists"]:
        text += "❌ Персонажа не знайдено."
        return text

    if not status["unlocked"]:
        text += (
            f"🔒 Контракти відкриються з 5 рівня.\n"
            f"👤 Твій рівень: {status['level']}\n"
        )
        return text

    text += (
        f"📆 Сьогодні здано контрактів: "
        f"{status['completed_today']}/{status['daily_limit']}\n"
    )

    active = status["active_contract"]

    if active:
        if active.get("completed"):
            text += (
                f"\n✅ Виконаний контракт очікує здачі:\n"
                f"🎯 Ціль: {active['target_mob_name']}\n"
                f"📈 Прогрес: {active['current_kills']}/{active['target_kills']}\n"
                f"✨ Нагорода: {active['reward_exp']} EXP\n\n"
                f"Зайди до дошки контрактів, щоб здати його."
            )
        else:
            text += (
                f"\n📌 Активний контракт:\n"
                f"🎯 Ціль: {active['target_mob_name']}\n"
                f"📈 Прогрес: {active['current_kills']}/{active['target_kills']}\n"
                f"✨ Нагорода після здачі: {active['reward_exp']} EXP\n"
            )
    else:
        text += "\n✅ Можна переглянути дошку контрактів."

    return text


def build_townhall_text():
    return (
        f"🏛️ Ратуша\n\n"
        f"Усередині тихо. На стінах висять старі карти околиць, "
        f"а за великим столом лежать списки податків, звіти варти "
        f"та прохання мешканців.\n\n"
        f"Тут можна отримати щоденне завдання від місцевих жителів.\n\n"
        f"Доступні дії:\n"
        f"• 📆 Щоденне завдання"
    )


def build_tavern_text():
    return (
        f"🍺 Таверна\n\n"
        f"Усередині тепло, пахне юшкою, свіжим хлібом і димом від каміна. "
        f"Мандрівники обмінюються чутками про небезпечних істот, "
        f"елітних ворогів і старі руїни за межами табору.\n\n"
        f"Поки що таверна працює як атмосферне місце для майбутніх функцій.\n\n"
        f"ℹ️ Пізніше тут можна буде додати:\n"
        f"• 🛏️ Відпочинок для прискорення відновлення HP\n"
        f"• 🍲 Їжу з тимчасовими бонусами\n"
        f"• 🗣️ Чутки про елітних мобів або босів"
    )


def get_nearby_mobs_for_level(player_level, location_id):
    mobs = get_mobs_for_location(location_id)
    available = []

    for mob in mobs:
        mob_level = int(mob.get("level", 1))
        min_player_level = int(mob.get("min_player_level", 1))

        if min_player_level <= player_level and player_level - 1 <= mob_level <= player_level + 1:
            available.append(mob)

    if not available:
        for mob in mobs:
            if int(mob.get("min_player_level", 1)) <= player_level:
                available.append(mob)

    return available


def build_contracts_short_status(user_id):
    status = get_contract_status(user_id)

    if not status["exists"]:
        return "📜 Контракти: недоступно\n"

    if not status["unlocked"]:
        return "📜 Контракти: 🔒 з 5 рівня\n"

    completed = status["completed_today"]
    daily_limit = status["daily_limit"]
    active = status["active_contract"]

    text = f"📜 Контракти: {completed}/{daily_limit}\n"

    if active:
        if active.get("completed"):
            text += (
                f"✅ Контракт виконано: "
                f"{active['target_mob_name']} "
                f"{active['current_kills']}/{active['target_kills']} — здати в Гільдії\n"
            )
        else:
            text += (
                f"📌 Активний контракт: "
                f"{active['target_mob_name']} "
                f"{active['current_kills']}/{active['target_kills']}\n"
            )

    return text


def build_main_menu_text(user_id):
    process_passive_regeneration(user_id)
    location_id = get_current_location(user_id)
    location = LOCATIONS.get(location_id, LOCATIONS["start_path"])

    stats = get_player_stats(user_id)

    if stats:
        _, _, _, _, _, lvl = stats
    else:
        lvl = 1

    current_hp = get_current_hp(user_id)
    max_hp = get_max_hp(user_id)

    energy_data = get_user_energy(user_id)
    energy = energy_data["energy"]
    max_energy = energy_data["max_energy"]

    used_slots = get_inventory_used_slots(user_id)
    capacity = get_bag_capacity(user_id)

    contracts_text = build_contracts_short_status(user_id)

    nearby_mobs = get_nearby_mobs_for_level(lvl, location_id)

    mobs_text = ""

    if nearby_mobs:
        for mob in nearby_mobs:
            attack_icon = "⚔️" if mob.get("attack_type") == "physical" else "🔮"

            mobs_text += (
                f"• {attack_icon} {mob['name']} — "
                f"рівень {mob['level']}\n"
            )
    else:
        mobs_text = "• Навколо поки тихо...\n"

    text = (
        f"🏕️ Табір мандрівників\n\n"
        f"📍 Поточна зона:\n"
        f"{location['name']}\n\n"
        f"📖 {location['description']}\n\n"

        f"Під ногами волога земля, поруч потріскує багаття, "
        f"а за межами табору вже чути рух диких звірів. "
        f"Тут шукачі пригод готуються до наступного полювання.\n\n"

        f"👤 Твій рівень: {lvl}\n"
        f"❤️ Здоров’я: {current_hp}/{max_hp}\n"
        f"😴 Втома: {energy}/{max_energy}\n"
        f"🎒 Сумка: {used_slots}/{capacity}\n"
        f"{contracts_text}\n"

        f"👀 Поблизу твого рівня можна зустріти:\n"
        f"{mobs_text}\n"

        f"Доступні дії:\n"
        f"🔎 Полювання — вийти за межі табору\n"
        f"🗺️ Мапа — переглянути напрямки та місто\n"
        f"👤 Профіль — персонаж, інвентар і спорядження\n"
        f"👀 Роззирнутися — оновити стан персонажа"
    )

    return text


# ==============================
# HELPERS: SERVICES
# ==============================

# ROM 17.19.3 ALCHEMIST POTION BUY SELL
_ALCHEMIST_INPUT_17_19_3 = {}

# ROM 17.19.3.6 ALCHEMIST SELL QUANTITY CONTROLS

# ROM 17.19.3.5 ALCHEMIST BUY RETURN POTION STACK NORMALIZATION

# ROM 17.19.3.4 ALCHEMIST CATALOG ORDER AND DB RECOVERY
def alchemist_reply_kb_17_19_3_1():
    """Persistent Alchemist navigation: two actions in one row, return below."""
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    kb.row("🛒 Купити зілля", "💰 Продати зілля")
    kb.row("🔙 Ремісничий квартал")
    return kb


def build_alchemist_root_17_19_3(user_id):
    gold=get_wallet(user_id); kb=types.InlineKeyboardMarkup(row_width=1)
    kb.add(types.InlineKeyboardButton("🛒 Купити зілля",callback_data="alchemist:buy"))
    kb.add(types.InlineKeyboardButton("💰 Продати зілля",callback_data="alchemist:sell"))
    return f"🧪 Алхімік\n\n💰 Твоє золото: {format_gold(gold)}\n\nОберіть дію:",kb

def build_alchemist_buy_list_17_19_3(user_id):
    gold = get_wallet(user_id)
    kb = types.InlineKeyboardMarkup(row_width=1)
    text = (
        f"🛒 Купівля зіль\n\n"
        f"💰 Твоє золото: {format_gold(gold)}\n\n"
        f"Оберіть зілля для перегляду покупки:\n\n"
    )
    for item_id in ALCHEMIST_SHOP:
        potion = POTIONS[item_id]
        effect = f"+{potion['restore']} {'HP' if potion['type'] == 'hp' else 'MP'}"
        text += (
            f"{potion['name']}\n"
            f"Ефект: {effect}\n"
            f"Ціна: {format_gold(potion['buy_price'])}\n"
            f"Стак: {potion['max_stack']}\n\n"
        )
        kb.add(types.InlineKeyboardButton(
            text=f"{potion['name']} — {format_gold(potion['buy_price'])}",
            callback_data=f"alchemist:buyitem:{item_id}",
        ))
    return text, kb

def build_alchemist_buy_preview_17_19_3(user_id,item_id,quantity=1):
    potion=POTIONS.get(int(item_id)); quantity=max(1,min(999,int(quantity)))
    if not potion: return "❌ Зілля не знайдено.",types.InlineKeyboardMarkup()
    total=round(float(potion["buy_price"])*quantity,2); gold=get_wallet(user_id)
    effect=f"+{potion['restore']} {'HP' if potion['type']=='hp' else 'MP'}"
    text=(f"🛒 Купівля зілля\n\n{potion['name']}\nЕфект: {effect}\nЦіна за одне: {format_gold(potion['buy_price'])}\n📦 Кількість: {quantity}\n💳 Загальна вартість: {format_gold(total)}\n💰 Твоє золото: {format_gold(gold)}")
    kb=types.InlineKeyboardMarkup(row_width=3)
    kb.row(types.InlineKeyboardButton("➖",callback_data=f"alchemist:buyset:{item_id}:{max(1,quantity-1)}"),types.InlineKeyboardButton(f"×{quantity}",callback_data=f"alchemist:buyqty:{item_id}"),types.InlineKeyboardButton("➕",callback_data=f"alchemist:buyset:{item_id}:{min(999,quantity+1)}"))
    kb.add(types.InlineKeyboardButton("✏️ Вказати кількість",callback_data=f"alchemist:buyqty:{item_id}"))
    kb.add(types.InlineKeyboardButton(f"✅ Купити за {format_gold(total)}",callback_data=f"alchemist:buydo:{item_id}:{quantity}"))
    kb.add(types.InlineKeyboardButton("🔙 До зіль",callback_data="alchemist:buy"))
    return text,kb

def build_alchemist_sell_list_17_19_3(user_id):
    rows=get_alchemist_potion_stock_17_19_3(user_id); kb=types.InlineKeyboardMarkup(row_width=1)
    text=f"💰 Продаж зіль\n\n💰 Твоє золото: {format_gold(get_wallet(user_id))}\n\n"
    available=[r for r in rows if r['available']>0]
    if not available: text+="У тебе немає доступних зіль для продажу."
    else:
        text+="Оберіть зілля:\n"
        for r in available: kb.add(types.InlineKeyboardButton(f"{r['name']} ×{r['available']} — {format_gold(r['sell_price'])}/шт.",callback_data=f"alchemist:sellitem:{r['item_id']}"))
    kb.add(types.InlineKeyboardButton("🔙 До Алхіміка",callback_data="alchemist:root")); return text,kb

def build_alchemist_sell_preview_17_19_3(user_id,item_id,quantity=1):
    potion = POTIONS.get(int(item_id))
    stock = next(
        (row for row in get_alchemist_potion_stock_17_19_3(user_id)
         if row["item_id"] == int(item_id)),
        None,
    )
    available = int((stock or {}).get("available", 0))
    if not potion or available <= 0:
        return build_alchemist_sell_list_17_19_3(user_id)

    quantity = max(1, min(available, int(quantity)))
    total = round(float(potion["sell_price"]) * quantity, 2)
    text = (
        f"💰 Продаж зілля\n\n"
        f"{potion['name']}\n"
        f"🎒 Доступно: {available}\n"
        f"🔒 Зарезервовано: {int((stock or {}).get('reserved', 0))}\n"
        f"Ціна за одне: {format_gold(potion['sell_price'])}\n"
        f"📦 Кількість: {quantity}\n"
        f"💰 Отримаєш: {format_gold(total)}"
    )

    kb = types.InlineKeyboardMarkup(row_width=3)
    kb.row(
        types.InlineKeyboardButton(
            "➖",
            callback_data=f"alchemist:sellset:{item_id}:{max(1, quantity - 1)}",
        ),
        types.InlineKeyboardButton(
            f"×{quantity}",
            callback_data=f"alchemist:sellqty:{item_id}",
        ),
        types.InlineKeyboardButton(
            "➕",
            callback_data=f"alchemist:sellset:{item_id}:{min(available, quantity + 1)}",
        ),
    )
    kb.add(types.InlineKeyboardButton(
        f"📦 Продати все ×{available}",
        callback_data=f"alchemist:sellset:{item_id}:{available}",
    ))
    kb.add(types.InlineKeyboardButton(
        "✏️ Вказати кількість",
        callback_data=f"alchemist:sellqty:{item_id}",
    ))
    kb.add(types.InlineKeyboardButton(
        f"✅ Продати за {format_gold(total)}",
        callback_data=f"alchemist:sellconfirm:{item_id}:{quantity}",
    ))
    kb.add(types.InlineKeyboardButton(
        "🔙 До списку",
        callback_data="alchemist:sell",
    ))
    return text, kb

def build_alchemist_sell_confirm_17_19_3(user_id,item_id,quantity):
    potion=POTIONS.get(int(item_id)); quantity=int(quantity); total=round(float(potion['sell_price'])*quantity,2)
    kb=types.InlineKeyboardMarkup(row_width=1); kb.add(types.InlineKeyboardButton("✅ Продати",callback_data=f"alchemist:selldo:{item_id}:{quantity}")); kb.add(types.InlineKeyboardButton("❌ Скасувати",callback_data=f"alchemist:sellitem:{item_id}"))
    return f"Продати {potion['name']} ×{quantity}?\n\nЦіна за одне: {format_gold(potion['sell_price'])}\nОтримаєш: {format_gold(total)}",kb

def build_alchemist_catalog(user_id):
    gold = get_wallet(user_id)

    kb = types.InlineKeyboardMarkup()

    text = (
        f"🧪 Алхімік\n\n"
        f"💰 Твоє золото: {format_gold(gold)}\n\n"
        f"Алхімік продає зілля для виживання в бою.\n\n"
        f"Асортимент:\n\n"
    )

    for item_id in ALCHEMIST_SHOP:
        potion = POTIONS[item_id]

        if potion["type"] == "hp":
            effect = f"+{potion['restore']} HP"
        else:
            effect = f"+{potion['restore']} MP"

        text += (
            f"{potion['name']}\n"
            f"Ефект: {effect}\n"
            f"Ціна: {format_gold(potion['buy_price'])}\n"
            f"Стак: {potion['max_stack']}\n\n"
        )

        kb.add(types.InlineKeyboardButton(
            text=f"Купити: {potion['name']} — {format_gold(potion['buy_price'])}",
            callback_data=f"buy_potion_{item_id}"
        ))

    text += (
        f"⚠️ Мана ще не реалізована, тому сині зілля можна купити на майбутнє, "
        f"але використати поки не можна."
    )

    return text, kb



# ==============================
# ✅ BLACKSMITH MENU TEXT V2
# ==============================

def build_blacksmith_text(user_id):
    gold = get_wallet(user_id)

    return (
        "⚒️ Коваль\n\n"
        "Біля розпеченого горна працює досвідчений коваль. "
        "Він може полагодити твоє спорядження або посилити його за допомогою каменів заточки.\n\n"
        "Доступні дії:\n"
        "• 🛠️ Ремонт спорядження\n"
        "• ✨ Заточка спорядження\n\n"
        f"💰 Твоє золото: {gold:.2f} 💰"
    )

def build_blacksmith_repair_text(user_id):
    equipped_items = get_equipped_items_for_repair(user_id)
    total_cost = get_total_repair_cost(user_id)
    gold = get_wallet(user_id)

    text = (
        f"⚒️ КОВАЛЬ: РЕМОНТ ТА КУЗНЯ\n\n"
        f"💰 Твоє золото: {format_gold(gold)}\n\n"
        f"📦 Стан твого спорядження:\n\n"
    )

    kb = types.InlineKeyboardMarkup()

    damaged_count = 0

    for item in equipped_items:
        slot = item["slot"]
        name = item["name"]
        durability = item["durability"]
        repair_cost = item["repair_cost"]
        is_broken = item["is_broken"]
        inventory_id = item["inventory_id"]

        if inventory_id is None:
            text += f"{slot}: порожньо\n\n"
            continue

        broken_text = " ⚠️ [ЗЛАМАНО]" if is_broken else ""

        text += (
            f"{slot}: {name}\n"
            f"🛠️ Міцність: {durability}/100{broken_text}\n"
            f"💰 Ремонт: {format_gold(repair_cost)}\n\n"
        )

        if repair_cost > 0:
            damaged_count += 1

            kb.add(types.InlineKeyboardButton(
                text=f"🛠️ Ремонт: {name} — {format_gold(repair_cost)}",
                callback_data=f"repair_prompt_one_v3_{inventory_id}"
            ))

    text += (
        f"💳 Разом за повний ремонт: {format_gold(total_cost)}\n"
        f"💰 Твоє золото: {format_gold(gold)}\n\n"
    )

    if damaged_count <= 0:
        text += "✅ Усе спорядження вже в ідеальному стані."
    elif gold < total_cost:
        text += (
            "❌ Недостатньо золота для повного ремонту.\n"
            "ℹ️ Можеш відремонтувати окрему річ, якщо вистачає золота."
        )
    else:
        text += "👇 Можна полагодити все або окрему річ."

    if total_cost > 0:
        kb.add(types.InlineKeyboardButton(
            text=f"🛠️ Полагодити все за {format_gold(total_cost)}",
            callback_data="repair_prompt_all_v3"
        ))

    return text, kb


def build_common_equipment_shop_text(user_id):
    offers = get_common_equipment_shop_offer(user_id)
    gold = get_wallet(user_id)

    text = (
        f"⚪ Базове спорядження\n\n"
        f"💰 Твоє золото: {format_gold(gold)}\n\n"
        f"Торговець продає прості білі речі поточного рівня персонажа.\n"
        f"Перед купівлею ти побачиш точні характеристики предмета.\n\n"
        f"Одяг поки має універсальний тип, але для зброї та другої руки "
        f"можна вибрати конкретний вид предмета.\n\n"
        f"Оберіть слот:"
    )

    kb = types.InlineKeyboardMarkup(row_width=1)

    for offer in offers:
        slot_key = offer["slot_key"]

        if slot_key in ["main_hand", "off_hand"]:
            callback_data = f"common_equipment_slot:{slot_key}"
        else:
            callback_data = f"buy_common_equipment:{slot_key}:"

        kb.add(types.InlineKeyboardButton(
            text=(
                f"{offer['slot_name']} — "
                f"{format_gold(offer['price'])} "
                f"(рівень {offer['item_level']})"
            ),
            callback_data=callback_data
        ))

    return text, kb


def build_common_equipment_slot_choice_text(user_id, slot_key):
    offers = get_common_equipment_shop_suboffers(user_id, slot_key)
    gold = get_wallet(user_id)

    if slot_key == "main_hand":
        title = "🗡️ Вибір зброї"
        description = (
            "Оберіть конкретний тип базової зброї.\n\n"
            "Фізична зброя використовує STR або DEX.\n"
            "Магічна зброя використовує INT/WIS і магічна шкода.\n"
            "Дворучна зброя блокує другу руку."
        )
    elif slot_key == "off_hand":
        title = "🛡️ Вибір другої руки"
        description = (
            "Оберіть конкретний предмет для другої руки.\n\n"
            "Щит дає PDEF і STA.\n"
            "Талісман дає MDEF і WIS.\n"
            "Кинджал дає DEX/STR і не є танковим предметом."
        )
    else:
        title = "⚪ Базове спорядження"
        description = "Оберіть предмет."

    text = (
        f"{title}\n\n"
        f"💰 Твоє золото: {format_gold(gold)}\n\n"
        f"{description}\n\n"
        f"Доступні варіанти:"
    )

    kb = types.InlineKeyboardMarkup(row_width=1)

    for offer in offers:
        hands_text = ""

        if slot_key == "main_hand":
            if offer["hands"] == 2:
                hands_text = " — дворучна"
            else:
                hands_text = " — одноручна"

        kb.add(types.InlineKeyboardButton(
            text=(
                f"{offer['name']}{hands_text} — "
                f"{format_gold(offer['price'])} "
                f"(рівень {offer['item_level']})"
            ),
            callback_data=f"buy_common_equipment:{slot_key}:{offer['profile_key']}"
        ))

    kb.add(types.InlineKeyboardButton(
        text="⬅️ Назад до слотів",
        callback_data="common_equipment_back_to_slots"
    ))

    return text, kb


def format_shop_preview_bonuses(b_str, b_dex, b_int, b_wis, b_sta, pdef, mdef):
    bonuses = []

    if b_str:
        bonuses.append(f"💪 Сила +{b_str}")
    if b_dex:
        bonuses.append(f"🎯 Спритність +{b_dex}")
    if b_int:
        bonuses.append(f"🔮 Інтелект +{b_int}")
    if b_wis:
        bonuses.append(f"🦉 Мудрість +{b_wis}")
    if b_sta:
        bonuses.append(f"🛡 Витривалість +{b_sta}")
    if pdef:
        bonuses.append(f"🛡 Фіз. захист +{pdef}")
    if mdef:
        bonuses.append(f"🔮 Маг. захист +{mdef}")

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

    if f"[{armor_label}]" in name:
        return name

    marker = " рівня"

    if marker in name:
        index = name.rfind(marker)
        before_level = name[:index]
        after_level = name[index:]
        parts = before_level.rsplit(" ", 1)

        if len(parts) == 2 and parts[1].isdigit():
            return f"{parts[0]} [{armor_label}] {parts[1]}{after_level}"

    return f"{name} [{armor_label}]"


def build_base_equipment_return_view_17_11_1_1(user_id, slot_key=None):
    """Return to the closest valid base-equipment list after preview completion."""
    if slot_key in ("main_hand", "off_hand"):
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
        text = "❌ Попередній перегляд предмета не знайдено або застарів."

        kb = types.InlineKeyboardMarkup()
        kb.add(types.InlineKeyboardButton(
            text="⬅️ Назад до базового спорядження",
            callback_data="common_equipment_back_to_slots"
        ))

        return text, kb

    (
        item_id,
        name,
        type_,
        rarity,
        category,
        slot_key,
        weapon_hands,
        max_stack,
        sell_price,
        b_str,
        b_dex,
        b_int,
        b_wis,
        b_sta,
        pdef,
        mdef,
        item_level,
        item_subtype,
        weapon_min_damage,
        weapon_max_damage,
        weapon_min_magic_damage,
        weapon_max_magic_damage,
        weapon_attack_type,
        armor_type,
        price
    ) = preview

    gold = get_wallet(user_id)
    slot_name = EQUIPMENT_SLOTS.get(slot_key, slot_key)
    display_name = build_shop_preview_display_name(
        name=name,
        slot_key=slot_key,
        armor_type=armor_type
    )

    text = (
        f"🛒 Перегляд покупки\n\n"
        f"📦 {display_name}\n\n"
        f"🧰 Тип: спорядження\n"
        f"🎯 Слот: {slot_name}\n"
        f"🏷 Рівень предмета: {item_level}\n"
    )

    if is_armor_slot(slot_key):
        text += (
            f"🧵 Тип броні: {get_armor_type_label(armor_type)}\n"
            f"🧭 Класова сумісність: ✅ Підходить твоєму класу\n"
        )

    elif slot_key in ["main_hand", "off_hand"]:
        text += (
            f"⚔️ Тип предмета: {get_item_subtype_label(item_subtype)}\n"
            f"🧭 Класова сумісність: ✅ Підходить твоєму класу\n"
        )

    if slot_key == "main_hand":
        if weapon_hands == 2:
            text += "👐 Тип зброї: дворучна\n"
            text += "⚠️ Дворучна зброя блокує другу руку.\n"
        else:
            text += "✋ Тип зброї: одноручна\n"

        weapon_text = get_shop_preview_weapon_damage_text(item_id)

        if weapon_text:
            text += f"{weapon_text}\n"

    text += "🧱 Міцність: 100/100\n"

    bonuses = format_shop_preview_bonuses(
        b_str,
        b_dex,
        b_int,
        b_wis,
        b_sta,
        pdef,
        mdef
    )

    if bonuses:
        text += "\n📊 Бонуси:\n"

        for bonus in bonuses:
            text += f"• {bonus}\n"
    else:
        text += "\n📊 Бонуси: немає\n"

    text += (
        f"\n💳 Ціна: {format_gold(price)}\n"
        f"💰 Твоє золото: {format_gold(gold)}\n\n"
        f"Купити цей предмет?"
    )

    kb = types.InlineKeyboardMarkup()

    kb.add(types.InlineKeyboardButton(
        text=f"✅ Купити за {format_gold(price)}",
        callback_data=f"common_shop_confirm:{item_id}"
    ))

    kb.add(types.InlineKeyboardButton(
        text="❌ Скасувати",
        callback_data=f"common_shop_cancel:{item_id}"
    ))

    return text, kb


def build_sell_equipment_list_text(user_id, page=0):
    items = get_sellable_equipment_items(user_id)
    gold = get_wallet(user_id)

    if not items:
        text = (
            f"🧰 Продаж спорядження\n\n"
            f"💰 Твоє золото: {format_gold(gold)}\n\n"
            f"У тебе немає невдягненого спорядження для продажу.\n\n"
            f"ℹ️ Вдягнені речі не показуються у цьому списку."
        )

        kb = types.InlineKeyboardMarkup()
        return text, kb

    total_items = len(items)
    total_pages = max(1, (total_items + SELL_EQUIPMENT_ITEMS_PER_PAGE - 1) // SELL_EQUIPMENT_ITEMS_PER_PAGE)

    if page < 0:
        page = 0

    if page >= total_pages:
        page = total_pages - 1

    start = page * SELL_EQUIPMENT_ITEMS_PER_PAGE
    end = start + SELL_EQUIPMENT_ITEMS_PER_PAGE
    page_items = items[start:end]

    text = (
        f"🧰 Продаж спорядження\n\n"
        f"💰 Твоє золото: {format_gold(gold)}\n\n"
        f"Торговець готовий купити невдягнені речі з твого інвентаря.\n"
        f"Вдягнене спорядження продавати не можна.\n\n"
        f"📄 Сторінка: {page + 1}/{total_pages}\n\n"
        f"Оберіть предмет:"
    )

    kb = types.InlineKeyboardMarkup()

    for item in page_items:
        (
            inv_id,
            item_id,
            name,
            type_,
            rarity,
            category,
            slot_key,
            weapon_hands,
            quantity,
            max_stack,
            durability,
            b_str,
            b_dex,
            b_int,
            b_wis,
            b_sta,
            pdef,
            mdef,
            sell_price
        ) = item

        quantity = quantity or 1
        sell_price = sell_price or 0
        total_price = round(quantity * sell_price, 2)

        durability_text = ""

        if durability is not None:
            durability_text = f" [{durability}/100]"

        kb.add(types.InlineKeyboardButton(
            text=f"{name}{durability_text} — {format_gold(total_price)}",
            callback_data=f"sell_eq_confirm:{inv_id}:{page}"
        ))

    nav_buttons = []

    if page > 0:
        nav_buttons.append(types.InlineKeyboardButton(
            text="⬅️ Назад",
            callback_data=f"sell_eq_page:{page - 1}"
        ))

    if page < total_pages - 1:
        nav_buttons.append(types.InlineKeyboardButton(
            text="➡️ Далі",
            callback_data=f"sell_eq_page:{page + 1}"
        ))

    if nav_buttons:
        kb.add(*nav_buttons)

    return text, kb


def build_sell_equipment_confirm_text(user_id, inventory_id, page=0):
    item = get_item_by_inventory_id_full(inventory_id)

    if not item:
        text = "❌ Предмет не знайдено."

        kb = types.InlineKeyboardMarkup()
        kb.add(types.InlineKeyboardButton(
            text="⬅️ Назад",
            callback_data=f"sell_eq_page:{page}"
        ))

        return text, kb

    (
        inv_id,
        item_id,
        name,
        type_,
        rarity,
        category,
        slot_key,
        weapon_hands,
        quantity,
        max_stack,
        durability,
        b_str,
        b_dex,
        b_int,
        b_wis,
        b_sta,
        pdef,
        mdef,
        sell_price
    ) = item

    quantity = quantity or 1
    sell_price = sell_price or 0
    total_price = round(quantity * sell_price, 2)

    text = (
        f"💰 Підтвердження продажу\n\n"
        f"Ти точно хочеш продати цей предмет торговцю?\n\n"
        f"📦 {name} ×{quantity}\n"
        f"💰 Ціна: {format_gold(total_price)}\n"
    )

    if durability is not None:
        text += f"🛠️ Міцність: {durability}/100\n"

    text += "\n⚠️ Після продажу предмет зникне з інвентаря."

    kb = types.InlineKeyboardMarkup()

    kb.add(types.InlineKeyboardButton(
        text=f"✅ Продати за {format_gold(total_price)}",
        callback_data=f"sell_eq_do:{inventory_id}:{page}"
    ))

    kb.add(types.InlineKeyboardButton(
        text="❌ Назад",
        callback_data=f"sell_eq_page:{page}"
    ))

    return text, kb


# ==============================
# HANDLERS
# ==============================

def trade_district_submenu_kb_17_11_1():
    """Reply navigation used inside Trade District sell/buy submenus."""
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
    kb.add(TRADE_DISTRICT_BACK_BUTTON_17_11_1)
    kb.add(TRADE_DISTRICT_CITY_BUTTON_17_11_1)
    return kb


def send_trade_district_submenu_17_11_1(bot, chat_id):
    """Replace persistent Trade District actions with contextual navigation."""
    bot.send_message(
        chat_id,
        "Оберіть дію зі списку нижче.",
        reply_markup=trade_district_submenu_kb_17_11_1(),
    )


def register_city_handlers(bot):

    # ==============================
    # CITY ROOT
    # ==============================

    @bot.message_handler(func=lambda m: m.text == "🏙️ Місто")
    def show_city(message):
        user_id = message.from_user.id

        bot.send_message(
            message.chat.id,
            build_city_text(user_id),
            reply_markup=city_kb()
        )

    @bot.message_handler(func=lambda m: m.text == "👀 Роззирнутися")
    def look_around(message):
        user_id = message.from_user.id

        bot.send_message(
            message.chat.id,
            build_main_menu_text(user_id),
            reply_markup=main_kb()
        )

    @bot.message_handler(func=lambda m: m.text in ("🔙 Місто", "⬅️ Місто"))
    def back_to_city(message):
        user_id = message.from_user.id

        bot.send_message(
            message.chat.id,
            build_city_text(user_id),
            reply_markup=city_kb()
        )

    # ==============================
    # DISTRICTS
    # ==============================

    @bot.message_handler(func=lambda m: m.text == "🛒 Торговий ряд")
    def show_trade_district(message):
        user_id = message.from_user.id

        bot.send_message(
            message.chat.id,
            build_trade_district_text(user_id),
            reply_markup=trader_kb()
        )

    @bot.message_handler(func=lambda m: m.text == "⚒️ Ремісничий квартал")
    def show_craft_district(message):
        user_id = message.from_user.id

        bot.send_message(
            message.chat.id,
            build_craft_district_text(user_id),
            reply_markup=craft_kb()
        )

    @bot.message_handler(func=lambda m: m.text == "📜 Гільдія Найманців")
    def show_guild_district(message):
        user_id = message.from_user.id

        bot.send_message(
            message.chat.id,
            build_guild_district_text(user_id),
            reply_markup=guild_kb()
        )

    @bot.message_handler(func=lambda m: m.text == "🏛️ Ратуша")
    def show_townhall(message):
        bot.send_message(
            message.chat.id,
            build_townhall_text(),
            reply_markup=townhall_kb()
        )

    @bot.message_handler(func=lambda m: m.text == "🍺 Таверна")
    def show_tavern(message):
        bot.send_message(
            message.chat.id,
            build_tavern_text(),
            reply_markup=tavern_kb()
        )

    # ==============================
    # DISTRICT BACK BUTTONS
    # ==============================

    @bot.message_handler(func=lambda m: m.text == "🔙 Торговий ряд")
    def back_to_trade_district_message(message):
        user_id = message.from_user.id

        bot.send_message(
            message.chat.id,
            build_trade_district_text(user_id),
            reply_markup=trader_kb()
        )

    @bot.message_handler(func=lambda m: m.text == "🔙 Ремісничий квартал")
    def back_to_craft_district_message(message):
        user_id = message.from_user.id
        _ALCHEMIST_INPUT_17_19_3.pop(int(user_id), None)

        bot.send_message(
            message.chat.id,
            build_craft_district_text(user_id),
            reply_markup=craft_kb()
        )

    @bot.message_handler(func=lambda m: m.text == "🔙 Гільдія Найманців")
    def back_to_guild_district_message(message):
        user_id = message.from_user.id

        bot.send_message(
            message.chat.id,
            build_guild_district_text(user_id),
            reply_markup=guild_kb()
        )

    # ==============================
    # TRADING DISTRICT
    # ==============================

    @bot.message_handler(func=lambda m: m.text == "🪙 Продати весь мотлох")
    def sell_trash(message):
        user_id = message.from_user.id

        result = sell_all_trash(user_id)

        if result["sold_items_count"] == 0:
            bot.send_message(
                message.chat.id,
                "💰 У тебе немає сірого луту для продажу.",
                reply_markup=trader_kb()
            )
            return

        text = "💰 Продаж сірого луту\n\n"

        for line in result["details"]:
            text += f"• {line}\n"

        text += (
            f"\n✅ Отримано золота: {format_gold(result['gold_earned'])}\n"
            f"🎒 Звільнено слотів: {result['freed_slots']}"
        )

        bot.send_message(
            message.chat.id,
            text,
            reply_markup=trader_kb()
        )

    @bot.message_handler(func=lambda m: m.text == "🧰 Продати спорядження")
    def show_sell_equipment(message):
        user_id = message.from_user.id

        text, kb = build_sell_equipment_list_text(user_id, page=0)

        send_trade_district_submenu_17_11_1(bot, message.chat.id)
        bot.send_message(
            message.chat.id,
            text,
            reply_markup=kb
        )

    @bot.callback_query_handler(func=lambda call: call.data.startswith("sell_eq_page:"))
    def sell_equipment_page(call):
        user_id = call.from_user.id
        page = int(call.data.split(":")[1])

        text, kb = build_sell_equipment_list_text(user_id, page=page)

        bot.answer_callback_query(call.id)

        bot.send_message(
            call.message.chat.id,
            text,
            reply_markup=kb
        )

    @bot.callback_query_handler(func=lambda call: call.data.startswith("sell_eq_confirm:"))
    def sell_equipment_confirm(call):
        user_id = call.from_user.id

        parts = call.data.split(":")
        inventory_id = int(parts[1])
        page = int(parts[2]) if len(parts) > 2 else 0

        text, kb = build_sell_equipment_confirm_text(
            user_id=user_id,
            inventory_id=inventory_id,
            page=page
        )

        bot.answer_callback_query(call.id)

        bot.send_message(
            call.message.chat.id,
            text,
            reply_markup=kb
        )

    @bot.callback_query_handler(func=lambda call: call.data.startswith("sell_eq_do:"))
    def sell_equipment_do(call):
        user_id = call.from_user.id

        parts = call.data.split(":")
        inventory_id = int(parts[1])
        page = int(parts[2]) if len(parts) > 2 else 0

        result = sell_inventory_item_to_trader(
            user_id=user_id,
            inventory_id=inventory_id
        )

        bot.answer_callback_query(call.id)

        bot.send_message(
            call.message.chat.id,
            result["message"],
            reply_markup=trade_district_submenu_kb_17_11_1()
        )

        text, kb = build_sell_equipment_list_text(user_id, page=page)

        bot.send_message(
            call.message.chat.id,
            text,
            reply_markup=kb
        )

    # ==============================
    # COMMON EQUIPMENT SHOP
    # ==============================

    @bot.message_handler(func=lambda m: m.text == "⚪ Базове спорядження")
    def show_common_equipment_shop(message):
        user_id = message.from_user.id

        text, kb = build_common_equipment_shop_text(user_id)

        send_trade_district_submenu_17_11_1(bot, message.chat.id)
        bot.send_message(
            message.chat.id,
            text,
            reply_markup=kb
        )

    @bot.callback_query_handler(func=lambda call: call.data == "common_equipment_back_to_slots")
    def common_equipment_back_to_slots(call):
        user_id = call.from_user.id

        text, kb = build_common_equipment_shop_text(user_id)

        bot.answer_callback_query(call.id)

        bot.send_message(
            call.message.chat.id,
            text,
            reply_markup=kb
        )

    @bot.callback_query_handler(func=lambda call: call.data.startswith("common_equipment_slot:"))
    def common_equipment_slot_choice(call):
        user_id = call.from_user.id
        slot_key = call.data.split(":")[1]

        text, kb = build_common_equipment_slot_choice_text(user_id, slot_key)

        bot.answer_callback_query(call.id)

        bot.send_message(
            call.message.chat.id,
            text,
            reply_markup=kb
        )

    @bot.callback_query_handler(func=lambda call: call.data.startswith("buy_common_equipment:"))
    def preview_common_equipment(call):
        user_id = call.from_user.id

        parts = call.data.split(":")
        slot_key = parts[1]
        item_profile = parts[2] if len(parts) > 2 and parts[2] else None

        result = create_common_equipment_shop_preview(
            user_id=user_id,
            slot_key=slot_key,
            item_profile=item_profile
        )

        bot.answer_callback_query(call.id)

        if not result.get("success"):
            bot.send_message(
                call.message.chat.id,
                result["message"],
                reply_markup=trade_district_submenu_kb_17_11_1()
            )
            return

        text, kb = build_common_shop_preview_text(
            user_id=user_id,
            item_id=result["item_id"]
        )

        bot.send_message(
            call.message.chat.id,
            text,
            reply_markup=kb
        )

    @bot.callback_query_handler(func=lambda call: call.data.startswith("common_shop_confirm:"))
    def confirm_common_shop_purchase(call):
        user_id = call.from_user.id
        item_id = int(call.data.split(":")[1])
        slot_key = get_base_equipment_preview_slot_17_11_1_1(user_id, item_id)

        result = confirm_common_equipment_shop_preview(
            user_id=user_id,
            item_id=item_id
        )

        bot.answer_callback_query(call.id)

        bot.send_message(
            call.message.chat.id,
            result["message"],
            reply_markup=trade_district_submenu_kb_17_11_1()
        )

        text, kb = build_base_equipment_return_view_17_11_1_1(user_id, slot_key)

        bot.send_message(
            call.message.chat.id,
            text,
            reply_markup=kb
        )

    @bot.callback_query_handler(func=lambda call: call.data.startswith("common_shop_cancel:"))
    def cancel_common_shop_purchase(call):
        user_id = call.from_user.id
        item_id = int(call.data.split(":")[1])
        slot_key = get_base_equipment_preview_slot_17_11_1_1(user_id, item_id)

        result = cancel_common_equipment_shop_preview(
            user_id=user_id,
            item_id=item_id
        )

        bot.answer_callback_query(call.id)

        bot.send_message(
            call.message.chat.id,
            result["message"],
            reply_markup=trade_district_submenu_kb_17_11_1()
        )

        text, kb = build_base_equipment_return_view_17_11_1_1(user_id, slot_key)

        bot.send_message(
            call.message.chat.id,
            text,
            reply_markup=kb
        )

    @bot.callback_query_handler(func=lambda call: call.data == "back_to_trade_district")
    def back_to_trade_district(call):
        user_id = call.from_user.id

        bot.answer_callback_query(call.id)

        bot.send_message(
            call.message.chat.id,
            build_trade_district_text(user_id),
            reply_markup=trader_kb()
        )

    @bot.callback_query_handler(func=lambda call: call.data == "back_to_trader")
    def back_to_trader_callback(call):
        user_id = call.from_user.id

        bot.answer_callback_query(call.id)

        bot.send_message(
            call.message.chat.id,
            build_trade_district_text(user_id),
            reply_markup=trader_kb()
        )

    # ==============================
    # CRAFT DISTRICT: ALCHEMIST
    # ROM 17.19.3 ALCHEMIST POTION BUY SELL
    @bot.message_handler(func=lambda m: m.text == "🧪 Алхімік")
    def show_alchemist(message):
        user_id = int(message.from_user.id)
        _ALCHEMIST_INPUT_17_19_3.pop(user_id, None)
        text, _ = build_alchemist_root_17_19_3(user_id)
        bot.send_message(
            message.chat.id,
            text,
            reply_markup=alchemist_reply_kb_17_19_3_1(),
        )

    @bot.callback_query_handler(func=lambda call: str(call.data).startswith("alchemist:"))
    def alchemist_trade_17_19_3(call):
        user_id=int(call.from_user.id); data=str(call.data); parts=data.split(":")
        try: bot.answer_callback_query(call.id)
        except Exception: pass
        if data=="alchemist:root": text,kb=build_alchemist_root_17_19_3(user_id)
        elif data=="alchemist:buy": text,kb=build_alchemist_buy_list_17_19_3(user_id)
        elif data=="alchemist:sell": text,kb=build_alchemist_sell_list_17_19_3(user_id)
        elif parts[1]=="buyitem": text,kb=build_alchemist_buy_preview_17_19_3(user_id,int(parts[2]),1)
        elif parts[1]=="buyset": text,kb=build_alchemist_buy_preview_17_19_3(user_id,int(parts[2]),int(parts[3]))
        elif parts[1]=="buyqty":
            _ALCHEMIST_INPUT_17_19_3[user_id]={"mode":"buy","item_id":int(parts[2]),"chat_id":call.message.chat.id}
            bot.send_message(call.message.chat.id,"Введи кількість зіль для купівлі, від 1 до 999."); return
        elif parts[1]=="buydo":
            result=buy_alchemist_potion_17_19_3(user_id,int(parts[2]),int(parts[3]))
            bot.send_message(call.message.chat.id,result['message'],reply_markup=alchemist_reply_kb_17_19_3_1())
            if result.get("success"):
                text,kb=build_alchemist_buy_list_17_19_3(user_id)
            else:
                text,kb=build_alchemist_buy_preview_17_19_3(user_id,int(parts[2]),int(parts[3]))
        elif parts[1]=="sellitem": text,kb=build_alchemist_sell_preview_17_19_3(user_id,int(parts[2]),1)
        elif parts[1]=="sellset": text,kb=build_alchemist_sell_preview_17_19_3(user_id,int(parts[2]),int(parts[3]))
        elif parts[1]=="sellqty":
            _ALCHEMIST_INPUT_17_19_3[user_id]={"mode":"sell","item_id":int(parts[2]),"chat_id":call.message.chat.id}
            bot.send_message(call.message.chat.id,"Введи кількість зіль для продажу."); return
        elif parts[1]=="sellconfirm": text,kb=build_alchemist_sell_confirm_17_19_3(user_id,int(parts[2]),int(parts[3]))
        elif parts[1]=="selldo":
            result=sell_alchemist_potion_17_19_3(user_id,int(parts[2]),int(parts[3])); bot.send_message(call.message.chat.id,result['message'],reply_markup=alchemist_reply_kb_17_19_3_1()); text,kb=build_alchemist_sell_list_17_19_3(user_id)
        else: return
        bot.send_message(call.message.chat.id,text,reply_markup=kb)

    @bot.message_handler(func=lambda m: m.text == "🛒 Купити зілля")
    def alchemist_buy_message_17_19_3_1(message):
        user_id = int(message.from_user.id)
        _ALCHEMIST_INPUT_17_19_3.pop(user_id, None)
        text, kb = build_alchemist_buy_list_17_19_3(user_id)
        bot.send_message(message.chat.id, text, reply_markup=kb)

    @bot.message_handler(func=lambda m: m.text == "💰 Продати зілля")
    def alchemist_sell_message_17_19_3_1(message):
        user_id = int(message.from_user.id)
        _ALCHEMIST_INPUT_17_19_3.pop(user_id, None)
        text, kb = build_alchemist_sell_list_17_19_3(user_id)
        bot.send_message(message.chat.id, text, reply_markup=kb)

    @bot.message_handler(func=lambda m: int(getattr(m.from_user,"id",0)) in _ALCHEMIST_INPUT_17_19_3)
    def alchemist_exact_quantity_17_19_3(message):
        user_id=int(message.from_user.id); state=_ALCHEMIST_INPUT_17_19_3.pop(user_id,None)
        try: quantity=int(str(message.text).strip())
        except Exception: bot.send_message(message.chat.id,"❌ Введи ціле число."); return
        if quantity<1: bot.send_message(message.chat.id,"❌ Кількість має бути більшою за нуль."); return
        if state['mode']=="buy": text,kb=build_alchemist_buy_preview_17_19_3(user_id,state['item_id'],quantity)
        else:
            stock=next((r for r in get_alchemist_potion_stock_17_19_3(user_id) if r['item_id']==state['item_id']),None); available=int((stock or {}).get('available',0))
            if quantity>available: bot.send_message(message.chat.id,f"❌ Доступно для продажу лише {available}."); return
            text,kb=build_alchemist_sell_confirm_17_19_3(user_id,state['item_id'],quantity)
        bot.send_message(message.chat.id,text,reply_markup=kb)

    # CRAFT DISTRICT: BLACKSMITH
    # ==============================

    @bot.message_handler(func=lambda m: m.text == "⚒️ Коваль")
    def show_blacksmith(message):
        user_id = message.from_user.id

        bot.send_message(
            message.chat.id,
            "⚒️ Ти підійшов до Коваля.",
            reply_markup=blacksmith_kb()
        )

        text, kb = build_blacksmith_text(user_id)

        bot.send_message(
            message.chat.id,
            text,
            reply_markup=kb
        )

    @bot.callback_query_handler(func=lambda call: call.data == "repair_all_equipped")
    def repair_all(call):
        user_id = call.from_user.id

        result = repair_all_equipped(user_id)

        bot.answer_callback_query(call.id)

        bot.send_message(
            call.message.chat.id,
            result["message"],
            reply_markup=blacksmith_kb()
        )

        text, kb = build_blacksmith_text(user_id)

        bot.send_message(
            call.message.chat.id,
            text,
            reply_markup=kb
        )

    @bot.callback_query_handler(func=lambda call: call.data.startswith("repair_one_"))
    def repair_one(call):
        user_id = call.from_user.id
        inventory_id = int(call.data.split("_")[2])

        result = repair_equipped_item(user_id, inventory_id)

        bot.answer_callback_query(call.id)

        bot.send_message(
            call.message.chat.id,
            result["message"],
            reply_markup=blacksmith_kb()
        )

        text, kb = build_blacksmith_text(user_id)

        bot.send_message(
            call.message.chat.id,
            text,
            reply_markup=kb
        )

    # ==============================
    # BACK TO MAIN
    # ==============================

    @bot.message_handler(func=lambda m: m.text == "🔙 Назад")
    def back_to_main(message):
        user_id = message.from_user.id

        bot.send_message(
            message.chat.id,
            build_main_menu_text(user_id),
            reply_markup=main_kb()
        )

# 6.0.4 note: refine UI registered globally. Use /refine or text '✨ Заточка'.

# ✅ REFINE BUTTON CITY FALLBACK V1
# refine_menu callback is handled by handlers/refine.py

# ==============================
# ✅ BLACKSMITH REPAIR BUTTON V2
# ==============================

def register_blacksmith_repair_button_v2(bot):
    @bot.message_handler(func=lambda message: message.text == "🛠️ Ремонт")
    def blacksmith_repair_button_v2(message):
        bot.send_message(
            message.chat.id,
            build_blacksmith_repair_text(message.from_user.id),
            reply_markup=blacksmith_kb()
        )

# ==============================
# ✅ BLACKSMITH MENU V2 FINAL TUPLE FIX
# ==============================

# show_blacksmith() у цьому проєкті очікує:
#   text, kb = build_blacksmith_text(user_id)
# Тому build_blacksmith_text() має повертати саме tuple: (text, blacksmith_kb()).


def build_blacksmith_text(user_id):
    gold = get_wallet(user_id)

    text = (
        "⚒️ Коваль\n\n"
        "Біля розпеченого горна працює досвідчений коваль. "
        "Він може полагодити твоє спорядження або посилити його за допомогою каменів заточки.\n\n"
        "Доступні дії:\n"
        "• 🛠️ Ремонт спорядження\n"
        "• ✨ Заточка спорядження\n\n"
        f"💰 Твоє золото: {gold:.2f} 💰"
    )

    return text, blacksmith_kb()


def _normalize_text_kb_result(result, fallback_kb=None):
    """
    Допоміжна функція для старих build_* функцій:
    - якщо функція повертає (text, kb), залишаємо як є;
    - якщо повертає тільки text, додаємо fallback_kb.
    """

    if isinstance(result, tuple):
        if len(result) >= 2:
            return result[0], result[1]
        if len(result) == 1:
            return result[0], fallback_kb

    return result, fallback_kb


def register_blacksmith_repair_button_v2(bot):
    @bot.message_handler(func=lambda message: message.text == "🛠️ Ремонт")
    def blacksmith_repair_button_v2(message):
        result = build_blacksmith_repair_text(message.from_user.id)
        text, kb = _normalize_text_kb_result(result, blacksmith_kb())

        bot.send_message(
            message.chat.id,
            text,
            reply_markup=kb
        )


# ==============================
# ✅ SELL REFINE DISPLAY V1
# ==============================

# 6.0.7a
# Виправляє UI продажу спорядження: у списку продажу і підтвердженні продажу
# заточені предмети мають показувати [+N].
# Механіку продажу не змінює.

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

    # Найчастіші формати:
    # (inventory_id, name, ...)
    # (inventory_id, item_id, name, ...)
    preferred_indexes = [1, 2]

    for index in preferred_indexes:
        if index < len(row) and isinstance(row[index], str):
            value = row[index]
            if value and value not in ["equipment", "weapon", "armor", "common", "uncommon", "rare", "epic"]:
                return index

    # Fallback: перший рядок, схожий на назву предмета.
    for index, value in enumerate(row):
        if not isinstance(value, str):
            continue

        if " рівня" in value:
            return index

        if any(marker in value for marker in ["⚪", "🟢", "🔵", "🟣", "Посох", "Меч", "Кинджал", "Обладунок", "Шолом", "Поножі", "Рукавиці", "Чоботи"]):
            return index

    return None


def _city_refine_display_for_row(row):
    """
    Додає [+N] у назву row, не змінюючи структуру row.
    """

    try:
        if isinstance(row, dict):
            inventory_id = row.get("inventory_id") or row.get("id")
            name = row.get("name")

            if not inventory_id or not name:
                return row

            updated = dict(row)
            updated["name"] = get_inventory_refined_display_name(inventory_id, name)
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
            if "name" in row:
                updated = dict(row)
                updated["name"] = get_inventory_refined_display_name(inventory_id, updated.get("name"))
                return updated
            return row

        if isinstance(row, (tuple, list)):
            values = list(row)

            # Для get_item_by_inventory_id_full у проєкті зазвичай:
            # inventory.id, inventory.item_id, items.name, ...
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


# ==============================
# ✅ SELL REFINE DISPLAY V2 IMPORT FIX
# ==============================

# 6.0.7b
# Попередній sell refine display міг не спрацювати, якщо city.py не імпортував
# get_inventory_refined_display_name із db.py. Цей override робить локальний import
# всередині helper-а і більш агресивно оновлює назву у row.

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

    # Назви спорядження майже завжди мають рівень або rarity emoji.
    if " рівня" in value:
        return True

    item_markers = [
        "⚪", "🟢", "🔵", "🟣",
        "Посох", "Жезл", "Меч", "Кинджал", "Лук", "Арбалет", "Щит",
        "Обладунок", "Шолом", "Поножі", "Рукавиці", "Чоботи", "Каптур", "Капелюх",
        "Амулет", "Кільце", "Талісман"
    ]

    return any(marker in value for marker in item_markers)


def _city_refine_display_for_sell_row_v2(row):
    try:
        if isinstance(row, dict):
            inventory_id = row.get("inventory_id") or row.get("id")

            if not inventory_id:
                return row

            updated = dict(row)

            for key in ["name", "item_name", "display_name", "label"]:
                if key in updated and isinstance(updated[key], str):
                    updated[key] = _city_get_refined_name_v2(inventory_id, updated[key])

            return updated

        if isinstance(row, (tuple, list)):
            if not row:
                return row

            inventory_id = row[0]
            values = list(row)
            changed = False

            # Міняємо всі поля, які схожі на назву предмета.
            # Це безпечніше для різних форматів get_sellable_equipment_items().
            for index, value in enumerate(values):
                if _city_string_looks_like_item_name_v2(value):
                    values[index] = _city_get_refined_name_v2(inventory_id, value)
                    changed = True

            if not changed:
                # Fallback для найчастіших форматів:
                # (inventory_id, name, ...)
                # (inventory_id, item_id, name, ...)
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
            for key in ["name", "item_name", "display_name", "label"]:
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

# ✅ ROM 9.0.8d CITY REPAIR CALLBACK FINAL FIX
# Repair menu now uses confirmation callbacks: repair_prompt_one_v3_* / repair_prompt_all_v3

# ==============================
# ROM 11.4.1 TRADER EQUIPMENT TYPE DISPLAY
# ==============================
_CITY_SELLABLE_BEFORE_TYPE_DISPLAY_11_4_1 = get_sellable_equipment_items
_CITY_ITEM_FULL_BEFORE_TYPE_DISPLAY_11_4_1 = get_item_by_inventory_id_full


def _city_equipment_typed_name_11_4_1(inventory_id, name):
    """Apply the same [armor type] label used by inventory and loot UI."""
    from db import get_item_classification_by_inventory_id, get_armor_type_label, is_armor_slot

    display_name = str(name or "Предмет")
    try:
        classification = get_item_classification_by_inventory_id(int(inventory_id)) or {}
        slot_key = classification.get("slot_key", "")
        armor_type = classification.get("armor_type", "")
        if not is_armor_slot(slot_key) or not armor_type:
            return display_name
        label = get_armor_type_label(armor_type)
        if not label or f"[{label}]" in display_name:
            return display_name
        marker = " рівня"
        if marker in display_name:
            index = display_name.rfind(marker)
            before = display_name[:index]
            after = display_name[index:]
            parts = before.rsplit(" ", 1)
            if len(parts) == 2 and parts[1].isdigit():
                return f"{parts[0]} [{label}] {parts[1]}{after}"
        return f"{display_name} [{label}]"
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
            for key in ("name", "item_name", "display_name", "label"):
                if key in updated and updated[key]:
                    updated[key] = _city_equipment_typed_name_11_4_1(inventory_id, updated[key])
                    break
            return updated
        values = list(row)
        # Current full-item tuple keeps static item name at index 1.
        for index in (1, 2):
            if index < len(values) and isinstance(values[index], str):
                values[index] = _city_equipment_typed_name_11_4_1(inventory_id, values[index])
                break
        return tuple(values) if isinstance(row, tuple) else values
    except Exception:
        return row

# Stage 17.11.2 compact text and location description toggle.
_BASE_BUILD_MAIN_MENU_TEXT_17_11_2 = build_main_menu_text
_BASE_BUILD_TOWNHALL_TEXT_17_11_2 = build_townhall_text
_BASE_BUILD_BLACKSMITH_TEXT_17_11_2 = build_blacksmith_text
_BASE_REGISTER_CITY_HANDLERS_17_11_2 = register_city_handlers


def _remove_static_actions_block_17_11_2(text, stop_marker=None):
    marker = "\n\nДоступні дії:\n"
    if marker not in text:
        marker = "Доступні дії:\n"
    if marker not in text:
        return text
    start = text.index(marker)
    if stop_marker and stop_marker in text[start:]:
        end = text.index(stop_marker, start)
        return (text[:start].rstrip() + "\n\n" + text[end:].lstrip()).strip()
    return text[:start].rstrip()


def build_main_menu_text(user_id, show_location_description=False):
    text = _BASE_BUILD_MAIN_MENU_TEXT_17_11_2(user_id)
    location_id = get_current_location(user_id)
    location = LOCATIONS.get(location_id, LOCATIONS["start_path"])
    description_line = f"📖 {location['description']}\n\n"
    text = text.replace(description_line, "", 1)
    text = _remove_static_actions_block_17_11_2(text)
    if show_location_description:
        anchor = f"{location['name']}\n\n"
        if anchor in text:
            text = text.replace(anchor, anchor + description_line, 1)
    return text.strip()


def build_townhall_text(*args, **kwargs):
    return _remove_static_actions_block_17_11_2(
        _BASE_BUILD_TOWNHALL_TEXT_17_11_2(*args, **kwargs)
    )


def build_blacksmith_text(*args, **kwargs):
    return _remove_static_actions_block_17_11_2(
        _BASE_BUILD_BLACKSMITH_TEXT_17_11_2(*args, **kwargs),
        stop_marker="💰 Твоє золото:",
    )


def location_description_kb_17_11_2(expanded=False):
    kb = types.InlineKeyboardMarkup(row_width=1)
    if expanded:
        kb.add(types.InlineKeyboardButton(
            text="🔙 Сховати опис",
            callback_data="location_desc:hide",
        ))
    else:
        kb.add(types.InlineKeyboardButton(
            text="📖 Опис локації",
            callback_data="location_desc:show",
        ))
    return kb


def register_city_handlers(bot):
    _BASE_REGISTER_CITY_HANDLERS_17_11_2(bot)

    @bot.callback_query_handler(
        func=lambda call: call.data in ("location_desc:show", "location_desc:hide")
    )
    def location_description_toggle_17_11_2(call):
        expanded = call.data == "location_desc:show"
        user_id = call.from_user.id
        try:
            bot.edit_message_text(
                build_main_menu_text(user_id, show_location_description=expanded),
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                reply_markup=location_description_kb_17_11_2(expanded),
            )
        except Exception:
            # No send_message fallback: a stale or unchanged message must not spam chat.
            pass
        finally:
            try:
                bot.answer_callback_query(call.id)
            except Exception:
                pass

# Stage 17.11.2.1 City, Craft District and Tavern text cleanup.
_BASE_BUILD_CITY_TEXT_17_11_2_1 = build_city_text
_BASE_BUILD_CRAFT_DISTRICT_TEXT_17_11_2_1 = build_craft_district_text
_BASE_BUILD_TAVERN_TEXT_17_11_2_1 = build_tavern_text


def build_city_text(user_id):
    location_id = get_current_location(user_id)
    location = LOCATIONS.get(location_id, LOCATIONS["start_path"])
    return (
        f"🏙️ Місто\n\n"
        f"📍 Регіон:\n"
        f"{location['name']}\n\n"
        f"Перед тобою центральна площа табору мандрівників, де сходяться "
        f"дороги торговців, ремісників і шукачів пригод. З майстерень "
        f"долинає дзенькіт металу, торговці закликають оглянути товари, "
        f"а біля дошок оголошень збираються найманці. Тут можна "
        f"підготуватися до нової подорожі, поповнити припаси та дізнатися "
        f"останні новини."
    )


def build_craft_district_text(user_id):
    text = _BASE_BUILD_CRAFT_DISTRICT_TEXT_17_11_2_1(user_id)
    marker = "\n\nДоступні місця:\n"
    if marker in text:
        text = text.split(marker, 1)[0]
    return text.rstrip()


def build_tavern_text():
    text = _BASE_BUILD_TAVERN_TEXT_17_11_2_1()
    marker = "\n\nℹ️ Пізніше тут можна буде додати:\n"
    if marker in text:
        text = text.split(marker, 1)[0]
    return text.rstrip()

