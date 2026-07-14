from telebot import types

from data.locations import LOCATIONS

from db import (
    get_player_stats,
    get_player_attack_profile,
    get_physical_defense,
    get_magic_defense,
    get_max_hp,
    get_current_hp,
    get_current_hp_raw,
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
    get_character_name,
    get_user_mp,
    get_character_class,
    spend_user_mp,
    restore_user_mp_to_full
)

from keyboards import main_kb, fight_kb, build_combat_inline_kb, combat_placeholder_kb
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
# ✅ ROGUE COMBO HELPERS
# ==============================

def add_rogue_combo_point(mob, amount=1):
    if mob.get("player_resource_type") != "combat_energy_combo":
        return ""

    old_combo = mob.get("player_combo_points", 0)
    max_combo = mob.get("player_max_combo_points", 3)

    new_combo = min(max_combo, old_combo + amount)
    mob["player_combo_points"] = new_combo

    if new_combo > old_combo:
        return f"⚔️ Комбо: +{new_combo - old_combo} ({new_combo}/{max_combo})\n"

    return ""


def consume_rogue_combo_points(mob):
    if mob.get("player_resource_type") != "combat_energy_combo":
        return 0

    combo = mob.get("player_combo_points", 0)
    mob["player_combo_points"] = 0

    return combo


# ==============================
# ✅ STATUS / EFFECT FRAMEWORK
# ==============================

def init_combat_effects(mob):
    if "enemy_effects" not in mob:
        mob["enemy_effects"] = {}

    if "player_effects" not in mob:
        mob["player_effects"] = {}


def add_enemy_effect(mob, key, effect):
    init_combat_effects(mob)

    effect["key"] = key
    mob["enemy_effects"][key] = effect


def add_player_effect(mob, key, effect):
    init_combat_effects(mob)

    effect["key"] = key
    mob["player_effects"][key] = effect


def remove_enemy_effect(mob, key):
    init_combat_effects(mob)

    if key in mob["enemy_effects"]:
        del mob["enemy_effects"][key]


def remove_player_effect(mob, key):
    init_combat_effects(mob)

    if key in mob["player_effects"]:
        del mob["player_effects"][key]


def get_enemy_effects_text(mob):
    init_combat_effects(mob)

    if not mob["enemy_effects"]:
        return ""

    text = "📌 Ефекти на ворогу:\n"

    for key, effect in mob["enemy_effects"].items():
        name = effect.get("name", key)
        turns = effect.get("turns", 0)

        text += f"• {name} — {turns} ход.\n"

    return text


def get_player_effects_text(mob):
    init_combat_effects(mob)

    if not mob["player_effects"]:
        return ""

    text = "📌 Ефекти на тобі:\n"

    for key, effect in mob["player_effects"].items():
        name = effect.get("name", key)
        turns = effect.get("turns", 0)

        if effect.get("type") == "shield":
            absorb_left = effect.get("absorb_left", 0)
            text += f"• {name} — {turns} ход., щит {absorb_left}\n"
        else:
            text += f"• {name} — {turns} ход.\n"

    return text


def get_effective_mob_def(mob, attack_type):
    init_combat_effects(mob)

    if attack_type == "magical":
        base_def = mob.get("mdef", mob.get("def", 0))
        flat_key = "mdef_flat"
        percent_key = "mdef_percent"
    else:
        base_def = mob.get("pdef", mob.get("def", 0))
        flat_key = "pdef_flat"
        percent_key = "pdef_percent"

    effective_def = float(base_def)

    for effect in mob["enemy_effects"].values():
        modifiers = effect.get("modifiers", {})

        if flat_key in modifiers:
            effective_def += float(modifiers.get(flat_key, 0))

        if percent_key in modifiers:
            percent = float(modifiers.get(percent_key, 0))
            effective_def *= (1 + percent / 100)

    if effective_def < 0:
        effective_def = 0

    return int(round(effective_def))


def get_effective_player_defenses(user_id, mob):
    init_combat_effects(mob)

    pdef = float(get_physical_defense(user_id))
    mdef = float(get_magic_defense(user_id))

    for effect in mob["player_effects"].values():
        modifiers = effect.get("modifiers", {})

        if "pdef_flat" in modifiers:
            pdef += float(modifiers.get("pdef_flat", 0))

        if "mdef_flat" in modifiers:
            mdef += float(modifiers.get("mdef_flat", 0))

        if "pdef_percent" in modifiers:
            pdef *= (1 + float(modifiers.get("pdef_percent", 0)) / 100)

        if "mdef_percent" in modifiers:
            mdef *= (1 + float(modifiers.get("mdef_percent", 0)) / 100)

    if pdef < 0:
        pdef = 0

    if mdef < 0:
        mdef = 0

    return int(round(pdef)), int(round(mdef))


def process_player_turn_start_effects(user_id, mob):
    init_combat_effects(mob)

    # Скільки HoT вилікував саме на старті поточного ходу.
    # Якщо цей самий хід завершиться перемогою, process_victory() відкочує цей тик.
    mob["_turn_start_hot_heal_applied"] = 0

    if not mob["player_effects"]:
        return ""

    text = ""
    effects_to_remove = []

    if "player_hp" in mob and "player_max_hp" in mob:
        current_hp = int(mob["player_hp"])
        max_hp = int(mob["player_max_hp"])
    else:
        current_hp = get_current_hp_raw(user_id)
        max_hp = get_max_hp(user_id)
        mob["player_hp"] = current_hp
        mob["player_max_hp"] = max_hp

    initial_hp = current_hp
    total_hot_healed = 0

    for key, effect in list(mob["player_effects"].items()):
        effect_type = effect.get("type", "")
        turns = int(effect.get("turns", 0))

        if effect_type == "hot":
            heal = int(effect.get("heal", 0))

            if heal > 0 and current_hp < max_hp:
                prev_hp = current_hp
                current_hp = min(max_hp, current_hp + heal)
                healed = current_hp - prev_hp

                if healed > 0:
                    total_hot_healed += healed
                    text += f"🌿 {effect.get('name', 'Лікування')}: +{healed} HP\n"

        turns -= 1
        effect["turns"] = turns

        if turns <= 0:
            effects_to_remove.append(key)

    if current_hp != initial_hp:
        set_current_hp(user_id, current_hp)
        mob["player_hp"] = current_hp

    mob["_turn_start_hot_heal_applied"] = total_hot_healed

    for key in effects_to_remove:
        name = mob["player_effects"].get(key, {}).get("name", key)
        remove_player_effect(mob, key)
        text += f"⌛ Ефект завершився: {name}\n"

    return text

def process_enemy_turn_start_effects(mob):
    init_combat_effects(mob)

    if not mob["enemy_effects"]:
        return {
            "text": "",
            "damage": 0
        }

    text = ""
    total_damage = 0
    effects_to_remove = []

    for key, effect in list(mob["enemy_effects"].items()):
        effect_type = effect.get("type", "")
        turns = int(effect.get("turns", 0))

        if effect_type == "dot":
            damage = int(effect.get("damage", 0))

            if damage > 0:
                mob["hp"] -= damage
                total_damage += damage
                text += f"{effect.get('icon', '🔥')} {effect.get('name', 'Ефект')}: ворог отримує {damage} шкоди.\n"

        turns -= 1
        effect["turns"] = turns

        if turns <= 0:
            effects_to_remove.append(key)

    for key in effects_to_remove:
        name = mob["enemy_effects"].get(key, {}).get("name", key)
        remove_enemy_effect(mob, key)
        text += f"⌛ Ефект на ворогу завершився: {name}\n"

    return {
        "text": text,
        "damage": total_damage
    }


def apply_player_shield_absorb(mob, damage):
    init_combat_effects(mob)

    if damage <= 0:
        return damage, ""

    text = ""
    remaining_damage = damage

    for key, effect in list(mob["player_effects"].items()):
        if effect.get("type") != "shield":
            continue

        absorb_left = int(effect.get("absorb_left", 0))

        if absorb_left <= 0:
            continue

        absorbed = min(absorb_left, remaining_damage)
        remaining_damage -= absorbed
        absorb_left -= absorbed

        effect["absorb_left"] = absorb_left

        text += f"🧱 {effect.get('name', 'Щит')} поглинув {absorbed} шкоди.\n"

        if absorb_left <= 0:
            name = effect.get("name", "Щит")
            remove_player_effect(mob, key)
            text += f"💥 {name} зруйновано.\n"

        if remaining_damage <= 0:
            remaining_damage = 0
            break

    return remaining_damage, text


# ==============================
# ✅ SKILL COOLDOWN HELPERS
# ==============================

def init_skill_cooldowns(mob):
    if "skill_cooldowns" not in mob:
        mob["skill_cooldowns"] = {}


def get_skill_cooldown(mob, skill_key):
    init_skill_cooldowns(mob)

    return int(mob["skill_cooldowns"].get(skill_key, 0) or 0)


def set_skill_cooldown(mob, skill_key, cooldown_turns):
    init_skill_cooldowns(mob)

    cooldown_turns = int(cooldown_turns or 0)

    if cooldown_turns <= 0:
        mob["skill_cooldowns"].pop(skill_key, None)
        return ""

    mob["skill_cooldowns"][skill_key] = cooldown_turns

    return f"⏳ Навичка пішла на перезарядку: {cooldown_turns} ход.\n"


def tick_skill_cooldowns_at_player_turn(mob):
    init_skill_cooldowns(mob)

    if not mob["skill_cooldowns"]:
        return ""

    expired = []

    for skill_key in list(mob["skill_cooldowns"].keys()):
        old_value = int(mob["skill_cooldowns"].get(skill_key, 0) or 0)
        new_value = max(0, old_value - 1)

        if new_value <= 0:
            expired.append(skill_key)
            del mob["skill_cooldowns"][skill_key]
        else:
            mob["skill_cooldowns"][skill_key] = new_value

    text = ""

    if expired:
        text += "✅ Деякі навички знову доступні.\n"

    return text


def validate_skill_cooldown(mob, skill):
    skill_key = skill["key"]
    cooldown = get_skill_cooldown(mob, skill_key)

    if cooldown > 0:
        return {
            "success": False,
            "message": (
                f"⏳ Навичка ще перезаряджається.\n\n"
                f"{skill['name']}\n"
                f"Залишилось: {cooldown} ход."
            )
        }

    return {
        "success": True,
        "message": ""
    }


# ==============================
# ✅ CLASS SKILLS
# ==============================

CLASS_SKILLS_V1 = {
    "warrior": [
        {
            "key": "warrior_cleave",
            "name": "🪓 Розсікання",
            "description": "Завдає 110% фізичної шкоди та додатково дає +10 Люті.",
            "cost_type": "rage",
            "cost": 0,
            "cooldown": 0,
            "damage_multiplier": 1.10,
            "attack_type": "physical",
            "extra_rage": 10,
            "stun_chance": 0,
            "no_damage": False
        },
        {
            "key": "warrior_suppression",
            "name": "🛡️ Пригнічення",
            "description": "Витрачає 20 Люті та знижує фізичний захист ворога на 30% на 3 ходи.",
            "cost_type": "rage",
            "cost": 20,
            "cooldown": 3,
            "damage_multiplier": 0,
            "attack_type": "physical",
            "extra_rage": 0,
            "stun_chance": 0,
            "no_damage": True,
            "effect": "enemy_pdef_down"
        },
        {
            "key": "warrior_subjugation_strike",
            "name": "💥 Удар підкорення",
            "description": "Потребує мінімум 30 Люті, витрачає всю Лють і завдає посилену фізичну шкоду.",
            "cost_type": "rage_all_min",
            "cost": 0,
            "min_cost": 30,
            "cooldown": 3,
            "damage_multiplier": 1.00,
            "attack_type": "physical",
            "extra_rage": 0,
            "stun_chance": 0,
            "no_damage": False,
            "scales_with_spent_rage": True
        }
    ],

    "knight": [
        {
            "key": "knight_shield_bash",
            "name": "🛡️ Удар щитом",
            "description": "Витрачає 20 Люті, завдає 90% фізичної шкоди та має 25% шанс оглушити ворога.",
            "cost_type": "rage",
            "cost": 20,
            "cooldown": 2,
            "damage_multiplier": 0.90,
            "attack_type": "physical",
            "extra_rage": 0,
            "stun_chance": 25,
            "no_damage": False
        },
        {
            "key": "knight_holy_protection",
            "name": "🧱 Святий захист",
            "description": "Витрачає 25 Люті та створює щит, який поглинає шкоду протягом 3 ходів.",
            "cost_type": "rage",
            "cost": 25,
            "cooldown": 4,
            "damage_multiplier": 0,
            "attack_type": "physical",
            "extra_rage": 0,
            "stun_chance": 0,
            "no_damage": True,
            "effect": "player_shield"
        },
        {
            "key": "knight_judgement",
            "name": "⚖️ Кара лицаря",
            "description": "Витрачає 50 Люті та завдає фізичної шкоди, що масштабується від твого фізичного захисту.",
            "cost_type": "rage",
            "cost": 50,
            "cooldown": 4,
            "damage_multiplier": 1.00,
            "attack_type": "physical",
            "extra_rage": 0,
            "stun_chance": 0,
            "no_damage": False,
            "scales_with_player_pdef": True
        }
    ],

    "scout": [
        {
            "key": "scout_aimed_shot",
            "name": "🏹 Прицільний постріл",
            "description": "Витрачає 30 Енергії та завдає 140% фізичної шкоди.",
            "cost_type": "combat_energy",
            "cost": 30,
            "cooldown": 1,
            "damage_multiplier": 1.40,
            "attack_type": "physical",
            "extra_rage": 0,
            "stun_chance": 0,
            "no_damage": False
        },
        {
            "key": "scout_trap",
            "name": "🪤 Пастка",
            "description": "Витрачає 20 Енергії та знижує фізичний захист ворога на 50% на 2 ходи.",
            "cost_type": "combat_energy",
            "cost": 20,
            "cooldown": 3,
            "damage_multiplier": 0,
            "attack_type": "physical",
            "extra_rage": 0,
            "stun_chance": 0,
            "no_damage": True,
            "effect": "enemy_pdef_trap"
        },
        {
            "key": "scout_sting_arrow",
            "name": "☠️ Стріла-жало",
            "description": "Витрачає 35 Енергії, завдає 100% фізичної шкоди та накладає отруту на 3 ходи.",
            "cost_type": "combat_energy",
            "cost": 35,
            "cooldown": 2,
            "damage_multiplier": 1.00,
            "attack_type": "physical",
            "extra_rage": 0,
            "stun_chance": 0,
            "no_damage": False,
            "effect": "enemy_poison"
        }
    ],

    "rogue": [
        {
            "key": "rogue_sneak_strike",
            "name": "⚔️ Підступний випад",
            "description": "Витрачає 25 Енергії, завдає 115% фізичної шкоди та дає 1 комбо.",
            "cost_type": "combat_energy",
            "cost": 25,
            "cooldown": 0,
            "damage_multiplier": 1.15,
            "attack_type": "physical",
            "extra_rage": 0,
            "stun_chance": 0,
            "no_damage": False,
            "combo_gain": 1
        },
        {
            "key": "rogue_bleeding_follow",
            "name": "🩸 Криваве слідування",
            "description": "Витрачає 25 Енергії, завдає 75% фізичної шкоди, накладає кровотечу та дає 1 комбо.",
            "cost_type": "combat_energy",
            "cost": 25,
            "cooldown": 2,
            "damage_multiplier": 0.75,
            "attack_type": "physical",
            "extra_rage": 0,
            "stun_chance": 0,
            "no_damage": False,
            "effect": "enemy_bleed",
            "combo_gain": 1
        },
        {
            "key": "rogue_eviscerate",
            "name": "🗡️ Потрошіння",
            "description": "Витрачає 40 Енергії та всі комбо-очки. Чим більше комбо, тим більша шкода.",
            "cost_type": "combat_energy_combo",
            "cost": 40,
            "min_combo": 1,
            "cooldown": 2,
            "damage_multiplier": 1.00,
            "attack_type": "physical",
            "extra_rage": 0,
            "scales_with_combo": True
        }
    ],

    "mage": [
        {
            "key": "mage_fireball",
            "name": "🔥 Вогняна куля",
            "description": "Витрачає 20 MP та завдає 135% магічної шкоди.",
            "cost_type": "mana",
            "cost": 20,
            "cooldown": 0,
            "damage_multiplier": 1.35,
            "attack_type": "magical",
            "extra_rage": 0,
            "stun_chance": 0,
            "no_damage": False
        },
        {
            "key": "mage_thunder_spell",
            "name": "⚡ Грозове заклинання",
            "description": "Витрачає 45 MP, завдає 160% магічної шкоди та має 25% шанс оглушити ворога.",
            "cost_type": "mana",
            "cost": 45,
            "cooldown": 4,
            "damage_multiplier": 1.60,
            "attack_type": "magical",
            "extra_rage": 0,
            "stun_chance": 25,
            "no_damage": False
        },
        {
            "key": "mage_arcane_flow",
            "name": "🔮 Магічний потік",
            "description": "Не завдає шкоди. Відновлює 25% максимальної Мани в бою.",
            "cost_type": "mana",
            "cost": 0,
            "cooldown": 5,
            "damage_multiplier": 0,
            "attack_type": "magical",
            "extra_rage": 0,
            "stun_chance": 0,
            "no_damage": True,
            "effect": "restore_mana_percent"
        }
    ],

    "priest": [
        {
            "key": "priest_holy_ray",
            "name": "✨ Святий промінь",
            "description": "Витрачає 12 MP та завдає 115% магічної шкоди.",
            "cost_type": "mana",
            "cost": 12,
            "cooldown": 0,
            "damage_multiplier": 1.15,
            "attack_type": "magical",
            "extra_rage": 0,
            "stun_chance": 0,
            "no_damage": False
        },
        {
            "key": "priest_healing_blessing",
            "name": "🌿 Благословення зцілення",
            "description": "Витрачає 30 MP та відновлює здоров’я протягом 4 ходів.",
            "cost_type": "mana",
            "cost": 30,
            "cooldown": 3,
            "damage_multiplier": 0,
            "attack_type": "magical",
            "extra_rage": 0,
            "stun_chance": 0,
            "no_damage": True,
            "effect": "player_hot"
        },
        {
            "key": "priest_purify_faith",
            "name": "🛡️ Очищення віри",
            "description": "Витрачає 20 MP, очищає негативні ефекти, підвищує магічний захист на 3 ходи та відновлює 15% Мани.",
            "cost_type": "mana",
            "cost": 20,
            "cooldown": 4,
            "damage_multiplier": 0,
            "attack_type": "magical",
            "extra_rage": 0,
            "stun_chance": 0,
            "no_damage": True,
            "effect": "player_cleanse_mdef_buff"
        }
    ]
}


def get_player_class_skills(user_id):
    class_key = get_character_class(user_id)

    if not class_key:
        return []

    return CLASS_SKILLS_V1.get(class_key, [])


def get_player_class_skill(user_id):
    skills = get_player_class_skills(user_id)

    if not skills:
        return None

    return skills[0]


def get_player_skill_by_key(user_id, skill_key):
    skills = get_player_class_skills(user_id)

    for skill in skills:
        if skill["key"] == skill_key:
            return skill

    return None


def build_skill_menu_text(user_id, mob):
    skills = get_player_class_skills(user_id)
    class_resource_text = get_class_resource_line(mob)

    if not skills:
        return (
            "✨ Навички\n\n"
            "❌ Для твого класу ще немає доступних навичок."
        ), None

    text = "✨ Навички\n\n"
    text += f"{class_resource_text}\n"

    kb = types.InlineKeyboardMarkup()

    for skill in skills:
        cooldown = get_skill_cooldown(mob, skill["key"])

        text += (
            f"{skill['name']}\n"
            f"{skill['description']}\n"
            f"Вартість: {skill.get('cost', 0)}"
        )

        if skill["cost_type"] == "rage":
            text += " Люті\n"
        elif skill["cost_type"] == "rage_all_min":
            text += f" Люті, мінімум {skill.get('min_cost', 30)}\n"
        elif skill["cost_type"] == "combat_energy":
            text += " Енергії\n"
        elif skill["cost_type"] == "combat_energy_combo":
            text += f" Енергії + мінімум {skill.get('min_combo', 1)} комбо\n"
        elif skill["cost_type"] == "mana":
            text += " MP\n"
        else:
            text += "\n"

        if skill.get("cooldown", 0) > 0:
            text += f"Перезарядка: {skill['cooldown']} ход.\n"

        if cooldown > 0:
            text += f"⏳ Поточна перезарядка: {cooldown} ход.\n\n"
            button_text = f"🔒 {skill['name']} — {cooldown} ход."
            callback_data = f"skill_locked:{skill['key']}"
        else:
            text += "✅ Навичка доступна.\n\n"
            button_text = skill["name"]
            callback_data = f"use_skill:{skill['key']}"

        kb.add(types.InlineKeyboardButton(
            text=button_text,
            callback_data=callback_data
        ))

    enemy_effects_text = get_enemy_effects_text(mob)
    player_effects_text = get_player_effects_text(mob)

    if enemy_effects_text or player_effects_text:
        text += "\n"
        text += enemy_effects_text
        text += player_effects_text

    kb.add(types.InlineKeyboardButton(
        text="⬅️ Назад до бою",
        callback_data="combat_back"
    ))

    return text, kb


def validate_and_pay_skill_cost(user_id, mob, skill):
    cost_type = skill["cost_type"]
    cost = int(skill.get("cost", 0))

    mob["last_skill_spent_rage"] = 0
    mob["last_skill_spent_combo"] = 0

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

    if cost_type == "rage_all_min":
        current_rage = mob.get("player_rage", 0)
        min_cost = int(skill.get("min_cost", 30))

        if current_rage < min_cost:
            return {
                "success": False,
                "message": (
                    f"❌ Недостатньо Люті.\n\n"
                    f"🔴 Потрібно мінімум: {min_cost}\n"
                    f"🔴 У тебе: {current_rage}/{mob.get('player_max_rage', 100)}"
                )
            }

        mob["last_skill_spent_rage"] = current_rage
        mob["player_rage"] = 0

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

    if cost_type == "combat_energy_combo":
        current_energy = mob.get("player_combat_energy", 0)
        current_combo = mob.get("player_combo_points", 0)
        min_combo = int(skill.get("min_combo", 1))

        if current_energy < cost:
            return {
                "success": False,
                "message": (
                    f"❌ Недостатньо Енергії.\n\n"
                    f"🟡 Потрібно: {cost}\n"
                    f"🟡 У тебе: {current_energy}/{mob.get('player_max_combat_energy', 100)}"
                )
            }

        if current_combo < min_combo:
            return {
                "success": False,
                "message": (
                    f"❌ Недостатньо комбо-очок.\n\n"
                    f"⚔️ Потрібно мінімум: {min_combo}\n"
                    f"⚔️ У тебе: {current_combo}/{mob.get('player_max_combo_points', 3)}"
                )
            }

        mob["player_combat_energy"] = max(0, current_energy - cost)
        mob["last_skill_spent_combo"] = consume_rogue_combo_points(mob)

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
        return f"💫 {mob['name']} оглушений на 1 хід!\n"

    return ""


def apply_skill_special_effect(user_id, mob, skill, damage_done):
    effect_key = skill.get("effect", "")

    if not effect_key:
        return ""

    text = ""

    if effect_key == "enemy_pdef_down":
        add_enemy_effect(
            mob,
            "warrior_suppression_pdef_down",
            {
                "name": "🛡️ Пригнічення",
                "type": "debuff",
                "turns": 3,
                "modifiers": {
                    "pdef_percent": -30
                }
            }
        )

        text += f"🛡️ {mob['name']} пригнічений: фізичний захист знижено на 30% на 3 ходи.\n"

    elif effect_key == "player_shield":
        player_pdef, player_mdef = get_effective_player_defenses(user_id, mob)
        stats = get_player_stats(user_id)

        if stats:
            _, _, _, _, _, level = stats
        else:
            level = 1

        absorb_amount = max(
            15,
            int(player_pdef * 2 + level * 3)
        )

        add_player_effect(
            mob,
            "knight_holy_protection_shield",
            {
                "name": "🧱 Святий захист",
                "type": "shield",
                "turns": 3,
                "absorb_left": absorb_amount,
                "modifiers": {}
            }
        )

        text += f"🧱 Святий захист створив щит на {absorb_amount} шкоди на 3 ходи.\n"

    elif effect_key == "enemy_pdef_trap":
        add_enemy_effect(
            mob,
            "scout_trap_pdef_down",
            {
                "name": "🪤 Пастка",
                "type": "debuff",
                "turns": 2,
                "modifiers": {
                    "pdef_percent": -50
                }
            }
        )

        text += f"🪤 {mob['name']} потрапив у пастку: фізичний захист знижено на 50% на 2 ходи.\n"

    elif effect_key == "enemy_bleed":
        bleed_damage = max(
            2,
            int(round(max(1, damage_done) * 0.30))
        )

        add_enemy_effect(
            mob,
            "rogue_bleed",
            {
                "name": "🩸 Кровотеча",
                "icon": "🩸",
                "type": "dot",
                "turns": 3,
                "damage": bleed_damage,
                "modifiers": {}
            }
        )

        text += f"🩸 На {mob['name']} накладено кровотечу: {bleed_damage} шкоди протягом 3 ходів.\n"

    elif effect_key == "enemy_poison":
        poison_damage = max(
            2,
            int(round(max(1, damage_done) * 0.30))
        )

        add_enemy_effect(
            mob,
            "scout_poison",
            {
                "name": "☠️ Отрута",
                "icon": "☠️",
                "type": "dot",
                "turns": 3,
                "damage": poison_damage,
                "modifiers": {}
            }
        )

        text += f"☠️ {mob['name']} отруєний: {poison_damage} шкоди протягом 3 ходів.\n"

    elif effect_key == "player_hot":
        max_hp = get_max_hp(user_id)

        heal_per_turn = max(
            5,
            int(round(max_hp * 0.10))
        )

        add_player_effect(
            mob,
            "priest_healing_blessing_hot",
            {
                "name": "🌿 Благословення зцілення",
                "type": "hot",
                "turns": 4,
                "heal": heal_per_turn,
                "modifiers": {}
            }
        )

        text += f"🌿 Благословення зцілення: +{heal_per_turn} HP протягом 4 ходів.\n"

    elif effect_key == "restore_mana_percent":
        mp_data = get_user_mp(user_id)

        current_mp = mp_data.get("mp", 0)
        max_mp = mp_data.get("max_mp", 0)

        restore_amount = max(
            1,
            int(round(max_mp * 0.25))
        )

        new_mp = min(max_mp, current_mp + restore_amount)
        restored = new_mp - current_mp

        try:
            from db import set_user_mp
            set_user_mp(user_id, new_mp)
        except Exception:
            pass

        mob["player_mp"] = new_mp
        mob["player_max_mp"] = max_mp

        text += f"🔮 Магічний потік відновив {restored} MP ({new_mp}/{max_mp}).\n"

    elif effect_key == "player_cleanse_mdef_buff":
        cleared = 0

        for key in list(mob.get("player_effects", {}).keys()):
            effect = mob["player_effects"].get(key, {})

            if effect.get("negative"):
                remove_player_effect(mob, key)
                cleared += 1

        add_player_effect(
            mob,
            "priest_purify_faith_mdef",
            {
                "name": "🛡️ Очищення віри",
                "type": "buff",
                "turns": 3,
                "modifiers": {
                    "mdef_percent": 30
                }
            }
        )

        # Restore 15% max MP
        mp_data = get_user_mp(user_id)
        current_mp = mp_data.get("mp", 0)
        max_mp = mp_data.get("max_mp", 0)
        restore_amount = max(1, int(round(max_mp * 0.15)))
        new_mp = min(max_mp, current_mp + restore_amount)
        restored = new_mp - current_mp

        try:
            from db import set_user_mp
            set_user_mp(user_id, new_mp)
        except Exception:
            pass

        mob["player_mp"] = new_mp
        mob["player_max_mp"] = max_mp

        if cleared > 0:
            text += f"🛡️ Очищення віри зняло негативних ефектів: {cleared}.\n"

        text += "🛡️ Магічний захист підвищено на 30% на 3 ходи.\n"
        text += f"🛡️ Очищення віри відновило {restored} MP ({new_mp}/{max_mp}).\n"

    return text


def append_mp_restore_text(text, mp_restore_result):
    if mp_restore_result and mp_restore_result.get("restored"):
        text += (
            f"\n🔵 Мана відновлена: "
            f"{mp_restore_result['mp']}/{mp_restore_result['max_mp']}"
        )

    return text


def append_effects_to_combat_text(text, mob):
    enemy_effects_text = get_enemy_effects_text(mob)
    player_effects_text = get_player_effects_text(mob)

    if enemy_effects_text or player_effects_text:
        text += "\n\n"
        text += enemy_effects_text
        text += player_effects_text

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


def build_victory_text(user_id, lvl, mob, reward, wear_result, contract_result, daily_result, prefix_text=""):
    exp_result = reward["exp_result"]

    victory_title = "🏆 ВИ ПЕРЕМОГЛИ!"

    if mob.get("is_elite"):
        victory_title = "🏆 ВИ ПЕРЕМОГЛИ ЕЛІТНОГО ВОРОГА!"

    text = f"{victory_title}\n\n"

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

    mp_restore_result = restore_user_mp_to_full(user_id)
    text = append_mp_restore_text(text, mp_restore_result)

    text += f"\n🎒 Сумка: {reward['used_slots']}/{reward['capacity']} слотів"

    return text



def rollback_turn_start_hot_heal_on_victory(user_id, mob):
    """
    Відкочує HoT, який спрацював на початку ходу,
    якщо цей самий хід завершився перемогою.
    """

    if not mob:
        return

    hot_heal = int(mob.get("_turn_start_hot_heal_applied", 0) or 0)

    if hot_heal <= 0:
        return

    if "player_hp" in mob and "player_max_hp" in mob:
        current_hp = int(mob.get("player_hp", 0) or 0)
        max_hp = int(mob.get("player_max_hp", get_max_hp(user_id)) or get_max_hp(user_id))
    else:
        current_hp = get_current_hp_raw(user_id)
        max_hp = get_max_hp(user_id)

    new_hp = current_hp - hot_heal
    new_hp = max(1, min(max_hp, new_hp))

    mob["player_hp"] = new_hp
    mob["player_max_hp"] = max_hp
    mob["_turn_start_hot_heal_applied"] = 0

    set_current_hp(user_id, new_hp)


def finalize_combat_state_before_victory(user_id, mob):
    """
    Фіналізує бойовий стан перед перемогою.

    Перед очищенням бойових ефектів відкочує HoT, який спрацював
    на старті переможного ходу. Потім зберігає поточне HP і очищає
    тимчасові ефекти бою.
    """

    if not mob:
        return

    rollback_turn_start_hot_heal_on_victory(user_id, mob)

    if "player_hp" in mob:
        try:
            player_hp = int(mob.get("player_hp", 0) or 0)
            player_max_hp = int(mob.get("player_max_hp", get_max_hp(user_id)) or get_max_hp(user_id))

            if player_max_hp <= 0:
                player_max_hp = get_max_hp(user_id)

            player_hp = max(1, min(player_max_hp, player_hp))
            set_current_hp(user_id, player_hp)

            mob["player_hp"] = player_hp
            mob["player_max_hp"] = player_max_hp

        except Exception:
            pass

    mob["player_effects"] = {}
    mob["enemy_effects"] = {}
    mob["stunned_turns"] = 0
    mob["_turn_start_hot_heal_applied"] = 0

def process_victory(bot, chat_id, user_id, lvl, mob, prefix_text=""):
    """
    Завершення бою перемогою.

    Перед виходом із бою фіксуємо поточне HP з бойового стану
    і очищаємо тимчасові бойові ефекти.

    Це виправляє кейс, коли жрець наклав HoT у фінальному раунді,
    а залишкові тіки лікування некоректно доліковували героя після перемоги.
    """

    finalize_combat_state_before_victory(
        user_id=user_id,
        mob=mob
    )

    if hasattr(bot, "user_data") and user_id in bot.user_data:
        del bot.user_data[user_id]

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

    text = build_victory_text(
        user_id=user_id,
        lvl=lvl,
        mob=mob,
        reward=reward,
        wear_result=wear_result,
        contract_result=contract_result,
        daily_result=daily_result,
        prefix_text=prefix_text
    )

    bot.send_message(
        chat_id,
        text,
        reply_markup=main_kb()
    )


# ==============================
# REGISTER HANDLERS
# ==============================

def register_combat_handlers(bot):

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

        current_hp = get_current_hp_raw(user_id)
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
        mob["skill_cooldowns"] = {}
        mob["enemy_effects"] = {}
        mob["player_effects"] = {}
        mob["last_skill_spent_rage"] = 0
        mob["last_skill_spent_combo"] = 0
        mob["player_hp"] = current_hp
        mob["player_max_hp"] = max_hp

        init_class_combat_resource(user_id, mob)
        init_combat_effects(mob)

        bot.user_data = getattr(bot, "user_data", {})
        bot.user_data[user_id] = mob

        attack_profile = get_player_attack_profile(user_id)

        player_pdef, player_mdef = get_effective_player_defenses(user_id, mob)

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
        character_name = get_character_name(user_id) or "Без імені"

        text = (
            f"📍 Мапа: {location['name']}\n"
            f"🔎 Ти зустрів {mob['name']}\n\n"
            f"{elite_text}"
            f"======================\n\n"

            f"👤 {character_name}\n"
            f"❤️ Здоров’я: {current_hp}/{max_hp}\n"
            f"{hp_bar(current_hp, max_hp)}\n"
            f"{class_resource_text}"
            f"⚔️ Тип атаки: {player_attack_type_text}\n"
            f"🗡️ Зброя: {weapon_text}\n"
            f"💥 Атака: {attack_profile['display_attack']}\n"
            f"🛡 Фіз. захист: {player_pdef}\n"
            f"🔮 Маг. захист: {player_mdef}\n\n"

            f"----------------------\n\n"

            f"👹 {mob['name']}\n"
            f"🏷 Рівень: {mob['level']}\n"
            f"❤️ Здоров’я: {mob['hp']}/{mob['max_hp']}\n"
            f"{hp_bar(mob['hp'], mob['max_hp'])}\n"
            f"⚔️ Атака: {mob['attack']}\n"
            f"🛡 Фіз. захист: {mob.get('pdef', mob.get('def', 0))}\n"
            f"🔮 Маг. захист: {mob.get('mdef', mob.get('def', 0))}\n"
            f"🎯 Тип атаки: {attack_type_text}\n\n"

            f"⚔️ Бій починається!"
        )

        # Спочатку показуємо фальшиву клавіатуру, щоб системна не з'являлася
        bot.send_message(
            message.chat.id,
            "⚔️ Бій розпочався!",
            reply_markup=combat_placeholder_kb()
        )
        # Потім показуємо повідомлення про бій з inline меню
        bot.send_message(
            message.chat.id,
            text,
            reply_markup=build_combat_inline_kb(user_id, mob)
        )

    @bot.message_handler(func=lambda m: m.text == "⚔️ Бій триває...")
    def combat_placeholder(message):
        # Обробник для фальшивої кнопки — нічого не робимо, просто відповідаємо
        user_id = message.from_user.id
        if hasattr(bot, "user_data") and user_id in bot.user_data:
            mob = bot.user_data[user_id]
            bot.send_message(
                message.chat.id,
                "Використовуй інлайн кнопки для бою!",
                reply_markup=combat_placeholder_kb()
            )
        else:
            bot.send_message(
                message.chat.id,
                "Ти не в бою!",
                reply_markup=main_kb()
            )

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
        init_combat_effects(mob)
        character_name = get_character_name(user_id) or "Без імені"

        cooldown_start_text = tick_skill_cooldowns_at_player_turn(mob)
        player_effects_text = process_player_turn_start_effects(user_id, mob)
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

        player_pdef, player_mdef = get_effective_player_defenses(user_id, mob)

        # Використовуємо здоров'я з mob, якщо воно там є, інакше з бази (на випадок старих сесій)
        if "player_hp" in mob and "player_max_hp" in mob:
            player_hp = mob["player_hp"]
            player_max_hp = mob["player_max_hp"]
        else:
            player_hp = get_current_hp_raw(user_id)
            player_max_hp = get_max_hp(user_id)
            mob["player_hp"] = player_hp
            mob["player_max_hp"] = player_max_hp

        if "max_hp" not in mob:
            mob["max_hp"] = mob["hp"]

        mob_def_for_player_attack = get_effective_mob_def(
            mob,
            attack_profile["attack_type"]
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

        if mob["hp"] <= 0:
            prefix_text = ""

            if cooldown_start_text or player_effects_text or resource_start_text or resource_attack_text:
                prefix_text += cooldown_start_text
                prefix_text += player_effects_text
                prefix_text += resource_start_text
                prefix_text += resource_attack_text

            process_victory(
                bot=bot,
                chat_id=message.chat.id,
                user_id=user_id,
                lvl=lvl,
                mob=mob,
                prefix_text=prefix_text
            )
            return

        enemy_effect_result = process_enemy_turn_start_effects(mob)
        enemy_effect_text = enemy_effect_result.get("text", "")

        if mob["hp"] <= 0:
            prefix_text = enemy_effect_text

            process_victory(
                bot=bot,
                chat_id=message.chat.id,
                user_id=user_id,
                lvl=lvl,
                mob=mob,
                prefix_text=prefix_text
            )
            return

        mob_dmg = 0
        is_mob_crit = False
        is_dodge = False
        resource_damage_text = ""

        if mob.get("stunned_turns", 0) > 0:
            mob["stunned_turns"] -= 1
            enemy_action_text = f"💫 {mob['name']} оглушений і пропускає хід.\n\n"
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

            shield_text = ""

            if not is_dodge and mob_dmg > 0:
                mob_dmg, shield_text = apply_player_shield_absorb(mob, mob_dmg)

            player_hp -= mob_dmg
            mob["player_hp"] = player_hp

            resource_damage_text = add_rage_for_damage_taken(mob, mob_dmg)

            if is_dodge:
                enemy_action_text = f"💨 УХИЛ! {character_name} уникнув атаки {mob['name']}\n\n"
            elif is_mob_crit:
                enemy_action_text = f"💥 КРИТ {mob['name']}! {character_name} отримав {mob_dmg} шкоди\n"
                enemy_action_text += shield_text
                enemy_action_text += "\n"
            else:
                enemy_action_text = f"👹 {mob['name']} завдав {character_name} {mob_dmg} шкоди\n"
                enemy_action_text += shield_text
                enemy_action_text += "\n"

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

        if mob.get("potion_cooldown", 0) > 0:
            mob["potion_cooldown"] -= 1

        text = "⚔️ БІЙ\n\n"

        if cooldown_start_text:
            text += cooldown_start_text

        if player_effects_text:
            text += player_effects_text

        if resource_start_text:
            text += resource_start_text

        if resource_attack_text:
            text += resource_attack_text

        if enemy_effect_text:
            text += enemy_effect_text

        if resource_damage_text:
            text += resource_damage_text

        if cooldown_start_text or player_effects_text or resource_start_text or resource_attack_text or enemy_effect_text or resource_damage_text:
            text += "\n"

        if is_player_crit:
            text += f"💥 КРИТ! {character_name} завдав {mob['name']} {dmg} шкоди"
        else:
            text += f"🗡️ {character_name} завдав {mob['name']} {dmg} шкоди"

        if weapon_damage > 0:
            text += f" (зброя: {weapon_damage})"

        text += "\n"
        text += enemy_action_text

        class_resource_text = get_class_resource_line(mob)

        text += (
            f"❤️ {character_name}: {player_hp}/{player_max_hp}\n"
            f"{hp_bar(player_hp, player_max_hp)}\n"
            f"{class_resource_text}\n"
            f"👹 {mob['name']}: {mob['hp']}/{mob['max_hp']}\n"
            f"{hp_bar(mob['hp'], mob['max_hp'])}"
        )

        text = append_effects_to_combat_text(text, mob)

        if mob.get("potion_cooldown", 0) > 0:
            text += f"\n\n🔴 Повний шлунок: {mob['potion_cooldown']} ход."


        bot.send_message(
            message.chat.id,
            text,
            reply_markup=build_combat_inline_kb(user_id, mob)
        )

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
        init_combat_effects(mob)

        text, kb = build_skill_menu_text(user_id, mob)

        if not kb:
    
            bot.send_message(
                message.chat.id,
                text,
                reply_markup=build_combat_inline_kb(user_id, mob)
            )
            return

        bot.send_message(
            message.chat.id,
            text,
            reply_markup=kb
        )
        
    # Старий обробник текстових кнопок скілів (не використовується, тепер використовуємо inline)
    # @bot.message_handler(func=lambda m: any(
    #     skill_name in m.text 
    #     for class_skills in CLASS_SKILLS_V1.values() 
    #     for skill_name in [s["name"] for s in class_skills]
    # ))
    def use_skill_text_button(message):
        user_id = message.from_user.id
        
        if not hasattr(bot, "user_data") or user_id not in bot.user_data:
            bot.send_message(
                message.chat.id,
                "❗ Ти не в бою",
                reply_markup=main_kb()
            )
            return
            
        mob = bot.user_data[user_id]
        init_combat_effects(mob)
        character_name = get_character_name(user_id) or "Без імені"
        class_key = get_character_class(user_id)
        class_skills = CLASS_SKILLS_V1.get(class_key, [])
        
        # Знайти навичку за ім'ям
        skill = None
        for s in class_skills:
            if s["name"] == message.text:
                skill = s
                break
        
        if not skill:
            class_key = get_character_class(user_id)
            skills = CLASS_SKILLS_V1.get(class_key, [])
            bot.send_message(
                message.chat.id,
                "❌ Навичку не знайдено.",
                reply_markup=fight_kb(skills)
            )
            return
            
        cooldown_result = validate_skill_cooldown(mob, skill)
        if not cooldown_result["success"]:
            class_key = get_character_class(user_id)
            skills = CLASS_SKILLS_V1.get(class_key, [])
            bot.send_message(
                message.chat.id,
                cooldown_result["message"],
                reply_markup=fight_kb(skills)
            )
            return
            
        cooldown_start_text = tick_skill_cooldowns_at_player_turn(mob)
        player_effects_text = process_player_turn_start_effects(user_id, mob)
        resource_start_text = regenerate_class_resource_at_player_turn(mob)
        
        pay_result = validate_and_pay_skill_cost(user_id, mob, skill)
        if not pay_result["success"]:
            class_key = get_character_class(user_id)
            skills = CLASS_SKILLS_V1.get(class_key, [])
            bot.send_message(
                message.chat.id,
                pay_result["message"],
                reply_markup=fight_kb(skills)
            )
            return
            
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
        player_pdef, player_mdef = get_effective_player_defenses(user_id, mob)
        if "player_hp" in mob and "player_max_hp" in mob:
            player_hp = mob["player_hp"]
            player_max_hp = mob["player_max_hp"]
        else:
            player_hp = get_current_hp_raw(user_id)
            player_max_hp = get_max_hp(user_id)
            mob["player_hp"] = player_hp
            mob["player_max_hp"] = player_max_hp
        
        if "max_hp" not in mob:
            mob["max_hp"] = mob["hp"]
            
        skill_attack_type = skill.get("attack_type", attack_profile["attack_type"])
        
        if skill.get("no_damage"):
            base_dmg = 0
            dmg = 0
            is_player_crit = False
            weapon_damage = 0
        else:
            if skill_attack_type == "magical":
                mob_def_for_player_attack = get_effective_mob_def(mob, "magical")
                player_stat_attack = int_
            else:
                mob_def_for_player_attack = get_effective_mob_def(mob, "physical")
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
            
            dmg = max(1, int(round(base_dmg * float(skill.get("damage_multiplier", 1.0)))))
            
            if skill.get("scales_with_spent_rage"):
                spent_rage = mob.get("last_skill_spent_rage", 0)
                bonus_multiplier = 1.0 + (spent_rage / 100)
                dmg = max(1, int(round(base_dmg * bonus_multiplier)))
                
            if skill.get("scales_with_player_pdef"):
                player_pdef, player_mdef = get_effective_player_defenses(user_id, mob)
                dmg = max(1, int(round(player_pdef * 0.85)))
                
            if skill.get("scales_with_combo"):
                spent_combo = mob.get("last_skill_spent_combo", 0)
                bonus_multiplier = 1.0 + (spent_combo * 0.35)
                dmg = max(1, int(round(base_dmg * bonus_multiplier)))
                
            mob["hp"] -= dmg
            
        resource_attack_text = ""
        if not skill.get("no_damage"):
            if mob.get("player_resource_type") == "rage":
                resource_attack_text += add_rage_for_player_attack(mob)
                
        combo_gain = int(skill.get("combo_gain", 0))
        if combo_gain > 0:
            resource_attack_text += add_rogue_combo_point(mob, combo_gain)
            
        resource_attack_text += apply_extra_rage_from_skill(mob, skill)
        
        stun_text = ""
        if not skill.get("no_damage"):
            stun_text = roll_skill_stun(mob, skill)
            
        special_effect_text = apply_skill_special_effect(
            user_id=user_id,
            mob=mob,
            skill=skill,
            damage_done=dmg
        )
        
        cooldown_set_text = set_skill_cooldown(
            mob,
            skill["key"],
            skill.get("cooldown", 0)
        )
        
        if mob["hp"] <= 0:
            prefix_text = ""
            if cooldown_start_text or player_effects_text or resource_start_text or resource_attack_text or cooldown_set_text or special_effect_text:
                prefix_text += cooldown_start_text
                prefix_text += player_effects_text
                prefix_text += resource_start_text
                prefix_text += resource_attack_text
                prefix_text += cooldown_set_text
                prefix_text += special_effect_text
                
            prefix_text += f"✨ Навичка: {skill['name']}\n"
            if skill.get("no_damage"):
                prefix_text += "Навичка застосована.\n"
            else:
                prefix_text += f"Ти завдав {dmg} шкоди.\n"
                
            process_victory(
                bot=bot,
                chat_id=message.chat.id,
                user_id=user_id,
                lvl=lvl,
                mob=mob,
                prefix_text=prefix_text
            )
            return
            
        enemy_effect_result = process_enemy_turn_start_effects(mob)
        enemy_effect_text = enemy_effect_result.get("text", "")
        
        if mob["hp"] <= 0:
            prefix_text = ""
            if cooldown_start_text or player_effects_text or resource_start_text or resource_attack_text or cooldown_set_text or special_effect_text or enemy_effect_text:
                prefix_text += cooldown_start_text
                prefix_text += player_effects_text
                prefix_text += resource_start_text
                prefix_text += resource_attack_text
                prefix_text += cooldown_set_text
                prefix_text += special_effect_text
                prefix_text += enemy_effect_text
                
            prefix_text += f"✨ Навичка: {skill['name']}\n"
            prefix_text += "Ворог повалений ефектами.\n"
            
            process_victory(
                bot=bot,
                chat_id=message.chat.id,
                user_id=user_id,
                lvl=lvl,
                mob=mob,
                prefix_text=prefix_text
            )
            return
            
        mob_dmg = 0
        is_mob_crit = False
        is_dodge = False
        resource_damage_text = ""
        
        if mob.get("stunned_turns", 0) > 0:
            mob["stunned_turns"] -= 1
            enemy_action_text = f"💫 {mob['name']} оглушений і пропускає хід.\n\n"
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
            
            shield_text = ""
            if not is_dodge and mob_dmg > 0:
                mob_dmg, shield_text = apply_player_shield_absorb(mob, mob_dmg)
                
            player_hp -= mob_dmg
            
            resource_damage_text = add_rage_for_damage_taken(mob, mob_dmg)
            
            if is_dodge:
                enemy_action_text = f"💨 УХИЛ! {character_name} уникнув атаки {mob['name']}\n\n"
            elif is_mob_crit:
                enemy_action_text = f"💥 КРИТ {mob['name']}! {character_name} отримав {mob_dmg} шкоди\n"
                enemy_action_text += shield_text
                enemy_action_text += "\n"
            else:
                enemy_action_text = f"👹 {mob['name']} завдав {character_name} {mob_dmg} шкоди\n"
                enemy_action_text += shield_text
                enemy_action_text += "\n"
                
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
        
        if mob.get("potion_cooldown", 0) > 0:
            mob["potion_cooldown"] -= 1
            
        text = "✨ НАВИЧКА\n\n"
        if cooldown_start_text:
            text += cooldown_start_text
        if player_effects_text:
            text += player_effects_text
        if resource_start_text:
            text += resource_start_text
        if resource_attack_text:
            text += resource_attack_text
        if cooldown_set_text:
            text += cooldown_set_text
        if special_effect_text:
            text += special_effect_text
        if enemy_effect_text:
            text += enemy_effect_text
        if resource_damage_text:
            text += resource_damage_text
            
        if cooldown_start_text or player_effects_text or resource_start_text or resource_attack_text or cooldown_set_text or special_effect_text or enemy_effect_text or resource_damage_text:
            text += "\n"
            
        text += f"{skill['name']}\n"
        
        if skill.get("no_damage"):
            text += "✨ Навичка застосована.\n"
        else:
            if is_player_crit:
                text += f"💥 КРИТ! {character_name} завдав {mob['name']} {dmg} шкоди"
            else:
                text += f"✨ {character_name} завдав {mob['name']} {dmg} шкоди"
                
            if weapon_damage > 0:
                text += f" (зброя: {weapon_damage})"
                
            text += "\n"
            
        text += enemy_action_text
        class_resource_text = get_class_resource_line(mob)
        
        text += (
            f"❤️ {character_name}: {player_hp}/{player_max_hp}\n"
            f"{hp_bar(player_hp, player_max_hp)}\n"
            f"{class_resource_text}\n"
            f"👹 {mob['name']}: {mob['hp']}/{mob['max_hp']}\n"
            f"{hp_bar(mob['hp'], mob['max_hp'])}"
        )
        
        text = append_effects_to_combat_text(text, mob)
        
        if mob.get("potion_cooldown", 0) > 0:
            text += f"\n\n🔴 Повний шлунок: {mob['potion_cooldown']} ход."
            
        class_key = get_character_class(user_id)
        skills = CLASS_SKILLS_V1.get(class_key, [])
        
        bot.send_message(
            message.chat.id,
            text,
            reply_markup=fight_kb(skills)
        )

    @bot.callback_query_handler(func=lambda call: call.data.startswith("skill_locked:"))
    def skill_locked(call):
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
        skill_key = call.data.split(":")[1]
        skill = get_player_skill_by_key(user_id, skill_key)

        bot.answer_callback_query(call.id)

        if not skill:
    
            bot.send_message(
                call.message.chat.id,
                "❌ Навичку не знайдено.",
                reply_markup=build_combat_inline_kb(user_id, mob)
            )
            return

        cooldown = get_skill_cooldown(mob, skill["key"])

        if cooldown <= 0:
            text, kb = build_skill_menu_text(user_id, mob)
            if kb:
                bot.send_message(
                    call.message.chat.id,
                    text,
                    reply_markup=kb
                )
            else:
        
                bot.send_message(
                    call.message.chat.id,
                    text,
                    reply_markup=build_combat_inline_kb(user_id, mob)
                )
            return


        bot.send_message(
            call.message.chat.id,
            (
                f"⏳ Навичка ще перезаряджається.\n\n"
                f"{skill['name']}\n"
                f"Залишилось: {cooldown} ход.\n\n"
                f"ℹ️ Виконай реальний хід: атакуй або використай доступну навичку."
            ),
            reply_markup=build_combat_inline_kb(user_id, mob)
        )

    # ==========================================
    # НОВІ ОБРОБНИКИ INLINE КНОПОК БОЮ
    # ==========================================
    
    @bot.callback_query_handler(func=lambda call: call.data == "combat_attack")
    def combat_attack_callback(call):
        user_id = call.from_user.id
        
        if not hasattr(bot, "user_data") or user_id not in bot.user_data:
            bot.answer_callback_query(call.id)
            bot.send_message(
                call.message.chat.id,
                "❗ Спочатку почни полювання",
                reply_markup=main_kb()
            )
            return
            
        # Викликаємо вже існуючу логіку атаки
        class FakeMessage:
            def __init__(self, chat_id, from_user_id):
                self.chat = type('obj', (object,), {'id': chat_id})
                self.from_user = type('obj', (object,), {'id': from_user_id})
        
        message = FakeMessage(call.message.chat.id, user_id)
        attack(message)
        
    @bot.callback_query_handler(func=lambda call: call.data == "combat_potion")
    def combat_potion_callback(call):
        user_id = call.from_user.id
        
        if not hasattr(bot, "user_data") or user_id not in bot.user_data:
            bot.answer_callback_query(call.id)
            bot.send_message(
                call.message.chat.id,
                "❗ Ти не в бою",
                reply_markup=main_kb()
            )
            return
            
        class FakeMessage:
            def __init__(self, chat_id, from_user_id):
                self.chat = type('obj', (object,), {'id': chat_id})
                self.from_user = type('obj', (object,), {'id': from_user_id})
        
        message = FakeMessage(call.message.chat.id, user_id)
        choose_potion_in_combat(message)

    @bot.callback_query_handler(func=lambda call: call.data == "combat_flee")
    def combat_flee_callback(call):
        user_id = call.from_user.id
        
        if not hasattr(bot, "user_data") or user_id not in bot.user_data:
            bot.answer_callback_query(call.id)
            bot.send_message(
                call.message.chat.id,
                "❗ Ти не в бою",
                reply_markup=main_kb()
            )
            return
            
        class FakeMessage:
            def __init__(self, chat_id, from_user_id):
                self.chat = type('obj', (object,), {'id': chat_id})
                self.from_user = type('obj', (object,), {'id': from_user_id})
        
        message = FakeMessage(call.message.chat.id, user_id)
        escape(message)
        
    @bot.callback_query_handler(func=lambda call: call.data.startswith("combat_skill_locked:"))
    def combat_skill_locked_callback(call):
        user_id = call.from_user.id
        skill_key = call.data.split(":")[1]
        
        if not hasattr(bot, "user_data") or user_id not in bot.user_data:
            bot.answer_callback_query(call.id, "❗ Бій вже завершено")
            return
            
        mob = bot.user_data[user_id]
        skill = get_player_skill_by_key(user_id, skill_key)
        cooldown = get_skill_cooldown(mob, skill["key"])
        
        bot.answer_callback_query(call.id, f"⏳ {skill['name']} ще перезаряджається: {cooldown} ходів")
        
    @bot.callback_query_handler(func=lambda call: call.data.startswith("combat_use_skill:"))
    def combat_use_skill_callback(call):
        user_id = call.from_user.id
        skill_key = call.data.split(":")[1]
        
        if not hasattr(bot, "user_data") or user_id not in bot.user_data:
            bot.answer_callback_query(call.id)
            bot.send_message(
                call.message.chat.id,
                "❗ Бій вже завершено",
                reply_markup=main_kb()
            )
            return
            
        mob = bot.user_data[user_id]
        init_combat_effects(mob)
        character_name = get_character_name(user_id) or "Без імені"
        skill = get_player_skill_by_key(user_id, skill_key)
        class_key = get_character_class(user_id)
        
        if not skill:
            bot.answer_callback_query(call.id)
    
            bot.send_message(
                call.message.chat.id,
                "❌ Навичку не знайдено.",
                reply_markup=build_combat_inline_kb(user_id, mob)
            )
            return
            
        cooldown_result = validate_skill_cooldown(mob, skill)
        if not cooldown_result["success"]:
            bot.answer_callback_query(call.id)
    
            bot.send_message(
                call.message.chat.id,
                cooldown_result["message"],
                reply_markup=build_combat_inline_kb(user_id, mob)
            )
            return
            
        cooldown_start_text = tick_skill_cooldowns_at_player_turn(mob)
        player_effects_text = process_player_turn_start_effects(user_id, mob)
        resource_start_text = regenerate_class_resource_at_player_turn(mob)
        
        pay_result = validate_and_pay_skill_cost(user_id, mob, skill)
        if not pay_result["success"]:
            bot.answer_callback_query(call.id)
    
            bot.send_message(
                call.message.chat.id,
                pay_result["message"],
                reply_markup=build_combat_inline_kb(user_id, mob)
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

        player_pdef, player_mdef = get_effective_player_defenses(user_id, mob)

        # Використовуємо здоров'я з mob, якщо воно там є, інакше з бази (на випадок старих сесій)
        if "player_hp" in mob and "player_max_hp" in mob:
            player_hp = mob["player_hp"]
            player_max_hp = mob["player_max_hp"]
        else:
            player_hp = get_current_hp_raw(user_id)
            player_max_hp = get_max_hp(user_id)
            mob["player_hp"] = player_hp
            mob["player_max_hp"] = player_max_hp

        if "max_hp" not in mob:
            mob["max_hp"] = mob["hp"]

        skill_attack_type = skill.get("attack_type", attack_profile["attack_type"])

        if skill.get("no_damage"):
            base_dmg = 0
            dmg = 0
            is_player_crit = False
            weapon_damage = 0
        else:
            if skill_attack_type == "magical":
                mob_def_for_player_attack = get_effective_mob_def(mob, "magical")
                player_stat_attack = int_
            else:
                mob_def_for_player_attack = get_effective_mob_def(mob, "physical")
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

            if skill.get("scales_with_spent_rage"):
                spent_rage = mob.get("last_skill_spent_rage", 0)
                bonus_multiplier = 1.0 + (spent_rage / 100)

                dmg = max(
                    1,
                    int(round(base_dmg * bonus_multiplier))
                )

            if skill.get("scales_with_player_pdef"):
                player_pdef, player_mdef = get_effective_player_defenses(user_id, mob)

                dmg = max(
                    1,
                    int(round(player_pdef * 0.85))
                )

            if skill.get("scales_with_combo"):
                spent_combo = mob.get("last_skill_spent_combo", 0)
                bonus_multiplier = 1.0 + (spent_combo * 0.35)

                dmg = max(
                    1,
                    int(round(base_dmg * bonus_multiplier))
                )

            mob["hp"] -= dmg

        resource_attack_text = ""

        if not skill.get("no_damage"):
            if mob.get("player_resource_type") == "rage":
                resource_attack_text += add_rage_for_player_attack(mob)

        combo_gain = int(skill.get("combo_gain", 0))

        if combo_gain > 0:
            resource_attack_text += add_rogue_combo_point(mob, combo_gain)

        resource_attack_text += apply_extra_rage_from_skill(mob, skill)

        stun_text = ""

        if not skill.get("no_damage"):
            stun_text = roll_skill_stun(mob, skill)

        special_effect_text = apply_skill_special_effect(
            user_id=user_id,
            mob=mob,
            skill=skill,
            damage_done=dmg
        )

        cooldown_set_text = set_skill_cooldown(
            mob,
            skill["key"],
            skill.get("cooldown", 0)
        )

        bot.answer_callback_query(call.id)

        if mob["hp"] <= 0:
            prefix_text = ""

            if cooldown_start_text or player_effects_text or resource_start_text or resource_attack_text or cooldown_set_text or special_effect_text:
                prefix_text += cooldown_start_text
                prefix_text += player_effects_text
                prefix_text += resource_start_text
                prefix_text += resource_attack_text
                prefix_text += cooldown_set_text
                prefix_text += special_effect_text

            prefix_text += f"✨ Навичка: {skill['name']}\n"

            if skill.get("no_damage"):
                prefix_text += "Навичка застосована.\n"
            else:
                prefix_text += f"Ти завдав {dmg} шкоди.\n"

            process_victory(
                bot=bot,
                chat_id=call.message.chat.id,
                user_id=user_id,
                lvl=lvl,
                mob=mob,
                prefix_text=prefix_text
            )
            return

        enemy_effect_result = process_enemy_turn_start_effects(mob)
        enemy_effect_text = enemy_effect_result.get("text", "")

        if mob["hp"] <= 0:
            prefix_text = ""

            if cooldown_start_text or player_effects_text or resource_start_text or resource_attack_text or cooldown_set_text or special_effect_text or enemy_effect_text:
                prefix_text += cooldown_start_text
                prefix_text += player_effects_text
                prefix_text += resource_start_text
                prefix_text += resource_attack_text
                prefix_text += cooldown_set_text
                prefix_text += special_effect_text
                prefix_text += enemy_effect_text

            prefix_text += f"✨ Навичка: {skill['name']}\n"
            prefix_text += "Ворог повалений ефектами.\n"

            process_victory(
                bot=bot,
                chat_id=call.message.chat.id,
                user_id=user_id,
                lvl=lvl,
                mob=mob,
                prefix_text=prefix_text
            )
            return

        mob_dmg = 0
        is_mob_crit = False
        is_dodge = False
        resource_damage_text = ""

        if mob.get("stunned_turns", 0) > 0:
            mob["stunned_turns"] -= 1
            enemy_action_text = f"💫 {mob['name']} оглушений і пропускає хід.\n\n"
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

            shield_text = ""

            if not is_dodge and mob_dmg > 0:
                mob_dmg, shield_text = apply_player_shield_absorb(mob, mob_dmg)

            player_hp -= mob_dmg
            mob["player_hp"] = player_hp

            resource_damage_text = add_rage_for_damage_taken(mob, mob_dmg)

            if is_dodge:
                enemy_action_text = f"💨 УХИЛ! {character_name} уникнув атаки {mob['name']}\n\n"
            elif is_mob_crit:
                enemy_action_text = f"💥 КРИТ {mob['name']}! {character_name} отримав {mob_dmg} шкоди\n"
                enemy_action_text += shield_text
                enemy_action_text += "\n"
            else:
                enemy_action_text = f"👹 {mob['name']} завдав {character_name} {mob_dmg} шкоди\n"
                enemy_action_text += shield_text
                enemy_action_text += "\n"

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

        if cooldown_start_text:
            text += cooldown_start_text

        if player_effects_text:
            text += player_effects_text

        if resource_start_text:
            text += resource_start_text

        if resource_attack_text:
            text += resource_attack_text

        if cooldown_set_text:
            text += cooldown_set_text

        if special_effect_text:
            text += special_effect_text

        if enemy_effect_text:
            text += enemy_effect_text

        if resource_damage_text:
            text += resource_damage_text

        if cooldown_start_text or player_effects_text or resource_start_text or resource_attack_text or cooldown_set_text or special_effect_text or enemy_effect_text or resource_damage_text:
            text += "\n"

        text += f"{skill['name']}\n"

        if skill.get("no_damage"):
            text += "✨ Навичка застосована.\n"
        else:
            if is_player_crit:
                text += f"💥 КРИТ! {character_name} завдав {mob['name']} {dmg} шкоди"
            else:
                text += f"✨ {character_name} завдав {mob['name']} {dmg} шкоди"

            if weapon_damage > 0:
                text += f" (зброя: {weapon_damage})"

            text += "\n"

        if stun_text:
            text += stun_text

        text += enemy_action_text

        class_resource_text = get_class_resource_line(mob)

        text += (
            f"❤️ {character_name}: {player_hp}/{player_max_hp}\n"
            f"{hp_bar(player_hp, player_max_hp)}\n"
            f"{class_resource_text}\n"
            f"👹 {mob['name']}: {mob['hp']}/{mob['max_hp']}\n"
            f"{hp_bar(mob['hp'], mob['max_hp'])}"
        )

        text = append_effects_to_combat_text(text, mob)

        if mob.get("potion_cooldown", 0) > 0:
            text += f"\n\n🔴 Повний шлунок: {mob['potion_cooldown']} ход."


        bot.send_message(
            call.message.chat.id,
            text,
            reply_markup=build_combat_inline_kb(user_id, mob)
        )

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
                reply_markup=build_combat_inline_kb(user_id, mob)
            )
            return

        kb = build_combat_potion_kb(user_id)

        if not kb:
    
            bot.send_message(
                message.chat.id,
                "❌ У тебе немає зілля здоров’я",
                reply_markup=build_combat_inline_kb(user_id, mob)
            )
            return

        bot.send_message(
            message.chat.id,
            "🧪 Обери зілля, яке хочеш випити:",
            reply_markup=kb
        )

    @bot.callback_query_handler(func=lambda call: call.data == "combat_back")
    def combat_back(call):
        user_id = call.from_user.id
        
        if not hasattr(bot, "user_data") or user_id not in bot.user_data:
            bot.answer_callback_query(call.id)
            bot.send_message(
                call.message.chat.id,
                "❗ Бій вже завершено",
                reply_markup=main_kb()
            )
            return
            
        mob = bot.user_data[user_id]

        
        bot.answer_callback_query(call.id)

        bot.send_message(
            call.message.chat.id,
            "⚔️ Повернення до бою",
            reply_markup=build_combat_inline_kb(user_id, mob)
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
        character_name = get_character_name(user_id) or "Без імені"

        cooldown = mob.get("potion_cooldown", 0)

        if cooldown > 0:
            bot.answer_callback_query(call.id)
    

            bot.send_message(
                call.message.chat.id,
                f"🔴 Повний шлунок: зілля можна буде випити через {cooldown} ход.",
                reply_markup=build_combat_inline_kb(user_id, mob)
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
                reply_markup=build_combat_inline_kb(user_id, mob)
            )
            return

        bot.answer_callback_query(call.id)

        mob["potion_cooldown"] = cooldown_turns

        player_hp = potion_result["new_hp"]
        player_max_hp = potion_result["max_hp"]

        # Оновлюємо здоров'я в mob
        mob["player_hp"] = player_hp
        mob["player_max_hp"] = player_max_hp

        class_resource_text = get_class_resource_line(mob)

        text = (
            f"🧪 ЗІЛЛЯ\n\n"
            f"{potion_result['message']}\n\n"
            f"✅ Хід не витрачено — {mob['name']} не атакує після використання зілля.\n"
            f"🔴 Повний шлунок: {cooldown_turns} ход.\n\n"
            f"❤️ {character_name}: {player_hp}/{player_max_hp}\n"
            f"{hp_bar(player_hp, player_max_hp)}\n"
            f"{class_resource_text}\n"
            f"👹 {mob['name']}: {mob['hp']}/{mob['max_hp']}\n"
            f"{hp_bar(mob['hp'], mob['max_hp'])}"
        )

        text = append_effects_to_combat_text(text, mob)


        bot.send_message(
            call.message.chat.id,
            text,
            reply_markup=build_combat_inline_kb(user_id, mob)
        )

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

        # Зберегти поточне здоров'я в базу перед втечею
        if hasattr(bot, "user_data") and user_id in bot.user_data:
            mob = bot.user_data[user_id]
            # Перевіряємо, чи маємо ми player_hp в mob, але якщо ні, то нічого не робимо
            if "player_hp" in mob:
                set_current_hp(user_id, mob["player_hp"])

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
        user_id = call.from_user.id
        
        if not hasattr(bot, "user_data") or user_id not in bot.user_data:
            bot.answer_callback_query(call.id)
            bot.send_message(
                call.message.chat.id,
                "❗ Бій вже завершено",
                reply_markup=main_kb()
            )
            return
            
        mob = bot.user_data[user_id]

        
        bot.answer_callback_query(call.id)

        bot.send_message(
            call.message.chat.id,
            "⚔️ Ти залишився в бою",
            reply_markup=build_combat_inline_kb(user_id, mob)
        )
