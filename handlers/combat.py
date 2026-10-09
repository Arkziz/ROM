
# ROM 17.20.1.1 CRITICAL PRODUCTION LOGGING PRINT CONTRACT RECOVERY
from systems.production_logging import get_production_logger, production_log_print as PRODUCTION_LOG_PRINT
from data.priest_healing_policy import (
    PRIEST_HEALING_DURATION_TURNS,
    PRIEST_HEALING_EFFECT_KEY,
    PRIEST_HEALING_TOTAL_HEALS,
    build_priest_healing_effect,
    calculate_priest_heal_amount,
)
PRODUCTION_LOGGER=get_production_logger('handlers.combat')
# ROM 17.18.2.2 BOW CROSSBOW DAMAGE DIFFERENTIATION
# ROM 17.16.1 PVE SKILL BUTTON STATES
# ROM 17.15.1 PERSISTENT MANA REGENERATION
# ROM 17.14.1.1 SEPARATE LEVEL REWARD MESSAGE AND DEV EXP SETTER
# ROM 17.14.1 LEVEL UP REWARDS
# ROM 17.10.1 ITEM QUANTITY DISPLAY FORMAT
from telebot import types

from systems.boss_system import (
    build_boss_damage_request,
    finalize_boss_turn,
    get_effective_boss_defenses,
    prepare_boss_turn,
    process_boss_player_dots,
    render_boss_action_text,
)


# ============================================================================
# Stage 15.5.0: boss bridge for every enemy action path
# ============================================================================
def _calculate_enemy_turn_15_5_0(
    mob, player_pdef, player_mdef, player_dex, sta, level
):
    """Preserve normal/elite behavior; route bosses through Stage 15 bridge."""
    if not mob.get("is_boss"):
        result = calculate_mob_attack(
            mob_attack=mob["attack"], player_pdef=player_pdef,
            player_mdef=player_mdef, player_dex=player_dex,
            mob_dex=mob["dex"], sta=sta, level=level,
            attack_type=mob["attack_type"]
        )
        result["boss_turn"] = None
        return result
    turn = prepare_boss_turn(mob)
    plan = turn["action_plan"]
    request = build_boss_damage_request(plan)
    if request is None:
        return {
            "damage": 0, "is_crit": False, "is_dodge": False,
            "dodge_chance": 0.0, "boss_turn": turn,
        }
    result = calculate_mob_attack(
        mob_attack=request["mob_attack"], player_pdef=player_pdef,
        player_mdef=player_mdef, player_dex=player_dex,
        mob_dex=mob["dex"], sta=sta, level=level,
        attack_type=request["attack_type"]
    )
    result["boss_turn"] = turn
    return result


def _finalize_enemy_turn_15_5_0(mob, attack_result, actual_damage):
    turn = attack_result.get("boss_turn")
    if not turn:
        return ""
    finalize_boss_turn(mob, turn["action_plan"], actual_damage=actual_damage)
    return render_boss_action_text(
        mob, turn, actual_damage=actual_damage,
        dodged=bool(attack_result.get("is_dodge"))
    ) + "\n"


def _apply_boss_dot_at_player_turn_15_5_0(mob):
    if not mob.get("is_boss"):
        return ""
    result = process_boss_player_dots(mob, int(mob.get("player_hp", 0) or 0))
    mob["player_hp"] = result["current_hp"]
    if result["damage"] <= 0:
        return ""
    return f"🩸 Кровотеча: отримано {result['damage']} шкоди.\n"



# ==============================
# ROM 11.3.1 COMBAT CALLBACK / TELEGRAM RATE-LIMIT GUARD
# ==============================
import re as _combat_rate_re_11_3_1
import time as _combat_rate_time_11_3_1

_COMBAT_CALLBACK_DEBOUNCE_SECONDS_11_3_1 = 0.90
_COMBAT_CALLBACK_LAST_ACTION_11_3_1 = {}
_COMBAT_TELEGRAM_BLOCKED_UNTIL_11_3_1 = {}
_COMBAT_SEND_WRAPPER_INSTALLED_11_3_1 = set()


def _combat_extract_retry_after_11_3_1(error):
    """Return Telegram retry_after seconds from an API exception, or None."""
    text = str(error or "")
    if "too many requests" not in text.lower():
        return None
    match = _combat_rate_re_11_3_1.search(
        r"retry after\s+(\d+)", text, _combat_rate_re_11_3_1.IGNORECASE
    )
    return int(match.group(1)) if match else 1


def _install_combat_safe_send_11_3_1(bot):
    """Contain Telegram 429 without retrying stale combat presentation."""
    marker = id(bot)
    if marker in _COMBAT_SEND_WRAPPER_INSTALLED_11_3_1:
        return
    original_send_message = bot.send_message

    def safe_send_message(chat_id, *args, **kwargs):
        now = _combat_rate_time_11_3_1.monotonic()
        blocked_until = float(_COMBAT_TELEGRAM_BLOCKED_UNTIL_11_3_1.get(chat_id, 0.0))
        if now < blocked_until:
            # Do not queue or replay stale combat screens. The next valid user
            # action will render the current authoritative combat state.
            return None
        try:
            return original_send_message(chat_id, *args, **kwargs)
        except Exception as error:
            retry_after = _combat_extract_retry_after_11_3_1(error)
            if retry_after is None:
                raise
            _COMBAT_TELEGRAM_BLOCKED_UNTIL_11_3_1[chat_id] = (
                _combat_rate_time_11_3_1.monotonic() + retry_after
            )
            PRODUCTION_LOG_PRINT(PRODUCTION_LOGGER, 'warning', f"⚠️ Telegram 429 for chat {chat_id}: presentation suppressed "
                f"for {retry_after}s; combat state will not be replayed.")
            return None

    bot.send_message = safe_send_message
    _COMBAT_SEND_WRAPPER_INSTALLED_11_3_1.add(marker)


def _combat_callback_allowed_11_3_1(bot, call, action_key):
    """Reject rapid duplicate callbacks before any combat-state mutation."""
    user_id = int(call.from_user.id)
    chat_id = int(call.message.chat.id)
    now = _combat_rate_time_11_3_1.monotonic()

    blocked_until = float(_COMBAT_TELEGRAM_BLOCKED_UNTIL_11_3_1.get(chat_id, 0.0))
    if now < blocked_until:
        remaining = max(1, int(blocked_until - now + 0.999))
        try:
            bot.answer_callback_query(
                call.id,
                f"⏳ Telegram просить зачекати {remaining} с.",
                show_alert=False,
            )
        except Exception:
            pass
        return False

    previous = float(_COMBAT_CALLBACK_LAST_ACTION_11_3_1.get(user_id, 0.0))
    if now - previous < _COMBAT_CALLBACK_DEBOUNCE_SECONDS_11_3_1:
        try:
            bot.answer_callback_query(
                call.id,
                "⏳ Попередня бойова дія ще обробляється.",
                show_alert=False,
            )
        except Exception:
            pass
        return False

    _COMBAT_CALLBACK_LAST_ACTION_11_3_1[user_id] = now
    try:
        bot.answer_callback_query(call.id)
    except Exception as error:
        retry_after = _combat_extract_retry_after_11_3_1(error)
        if retry_after is not None:
            _COMBAT_TELEGRAM_BLOCKED_UNTIL_11_3_1[chat_id] = now + retry_after
            return False
        # Callback acknowledgement is presentation-only. A non-429 failure
        # must not duplicate the mutation by retrying the action.
    return True


def _combat_message_allowed_11_3_1(message):
    """Prevent Hunt reply-button spam while Telegram has imposed a cooldown."""
    chat_id = int(message.chat.id)
    return _combat_rate_time_11_3_1.monotonic() >= float(
        _COMBAT_TELEGRAM_BLOCKED_UNTIL_11_3_1.get(chat_id, 0.0)
    )

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

from systems.character_system import (
    apply_post_combat_mp_floor_17_15_1,
    begin_mp_combat_pause_17_15_1,
)

from keyboards import main_kb, fight_kb, build_combat_inline_kb, combat_placeholder_kb
from utils import hp_bar

from systems.combat_system import (
    generate_mob,
    calculate_player_attack,
    calculate_mob_attack
)

from systems.reward_system import process_victory_reward
from systems.story_quest_combat_progress_system import process_region_kill_story_progress
from systems.story_quest_item_drop_system import process_story_quest_item_drop
from systems.story_quest_overlevel_system import process_overlevel_story_quest_skip
from systems.story_quest_boss_completion_system import process_rng_boss_story_completion
from systems.pve_auto_escape_system import begin_pve_encounter, get_active_pve_encounter, claim_pve_terminal, STALE_COMBAT_TEXT
from systems.boss_system import build_location_boss
from systems.story_quest_boss_call_system import BOSS_CALL_BUTTON, get_active_story_boss_call
from systems.potion_system import use_potion_from_inventory
from systems.combat_system import roll_player_normal_attack_hit, roll_player_pve_skill_hit


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
        begin_mp_combat_pause_17_15_1(user_id)
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
    """Add or refresh one canonical enemy effect without damage stacking."""
    init_combat_effects(mob)

    incoming = dict(effect)
    incoming["key"] = key
    existing = mob["enemy_effects"].get(key)

    if existing is None:
        incoming["fresh"] = True
        mob["enemy_effects"][key] = incoming
        return "applied"

    old_turns = max(0, int(existing.get("turns", 0) or 0))
    new_turns = max(0, int(incoming.get("turns", 0) or 0))
    old_power = max(
        abs(float(existing.get("damage", 0) or 0)),
        abs(float(existing.get("heal", 0) or 0)),
        max((abs(float(value or 0)) for value in existing.get("modifiers", {}).values()), default=0.0),
    )
    new_power = max(
        abs(float(incoming.get("damage", 0) or 0)),
        abs(float(incoming.get("heal", 0) or 0)),
        max((abs(float(value or 0)) for value in incoming.get("modifiers", {}).values()), default=0.0),
    )

    if new_power < old_power:
        return "kept_stronger"

    if new_power == old_power:
        if new_turns > old_turns:
            existing["turns"] = new_turns
            return "refreshed"
        return "unchanged"

    preserved_turns = max(old_turns, new_turns)
    incoming["turns"] = preserved_turns
    if existing.get("fresh", False):
        incoming["fresh"] = True
    else:
        incoming.pop("fresh", None)
    mob["enemy_effects"][key] = incoming
    return "replaced_stronger"



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

    if mob.get("is_boss"):
        boss_pdef, boss_mdef = get_effective_boss_defenses(mob)
        effective_def = float(boss_mdef if attack_type == "magical" else boss_pdef)

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

        # Бій почався: пасивна регенерація HP не має накопичуватись під час бою.
        # set_current_hp() також оновлює last_hp_regen_update.
        set_current_hp(user_id, current_hp)

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
    """Resolve existing enemy effects; newly applied effects start next turn."""
    init_combat_effects(mob)

    if not mob["enemy_effects"]:
        return {"text": "", "damage": 0}

    text = ""
    total_damage = 0
    effects_to_remove = []

    for key, effect in list(mob["enemy_effects"].items()):
        if effect.pop("fresh", False):
            continue

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

    return {"text": text, "damage": total_damage}



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
    """Store cooldown so N remains blocked for exactly N subsequent actions."""
    init_skill_cooldowns(mob)

    cooldown_turns = int(cooldown_turns or 0)
    if cooldown_turns <= 0:
        mob["skill_cooldowns"].pop(skill_key, None)
        return ""

    mob["skill_cooldowns"][skill_key] = cooldown_turns + 1
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
            "description": "Витрачає 30 MP. Одразу відновлює 10% максимального здоров’я, а потім лікує ще 2 рази на початку наступних ходів. Разом: 3 лікування. Перезарядка: 4 ходи.",
            "cost_type": "mana",
            "cost": 30,
            "cooldown": 4,
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
    from systems.pve_skill_action_state import get_pve_skill_action_state

    skills = get_player_class_skills(user_id)
    class_resource_text = get_class_resource_line(mob)
    if not skills:
        return "✨ Навички\n\n❌ Для твого класу ще немає доступних навичок.", None

    text = "✨ Навички\n\n" + f"{class_resource_text}\n"
    kb = types.InlineKeyboardMarkup()
    for skill in skills:
        state = get_pve_skill_action_state(user_id, mob, skill)
        text += f"{skill['name']}\n{skill['description']}\n"
        text += "✅ Навичка доступна.\n\n" if state["available"] else f"{state['message']}\n\n"
        kb.add(types.InlineKeyboardButton(
            text=state["label"], callback_data=state["callback_data"]
        ))

    enemy_effects_text = get_enemy_effects_text(mob)
    player_effects_text = get_player_effects_text(mob)
    if enemy_effects_text or player_effects_text:
        text += "\n" + enemy_effects_text + player_effects_text
    kb.add(types.InlineKeyboardButton(text="⬅️ Назад до бою", callback_data="combat_back"))
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

        heal_per_turn = calculate_priest_heal_amount(max_hp)

        # Activation is the first of three heals; the effect owns two later ticks.
        current_hp = int(mob.get("player_hp", 0))
        new_hp = min(max_hp, current_hp + heal_per_turn)
        immediate_heal = max(0, new_hp - current_hp)
        mob["player_hp"] = new_hp

        add_player_effect(
            mob,
            PRIEST_HEALING_EFFECT_KEY,
            build_priest_healing_effect(heal_per_turn)
        )

        text += (
            f"🌿 Благословення зцілення: +{immediate_heal} HP одразу, "
            f"потім ще {PRIEST_HEALING_DURATION_TURNS} лікування "
            f"по +{heal_per_turn} HP. "
            f"Разом: {PRIEST_HEALING_TOTAL_HEALS} лікування.\n"
        )

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
            f"\n🔵 Мана після бою: "
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

def format_combat_turns_uk(value):
    """Return a Ukrainian turn count with correct plural form."""
    try:
        value = max(0, int(value))
    except Exception:
        value = 0

    mod_10 = value % 10
    mod_100 = value % 100

    if mod_10 == 1 and mod_100 != 11:
        word = "хід"
    elif mod_10 in (2, 3, 4) and mod_100 not in (12, 13, 14):
        word = "ходи"
    else:
        word = "ходів"

    return f"{value} {word}"

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

    if type_ in ("potion_hp_medium", "potion_mp_medium"):
        return 5

    if type_ in ("potion_hp", "potion_mp"):
        return 3

    return 3



def build_combat_potion_kb(user_id, cooldown=0):
    items = get_inventory_detailed(user_id)
    profile_summary = get_character_profile_summary(user_id)
    uses_mana = profile_summary.get("resource_type") == "mana"

    try:
        cooldown = max(0, int(cooldown or 0))
    except Exception:
        cooldown = 0

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

        is_hp_potion = type_ in ("potion_hp", "potion_hp_medium")
        is_mp_potion = type_ in ("potion_mp", "potion_mp_medium")

        if category != "potion" or not (is_hp_potion or (uses_mana and is_mp_potion)):
            continue

        found = True

        if cooldown > 0:
            button_text = (
                f"⏳ {name} ×{quantity}, "
                f"доступно через {format_combat_turns_uk(cooldown)}"
            )
        else:
            potion_cooldown = (
                5 if type_ in ("potion_hp_medium", "potion_mp_medium") else 3
            )
            button_text = (
                f"{name} ×{quantity} — "
                f"cooldown {format_combat_turns_uk(potion_cooldown)}"
            )

        kb.add(types.InlineKeyboardButton(
            text=button_text,
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
        "❤️ Після поразки у тебе залишилось 1 HP\n"
        "🧱 Одягнене спорядження втратило 5 міцності\n"
    )

    if durability_damage:
        text += "\n📉 Стан спорядження:\n"

        for item in durability_damage:
            broken_text = " ⚠️ ЗЛАМАНО" if item["broken"] else ""
            text += f"• {item['name']}: {item['old']} → {item['new']}/100{broken_text}\n"

    return text


# ROM 17.3.0.1 DEATH DURABILITY CALL SIGNATURE RECOVERY
def build_lethal_combat_log(turn_context, player_hp, player_max_hp, durability_damage):
    """Preserve the terminal turn narrative and live enemy HP before death cleanup."""
    # ROM 17.3.0 PVE DEFEAT ENEMY HP
    context = dict(turn_context or {})
    parts = []

    for key in (
        "cooldown_start_text",
        "player_effects_text",
        "resource_start_text",
        "resource_attack_text",
        "cooldown_set_text",
        "special_effect_text",
        "enemy_effect_text",
    ):
        value = context.get(key)
        if value:
            parts.append(str(value).strip())

    skill = context.get("skill")
    skill_hit = context.get("skill_hit")
    if isinstance(skill, dict) and skill.get("name"):
        if skill_hit is False:
            parts.append("💨 ПРОМАХ! Навичка «{}» не влучила в ціль.".format(skill["name"]))
        elif skill.get("no_damage"):
            parts.append(f"✨ {skill['name']}\n✨ Навичка застосована.")
        elif context.get("dmg") is not None:
            parts.append(f"✨ {skill['name']}\n✨ Ти завдав {max(0, int(context.get('dmg') or 0))} шкоди.")
    elif context.get("dmg") is not None:
        parts.append(f"⚔️ Ти завдав {max(0, int(context.get('dmg') or 0))} шкоди.")

    enemy_action_text = context.get("enemy_action_text")
    if enemy_action_text:
        parts.append(str(enemy_action_text).strip())

    unique_parts = []
    for part in parts:
        if part and part not in unique_parts:
            unique_parts.append(part)

    death_text = build_death_text(durability_damage)
    death_heading, _, death_tail = death_text.partition("\n")
    text = f"{death_heading}\n\n💥 ОСТАННІЙ ХІД\n\n"
    if unique_parts:
        text += "\n".join(unique_parts) + "\n\n"

    # ROM 17.3.0.2 REMOVE REDUNDANT PLAYER HP BEFORE DEFEAT
    mob = context.get("mob")
    if isinstance(mob, dict):
        enemy_name = str(mob.get("name") or "Противник")
        try:
            enemy_current_hp = max(0, int(round(float(mob.get("hp", 0) or 0))))
        except Exception:
            enemy_current_hp = 0
        try:
            enemy_max_hp = max(1, int(round(float(mob.get("max_hp", enemy_current_hp) or enemy_current_hp or 1))))
        except Exception:
            enemy_max_hp = max(1, enemy_current_hp)
        enemy_current_hp = min(enemy_current_hp, enemy_max_hp)
        text += f"👹 Противник: {enemy_name}\n"
        text += f"❤️ Здоров’я противника: {enemy_current_hp}/{enemy_max_hp}\n\n"

    if death_tail:
        text += death_tail.lstrip("\n")
    return text



# Stage 18.29.4n: production-shaped event drop result contract
def _event_drop_victory_messages(event_drop_results):
    messages = []
    for entry in event_drop_results or ():
        if not isinstance(entry, dict):
            continue
        payload = entry.get("payload") or {}
        award_result = entry.get("result") or {}
        if not isinstance(payload, dict) or not isinstance(award_result, dict):
            continue
        if not award_result.get("success"):
            continue
        added = int(award_result.get("added", 0) or 0)
        item_name = str(award_result.get("name") or "").strip()
        if added <= 0 or not item_name:
            continue
        messages.append(f"{item_name} ×{added}")
    return messages


def build_victory_text(user_id, lvl, mob, reward, wear_result, contract_result, daily_result, prefix_text=""):
    exp_result = reward["exp_result"]

    victory_title = ""

    if mob.get("is_boss"):
        victory_title = "🏆👑 ВИ ПЕРЕМОГЛИ БОСА!"
    elif mob.get("is_elite"):
        victory_title = "🏆 ВИ ПЕРЕМОГЛИ ЕЛІТНОГО ВОРОГА!"

    final_round_parts = []
    last_damage = max(0, int(mob.get("_last_player_damage", 0) or 0))
    defeated_by_effect = "повалений ефектами" in str(prefix_text or "").lower()

    if last_damage > 0 and not defeated_by_effect:
        character_name = get_character_name(user_id) or "Персонаж"
        crit_label = "💥 КРИТ! " if mob.get("_last_player_crit") else "⚔️ "
        final_round_parts.append(
            f"{crit_label}{character_name} завдав {mob['name']} {last_damage} шкоди."
        )
    elif defeated_by_effect:
        final_round_parts.append("☠️ Ворог отримав смертельну шкоду від ефекту.")

    player_hp = max(1, int(mob.get("player_hp", get_current_hp_raw(user_id)) or 1))
    player_max_hp = max(1, int(mob.get("player_max_hp", get_max_hp(user_id)) or 1))
    player_hp = min(player_hp, player_max_hp)
    final_round_parts.append(
        f"❤️ Здоров’я після фінального ходу: {player_hp}/{player_max_hp}\n"
        f"{hp_bar(player_hp, player_max_hp)}"
    )

    text = "🏆 ВИ ПЕРЕМОГЛИ!\n\n💥 ФІНАЛЬНИЙ ХІД\n\n"
    text += "\n".join(final_round_parts)
    text += f"\n\n{victory_title}\n\n"

    text += (
        f"{mob['name']} повалений на землю."
        f"📈 Нагорода:\n"
    )

    premium_bonus = int(reward.get("premium_exp_bonus", 0) or 0)
    if bool(reward.get("exp_bonus_active")) and premium_bonus > 0:
        text += (
            f"✨ Досвід: +{reward['exp']} EXP\n"
            f"   ├ Базовий: {int(reward.get('base_exp', reward['exp']))} EXP\n"
            f"   ├ Premium +25%: +{premium_bonus} EXP"
        )
        if exp_result:
            text += f"\n   └ Прогрес: {exp_result['exp']}/{exp_result['exp_to_next']}"
    else:
        text += f"✨ Досвід: +{reward['exp']} EXP"
        if exp_result:
            text += f" ({exp_result['exp']}/{exp_result['exp_to_next']})"

        # Stage 17.14.1.1 sends level-up information separately.

    text += f"\n💰 Золото: +{reward['gold']}\n"

    event_drop_messages = _event_drop_victory_messages(
        reward.get("event_drop_results")
    )

    if reward["loot_messages"] or event_drop_messages:
        if reward["loot_messages"]:
            text += "\n🎒 Знайдений лут:\n"
            for loot in reward["loot_messages"]:
                text += f"• {loot}\n"
        if event_drop_messages:
            text += "\n🎉 Івентна нагорода:\n"
            for event_message in event_drop_messages:
                text += f"• {event_message}\n"
    else:
        text += "\n🎒 Лут не знайдено.\n"

    if wear_result and wear_result.get("triggered"):
        text += f"\n{wear_result['message']}\n"

    if contract_result and contract_result.get("message"):
        text += f"\n{contract_result['message']}\n"

    if daily_result and daily_result.get("message"):
        text += f"\n{daily_result['message']}\n"

    mp_restore_result = apply_post_combat_mp_floor_17_15_1(user_id)
    text = append_mp_restore_text(text, mp_restore_result)

    text += f"\n🎒 Сумка: {reward['used_slots']}/{reward['capacity']} слотів"

    # ROM Stage 18.xx.3b: normalize rendered victory block boundaries.
    while "\n\n\n" in text:
        text = text.replace("\n\n\n", "\n\n")
    text = text.replace("повалений на землю.📈 Нагорода:", "повалений на землю.\n\n📈 Нагорода:")
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

    # A HoT tick applied at the start of the winning turn is legitimate healing.
    # Keep the already-clamped mob["player_hp"] value instead of subtracting it again.
    mob["_turn_start_hot_heal_applied"] = 0

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
    encounter_id = (mob or {}).get("pve_encounter_id")
    if encounter_id and not claim_pve_terminal(user_id, 'victory', encounter_id):
        bot.send_message(chat_id, STALE_COMBAT_TEXT, reply_markup=main_kb())
        return
    # ROM_STAGE_18_29_3F_EVENT_VICTORY_STATISTICS
    event_key = str((mob or {}).get("event_key") or "").strip()
    event_mob_key = str((mob or {}).get("event_mob_key") or "").strip()
    if encounter_id and event_key and event_mob_key:
        from db_modules.connection import conn as event_statistics_conn
        from systems.event_statistics_system import record_event_mob_victory
        record_event_mob_victory(
            event_statistics_conn,
            event_key=event_key,
            user_id=user_id,
            mob_key=event_mob_key,
            terminal_event_id=encounter_id,
        )
        event_statistics_conn.commit()
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

    if mob.get("is_boss"):
        encounter_id = mob.get("pve_encounter_id")
        if encounter_id:
            from systems.world_chronicle_system import (
                get_character_name_snapshot,
                record_world_chronicle_event,
            )
            character_name = get_character_name_snapshot(user_id)
            if character_name:
                record_world_chronicle_event(
                    "location_boss_defeated",
                    user_id,
                    character_name,
                    f"location_boss_defeated:{encounter_id}",
                    subject_key=str(mob.get("boss_key") or ""),
                    subject_name_snapshot=str(mob.get("name") or mob.get("base_name") or "Бос"),
                    location_id=str(mob.get("location_id") or ""),
                )

    # The RNG encounter has already passed the canonical terminal claim. A
    # matching ACTIVE BOSS quest now completes and rewards exactly once.
    story_boss_result = process_rng_boss_story_completion(
        user_id=user_id,
        mob=mob,
        location_id=get_current_location(user_id),
        encounter_id=encounter_id,
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

    # Terminal victory was already claimed above, so this hook runs once per
    # encounter and cannot double-count repeated Telegram terminal updates.
    story_region_result = process_region_kill_story_progress(
        user_id=user_id,
        location_id=get_current_location(user_id),
    )

    # Dedicated quest items are rolled after the same terminal claim and never
    # enter ordinary inventory or consume bag capacity.
    story_item_result = process_story_quest_item_drop(
        user_id=user_id,
        location_id=get_current_location(user_id),
    )

    # Combat EXP was awarded before story progress. Evaluate the resulting level
    # only after this terminal victory's progress/drop hooks have run.
    exp_result = reward.get("exp_result") or {}
    resulting_level = int(exp_result.get("level") or get_player_level(user_id))
    story_skip_result = process_overlevel_story_quest_skip(
        user_id=user_id,
        current_level=resulting_level,
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

    # Quest-item persistence is owned by the drop system. Telegram output is a
    # separate consumer and is emitted exactly once only for an actual grant.
    if int(story_item_result.get("granted", 0) or 0) > 0:
        story_drop_message = str(story_item_result.get("drop_message") or "").strip()
        if story_drop_message:
            bot.send_message(chat_id, story_drop_message)

    exp_result = reward.get("exp_result") or {}
    reward_message = str(exp_result.get("level_up_reward_message") or "").strip()
    level_ups = int(exp_result.get("level_ups", 0) or 0)
    if level_ups > 0 and not reward_message:
        # Some levels have no special milestone item message. Always announce
        # the canonical level transition and permanent attribute-point reward.
        old_level = int(exp_result.get("old_level", resulting_level - level_ups) or 0)
        new_level = int(exp_result.get("level", resulting_level) or resulting_level)
        points = int(exp_result.get("attribute_points_awarded", level_ups * 5) or 0)
        reward_message = (
            "🎉 Рівень підвищено!\n\n"
            f"🏆 Рівень: {old_level} → {new_level}\n"
            f"🌟 Вільні очки характеристик: +{points}"
        )
    if reward_message:
        bot.send_message(chat_id, reward_message)

    # Emit one campaign-level summary only after the level-up notification.
    # The lifecycle mutation is already committed and idempotent.
    story_skip_message = str((story_skip_result or {}).get("message") or "").strip()
    if story_skip_message:
        bot.send_message(chat_id, story_skip_message)


# ==============================
# REGISTER HANDLERS
# ==============================

def register_combat_handlers(bot):

    @bot.message_handler(func=lambda m: getattr(m, "text", None) == BOSS_CALL_BUTTON)
    def call_active_story_boss(message):
        """Start the canonical location boss only while its story quest is ACTIVE.

        Eligibility is revalidated on every press. After a successful kill,
        Stage 19.19 immediately marks the quest COMPLETED, so stale buttons and
        deliberate delayed turn-in cannot be used to farm guaranteed summons.
        Defeat or escape leaves the quest ACTIVE and permits another attempt.
        """
        user_id = int(message.from_user.id)
        location_id = get_current_location(user_id)
        call = get_active_story_boss_call(user_id=user_id, current_location_id=location_id)
        if not call.get("allowed"):
            bot.send_message(message.chat.id, "⚠️ Виклик сюжетного боса зараз недоступний.", reply_markup=main_kb())
            return
        if get_active_pve_encounter(user_id) is not None:
            bot.send_message(message.chat.id, "⚔️ Спочатку заверши поточний бій.", reply_markup=combat_placeholder_kb())
            return
        stats=get_player_stats(user_id)
        if not stats:
            bot.send_message(message.chat.id,"❗ Спочатку натисни /start",reply_markup=main_kb());return
        lvl=int(stats[-1]);current_hp=get_current_hp_raw(user_id);max_hp=get_max_hp(user_id)
        if max_hp<=0 or (current_hp/max_hp)*100<=25:
            bot.send_message(message.chat.id,"😴 Здоров’я занадто низьке для виклику боса.",reply_markup=main_kb());return
        mob=build_location_boss(location_id,lvl)
        if str(mob.get("boss_key")) != str(call.get("boss_key")):
            bot.send_message(message.chat.id,"⚠️ Ціль сюжетного квесту не відповідає босу цієї локації.",reply_markup=main_kb());return
        mob.update({"potion_cooldown":0,"stunned_turns":0,"skill_cooldowns":{},"enemy_effects":{},"player_effects":{},"last_skill_spent_rage":0,"last_skill_spent_combo":0,"player_hp":current_hp,"player_max_hp":max_hp,"story_boss_call":True})
        init_class_combat_resource(user_id,mob);init_combat_effects(mob)
        encounter=begin_pve_encounter(user_id,message.chat.id,mob)
        mob["pve_encounter_id"]=encounter["encounter_id"];mob["pve_started_at"]=encounter["started_at"];mob["pve_deadline_at"]=encounter["deadline_at"]
        bot.user_data=getattr(bot,"user_data",{});bot.user_data[user_id]=mob
        # Match the canonical hunt startup: replace the persistent location
        # keyboard with the combat placeholder before showing inline actions.
        # This prevents Hunt, Map, Profile and Look Around from remaining usable
        # while the guaranteed story-boss encounter is active.
        bot.send_message(
            message.chat.id,
            "⚔️ Бій розпочався!",
            reply_markup=combat_placeholder_kb(),
        )
        bot.send_message(
            message.chat.id,
            f"👑 Голова Найманців викликає {mob['name']}!\n\n"
            "Після перемоги потрібно повернутися до Голови Найманців із доповіддю, "
            "а повторний гарантований виклик стане недоступним.",
            reply_markup=build_combat_inline_kb(user_id,mob),
        )

    @bot.message_handler(func=lambda m: m.text == "🔎 Полювання")
    def hunt(message):
        user_id = message.from_user.id
        from systems.travel_system import is_user_travelling
        if is_user_travelling(user_id):
            from keyboards import map_kb
            bot.send_message(
                message.chat.id,
                (
                    "🚶 Полювання недоступне під час подорожі.\n\n"
                    "Відкрий мапу, щоб оновити час у дорозі "
                    "або скасувати маршрут."
                ),
                reply_markup=map_kb(),
            )
            return
        if not _combat_message_allowed_11_3_1(message):
            return

        current_location = get_current_location(user_id)
        if current_location == "city":
            from keyboards import city_kb
            bot.send_message(
                message.chat.id,
                "🏙️ У Місті не можна полювати. Відкрий 🗺️ Мапу та вирушай у доступну локацію.",
                reply_markup=city_kb(),
            )
            return

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
        encounter = begin_pve_encounter(user_id, message.chat.id, mob)
        mob["pve_encounter_id"] = encounter["encounter_id"]
        mob["pve_started_at"] = encounter["started_at"]
        mob["pve_deadline_at"] = encounter["deadline_at"]
        bot.user_data[user_id] = mob

        attack_profile = get_player_attack_profile(user_id)

        player_pdef, player_mdef = get_effective_player_defenses(user_id, mob)

        attack_type_text = "Фізична" if mob["attack_type"] == "physical" else "Магічна"
        player_attack_type_text = "Фізична" if attack_profile["attack_type"] == "physical" else "Магічна"

        elite_text = ""

        if mob.get("is_boss"):
            elite_text = (
                "👑 БОС ЛОКАЦІЇ!\n"
                "⚠️ Надзвичайно небезпечний ворог із унікальними навичками та фазою Люті.\n\n"
            )
        elif mob.get("is_elite"):
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
        player_effects_text += _apply_boss_dot_at_player_turn_15_5_0(mob)
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

        normal_attack_uses_hit_roll = attack_profile["attack_type"] == "physical"

        if normal_attack_uses_hit_roll:
            player_hit_result = roll_player_normal_attack_hit(
                player_dex=dex_,
                mob_dex=mob.get("dex", 0),
            )
            player_attack_hit = bool(player_hit_result["hit"])
        else:
            player_hit_result = None
            player_attack_hit = True

        if player_attack_hit:
            player_attack_result = calculate_player_attack(
                player_stat_attack=attack_profile["stat_attack"],
                mob_def=mob_def_for_player_attack,
                dex=dex_,
                wis=wis_,
                level=lvl,
                attack_type=attack_profile["attack_type"],
                weapon_min_damage=attack_profile["weapon_min_damage"],
                weapon_max_damage=attack_profile["weapon_max_damage"],
                weapon_subtype=attack_profile.get("weapon_subtype", ""),
            )
            dmg = player_attack_result["damage"]
            is_player_crit = player_attack_result["is_crit"]
            weapon_damage = player_attack_result.get("weapon_damage", 0)
        else:
            dmg = 0
            is_player_crit = False
            weapon_damage = 0

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
            mob_attack_result = _calculate_enemy_turn_15_5_0(
                mob=mob,
                player_pdef=player_pdef,
                player_mdef=player_mdef,
                player_dex=dex_,
                sta=sta_,
                level=lvl,
            )

            mob_dmg = mob_attack_result["damage"]
            is_mob_crit = mob_attack_result["is_crit"]
            is_dodge = mob_attack_result["is_dodge"]

            shield_text = ""

            if not is_dodge and mob_dmg > 0:
                mob_dmg, shield_text = apply_player_shield_absorb(mob, mob_dmg)
            boss_action_text = _finalize_enemy_turn_15_5_0(
                mob, mob_attack_result, mob_dmg
            )

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

        if mob.get("is_boss") and 'boss_action_text' in locals() and boss_action_text:
            enemy_action_text = boss_action_text

        if player_hp <= 0:
            defeat_claimed = claim_pve_terminal(user_id, "defeat")
            if not defeat_claimed:
                return

            durability_damage = damage_equipped_items_on_death(
                user_id=user_id
            )

            set_current_hp(user_id, 1)
            try:
                from db import reset_hp_regen_timers_now
                reset_hp_regen_timers_now(user_id)
            except Exception:
                pass

            mp_restore_result = apply_post_combat_mp_floor_17_15_1(user_id)

            if user_id in bot.user_data:
                del bot.user_data[user_id]

            text = build_lethal_combat_log(
                turn_context=locals(),
                player_hp=player_hp,
                player_max_hp=player_max_hp,
                durability_damage=durability_damage,
            )
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

        if not player_attack_hit:
            text += f"💨 ПРОМАХ! {character_name} не влучив у {mob['name']}"
        elif is_player_crit:
            text += f"💥 КРИТ! {character_name} завдав {mob['name']} {dmg} шкоди"
        else:
            text += f"🗡️ {character_name} завдав {mob['name']} {dmg} шкоди"


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
        player_effects_text += _apply_boss_dot_at_player_turn_15_5_0(mob)
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
        skill_hit_result = roll_player_pve_skill_hit(
            skill=skill,
            player_dex=dex_,
            player_int=int_,
            mob=mob,
        )
        skill_hit = bool(skill_hit_result["hit"])
        skill_miss_text = "" if skill_hit else "💨 ПРОМАХ! Навичка «{}» не влучила в ціль.\n".format(skill["name"])
        
        if skill.get("no_damage") or not skill_hit:
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
                weapon_max_damage=attack_profile["weapon_max_damage"],
                weapon_subtype=attack_profile.get("weapon_subtype", ""),
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
            mob["_last_player_damage"] = int(dmg or 0)
            mob["_last_player_crit"] = bool(is_player_crit)
            
        resource_attack_text = ""
        if skill_hit and not skill.get("no_damage"):
            if mob.get("player_resource_type") == "rage":
                resource_attack_text += add_rage_for_player_attack(mob)
                
        combo_gain = int(skill.get("combo_gain", 0))
        if skill_hit and combo_gain > 0:
            resource_attack_text += add_rogue_combo_point(mob, combo_gain)
            
        if skill_hit:
            
            resource_attack_text += apply_extra_rage_from_skill(mob, skill)
        
        stun_text = ""
        if not skill.get("no_damage"):
            if skill_hit:
                stun_text = roll_skill_stun(mob, skill)
            
        special_effect_text = ""
        if skill_hit:
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
            mob_attack_result = _calculate_enemy_turn_15_5_0(
                mob=mob,
                player_pdef=player_pdef,
                player_mdef=player_mdef,
                player_dex=dex_,
                sta=sta_,
                level=lvl,
            )
            
            mob_dmg = mob_attack_result["damage"]
            is_mob_crit = mob_attack_result["is_crit"]
            is_dodge = mob_attack_result["is_dodge"]
            
            shield_text = ""
            if not is_dodge and mob_dmg > 0:
                mob_dmg, shield_text = apply_player_shield_absorb(mob, mob_dmg)
            boss_action_text = _finalize_enemy_turn_15_5_0(
                mob, mob_attack_result, mob_dmg
            )
                
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
                
        if mob.get("is_boss") and 'boss_action_text' in locals() and boss_action_text:
            enemy_action_text = boss_action_text

        if player_hp <= 0:
            defeat_claimed = claim_pve_terminal(user_id, "defeat")
            if not defeat_claimed:
                return

            durability_damage = damage_equipped_items_on_death(
                user_id=user_id
            )
            set_current_hp(user_id, 1)
            try:
                from db import reset_hp_regen_timers_now
                reset_hp_regen_timers_now(user_id)
            except Exception:
                pass
            mp_restore_result = apply_post_combat_mp_floor_17_15_1(user_id)
            
            if user_id in bot.user_data:
                del bot.user_data[user_id]
                
            text = build_lethal_combat_log(
                turn_context=locals(),
                player_hp=player_hp,
                player_max_hp=player_max_hp,
                durability_damage=durability_damage,
            )
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
            
        if skill_miss_text:
            
            text += skill_miss_text
        
        if not skill_hit:
            pass
        elif skill.get("no_damage"):
            text += "✨ Навичка застосована.\n"
        else:
            if is_player_crit:
                text += f"💥 КРИТ! {character_name} завдав {mob['name']} {dmg} шкоди"
            else:
                text += f"✨ {character_name} завдав {mob['name']} {dmg} шкоди"
                
                
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
            from systems.pve_skill_action_state import get_pve_skill_action_state

            user_id = call.from_user.id
            if not hasattr(bot, "user_data") or user_id not in bot.user_data:
                bot.answer_callback_query(call.id, "❗ Бій уже завершено")
                return

            mob = bot.user_data[user_id]
            parts = str(call.data or "").split(":", 2)
            skill_key = parts[1] if len(parts) > 1 else ""
            skill = get_player_skill_by_key(user_id, skill_key)
            if not skill:
                bot.answer_callback_query(call.id, "❌ Навичку не знайдено")
                return

            state = get_pve_skill_action_state(user_id, mob, skill)
            if state.get("available"):
                bot.answer_callback_query(call.id, "✅ Навичка вже доступна")
                return

            bot.answer_callback_query(
                call.id,
                state.get("message") or "🔒 Навичка зараз недоступна.",
                show_alert=True,
            )

    # ==========================================
    # НОВІ ОБРОБНИКИ INLINE КНОПОК БОЮ
    # ==========================================
    
    @bot.callback_query_handler(func=lambda call: call.data == "combat_attack")
    def combat_attack_callback(call):
        user_id = call.from_user.id
        if not _combat_callback_allowed_11_3_1(bot, call, "attack"):
            return
        
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
        if not _combat_callback_allowed_11_3_1(bot, call, "potion"):
            return
        
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
        if not _combat_callback_allowed_11_3_1(bot, call, "flee"):
            return
        
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
        if not _combat_callback_allowed_11_3_1(bot, call, "skill"):
            return
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
        player_effects_text += _apply_boss_dot_at_player_turn_15_5_0(mob)
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
        skill_hit_result = roll_player_pve_skill_hit(
            skill=skill,
            player_dex=dex_,
            player_int=int_,
            mob=mob,
        )
        skill_hit = bool(skill_hit_result["hit"])
        skill_miss_text = "" if skill_hit else "💨 ПРОМАХ! Навичка «{}» не влучила в ціль.\n".format(skill["name"])

        if skill.get("no_damage") or not skill_hit:
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
                weapon_max_damage=attack_profile["weapon_max_damage"],
                weapon_subtype=attack_profile.get("weapon_subtype", ""),
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
            mob["_last_player_damage"] = int(dmg or 0)
            mob["_last_player_crit"] = bool(is_player_crit)

        resource_attack_text = ""

        if skill_hit and not skill.get("no_damage"):
            if mob.get("player_resource_type") == "rage":
                resource_attack_text += add_rage_for_player_attack(mob)

        combo_gain = int(skill.get("combo_gain", 0))

        if skill_hit and combo_gain > 0:
            resource_attack_text += add_rogue_combo_point(mob, combo_gain)

        if skill_hit:

            resource_attack_text += apply_extra_rage_from_skill(mob, skill)

        stun_text = ""

        if not skill.get("no_damage"):
            if skill_hit:
                stun_text = roll_skill_stun(mob, skill)

        special_effect_text = ""
        if skill_hit:
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
            mob_attack_result = _calculate_enemy_turn_15_5_0(
                mob=mob,
                player_pdef=player_pdef,
                player_mdef=player_mdef,
                player_dex=dex_,
                sta=sta_,
                level=lvl,
            )

            mob_dmg = mob_attack_result["damage"]
            is_mob_crit = mob_attack_result["is_crit"]
            is_dodge = mob_attack_result["is_dodge"]

            shield_text = ""

            if not is_dodge and mob_dmg > 0:
                mob_dmg, shield_text = apply_player_shield_absorb(mob, mob_dmg)
            boss_action_text = _finalize_enemy_turn_15_5_0(
                mob, mob_attack_result, mob_dmg
            )

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

        if mob.get("is_boss") and 'boss_action_text' in locals() and boss_action_text:
            enemy_action_text = boss_action_text

        if player_hp <= 0:
            defeat_claimed = claim_pve_terminal(user_id, "defeat")
            if not defeat_claimed:
                return

            durability_damage = damage_equipped_items_on_death(
                user_id=user_id
            )

            set_current_hp(user_id, 1)
            try:
                from db import reset_hp_regen_timers_now
                reset_hp_regen_timers_now(user_id)
            except Exception:
                pass

            mp_restore_result = apply_post_combat_mp_floor_17_15_1(user_id)

            if user_id in bot.user_data:
                del bot.user_data[user_id]

            text = build_lethal_combat_log(
                turn_context=locals(),
                player_hp=player_hp,
                player_max_hp=player_max_hp,
                durability_damage=durability_damage,
            )
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

        if skill_miss_text:

            text += skill_miss_text

        if not skill_hit:
            pass
        elif skill.get("no_damage"):
            text += "✨ Навичка застосована.\n"
        else:
            if is_player_crit:
                text += f"💥 КРИТ! {character_name} завдав {mob['name']} {dmg} шкоди"
            else:
                text += f"✨ {character_name} завдав {mob['name']} {dmg} шкоди"


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
            kb = build_combat_potion_kb(user_id, cooldown=cooldown)

            if not kb:
        
                bot.send_message(
                    message.chat.id,
                    "❌ У тебе немає доступних зіль",
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
            if not _combat_callback_allowed_11_3_1(bot, call, "potion_use"):
                return

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
                    f"🔴 Повний шлунок: зілля можна буде випити через {format_combat_turns_uk(cooldown)}.",
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

            resource = potion_result.get("resource", "hp")

            if resource == "mp":
                mob["player_mp"] = potion_result["new_mp"]
                mob["player_max_mp"] = potion_result["max_mp"]
            else:
                player_hp = potion_result["new_hp"]
                player_max_hp = potion_result["max_hp"]
                mob["player_hp"] = player_hp
                mob["player_max_hp"] = player_max_hp

            player_hp = mob.get("player_hp", get_current_hp(user_id))
            player_max_hp = mob.get("player_max_hp", get_max_hp(user_id))
            class_resource_text = get_class_resource_line(mob)

            text = (
                f"🧪 ЗІЛЛЯ\n\n"
                f"{potion_result['message']}\n\n"
                f"✅ Хід не витрачено — {mob['name']} не атакує після використання зілля.\n"
                f"🔴 Повний шлунок: {format_combat_turns_uk(cooldown_turns)}.\n\n"
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
        encounter_id = None
        if hasattr(bot, "user_data") and user_id in bot.user_data:
            encounter_id = bot.user_data[user_id].get("pve_encounter_id")
        if encounter_id and not claim_pve_terminal(user_id, 'manual_escape', encounter_id):
            bot.answer_callback_query(call.id)
            bot.send_message(call.message.chat.id, STALE_COMBAT_TEXT, reply_markup=main_kb())
            return

        # Зберегти поточне здоров'я в базу перед втечею
        if hasattr(bot, "user_data") and user_id in bot.user_data:
            mob = bot.user_data[user_id]
            # Перевіряємо, чи маємо ми player_hp в mob, але якщо ні, то нічого не робимо
            if "player_hp" in mob:
                set_current_hp(user_id, mob["player_hp"])

        mp_restore_result = apply_post_combat_mp_floor_17_15_1(user_id)

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


# ==============================
# ✅ COMBAT SAFE SEND RATE LIMIT V1
# ==============================

# Telegram може повернути 429 Too Many Requests, якщо бот надсилає багато повідомлень
# або якщо старі callback-и обробляються повторно після exception.
# Цей wrapper не дає polling падати через 429: чекає retry_after і повторює send один раз.


def patch_combat_bot_rate_limit_safe_send(bot):
    if getattr(bot, "_rom_safe_send_patched", False):
        return

    original_send_message = bot.send_message
    bot._rom_original_send_message = original_send_message

    def safe_send_message(chat_id, text, *args, **kwargs):
        try:
            return original_send_message(chat_id, text, *args, **kwargs)
        except Exception as error:
            retry_after = None
            error_code = getattr(error, "error_code", None)
            result_json = getattr(error, "result_json", None)

            if isinstance(result_json, dict):
                parameters = result_json.get("parameters", {}) or {}
                retry_after = parameters.get("retry_after")

                if error_code is None:
                    error_code = result_json.get("error_code")

            description = str(error)

            is_rate_limit = (
                error_code == 429
                or "Too Many Requests" in description
                or "retry after" in description
            )

            if not is_rate_limit:
                raise

            if retry_after is None:
                retry_after = 3

            try:
                retry_after = int(retry_after)
            except Exception:
                retry_after = 3

            retry_after = max(1, min(60, retry_after))

            try:
                import time
                PRODUCTION_LOG_PRINT(PRODUCTION_LOGGER, 'warning', f"⚠️ Telegram rate limit 429. Waiting {retry_after + 1}s before retry send_message.")
                time.sleep(retry_after + 1)
                return original_send_message(chat_id, text, *args, **kwargs)
            except Exception as retry_error:
                PRODUCTION_LOG_PRINT(PRODUCTION_LOGGER, 'error', f"❌ send_message retry failed after 429: {retry_error}")
                return None

    bot.send_message = safe_send_message
    bot._rom_safe_send_patched = True
