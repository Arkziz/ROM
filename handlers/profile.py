from db import (
    get_player_stats,
    get_current_hp,
    get_max_hp,
    get_user_energy,
    get_user_progress,

    get_physical_defense,
    get_magic_defense,
    get_physical_crit_chance_display,
    get_magical_crit_chance_display,
    get_base_dodge_chance_display,
    get_enemy_crit_chance_against_player,

    get_all_equipped_slots,
    get_item_by_inventory_id_full,
    get_inventory_weapon_damage_display,

    get_character_profile_summary
)

from keyboards import profile_kb, main_kb
from utils import hp_bar


# ==============================
# HELPERS
# ==============================

def format_resource_line(profile_summary):
    resource_type = profile_summary.get("resource_type", "")

    if resource_type == "rage":
        return "🔴 Бойовий ресурс: Лютість\n"

    if resource_type == "combat_energy":
        return "🟡 Бойовий ресурс: Енергія\n"

    if resource_type == "combat_energy_combo":
        return "🟡 Бойовий ресурс: Енергія + комбо\n"

    if resource_type == "mana":
        mp_data = profile_summary.get("mp_data", {})
        mp = mp_data.get("mp", 0)
        max_mp = mp_data.get("max_mp", 0)

        return f"🔵 Мана: {mp}/{max_mp}\n"

    return "Бойовий ресурс: не визначено\n"


def build_character_text(user_id):
    stats = get_player_stats(user_id)

    if not stats:
        return "❗ Персонажа не знайдено. Натисни /start."

    str_, dex_, int_, wis_, sta_, lvl = stats

    current_hp = get_current_hp(user_id)
    max_hp = get_max_hp(user_id)

    energy_data = get_user_energy(user_id)
    energy = energy_data["energy"]
    max_energy = energy_data["max_energy"]

    progress = get_user_progress(user_id)

    if progress:
        exp = progress["exp"]
        exp_to_next = progress["exp_to_next"]
        gold = progress["gold"]
        kills = progress["kills"]
    else:
        exp = 0
        exp_to_next = 0
        gold = 0
        kills = 0

    exp_percent = 0

    if exp_to_next > 0:
        exp_percent = (exp / exp_to_next) * 100

    profile_summary = get_character_profile_summary(user_id)
    character_name = profile_summary.get("name") or "Без імені"
    class_name = profile_summary.get("class_name") or "Не обрано"

    text = (
        f"👤 Персонаж\n\n"
        f"📝 Ім’я: {character_name}\n"
        f"🧭 Клас: {class_name}\n"
        f"{format_resource_line(profile_summary)}\n"

        f"🏆 Рівень: {lvl}\n"
        f"❤️ Здоров’я: {current_hp}/{max_hp}\n"
        f"{hp_bar(current_hp, max_hp)}\n"
        f"🔋 Енергія полювання: {energy}/{max_energy}\n\n"

        f"— Характеристики —\n"
        f"💪 Сила: {str_}\n"
        f"🎯 Спритність: {dex_}\n"
        f"🔮 Інтелект: {int_}\n"
        f"🦉 Мудрість: {wis_}\n"
        f"🛡 Витривалість: {sta_}\n\n"

        f"— Прогрес —\n"
        f"✨ Досвід: {exp}/{exp_to_next} ({exp_percent:.1f}%)\n"
        f"👹 Вбито мобів: {kills}\n\n"

        f"— Гаманець —\n"
        f"💰 Золото: {gold:.2f}"
    )

    return text


def build_stats_text(user_id):
    stats = get_player_stats(user_id)

    if not stats:
        return "❗ Персонажа не знайдено."

    total_str, total_dex, total_int, total_wis, total_sta, lvl = stats

    pdef = get_physical_defense(user_id)
    mdef = get_magic_defense(user_id)

    physical_crit = get_physical_crit_chance_display(user_id)
    magical_crit = get_magical_crit_chance_display(user_id)
    dodge = get_base_dodge_chance_display(user_id)
    enemy_crit = get_enemy_crit_chance_against_player(user_id)

    profile_summary = get_character_profile_summary(user_id)
    character_name = profile_summary.get("name") or "Без імені"
    class_name = profile_summary.get("class_name") or "Не обрано"

    physical_attack = total_str
    magical_attack = total_int

    text = (
        f"📊 Параметри персонажа\n\n"
        f"📝 Ім’я: {character_name}\n"
        f"🧭 Клас: {class_name}\n"
        f"{format_resource_line(profile_summary)}\n"

        f"— Атака —\n"
        f"⚔️ Фізична атака: {physical_attack}\n"
        f"🔮 Магічна атака: {magical_attack}\n\n"

        f"— Захист —\n"
        f"🛡 Фіз. захист: {pdef}\n"
        f"🔮 Маг. захист: {mdef}\n\n"

        f"— Шанси —\n"
        f"🎯 Фіз. крит: {physical_crit:.2f}%\n"
        f"🔮 Маг. крит: {magical_crit:.2f}%\n"
        f"💨 Базовий ухил: {dodge:.2f}%\n"
        f"💥 Крит ворога по тобі: {enemy_crit:.2f}%\n\n"

        f"ℹ️ Ухил у реальному бою залежить від спритності конкретного ворога."
    )

    return text


def build_equipment_text(user_id):
    equipped_slots = get_all_equipped_slots(user_id)

    text = (
        f"🧰 Екіпірування персонажа\n\n"
        f"Стан активних слотів:\n\n"
    )

    for slot_key, slot_label in equipped_slots.items():
        # у старій реалізації get_all_equipped_slots може повертати slot_key -> inventory_id
        pass

    # Безпечний варіант: беремо порядок із db через dict, але виводимо вручну
    from db import SLOT_ORDER, EQUIPMENT_SLOTS

    equipped_slots = get_all_equipped_slots(user_id)

    for slot_key in SLOT_ORDER:
        slot_label = EQUIPMENT_SLOTS.get(slot_key, slot_key)
        inventory_id = equipped_slots.get(slot_key)

        if not inventory_id:
            text += f"{slot_label}: порожньо\n\n"
            continue

        item = get_item_by_inventory_id_full(inventory_id)

        if not item:
            text += f"{slot_label}: помилка предмета\n\n"
            continue

        (
            inv_id,
            item_id,
            name,
            type_,
            rarity,
            category,
            item_slot_key,
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

        text += f"{slot_label}: {name}\n"

        if durability is not None:
            broken_text = " ⚠️ [ЗЛАМАНО]" if durability <= 0 else ""
            text += f"🧱 Міцність: {durability}/100{broken_text}\n"

        if item_slot_key == "main_hand":
            if weapon_hands == 2:
                text += "👐 Тип зброї: дворучна\n"
            else:
                text += "✋ Тип зброї: одноручна\n"

            weapon_damage_text = get_inventory_weapon_damage_display(inv_id)

            if weapon_damage_text:
                text += f"{weapon_damage_text}\n"

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

        if bonuses:
            text += "📊 Бонуси:\n"

            for bonus in bonuses:
                text += f"• {bonus}\n"
        else:
            text += "📊 Бонуси: немає\n"

        text += "\n"

    return text


# ==============================
# HANDLERS
# ==============================

def register_profile_handlers(bot):

    @bot.message_handler(func=lambda m: m.text == "👤 Профіль")
    def profile(message):
        user_id = message.from_user.id

        bot.send_message(
            message.chat.id,
            "👤 Розділ персонажа відкрито",
            reply_markup=profile_kb()
        )

        bot.send_message(
            message.chat.id,
            build_character_text(user_id),
            reply_markup=profile_kb()
        )

    @bot.message_handler(func=lambda m: m.text == "📊 Параметри")
    def stats(message):
        user_id = message.from_user.id

        bot.send_message(
            message.chat.id,
            build_stats_text(user_id),
            reply_markup=profile_kb()
        )

    @bot.message_handler(func=lambda m: m.text == "🧰 Екіпірування")
    def equipment(message):
        user_id = message.from_user.id

        bot.send_message(
            message.chat.id,
            build_equipment_text(user_id),
            reply_markup=profile_kb()
        )

    @bot.message_handler(func=lambda m: m.text == "🔙 Назад")
    def back_from_profile(message):
        bot.send_message(
            message.chat.id,
            "🏕️ Повернення до табору.",
            reply_markup=main_kb()
        )