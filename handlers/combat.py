from telebot import types

from data.locations import LOCATIONS

from db import (
    get_player_stats,
    get_player_attack_profile,
    get_physical_defense,
    get_magic_defense,
    get_max_hp,
    get_current_hp,
    set_current_hp,
    get_current_location,
    get_inventory_detailed,
    get_item_by_inventory_id_full,

    damage_equipped_items_on_death,
    apply_random_durability_wear_on_victory,
    process_contract_progress_on_kill,
    process_daily_quest_progress_on_kill,
    consume_energy_for_hunt,

    get_character_profile_summary,
    get_user_mp,
    get_character_class,
    spend_user_mp,
    restore_user_mp_to_full
)

from keyboards import main_kb, fight_kb
from utils import hp_bar

from systems.combat_system import (
    generate_mob,
    calculate_player_attack,
    calculate_mob_attack
)

from systems.reward_system import process_victory_reward
from systems.potion_system import use_potion_from_inventory


# ==============================
# ✅ CLASS COMBAT RESOURCE HELPERS
# ==============================

def init_class_combat_resource(user_id, mob):
    """
    Ініціалізація бойового ресурсу класу на старті бою.

    rage:
        Воїн / Лицар
        0/100 на старті бою

    combat_energy:
        Скаут
        100/100 на старті бою

    combat_energy_combo:
        Розбійник
        100/100 енергії + 0/3 комбо

    mana:
        Маг / Жрець
        береться з глобального MP персонажа
    """

    profile_summary = get_character_profile_summary(user_id)
    resource_type = profile_summary.get("resource_type", "")
    class_key = profile_summary.get("class_key", "")

    mob["player_resource_type"] = resource_type
    mob["player_class_key"] = class_key

    if resource_type == "rage":
        mob["player_rage"] = 0
        mob["player_max_rage"] = 100

    elif resource_type in ["combat_energy", "combat_energy_combo"]:
        mob["player_combat_energy"] = 100
        mob["player_max_combat_energy"] = 100

        if resource_type == "combat_energy_combo":
            mob["player_combo_points"] = 0
            mob["player_max_combo_points"] = 3

    elif resource_type == "mana":
        mp_data = get_user_mp(user_id)

        mob["player_mp"] = mp_data.get("mp", 0)
        mob["player_max_mp"] = mp_data.get("max_mp", 0)


def get_class_resource_line(mob):
    resource_type = mob.get("player_resource_type", "")

    if resource_type == "rage":
        rage = mob.get("player_rage", 0)
        max_rage = mob.get("player_max_rage", 100)

        return f"🔴 Лютість: {rage}/{max_rage}\n"

    if resource_type == "combat_energy":
        energy = mob.get("player_combat_energy", 100)
        max_energy = mob.get("player_max_combat_energy", 100)

        return f"🟡 Енергія: {energy}/{max_energy}\n"

    if resource_type == "combat_energy_combo":
        energy = mob.get("player_combat_energy", 100)
        max_energy = mob.get("player_max_combat_energy", 100)
        combo = mob.get("player_combo_points", 0)
        max_combo = mob.get("player_max_combo_points", 3)

        return (
            f"🟡 Енергія: {energy}/{max_energy}\n"
            f"⚔️ Комбо: {combo}/{max_combo}\n"
        )

    if resource_type == "mana":
        mp = mob.get("player_mp", 0)
        max_mp = mob.get("player_max_mp", 0)

        return f"🔵 Мана: {mp}/{max_mp}\n"

    return ""


def regenerate_class_resource_at_player_turn(mob):
    """
    Початок ходу гравця.

    Для Скаута / Розбійника:
        +20 енергії, максимум 100.

    Для інших класів поки нічого.
    """

    resource_type = mob.get("player_resource_type", "")

    if resource_type not in ["combat_energy", "combat_energy_combo"]:
        return ""

    current_energy = mob.get("player_combat_energy", 100)
    max_energy = mob.get("player_max_combat_energy", 100)

    old_energy = current_energy
    current_energy = min(max_energy, current_energy + 20)

    mob["player_combat_energy"] = current_energy

    if current_energy > old_energy:
        return f"🟡 Енергія відновлена: {old_energy} → {current_energy}/{max_energy}\n"

    return ""


def add_rage_for_player_attack(mob):
    """
    Воїн / Лицар отримують +15 Люті за базову атаку або атакуючий скіл.
    """

    if mob.get("player_resource_type") != "rage":
        return ""

    old_rage = mob.get("player_rage", 0)
    max_rage = mob.get("player_max_rage", 100)

    new_rage = min(max_rage, old_rage + 15)
    mob["player_rage"] = new_rage

    if new_rage > old_rage:
        return f"🔴 Лютість: +{new_rage - old_rage} ({new_rage}/{max_rage})\n"

    return ""


def add_rage_for_damage_taken(mob, damage):
    """
    Воїн / Лицар отримують +10 Люті, якщо ворог реально завдав шкоди.
    Ухил не дає Лютість.
    """

    if mob.get("player_resource_type") != "rage":
        return ""

    if damage <= 0:
        return ""

    old_rage = mob.get("player_rage", 0)
    max_rage = mob.get("player_max_rage", 100)

    new_rage = min(max_rage, old_rage + 10)
    mob["player_rage"] = new_rage

    if new_rage > old_rage:
        return f"🔴 Лютість за отриману шкоду: +{new_rage - old_rage} ({new_rage}/{max_rage})\n"

    return ""


# ==============================
# ✅ CLASS SKILLS V1
# ==============================

CLASS_SKILLS_V1 = {
    "warrior": {
        "key": "warrior_cleave",
        "name": "🪓 Розсікання",
        "description": "Завдає 110% фізичної шкоди та додатково дає +10 Люті.",
        "cost_type": "rage",
        "cost": 0,
        "damage_multiplier": 1.10,
        "attack_type": "physical",
        "extra_rage": 10,
        "stun_chance": 0
    },

    "knight": {
        "key": "knight_shield_bash",
        "name": "🛡️ Удар щитом",
        "description": "Витрачає 20 Люті, завдає 90% фізичної шкоди та має 25% шанс оглушити ворога.",
        "cost_type": "rage",
        "cost": 20,
        "damage_multiplier": 0.90,
        "attack_type": "physical",
        "extra_rage": 0,
        "stun_chance": 25
    },

    "scout": {
        "key": "scout_aimed_shot",
        "name": "🏹 Прицільний постріл",
        "description": "Витрачає 30 Енергії та завдає 140% фізичної шкоди.",
        "cost_type": "combat_energy",
        "cost": 30,
        "damage_multiplier": 1.40,
        "attack_type": "physical",
        "extra_rage": 0,
        "stun_chance": 0
    },

    "rogue": {
        "key": "rogue_sneak_strike",
        "name": "⚔️ Підступний випад",
        "description": "Витрачає 25 Енергії та завдає 130% фізичної шкоди.",
        "cost_type": "combat_energy",
        "cost": 25,
        "damage_multiplier": 1.30,
        "attack_type": "physical",
        "extra_rage": 0,
        "stun_chance": 0
    },

    "mage": {
        "key": "mage_fireball",
        "name": "🔥 Вогняна куля",
        "description": "Витрачає 20 MP та завдає 150% магічної шкоди.",
        "cost_type": "mana",
        "cost": 20,
        "damage_multiplier": 1.50,
        "attack_type": "magical",
        "extra_rage": 0,
        "stun_chance": 0
    },

    "priest": {
        "key": "priest_holy_ray",
        "name": "✨ Святий промінь",
        "description": "Витрачає 15 MP та завдає 120% магічної шкоди.",
        "cost_type": "mana",
        "cost": 15,
        "damage_multiplier": 1.20,
        "attack_type": "magical",
        "extra_rage": 0,
        "stun_chance": 0
    }
}


def get_player_class_skill(user_id):
    class_key = get_character_class(user_id)

    if not class_key:
        return None

    return CLASS_SKILLS_V1.get(class_key)


def build_skill_menu_text(user_id, mob):
    skill = get_player_class_skill(user_id)

    class_resource_text = get_class_resource_line(mob)

    if not skill:
        return (
            "✨ Навички\n\n"
            "❌ Для твого класу ще немає доступної навички."
        ), None

    text = (
        "✨ Навички\n\n"
        f"{class_resource_text}\n"
        f"{skill['name']}\n"
        f"{skill['description']}\n\n"
        f"Вартість: {skill['cost']}"
    )

    if skill["cost_type"] == "rage":
        text += " Люті\n"
    elif skill["cost_type"] == "combat_energy":
        text += " Енергії\n"
    elif skill["cost_type"] == "mana":
        text += " MP\n"
    else:
        text += "\n"

    kb = types.InlineKeyboardMarkup()

    kb.add(types.InlineKeyboardButton(
        text=skill["name"],
        callback_data=f"use_skill:{skill['key']}"
    ))

    kb.add(types.InlineKeyboardButton(
        text="⬅️ Назад до бою",
        callback_data="combat_back"
    ))

    return text, kb


def validate_and_pay_skill_cost(user_id, mob, skill):
    cost_type = skill["cost_type"]
    cost = int(skill["cost"])

    if cost_type == "rage":
        current_rage = mob.get("player_rage", 0)

        if current_rage < cost:
            return {
                "success": False,
                "message": (
                    f"❌ Недостатньо Люті.\n\n"
                    f"🔴 Потрібно: {cost}\n"
                    f"🔴 У тебе: {current_rage}/{mob.get('player_max_rage', 100)}"
                )
            }

        mob["player_rage"] = max(0, current_rage - cost)

        return {
            "success": True,
            "message": ""
        }

    if cost_type == "combat_energy":
        current_energy = mob.get("player_combat_energy", 0)

        if current_energy < cost:
            return {
                "success": False,
                "message": (
                    f"❌ Недостатньо Енергії.\n\n"
                    f"🟡 Потрібно: {cost}\n"
                    f"🟡 У тебе: {current_energy}/{mob.get('player_max_combat_energy', 100)}"
                )
            }

        mob["player_combat_energy"] = max(0, current_energy - cost)

        return {
            "success": True,
            "message": ""
        }

    if cost_type == "mana":
        spend_result = spend_user_mp(user_id, cost)

        if not spend_result["success"]:
            return spend_result

        mob["player_mp"] = spend_result["mp"]
        mob["player_max_mp"] = spend_result["max_mp"]

        return {
            "success": True,
            "message": ""
        }

    return {
        "success": True,
        "message": ""
    }


def apply_extra_rage_from_skill(mob, skill):
    extra_rage = int(skill.get("extra_rage", 0))

    if extra_rage <= 0:
        return ""

    if mob.get("player_resource_type") != "rage":
        return ""

    old_rage = mob.get("player_rage", 0)
    max_rage = mob.get("player_max_rage", 100)

    new_rage = min(max_rage, old_rage + extra_rage)
    mob["player_rage"] = new_rage

    if new_rage > old_rage:
        return f"🔴 Додаткова Лютість від навички: +{new_rage - old_rage} ({new_rage}/{max_rage})\n"

    return ""


def roll_skill_stun(mob, skill):
    stun_chance = int(skill.get("stun_chance", 0))

    if stun_chance <= 0:
        return ""

    import random

    roll = random.randint(1, 100)

    if roll <= stun_chance:
        mob["stunned_turns"] = 1
        return "💫 Ворог оглушений на 1 хід!\n"

    return ""


def append_mp_restore_text(text, mp_restore_result):
    if mp_restore_result and mp_restore_result.get("restored"):
        text += (
            f"\n🔵 Мана відновлена: "
            f"{mp_restore_result['mp']}/{mp_restore_result['max_mp']}"
        )

    return text


# ==============================
# 🧪 POTION COOLDOWN
# ==============================

def get_potion_cooldown_turns_by_inventory_id(inventory_id):
    item = get_item_by_inventory_id_full(inventory_id)

    if not item:
        return 3

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

    if type_ == "potion_hp_medium":
        return 5

    if type_ == "potion_hp":
        return 3

    return 3


# ==============================
# 🧪 POTION SELECT IN COMBAT
# ==============================

def build_combat_potion_kb(user_id):
    items = get_inventory_detailed(user_id)

    kb = types.InlineKeyboardMarkup()
    found = False

    for item in items:
        (
            inv_id,
            item_id,
            name,
            type_,
            rarity,
            category,
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

        if category == "potion" and type_ in ["potion_hp", "potion_hp_medium"]:
            found = True

            cooldown = 3

            if type_ == "potion_hp_medium":
                cooldown = 5

            kb.add(types.InlineKeyboardButton(
                text=f"{name} x{quantity} — cooldown {cooldown} ход.",
                callback_data=f"combat_potion_{inv_id}"
            ))

    if not found:
        return None

    kb.add(types.InlineKeyboardButton(
        text="⬅️ Назад до бою",
        callback_data="combat_back"
    ))

    return kb


# ==============================
# DEATH TEXT
# ==============================

def build_death_text(durability_damage):
    text = (
        "💀 ТИ ЗАГИНУВ\n"
        "❤️ Здоров’я відновлено\n"
        "🧱 Одягнене спорядження втратило 5 міцності\n"
    )

    if durability_damage:
        text += "\n📉 Стан спорядження:\n"

        for item in durability_damage:
            broken_text = " ⚠️ ЗЛАМАНО" if item["broken"] else ""
            text += f"• {item['name']}: {item['old']} → {item['new']}/100{broken_text}\n"

    return text


# ==============================
# REGISTER HANDLERS
# ==============================

def register_combat_handlers(bot):

    # ==============================
    # 🔎 HUNT
    # ==============================

    @bot.message_handler(func=lambda m: m.text == "🔎 Полювання")
    def hunt(message):
        user_id = message.from_user.id

        stats = get_player_stats(user_id)

        if not stats:
            bot.send_message(
                message.chat.id,
                "❗ Спочатку натисни /start",
                reply_markup=main_kb()
            )
            return

        str_, dex_, int_, wis_, sta_, lvl = stats

        current_hp = get_current_hp(user_id)
        max_hp = get_max_hp(user_id)

        hp_percent = 0

        if max_hp > 0:
            hp_percent = (current_hp / max_hp) * 100

        if hp_percent <= 25:
            bot.send_message(
                message.chat.id,
                (
                    "😴 Ви занадто слабкі для полювання.\n\n"
                    f"❤️ Здоров’я: {current_hp}/{max_hp} ({hp_percent:.1f}%)\n"
                    "Ваше здоров’я нижче або дорівнює 25%.\n\n"
                    "Відпочиньте або використайте зілля!"
                ),
                reply_markup=main_kb()
            )
            return

        location_id = get_current_location(user_id)
        location = LOCATIONS.get(location_id, LOCATIONS["start_path"])

        # Заборона полювання у локації, яку герой вже переріс.
        location_max_level = int(location.get("level_max", lvl))

        if lvl > location_max_level:
            bot.send_message(
                message.chat.id,
                (
                    f"🌿 Ця місцевість більше не становить для тебе виклику.\n\n"
                    f"📍 Локація: {location['name']}\n"
                    f"🏷 Рівні локації: {location.get('level_min', 1)}–{location_max_level}\n"
                    f"👤 Твій рівень: {lvl}\n\n"
                    f"Ти занадто сильний для полювання тут.\n"
                    f"Відкрий 🗺️ Мапу та перейди до складнішої локації."
                ),
                reply_markup=main_kb()
            )
            return

        energy_result = consume_energy_for_hunt(user_id)

        if not energy_result["success"]:
            bot.send_message(
                message.chat.id,
                energy_result["message"],
                reply_markup=main_kb()
            )
            return

        mob = generate_mob(player_level=lvl, location_id=location_id)
        mob["max_hp"] = mob["hp"]
        mob["potion_cooldown"] = 0
        mob["stunned_turns"] = 0

        init_class_combat_resource(user_id, mob)

        bot.user_data = getattr(bot, "user_data", {})
        bot.user_data[user_id] = mob

        attack_profile = get_player_attack_profile(user_id)

        player_pdef = get_physical_defense(user_id)
        player_mdef = get_magic_defense(user_id)

        attack_type_text = "Фізична" if mob["attack_type"] == "physical" else "Магічна"
        player_attack_type_text = "Фізична" if attack_profile["attack_type"] == "physical" else "Магічна"

        elite_text = ""

        if mob.get("is_elite"):
            elite_text = (
                "⭐ ЕЛІТНИЙ ВОРОГ!\n"
                "Ця істота значно сильніша за звичайну.\n\n"
            )

        weapon_text = attack_profile.get("weapon_text") or "Без зброї"
        class_resource_text = get_class_resource_line(mob)

        text = (
            f"📍 Мапа: {location['name']}\n"
            f"🔎 Ти зустрів {mob['name']}\n\n"
            f"{elite_text}"
            f"🔋 Енергія полювання: {energy_result['energy']}/{energy_result['max_energy']}\n\n"

            f"======================\n\n"

            f"👤 ТИ\n"
            f"❤️ Здоров’я: {current_hp}/{max_hp}\n"
            f"{hp_bar(current_hp, max_hp)}\n"
            f"{class_resource_text}"
            f"⚔️ Тип атаки: {player_attack_type_text}\n"
            f"🗡️ Зброя: {weapon_text}\n"
            f"💥 Атака: {attack_profile['display_attack']}\n"
            f"🛡 Фіз. захист: {player_pdef}\n"
            f"🔮 Маг. захист: {player_mdef}\n\n"

            f"----------------------\n\n"

            f"👹 ВОРОГ\n"
            f"🏷 Рівень: {mob['level']}\n"
            f"❤️ Здоров’я: {mob['hp']}/{mob['max_hp']}\n"
            f"{hp_bar(mob['hp'], mob['max_hp'])}\n"
            f"⚔️ Атака: {mob['attack']}\n"
            f"🛡 Фіз. захист: {mob.get('pdef', mob.get('def', 0))}\n"
            f"🔮 Маг. захист: {mob.get('mdef', mob.get('def', 0))}\n"
            f"🎯 Тип атаки: {attack_type_text}\n\n"

            f"⚔️ Бій починається!"
        )

        bot.send_message(
            message.chat.id,
            text,
            reply_markup=fight_kb()
        )

    # ==============================
    # ⚔️ ATTACK
    # ==============================

    @bot.message_handler(func=lambda m: m.text == "⚔️ Атакувати")
    def attack(message):
        user_id = message.from_user.id

        if not hasattr(bot, "user_data") or user_id not in bot.user_data:
            bot.send_message(
                message.chat.id,
                "❗ Спочатку почни полювання",
                reply_markup=main_kb()
            )
            return

        mob = bot.user_data[user_id]

        resource_start_text = regenerate_class_resource_at_player_turn(mob)

        stats = get_player_stats(user_id)

        if not stats:
            bot.send_message(
                message.chat.id,
                "❗ Персонажа не знайдено",
                reply_markup=main_kb()
            )
            return

        str_, dex_, int_, wis_, sta_, lvl = stats

        attack_profile = get_player_attack_profile(user_id)

        player_pdef = get_physical_defense(user_id)
        player_mdef = get_magic_defense(user_id)

        player_hp = get_current_hp(user_id)
        player_max_hp = get_max_hp(user_id)

        if "max_hp" not in mob:
            mob["max_hp"] = mob["hp"]

        mob_def_for_player_attack = (
            mob.get("mdef", mob.get("def", 0))
            if attack_profile["attack_type"] == "magical"
            else mob.get("pdef", mob.get("def", 0))
        )

        player_attack_result = calculate_player_attack(
            player_stat_attack=attack_profile["stat_attack"],
            mob_def=mob_def_for_player_attack,
            dex=dex_,
            wis=wis_,
            level=lvl,
            attack_type=attack_profile["attack_type"],
            weapon_min_damage=attack_profile["weapon_min_damage"],
            weapon_max_damage=attack_profile["weapon_max_damage"]
        )

        dmg = player_attack_result["damage"]
        is_player_crit = player_attack_result["is_crit"]
        weapon_damage = player_attack_result.get("weapon_damage", 0)

        mob["hp"] -= dmg

        resource_attack_text = add_rage_for_player_attack(mob)

        # ==============================
        # VICTORY
        # ==============================

        if mob["hp"] <= 0:
            del bot.user_data[user_id]

            mp_restore_result = restore_user_mp_to_full(user_id)

            reward = process_victory_reward(
                user_id=user_id,
                player_level=lvl,
                mob=mob
            )

            wear_result = apply_random_durability_wear_on_victory(
                user_id=user_id,
                chance_percent=25
            )

            contract_result = process_contract_progress_on_kill(
                user_id=user_id,
                mob=mob
            )

            daily_result = process_daily_quest_progress_on_kill(
                user_id=user_id,
                mob=mob
            )

            exp_result = reward["exp_result"]

            victory_title = "🏆 ВИ ПЕРЕМОГЛИ!"

            if mob.get("is_elite"):
                victory_title = "🏆 ВИ ПЕРЕМОГЛИ ЕЛІТНОГО ВОРОГА!"

            text = f"{victory_title}\n\n"

            if resource_start_text or resource_attack_text:
                text += resource_start_text
                text += resource_attack_text
                text += "\n"

            text += (
                f"{mob['name']} повалений на землю.\n\n"
                f"📈 Нагорода:\n"
                f"✨ Досвід: +{reward['exp']} EXP"
            )

            if exp_result:
                text += f" ({exp_result['exp']}/{exp_result['exp_to_next']})"

                if exp_result["level_ups"] > 0:
                    text += f"\n🏆 Новий рівень: {exp_result['level']}!"

            text += f"\n💰 Золото: +{reward['gold']}\n"

            if reward["loot_messages"]:
                text += "\n🎒 Знайдений лут:\n"

                for loot in reward["loot_messages"]:
                    text += f"• {loot}\n"
            else:
                text += "\n🎒 Лут не знайдено.\n"

            if wear_result and wear_result.get("triggered"):
                text += f"\n{wear_result['message']}\n"

            if contract_result and contract_result.get("message"):
                text += f"\n{contract_result['message']}\n"

            if daily_result and daily_result.get("message"):
                text += f"\n{daily_result['message']}\n"

            text = append_mp_restore_text(text, mp_restore_result)

            text += f"\n🎒 Сумка: {reward['used_slots']}/{reward['capacity']} слотів"

            bot.send_message(
                message.chat.id,
                text,
                reply_markup=main_kb()
            )
            return

        # ==============================
        # MOB ATTACK
        # ==============================

        mob_dmg = 0
        is_mob_crit = False
        is_dodge = False
        resource_damage_text = ""

        if mob.get("stunned_turns", 0) > 0:
            mob["stunned_turns"] -= 1
            enemy_action_text = "💫 Ворог оглушений і пропускає хід.\n\n"
        else:
            mob_attack_result = calculate_mob_attack(
                mob_attack=mob["attack"],
                player_pdef=player_pdef,
                player_mdef=player_mdef,
                player_dex=dex_,
                mob_dex=mob["dex"],
                sta=sta_,
                level=lvl,
                attack_type=mob["attack_type"]
            )

            mob_dmg = mob_attack_result["damage"]
            is_mob_crit = mob_attack_result["is_crit"]
            is_dodge = mob_attack_result["is_dodge"]

            player_hp -= mob_dmg

            resource_damage_text = add_rage_for_damage_taken(mob, mob_dmg)

            if is_dodge:
                enemy_action_text = "💨 УХИЛ! Ти уникнув атаки ворога\n\n"
            elif is_mob_crit:
                enemy_action_text = f"💥 КРИТ ВОРОГА! Ти отримав {mob_dmg} шкоди\n\n"
            else:
                enemy_action_text = f"👹 Ворог завдав {mob_dmg} шкоди\n\n"

        if player_hp <= 0:
            durability_damage = damage_equipped_items_on_death(
                user_id=user_id,
                amount=5
            )

            set_current_hp(user_id, player_max_hp)

            mp_restore_result = restore_user_mp_to_full(user_id)

            if user_id in bot.user_data:
                del bot.user_data[user_id]

            text = build_death_text(durability_damage)
            text = append_mp_restore_text(text, mp_restore_result)

            bot.send_message(
                message.chat.id,
                text,
                reply_markup=main_kb()
            )
            return

        set_current_hp(user_id, player_hp)

        # cooldown зілля зменшується тільки після реального бойового ходу
        if mob.get("potion_cooldown", 0) > 0:
            mob["potion_cooldown"] -= 1

        text = "⚔️ БІЙ\n\n"

        if resource_start_text:
            text += resource_start_text

        if resource_attack_text:
            text += resource_attack_text

        if resource_damage_text:
            text += resource_damage_text

        if resource_start_text or resource_attack_text or resource_damage_text:
            text += "\n"

        if is_player_crit:
            text += f"💥 КРИТ! Ти завдав {dmg} шкоди"
        else:
            text += f"🗡️ Ти завдав {dmg} шкоди"

        if weapon_damage > 0:
            text += f" (зброя: {weapon_damage})"

        text += "\n"
        text += enemy_action_text

        class_resource_text = get_class_resource_line(mob)

        text += (
            f"❤️ Твоє здоров’я: {player_hp}/{player_max_hp}\n"
            f"{hp_bar(player_hp, player_max_hp)}\n"
            f"{class_resource_text}\n"
            f"👹 Здоров’я ворога: {mob['hp']}/{mob['max_hp']}\n"
            f"{hp_bar(mob['hp'], mob['max_hp'])}"
        )

        if mob.get("potion_cooldown", 0) > 0:
            text += f"\n\n🔴 Повний шлунок: {mob['potion_cooldown']} ход."

        bot.send_message(
            message.chat.id,
            text,
            reply_markup=fight_kb()
        )

    # ==============================
    # ✨ SKILLS MENU
    # ==============================

    @bot.message_handler(func=lambda m: m.text == "✨ Навички")
    def show_skills(message):
        user_id = message.from_user.id

        if not hasattr(bot, "user_data") or user_id not in bot.user_data:
            bot.send_message(
                message.chat.id,
                "❗ Ти не в бою",
                reply_markup=main_kb()
            )
            return

        mob = bot.user_data[user_id]

        text, kb = build_skill_menu_text(user_id, mob)

        if not kb:
            bot.send_message(
                message.chat.id,
                text,
                reply_markup=fight_kb()
            )
            return

        bot.send_message(
            message.chat.id,
            text,
            reply_markup=kb
        )

    # ==============================
    # ✨ USE SKILL
    # ==============================

    @bot.callback_query_handler(func=lambda call: call.data.startswith("use_skill:"))
    def use_skill(call):
        user_id = call.from_user.id
        skill_key = call.data.split(":")[1]

        if not hasattr(bot, "user_data") or user_id not in bot.user_data:
            bot.answer_callback_query(call.id)

            bot.send_message(
                call.message.chat.id,
                "❗ Бій уже завершено",
                reply_markup=main_kb()
            )
            return

        mob = bot.user_data[user_id]

        skill = get_player_class_skill(user_id)

        if not skill or skill["key"] != skill_key:
            bot.answer_callback_query(call.id)

            bot.send_message(
                call.message.chat.id,
                "❌ Навичку не знайдено.",
                reply_markup=fight_kb()
            )
            return

        resource_start_text = regenerate_class_resource_at_player_turn(mob)

        pay_result = validate_and_pay_skill_cost(user_id, mob, skill)

        if not pay_result["success"]:
            bot.answer_callback_query(call.id)

            bot.send_message(
                call.message.chat.id,
                pay_result["message"],
                reply_markup=fight_kb()
            )
            return

        stats = get_player_stats(user_id)

        if not stats:
            bot.answer_callback_query(call.id)

            bot.send_message(
                call.message.chat.id,
                "❗ Персонажа не знайдено",
                reply_markup=main_kb()
            )
            return

        str_, dex_, int_, wis_, sta_, lvl = stats

        attack_profile = get_player_attack_profile(user_id)

        player_pdef = get_physical_defense(user_id)
        player_mdef = get_magic_defense(user_id)

        player_hp = get_current_hp(user_id)
        player_max_hp = get_max_hp(user_id)

        if "max_hp" not in mob:
            mob["max_hp"] = mob["hp"]

        skill_attack_type = skill.get("attack_type", attack_profile["attack_type"])

        if skill_attack_type == "magical":
            mob_def_for_player_attack = mob.get("mdef", mob.get("def", 0))
            player_stat_attack = int_
        else:
            mob_def_for_player_attack = mob.get("pdef", mob.get("def", 0))
            player_stat_attack = attack_profile["stat_attack"]

        player_attack_result = calculate_player_attack(
            player_stat_attack=player_stat_attack,
            mob_def=mob_def_for_player_attack,
            dex=dex_,
            wis=wis_,
            level=lvl,
            attack_type=skill_attack_type,
            weapon_min_damage=attack_profile["weapon_min_damage"],
            weapon_max_damage=attack_profile["weapon_max_damage"]
        )

        base_dmg = player_attack_result["damage"]
        is_player_crit = player_attack_result["is_crit"]
        weapon_damage = player_attack_result.get("weapon_damage", 0)

        dmg = max(
            1,
            int(round(base_dmg * float(skill.get("damage_multiplier", 1.0))))
        )

        mob["hp"] -= dmg

        resource_attack_text = ""

        if mob.get("player_resource_type") == "rage":
            resource_attack_text += add_rage_for_player_attack(mob)

        resource_attack_text += apply_extra_rage_from_skill(mob, skill)

        stun_text = roll_skill_stun(mob, skill)

        bot.answer_callback_query(call.id)

        # ==============================
        # VICTORY
        # ==============================

        if mob["hp"] <= 0:
            del bot.user_data[user_id]

            mp_restore_result = restore_user_mp_to_full(user_id)

            reward = process_victory_reward(
                user_id=user_id,
                player_level=lvl,
                mob=mob
            )

            wear_result = apply_random_durability_wear_on_victory(
                user_id=user_id,
                chance_percent=25
            )

            contract_result = process_contract_progress_on_kill(
                user_id=user_id,
                mob=mob
            )

            daily_result = process_daily_quest_progress_on_kill(
                user_id=user_id,
                mob=mob
            )

            exp_result = reward["exp_result"]

            victory_title = "🏆 ВИ ПЕРЕМОГЛИ!"

            if mob.get("is_elite"):
                victory_title = "🏆 ВИ ПЕРЕМОГЛИ ЕЛІТНОГО ВОРОГА!"

            text = f"{victory_title}\n\n"

            if resource_start_text or resource_attack_text:
                text += resource_start_text
                text += resource_attack_text
                text += "\n"

            text += (
                f"✨ Навичка: {skill['name']}\n"
                f"Ти завдав {dmg} шкоди.\n\n"
                f"{mob['name']} повалений на землю.\n\n"
                f"📈 Нагорода:\n"
                f"✨ Досвід: +{reward['exp']} EXP"
            )

            if exp_result:
                text += f" ({exp_result['exp']}/{exp_result['exp_to_next']})"

                if exp_result["level_ups"] > 0:
                    text += f"\n🏆 Новий рівень: {exp_result['level']}!"

            text += f"\n💰 Золото: +{reward['gold']}\n"

            if reward["loot_messages"]:
                text += "\n🎒 Знайдений лут:\n"

                for loot in reward["loot_messages"]:
                    text += f"• {loot}\n"
            else:
                text += "\n🎒 Лут не знайдено.\n"

            if wear_result and wear_result.get("triggered"):
                text += f"\n{wear_result['message']}\n"

            if contract_result and contract_result.get("message"):
                text += f"\n{contract_result['message']}\n"

            if daily_result and daily_result.get("message"):
                text += f"\n{daily_result['message']}\n"

            text = append_mp_restore_text(text, mp_restore_result)

            text += f"\n🎒 Сумка: {reward['used_slots']}/{reward['capacity']} слотів"

            bot.send_message(
                call.message.chat.id,
                text,
                reply_markup=main_kb()
            )
            return

        # ==============================
        # MOB TURN / STUN CHECK
        # ==============================

        mob_dmg = 0
        is_mob_crit = False
        is_dodge = False
        resource_damage_text = ""

        if mob.get("stunned_turns", 0) > 0:
            mob["stunned_turns"] -= 1
            enemy_action_text = "💫 Ворог оглушений і пропускає хід.\n\n"
        else:
            mob_attack_result = calculate_mob_attack(
                mob_attack=mob["attack"],
                player_pdef=player_pdef,
                player_mdef=player_mdef,
                player_dex=dex_,
                mob_dex=mob["dex"],
                sta=sta_,
                level=lvl,
                attack_type=mob["attack_type"]
            )

            mob_dmg = mob_attack_result["damage"]
            is_mob_crit = mob_attack_result["is_crit"]
            is_dodge = mob_attack_result["is_dodge"]

            player_hp -= mob_dmg

            resource_damage_text = add_rage_for_damage_taken(mob, mob_dmg)

            if is_dodge:
                enemy_action_text = "💨 УХИЛ! Ти уникнув атаки ворога\n\n"
            elif is_mob_crit:
                enemy_action_text = f"💥 КРИТ ВОРОГА! Ти отримав {mob_dmg} шкоди\n\n"
            else:
                enemy_action_text = f"👹 Ворог завдав {mob_dmg} шкоди\n\n"

        if player_hp <= 0:
            durability_damage = damage_equipped_items_on_death(
                user_id=user_id,
                amount=5
            )

            set_current_hp(user_id, player_max_hp)

            mp_restore_result = restore_user_mp_to_full(user_id)

            if user_id in bot.user_data:
                del bot.user_data[user_id]

            text = build_death_text(durability_damage)
            text = append_mp_restore_text(text, mp_restore_result)

            bot.send_message(
                call.message.chat.id,
                text,
                reply_markup=main_kb()
            )
            return

        set_current_hp(user_id, player_hp)

        if mob.get("potion_cooldown", 0) > 0:
            mob["potion_cooldown"] -= 1

        text = "✨ НАВИЧКА\n\n"

        if resource_start_text:
            text += resource_start_text

        if resource_attack_text:
            text += resource_attack_text

        if resource_damage_text:
            text += resource_damage_text

        if resource_start_text or resource_attack_text or resource_damage_text:
            text += "\n"

        text += f"{skill['name']}\n"

        if is_player_crit:
            text += f"💥 КРИТ! Ти завдав {dmg} шкоди"
        else:
            text += f"✨ Ти завдав {dmg} шкоди"

        if weapon_damage > 0:
            text += f" (зброя: {weapon_damage})"

        text += "\n"

        if stun_text:
            text += stun_text

        text += enemy_action_text

        class_resource_text = get_class_resource_line(mob)

        text += (
            f"❤️ Твоє здоров’я: {player_hp}/{player_max_hp}\n"
            f"{hp_bar(player_hp, player_max_hp)}\n"
            f"{class_resource_text}\n"
            f"👹 Здоров’я ворога: {mob['hp']}/{mob['max_hp']}\n"
            f"{hp_bar(mob['hp'], mob['max_hp'])}"
        )

        if mob.get("potion_cooldown", 0) > 0:
            text += f"\n\n🔴 Повний шлунок: {mob['potion_cooldown']} ход."

        bot.send_message(
            call.message.chat.id,
            text,
            reply_markup=fight_kb()
        )

    # ==============================
    # 🧪 POTION BUTTON
    # ==============================

    @bot.message_handler(func=lambda m: m.text == "🧪 Зілля")
    def choose_potion_in_combat(message):
        user_id = message.from_user.id

        if not hasattr(bot, "user_data") or user_id not in bot.user_data:
            bot.send_message(
                message.chat.id,
                "❗ Ти не в бою",
                reply_markup=main_kb()
            )
            return

        mob = bot.user_data[user_id]

        cooldown = mob.get("potion_cooldown", 0)

        if cooldown > 0:
            bot.send_message(
                message.chat.id,
                f"🔴 Повний шлунок: зілля можна буде випити через {cooldown} ход.",
                reply_markup=fight_kb()
            )
            return

        kb = build_combat_potion_kb(user_id)

        if not kb:
            bot.send_message(
                message.chat.id,
                "❌ У тебе немає зілля здоров’я",
                reply_markup=fight_kb()
            )
            return

        bot.send_message(
            message.chat.id,
            "🧪 Обери зілля, яке хочеш випити:",
            reply_markup=kb
        )

    @bot.callback_query_handler(func=lambda call: call.data == "combat_back")
    def combat_back(call):
        bot.answer_callback_query(call.id)

        bot.send_message(
            call.message.chat.id,
            "⚔️ Повернення до бою",
            reply_markup=fight_kb()
        )

    @bot.callback_query_handler(func=lambda call: call.data.startswith("combat_potion_"))
    def use_selected_potion_in_combat(call):
        user_id = call.from_user.id

        if not hasattr(bot, "user_data") or user_id not in bot.user_data:
            bot.answer_callback_query(call.id)

            bot.send_message(
                call.message.chat.id,
                "❗ Бій уже завершено",
                reply_markup=main_kb()
            )
            return

        mob = bot.user_data[user_id]

        cooldown = mob.get("potion_cooldown", 0)

        if cooldown > 0:
            bot.answer_callback_query(call.id)

            bot.send_message(
                call.message.chat.id,
                f"🔴 Повний шлунок: зілля можна буде випити через {cooldown} ход.",
                reply_markup=fight_kb()
            )
            return

        inventory_id = int(call.data.split("_")[2])
        cooldown_turns = get_potion_cooldown_turns_by_inventory_id(inventory_id)

        potion_result = use_potion_from_inventory(user_id, inventory_id)

        if not potion_result["success"]:
            bot.answer_callback_query(call.id)

            bot.send_message(
                call.message.chat.id,
                potion_result["message"],
                reply_markup=fight_kb()
            )
            return

        bot.answer_callback_query(call.id)

        # ВАЖЛИВО:
        # Зілля більше НЕ витрачає хід.
        # Ворог НЕ атакує після використання зілля.
        mob["potion_cooldown"] = cooldown_turns

        player_hp = potion_result["new_hp"]
        player_max_hp = potion_result["max_hp"]

        class_resource_text = get_class_resource_line(mob)

        text = (
            f"🧪 ЗІЛЛЯ\n\n"
            f"{potion_result['message']}\n\n"
            f"✅ Хід не витрачено — ворог не атакує після використання зілля.\n"
            f"🔴 Повний шлунок: {cooldown_turns} ход.\n\n"
            f"❤️ Твоє здоров’я: {player_hp}/{player_max_hp}\n"
            f"{hp_bar(player_hp, player_max_hp)}\n"
            f"{class_resource_text}\n"
            f"👹 Здоров’я ворога: {mob['hp']}/{mob['max_hp']}\n"
            f"{hp_bar(mob['hp'], mob['max_hp'])}"
        )

        bot.send_message(
            call.message.chat.id,
            text,
            reply_markup=fight_kb()
        )

    # ==============================
    # 🏃 ESCAPE CONFIRM
    # ==============================

    @bot.message_handler(func=lambda m: m.text == "🏃 Втекти")
    def escape(message):
        user_id = message.from_user.id

        if not hasattr(bot, "user_data") or user_id not in bot.user_data:
            bot.send_message(
                message.chat.id,
                "❗ Ти не в бою",
                reply_markup=main_kb()
            )
            return

        kb = types.InlineKeyboardMarkup()
        kb.add(
            types.InlineKeyboardButton(
                text="✅ Так, втекти",
                callback_data="escape_yes"
            ),
            types.InlineKeyboardButton(
                text="❌ Ні, залишитись",
                callback_data="escape_no"
            )
        )

        bot.send_message(
            message.chat.id,
            "🏃 Ти точно хочеш втекти з бою?",
            reply_markup=kb
        )

    @bot.callback_query_handler(func=lambda call: call.data == "escape_yes")
    def escape_yes(call):
        user_id = call.from_user.id

        mp_restore_result = restore_user_mp_to_full(user_id)

        if hasattr(bot, "user_data") and user_id in bot.user_data:
            del bot.user_data[user_id]

        bot.answer_callback_query(call.id)

        text = "🏃 Ти втік з бою"
        text = append_mp_restore_text(text, mp_restore_result)

        bot.send_message(
            call.message.chat.id,
            text,
            reply_markup=main_kb()
        )

    @bot.callback_query_handler(func=lambda call: call.data == "escape_no")
    def escape_no(call):
        bot.answer_callback_query(call.id)

        bot.send_message(
            call.message.chat.id,
            "⚔️ Ти залишився в бою",
            reply_markup=fight_kb()
        )