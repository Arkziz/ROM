from db import (
    get_inventory_entry,
    consume_inventory_item,
    get_current_hp,
    set_current_hp,
    get_max_hp,
    find_first_item_stack_by_type
)


# ==============================
# ✅ POTION CONFIG
# ==============================

POTIONS = {
    201: {
        "name": "🔴 Мале зілля здоров’я",
        "type": "hp",
        "restore": 50,
        "buy_price": 5.0,
        "sell_price": 1.0,
        "max_stack": 10
    },
    203: {
        "name": "🔴 Середнє зілля здоров’я",
        "type": "hp",
        "restore": 120,
        "buy_price": 15.0,
        "sell_price": 3.0,
        "max_stack": 10
    },
    202: {
        "name": "🔵 Мале зілля мани",
        "type": "mp",
        "restore": 40,
        "buy_price": 6.0,
        "sell_price": 1.2,
        "max_stack": 10
    },
    204: {
        "name": "🔵 Середнє зілля мани",
        "type": "mp",
        "restore": 100,
        "buy_price": 18.0,
        "sell_price": 3.6,
        "max_stack": 10
    }
}


# ==============================
# ✅ USE POTION FROM INVENTORY
# ==============================

def use_potion_from_inventory(user_id, inventory_id):
    entry = get_inventory_entry(user_id, inventory_id)

    if not entry:
        return {
            "success": False,
            "message": "❌ Предмет не знайдено в інвентарі"
        }

    inv_id, item_id, name, item_type, category, quantity = entry

    if category != "potion":
        return {
            "success": False,
            "message": "❌ Це не зілля"
        }

    potion = POTIONS.get(item_id)

    if not potion:
        return {
            "success": False,
            "message": "❌ Це зілля ще не підтримується"
        }

    if potion["type"] == "mp":
        return {
            "success": False,
            "message": "🔵 Мана ще не реалізована. Це зілля поки не можна використати."
        }

    current_hp = get_current_hp(user_id)
    max_hp = get_max_hp(user_id)

    if current_hp >= max_hp:
        return {
            "success": False,
            "message": "❤️ Здоров’я вже повне"
        }

    healed_amount = potion["restore"]
    new_hp = min(max_hp, current_hp + healed_amount)
    real_heal = new_hp - current_hp

    consumed = consume_inventory_item(user_id, inventory_id, 1)

    if not consumed:
        return {
            "success": False,
            "message": "❌ Не вдалося використати зілля"
        }

    set_current_hp(user_id, new_hp)

    return {
        "success": True,
        "message": (
            f"{potion['name']} використано.\n"
            f"❤️ Відновлено: +{real_heal} HP\n"
            f"❤️ Здоров’я: {new_hp}/{max_hp}"
        ),
        "heal": real_heal,
        "new_hp": new_hp,
        "max_hp": max_hp
    }


# ==============================
# ✅ USE FIRST HP POTION
# ==============================

def use_first_hp_potion(user_id):
    # Спочатку шукаємо мале зілля HP
    inventory_id = find_first_item_stack_by_type(user_id, "potion_hp")

    # Якщо малого немає — шукаємо середнє
    if inventory_id is None:
        inventory_id = find_first_item_stack_by_type(user_id, "potion_hp_medium")

    if inventory_id is None:
        return {
            "success": False,
            "message": "❌ У тебе немає зілля здоров’я"
        }

    return use_potion_from_inventory(user_id, inventory_id)