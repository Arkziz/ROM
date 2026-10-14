import random

from data.player_progression import get_base_exp_for_level



from db import (

    add_exp,

    add_gold,

    add_kill,

    add_item,

    get_inventory_used_slots,

    get_bag_capacity,

    create_generated_equipment_item,

)





REWARD_SYSTEM_UI_VERSION = "5.9.3-final-trophy-messages"





# ==============================

# EQUIPMENT DROP CONFIG

# ==============================



NORMAL_EQUIPMENT_DROP_CHANCE = 0.20

ELITE_EQUIPMENT_DROP_CHANCE = 0.45



NORMAL_CLASS_AWARE_EQUIPMENT_CHANCE = 0.50

ELITE_CLASS_AWARE_EQUIPMENT_CHANCE = 0.70





def roll_normal_equipment_rarity():

    roll = random.random()



    if roll <= 0.80:

        return "common"



    return "uncommon"





def roll_elite_equipment_rarity():

    roll = random.random()



    if roll <= 0.75:

        return "uncommon"



    return "rare"





# ==============================

# LEVEL DIFFERENCE MULTIPLIER

# ==============================



def get_level_difference_multiplier(player_level, mob_level):

    delta = int(mob_level) - int(player_level)



    if delta <= -3:

        return 0.3



    if delta == -2:

        return 0.5



    if delta == -1:

        return 0.8



    if delta == 0:

        return 1.0



    if delta == 1:

        return 1.2



    if delta == 2:

        return 1.5



    return 1.8





# ==============================

# EXP CALCULATION

# ==============================



def calculate_exp_reward(player_level, mob):

    mob_level = int(mob.get("level", player_level))



    base_exp = get_base_exp_for_level(mob_level)

    level_multiplier = get_level_difference_multiplier(player_level, mob_level)

    random_factor = random.uniform(0.9, 1.1)

    elite_multiplier = float(mob.get("elite_exp_multiplier", 1.0))



    exp = round(

        base_exp

        * level_multiplier

        * random_factor

        * elite_multiplier

    )



    if exp < 1:

        exp = 1



    return int(exp)





# ==============================

# GOLD CALCULATION

# ==============================



def calculate_gold_reward(player_level, mob):

    mob_level = int(mob.get("level", player_level))



    if "gold" in mob:

        gold = float(mob["gold"])



    elif "gold_reward" in mob:

        gold = float(mob["gold_reward"])



    elif "min_gold" in mob and "max_gold" in mob:

        gold = random.uniform(

            float(mob["min_gold"]),

            float(mob["max_gold"])

        )



    else:

        min_gold = max(0.05, mob_level * 0.08)

        max_gold = max(0.10, mob_level * 0.18)

        gold = random.uniform(min_gold, max_gold)



    elite_multiplier = float(mob.get("elite_gold_multiplier", 1.0))



    return round(gold * elite_multiplier, 2)





# ==============================

# EQUIPMENT TROPHY DISPLAY HELPERS

# ==============================



def build_trophy_display_name(result):

    """

    Формує красиву назву трофея для повідомлення про лут.



    Для броні додає armor_type:

    Поножі 1 рівня -> Поножі [Тканина] 1 рівня



    Для зброї / off-hand тип у дужках не додається.

    """



    from db import (

        get_item_classification_by_inventory_id,

        get_armor_type_label,

        is_armor_slot,

    )



    name = result.get("name", "Трофей")

    inventory_id = result.get("inventory_id")



    if not inventory_id:

        return name



    classification = get_item_classification_by_inventory_id(inventory_id)



    if not classification:

        return name



    slot_key = classification.get("slot_key", "")

    armor_type = classification.get("armor_type", "")



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





def is_trophy_suitable_for_class(user_id, result):

    """

    Перевіряє фактичну сумісність випалого предмета з поточним класом.

    """



    from db import can_equip_inventory_item_by_class



    inventory_id = result.get("inventory_id")



    if not inventory_id:

        return False



    check = can_equip_inventory_item_by_class(

        user_id=user_id,

        inventory_id=inventory_id,

    )



    return bool(check.get("success"))





def build_trophy_drop_message(user_id, result, rarity, is_elite):

    rarity_text = {

        "common": "⚪",

        "uncommon": "🟢",

        "rare": "🔵",

        "epic": "🟣",

    }.get(rarity, "⚪")



    item_name = build_trophy_display_name(result)



    is_suitable = (

        bool(result.get("class_aware"))

        or is_trophy_suitable_for_class(user_id, result)

    )



    if is_elite:

        if is_suitable:

            return (

                f"{rarity_text} 🎯 Елітний трофей під твій клас:\n"

                f"  📦 {item_name}"

            )



        return (

            f"{rarity_text} Елітний трофей:\n"

            f"  📦 {item_name}"

        )



    if is_suitable:

        return (

            f"{rarity_text} 🎯 Знайдено трофей під твій клас:\n"

            f"  📦 {item_name}"

        )



    return (

        f"{rarity_text} Знайдено трофей:\n"

        f"  📦 {item_name}"

    )





# ==============================

# SIMPLE LOOT

# ==============================



def get_random_quantity(value):

    if isinstance(value, list) or isinstance(value, tuple):

        if len(value) >= 2:

            return random.randint(int(value[0]), int(value[1]))



    return int(value or 1)





# ==============================

# ✅ REFINE STONE DROP V1

# ==============================



# 6.0.6

# 🪨 Камінь Посилення падає з мобів.

# 💎 Руна Успіху НЕ падає з мобів — буде за кристали пізніше.



REFINE_STONE_ITEM_ID = 601

NORMAL_REFINE_STONE_DROP_CHANCE = 0.08

ELITE_REFINE_STONE_DROP_CHANCE = 0.20





def _guild_is_elite_mob_v1(mob):

    try:

        return bool(mob.get("is_elite", False) or mob.get("elite", False))

    except Exception:

        return False





def roll_refine_stone_drop(user_id, mob, random_func=None):

    """Compatibility API using the central Refine Stone chance table."""

    import random

    from systems.drop_system import roll_central_refine_stone_drop



    rng = random_func or random.random

    central = roll_central_refine_stone_drop(mob, rng)

    if not central.get("rolled"):

        return None



    payload = central.get("payload") or {}

    result = add_item(

        int(user_id),

        int(payload.get("item_id", REFINE_STONE_ITEM_ID)),

        int(payload.get("quantity", 1)),

    )

    if result.get("added", 0) > 0:

        name = result.get("name", "🪨 Камінь Посилення")

        return f"{name} x{int(result.get('added', 1))}"

    if result.get("lost", 0) > 0:

        name = result.get("name", "🪨 Камінь Посилення")

        return f"⚠️ Не влізло в сумку: {name} x{int(result.get('lost', 1))}"

    return None





def roll_equipment_drop(user_id, mob, random_func=None):

    """Compatibility API delegated to the central equipment drop rule."""

    from systems.drop_system import roll_central_equipment_drop



    rng = random_func or random.random

    central = roll_central_equipment_drop(mob, rng)

    if not central.get("rolled"):

        return None



    payload = central.get("payload") or {}

    result = create_generated_equipment_item(

        user_id=user_id,

        item_level=int(mob.get("level", 1)),

        rarity=str(payload["rarity"]),

        class_aware_chance=float(payload["class_aware_chance"]),

    )

    if not result.get("success"):

        return result.get("message", "🎒 Екіпірування не влізло в сумку.")



    return build_trophy_drop_message(

        user_id=user_id,

        result=result,

        rarity=str(payload["rarity"]),

        is_elite=central["enemy_type"] in ("elite", "boss"),

    )





def _append_central_trophy_award_11_5_0(messages, user_id, item_id, quantity):

    result = add_item(int(user_id), int(item_id), int(quantity))

    if result.get("added", 0) > 0:

        messages.append(

            f"{result.get('name', 'Предмет')} x{int(result.get('added', 0))}"

        )

    if result.get("lost", 0) > 0:

        messages.append(

            f"⚠️ Не влізло в сумку: "

            f"{result.get('name', 'Предмет')} x{int(result.get('lost', 0))}"

        )





def roll_loot_from_loot_table(user_id, loot_table, random_func=None):

    """Compatibility table path delegated to the central trophy rule."""

    from systems.drop_system import roll_central_trophy_table_entry



    rng = random_func or random.random

    messages = []

    for loot in loot_table:

        item_id = loot.get("item_id")

        # Preserve legacy RNG order: quantity is rolled before item validation

        # and before the chance roll.

        quantity = get_random_quantity(loot.get("quantity", 1))

        if not item_id:

            continue

        central = roll_central_trophy_table_entry(loot, rng)

        if central.get("rolled"):

            _append_central_trophy_award_11_5_0(

                messages, user_id, item_id, quantity

            )

    return messages





def roll_loot_from_simple_keys(

    user_id, mob, random_func=None, choice_func=None

):

    """Compatibility simple-pool path delegated to central trophy config."""

    from systems.drop_system import roll_central_trophy_simple



    rng = random_func or random.random

    chooser = choice_func or random.choice

    central = roll_central_trophy_simple(mob, rng, chooser)

    if not central.get("rolled"):

        return []

    payload = central.get("payload") or {}

    messages = []

    _append_central_trophy_award_11_5_0(

        messages,

        user_id,

        int(payload["item_id"]),

        int(payload.get("quantity", 1)),

    )

    return messages





def roll_potion_drop(user_id, mob, random_func=None):

    """Award zero or one potion after one central mutually-exclusive roll."""

    from systems.drop_system import roll_central_potion_drop



    rng = random_func or random.random

    central = roll_central_potion_drop(mob, rng)

    if not central.get("rolled"):

        return None

    payload = central.get("payload") or {}

    result = add_item(

        int(user_id), int(payload["item_id"]), int(payload.get("quantity", 1))

    )

    if result.get("added", 0) > 0:

        return f"{result.get('name', 'Зілля')} x{int(result.get('added', 0))}"

    if result.get("lost", 0) > 0:

        return (

            f"⚠️ Не влізло в сумку: "

            f"{result.get('name', 'Зілля')} x{int(result.get('lost', 0))}"

        )

    return None





def _central_guild_elite_reward_11_9_0(user_id, mob):

    """Preserve the non-item guild hook exactly once."""

    if not _guild_is_elite_mob_v1(mob):

        return None

    try:

        from db import award_guild_elite_kill, get_guild_activity_reward_text

        result = award_guild_elite_kill(user_id, mob)

        return get_guild_activity_reward_text(result)

    except Exception as error:

        print(f"⚠️ Guild elite reward failed: {error}")

        return None







def roll_rebirth_sphere_drop(user_id, mob, random_func=None):
    """Award zero or one Rebirth Sphere via the canonical central rule."""
    from systems.drop_system import roll_central_rebirth_sphere_drop
    rng = random_func or random.random
    central = roll_central_rebirth_sphere_drop(mob, rng)
    if not central.get("rolled"):
        return None
    payload = central.get("payload") or {}
    result = add_item(int(user_id), int(payload["item_id"]), int(payload.get("quantity", 1)))
    if result.get("added", 0) > 0:
        return f"{result.get('name', '♻️ Сфера Переродження')} ×{int(result.get('added', 0))}"
    if result.get("lost", 0) > 0:
        return f"⚠️ Не влізло в сумку: {result.get('name', '♻️ Сфера Переродження')} ×{int(result.get('lost', 0))}"
    return None

def process_enemy_drops(user_id, mob):

    """Award every active central drop rule once, in canonical order.



    This is the only production composition point after 11.9.0. Compatibility

    functions remain available, but the old nested roll_loot chain is bypassed

    to prevent duplicate equipment, trophy, stone, rune or potion awards.

    """

    from systems.drop_system import get_victory_drop_plan



    messages = []

    rune_result = {"dropped": False}

    executed = []



    for rule_id in get_victory_drop_plan():

        executed.append(rule_id)

        if rule_id == "trophy":

            if "loot_table" in mob and isinstance(mob["loot_table"], list):

                messages.extend(roll_loot_from_loot_table(user_id, mob["loot_table"]))

            elif "loot" in mob and isinstance(mob["loot"], list):

                messages.extend(roll_loot_from_loot_table(user_id, mob["loot"]))

            else:

                messages.extend(roll_loot_from_simple_keys(user_id, mob))

        elif rule_id == "equipment":

            message = roll_equipment_drop(user_id, mob)

            if message:

                messages.append(message)

        elif rule_id == "refine_stone":

            message = roll_refine_stone_drop(user_id, mob)

            if message:

                messages.append(message)

        elif rule_id == "rune":

            try:

                from systems.rune_system import award_rune_drop

                rune_result = award_rune_drop(user_id, mob)

            except Exception as error:

                print(f"⚠️ Rune drop reward failed: {error}")

                rune_result = {"dropped": False, "error": str(error)}

            if rune_result.get("dropped") and rune_result.get("message"):

                messages.append(rune_result["message"])

        elif rule_id == "potion":

            message = roll_potion_drop(user_id, mob)

            if message:

                messages.append(message)

        elif rule_id == "rebirth_sphere":
            message = roll_rebirth_sphere_drop(user_id, mob)
            if message:
                messages.append(message)
        else:

            raise RuntimeError(f"unsupported production victory rule: {rule_id}")



    fatigue_artifact_message = roll_fatigue_artifact_drop(user_id, mob)

    executed.append("fatigue_artifact")

    if fatigue_artifact_message:

        messages.append(fatigue_artifact_message)



    guild_message = _central_guild_elite_reward_11_9_0(user_id, mob)

    if guild_message:

        messages.append(guild_message)



    return {

        "messages": messages,

        "rune_drop": rune_result,

        "executed_rules": tuple(executed),

        "guild_hook_executed": bool(_guild_is_elite_mob_v1(mob)),

    }





def roll_loot(user_id, mob):

    """Compatibility API routed to the final central orchestration."""

    return process_enemy_drops(user_id, mob)["messages"]





def process_victory_reward(user_id, player_level, mob):

    """Apply Premium EXP and combat gold exactly once for a mob victory."""

    base_exp = calculate_exp_reward(player_level=player_level, mob=mob)

    gold = calculate_gold_reward(player_level=player_level, mob=mob)

    from systems.timed_exp_bonus_system import calculate_mob_kill_exp, calculate_mob_kill_gold

    exp_breakdown = calculate_mob_kill_exp(user_id, base_exp)

    gold_breakdown = calculate_mob_kill_gold(user_id, gold)

    gold = float(gold_breakdown["final_gold"])

    exp = int(exp_breakdown["final_exp"])

    exp_result = add_exp(user_id, exp)

    add_gold(user_id, gold)

    add_kill(user_id)

    drop_result = process_enemy_drops(user_id, mob)

    # ROM_STAGE_18_29_4B_EVENT_DROP_INTEGRATION
    event_drop_results = process_event_drops(user_id, mob)

    return {

        "exp": exp,

        "base_exp": int(base_exp),

        "premium_exp_bonus": int(exp_breakdown["bonus_exp"]),

        "exp_bonus_active": bool(exp_breakdown["active"]),

        "gold": gold,

        "base_gold": float(gold_breakdown["base_gold"]),

        "premium_gold_bonus": float(gold_breakdown["bonus_gold"]),

        "premium_gold_active": bool(gold_breakdown["active"]),

        "exp_result": exp_result,

        "loot_messages": drop_result["messages"],

        "rune_drop": drop_result["rune_drop"],

        "central_drop_rules": drop_result["executed_rules"],

        "event_drop_results": event_drop_results,

        "used_slots": get_inventory_used_slots(user_id),

        "capacity": get_bag_capacity(user_id),

    }



def roll_fatigue_artifact_drop(user_id, mob, random_func=None):

    import random

    from systems.fatigue_artifact_system import FATIGUE_ARTIFACT_ITEM_ID, add_fatigue_artifacts

    rng = random_func or random.random

    chance = 0.10 if mob.get("is_boss") else (0.05 if mob.get("is_elite") else 0.01)

    if float(rng()) >= chance:

        return None

    result = add_fatigue_artifacts(user_id, 1)

    if result.get("added"):

        return "💠 Артефакт відновлення сил ×1"

    return "⚠️ Не влізло в сумку: 💠 Артефакт відновлення сил ×1"


def process_event_drops(user_id, mob, context=None, now=None, random_func=None, rule_collector=None, add_item_func=None):
    """Award event-drop plan through the canonical inventory add_item owner."""
    from systems.drop_system import get_event_drop_plan
    from db_modules.inventory import add_item as canonical_add_item
    award=add_item_func or canonical_add_item
    plan=get_event_drop_plan(mob,context=context,now=now,random_func=random_func,rule_collector=rule_collector)
    results=[]
    for payload in plan:
        result=award(int(user_id),int(payload["item_id"]),int(payload["quantity"]))
        results.append({"payload":payload,"result":result})
    return tuple(results)
