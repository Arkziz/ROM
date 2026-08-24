# ROM 17.19.1 MANA POTION PRICE BALANCE

# ROM 17.15.1 PERSISTENT MANA REGENERATION

from db import (

    get_inventory_entry,

    consume_inventory_item,

    get_current_hp,

    set_current_hp,

    get_max_hp,

    get_user_mp,

    set_user_mp,

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

        "buy_price": 4.00,

        "sell_price": 0.80,

        "max_stack": 10

    },

    204: {

        "name": "🔵 Середнє зілля мани",

        "type": "mp",

        "restore": 100,

        "buy_price": 12.50,

        "sell_price": 2.50,

        "max_stack": 10

    }

}





ALCHEMIST_SHOP = [201, 203, 202, 204]





def get_potion_description(item_id):

    potion = POTIONS.get(item_id)



    if not potion:

        return "Невідоме зілля"



    if potion["type"] == "hp":

        effect = f"відновлює {potion['restore']} HP"

    elif potion["type"] == "mp":

        effect = f"відновлює {potion['restore']} MP"

    else:

        effect = "невідомий ефект"



    return (

        f"{potion['name']}\n"

        f"Ефект: {effect}\n"

        f"Ціна купівлі: {potion['buy_price']:.2f} золота\n"

        f"Ціна продажу: {potion['sell_price']:.2f} золота\n"

        f"Макс. стак: {potion['max_stack']}"

    )





# ==============================

# ✅ USE POTION FROM INVENTORY

# ==============================



def _consume_potion_and_compact_stacks_17_5_1_1(

    user_id, inventory_id, item_id, max_stack, *, resource, new_value, max_value

):

    """Consume one potion, compact same-item stacks, and update resource atomically."""

    # ROM 17.5.1.1 ATOMIC POTION CONSUME AND STACK COMPACTION

    from db_modules.connection import conn, cursor



    user_id = int(user_id)

    inventory_id = int(inventory_id)

    item_id = int(item_id)

    max_stack = max(1, int(max_stack or 1))

    savepoint = "rom_potion_17_5_1_1"

    try:

        cursor.execute(f"SAVEPOINT {savepoint}")

        active = cursor.execute(

            "SELECT quantity FROM inventory WHERE id=? AND user_id=? AND item_id=?",

            (inventory_id, user_id, item_id),

        ).fetchone()

        if not active or int(active[0] or 0) <= 0:

            cursor.execute(f"ROLLBACK TO {savepoint}")

            cursor.execute(f"RELEASE {savepoint}")

            return {"success": False, "reason": "stale_inventory"}



        rows = cursor.execute(

            """SELECT id, quantity FROM inventory

               WHERE user_id=? AND item_id=? AND quantity>0

               ORDER BY id ASC""",

            (user_id, item_id),

        ).fetchall()

        total_before = sum(max(0, int(row[1] or 0)) for row in rows)

        total_after = total_before - 1

        if total_after < 0:

            raise RuntimeError("Potion total became negative.")



        remaining = total_after

        canonical_inventory_id = None

        for row_id, _quantity in rows:

            row_id = int(row_id)

            target = min(max_stack, remaining)

            if target > 0:

                cursor.execute(

                    "UPDATE inventory SET quantity=? WHERE id=? AND user_id=? AND item_id=?",

                    (target, row_id, user_id, item_id),

                )

                if cursor.rowcount != 1:

                    raise RuntimeError("Failed to compact potion stack.")

                if canonical_inventory_id is None:

                    canonical_inventory_id = row_id

                remaining -= target

            else:

                cursor.execute(

                    "DELETE FROM inventory WHERE id=? AND user_id=? AND item_id=?",

                    (row_id, user_id, item_id),

                )

        if remaining != 0:

            raise RuntimeError("Potion stack capacity invariant failed.")



        if resource == "hp":

            changed = cursor.execute(

                "UPDATE users SET hp=? WHERE user_id=?",

                (int(new_value), user_id),

            ).rowcount

        elif resource == "mp":

            changed = cursor.execute(

                "UPDATE users SET mp=?, max_mp=? WHERE user_id=?",

                (int(new_value), int(max_value), user_id),

            ).rowcount

        else:

            raise RuntimeError("Unsupported potion resource.")

        if changed != 1:

            raise RuntimeError("Player resource update failed.")



        cursor.execute(f"RELEASE {savepoint}")

        conn.commit()

        return {

            "success": True,

            "inventory_id": canonical_inventory_id,

            "consumed_inventory_id": inventory_id,

            "remaining_total": total_after,

            "stack_count": (total_after + max_stack - 1) // max_stack if total_after else 0,

        }

    except Exception as error:

        try:

            cursor.execute(f"ROLLBACK TO {savepoint}")

            cursor.execute(f"RELEASE {savepoint}")

        except Exception:

            conn.rollback()

        return {"success": False, "reason": "transaction_failed", "error": str(error)}



def use_potion_from_inventory(user_id, inventory_id):

    """Use one supported potion and return the canonical post-compaction stack."""

    entry = get_inventory_entry(user_id, inventory_id)

    if not entry:

        return {"success": False, "message": "❌ Предмет не знайдено в інвентарі"}



    inv_id, item_id, name, item_type, category, quantity = entry

    if category != "potion":

        return {"success": False, "message": "❌ Це не зілля"}

    potion = POTIONS.get(item_id)

    if not potion:

        return {"success": False, "message": "❌ Це зілля ще не підтримується"}



    if potion["type"] == "mp":

        mp_data = get_user_mp(user_id)

        if isinstance(mp_data, dict):

            current_mp = int(mp_data.get("mp", mp_data.get("current_mp", 0)) or 0)

            max_mp = int(mp_data.get("max_mp", 0) or 0)

        else:

            current_mp = int(mp_data or 0)

            try:

                from db import get_max_mp

                max_mp = int(get_max_mp(user_id) or 0)

            except Exception:

                max_mp = 0

        if max_mp <= 0:

            return {"success": False, "message": "🔵 Твій клас не використовує ману"}

        if current_mp >= max_mp:

            return {"success": False, "message": "🔵 Мана вже повна"}

        new_mp = min(max_mp, current_mp + int(potion["restore"]))

        real_restore = new_mp - current_mp

        mutation = _consume_potion_and_compact_stacks_17_5_1_1(

            user_id, inv_id, item_id, potion["max_stack"],

            resource="mp", new_value=new_mp, max_value=max_mp,

        )

        if not mutation.get("success"):

            message = "❌ Предмет не знайдено в інвентарі" if mutation.get("reason") == "stale_inventory" else "❌ Не вдалося використати зілля"

            return {"success": False, "message": message}

        return {

            "success": True, "resource": "mp",

            "message": f"{potion['name']} використано.\n🔵 Відновлено: +{real_restore} MP\n🔵 Мана: {new_mp}/{max_mp}",

            "restore_mp": real_restore, "new_mp": new_mp, "max_mp": max_mp,

            **mutation,

        }



    current_hp = get_current_hp(user_id)

    max_hp = get_max_hp(user_id)

    if current_hp >= max_hp:

        return {"success": False, "message": "❤️ Здоров’я вже повне"}

    new_hp = min(max_hp, current_hp + int(potion["restore"]))

    real_heal = new_hp - current_hp

    mutation = _consume_potion_and_compact_stacks_17_5_1_1(

        user_id, inv_id, item_id, potion["max_stack"],

        resource="hp", new_value=new_hp, max_value=max_hp,

    )

    if not mutation.get("success"):

        message = "❌ Предмет не знайдено в інвентарі" if mutation.get("reason") == "stale_inventory" else "❌ Не вдалося використати зілля"

        return {"success": False, "message": message}

    return {

        "success": True, "resource": "hp",

        "message": f"{potion['name']} використано.\n❤️ Відновлено: +{real_heal} HP\n❤️ Здоров’я: {new_hp}/{max_hp}",

        "heal": real_heal, "new_hp": new_hp, "max_hp": max_hp,

        **mutation,

    }









# ==============================

# ✅ USE FIRST HP POTION

# ==============================



def use_first_hp_potion(user_id):

    inventory_id = find_first_item_stack_by_type(user_id, "potion_hp")



    if inventory_id is None:

        inventory_id = find_first_item_stack_by_type(user_id, "potion_hp_medium")



    if inventory_id is None:

        return {

            "success": False,

            "message": "❌ У тебе немає зілля здоров’я"

        }



    return use_potion_from_inventory(user_id, inventory_id)



# Stage 17.15.1 synchronize potion MP writes with passive-regeneration metadata.

_BASE_USE_POTION_FROM_INVENTORY_17_15_1 = use_potion_from_inventory





def use_potion_from_inventory(user_id, inventory_id):

    result = _BASE_USE_POTION_FROM_INVENTORY_17_15_1(user_id, inventory_id)

    if result and result.get("success"):

        try:

            from db_modules.connection import conn, cursor

            columns = {str(row[1]) for row in cursor.execute("PRAGMA table_info(users)").fetchall()}

            if "last_mp_regen_update" in columns:

                row = cursor.execute("SELECT mp,max_mp FROM users WHERE user_id=?", (int(user_id),)).fetchone()

                if row and int(row[1] or 0) > 0:

                    current, maximum = int(row[0] or 0), int(row[1] or 0)

                    cursor.execute(

                        "UPDATE users SET last_mp_regen_update=?, mp_full_notified=CASE WHEN ? < ? THEN 0 ELSE mp_full_notified END WHERE user_id=?",

                        (datetime.now().isoformat(), current, maximum, int(user_id)),

                    )

                    conn.commit()

        except Exception:

            pass

    return result

# ROM 17.19.3 ALCHEMIST POTION BUY SELL
def get_alchemist_potion_stock_17_19_3(user_id):
    """Return total, reserved and sellable quantities for potion IDs 201-204."""
    from db_modules.connection import cursor
    try:
        from systems.player_interaction_system import get_inventory_reserved_quantity
    except Exception:
        get_inventory_reserved_quantity = None
    rows = cursor.execute(
        """SELECT inv.id, inv.item_id, COALESCE(inv.quantity,0),
                  it.name, COALESCE(it.sell_price,0)
           FROM inventory inv JOIN items it ON it.id=inv.item_id
           WHERE inv.user_id=? AND inv.item_id IN (201,202,203,204)
           ORDER BY inv.item_id, inv.id""", (int(user_id),)
    ).fetchall()
    grouped = {}
    for inventory_id,item_id,quantity,name,sell_price in rows:
        item_id=int(item_id); quantity=max(0,int(quantity or 0))
        reserved=0
        if get_inventory_reserved_quantity is not None:
            try: reserved=max(0,int(get_inventory_reserved_quantity(int(inventory_id)) or 0))
            except TypeError:
                try: reserved=max(0,int(get_inventory_reserved_quantity(int(user_id),int(inventory_id)) or 0))
                except Exception: reserved=0
            except Exception: reserved=0
        rec=grouped.setdefault(item_id,{"item_id":item_id,"name":str(name),"sell_price":float(sell_price or 0),"total":0,"reserved":0,"available":0})
        rec["total"] += quantity; rec["reserved"] += min(quantity,reserved); rec["available"] += max(0,quantity-reserved)
    return [grouped[i] for i in sorted(grouped)]

# ROM 17.19.3.5 ALCHEMIST BUY RETURN POTION STACK NORMALIZATION
def build_potion_stack_plan_17_19_3_5(rows, max_stack):
    """Pure reservation-safe compaction plan.

    rows: iterable of (inventory_id, quantity, reserved_quantity).
    Reserved quantities stay attached to their inventory IDs. Free quantities are
    packed into the earliest rows up to max_stack. Empty unreserved rows become 0.
    """
    max_stack = max(1, int(max_stack or 1))
    normalized = []
    free_total = 0
    prepared = []
    for inventory_id, quantity, reserved in rows:
        quantity = max(0, int(quantity or 0))
        reserved = max(0, min(quantity, int(reserved or 0)))
        prepared.append((int(inventory_id), quantity, reserved))
        free_total += quantity - reserved
    for inventory_id, _quantity, reserved in prepared:
        capacity = max(0, max_stack - reserved)
        allocated = min(free_total, capacity)
        normalized.append((inventory_id, reserved + allocated))
        free_total -= allocated
    if free_total != 0:
        raise RuntimeError("Недостатня місткість наявних стаків для нормалізації")
    return normalized


def normalize_potion_stacks_17_19_3_5(user_id, item_id, cursor_obj=None):
    """Compact potion stacks inside the caller-owned transaction."""
    if int(item_id) not in ALCHEMIST_SHOP:
        return {"success": False, "reason": "unsupported_item"}
    if cursor_obj is None:
        from db_modules.connection import cursor as cursor_obj
    item_row = cursor_obj.execute(
        "SELECT COALESCE(max_stack,1) FROM items WHERE id=?", (int(item_id),)
    ).fetchone()
    max_stack = max(1, int((item_row[0] if item_row else 1) or 1))
    rows = cursor_obj.execute(
        """SELECT inv.id, COALESCE(inv.quantity,0),
                  COALESCE((SELECT SUM(r.quantity) FROM inventory_reservations r
                            WHERE r.inventory_id=inv.id),0)
           FROM inventory inv
           WHERE inv.user_id=? AND inv.item_id=?
           ORDER BY inv.id""",
        (int(user_id), int(item_id)),
    ).fetchall()
    plan = build_potion_stack_plan_17_19_3_5(rows, max_stack)
    for inventory_id, new_quantity in plan:
        if int(new_quantity) <= 0:
            cursor_obj.execute(
                "DELETE FROM inventory WHERE id=? AND user_id=? AND item_id=?",
                (int(inventory_id), int(user_id), int(item_id)),
            )
        else:
            cursor_obj.execute(
                "UPDATE inventory SET quantity=? WHERE id=? AND user_id=? AND item_id=?",
                (int(new_quantity), int(inventory_id), int(user_id), int(item_id)),
            )
    return {"success": True, "stacks": [int(q) for _inventory_id, q in plan if int(q) > 0]}


def buy_alchemist_potion_17_19_3(user_id,item_id,quantity):
    """Atomically purchase an exact quantity at the current canonical price."""
    from db_modules.connection import conn,cursor
    from db_modules.inventory import add_item
    item_id=int(item_id); quantity=int(quantity)
    potion=POTIONS.get(item_id)
    if not potion or item_id not in ALCHEMIST_SHOP: return {"success":False,"message":"❌ Такого зілля немає в Алхіміка."}
    if quantity<1 or quantity>999: return {"success":False,"message":"❌ Кількість має бути від 1 до 999."}
    unit=float(potion["buy_price"]); total=round(unit*quantity,2)
    try:
        cursor.execute("BEGIN IMMEDIATE")
        row=cursor.execute("SELECT COALESCE(gold,0) FROM users WHERE user_id=?",(int(user_id),)).fetchone()
        gold=float(row[0] or 0) if row else 0.0
        if gold<total: conn.rollback(); return {"success":False,"message":f"❌ Недостатньо золота. Потрібно: {total:.2f}, є: {gold:.2f}."}
        result=add_item(int(user_id),item_id,quantity,commit=False)
        if not result.get("success") or int(result.get("added",0) or 0)!=quantity or int(result.get("lost",0) or 0)!=0:
            conn.rollback(); return {"success":False,"message":result.get("message") or "❌ Зілля не вдалося додати."}
        changed=cursor.execute("UPDATE users SET gold=COALESCE(gold,0)-? WHERE user_id=? AND COALESCE(gold,0)>=?",(total,int(user_id),total)).rowcount
        if changed!=1: conn.rollback(); return {"success":False,"message":"❌ Баланс змінився. Купівлю скасовано."}
        normalize_potion_stacks_17_19_3_5(int(user_id), item_id, cursor)
        conn.commit(); return {"success":True,"message":f"✅ Куплено {potion['name']} ×{quantity} за {total:.2f} золота.","quantity":quantity,"total":total}
    except Exception as e:
        conn.rollback(); return {"success":False,"message":f"❌ Купівлю не завершено: {e}"}

def sell_alchemist_potion_17_19_3(user_id,item_id,quantity):
    """Atomically sell only unreserved potion quantity across multiple stacks."""
    from db_modules.connection import conn,cursor
    item_id=int(item_id); quantity=int(quantity)
    potion=POTIONS.get(item_id)
    if not potion or item_id not in ALCHEMIST_SHOP: return {"success":False,"message":"❌ Це зілля Алхімік не купує."}
    if quantity<1 or quantity>999999: return {"success":False,"message":"❌ Некоректна кількість."}
    try:
        cursor.execute("BEGIN IMMEDIATE")
        rows=cursor.execute("SELECT id,COALESCE(quantity,0) FROM inventory WHERE user_id=? AND item_id=? ORDER BY id",(int(user_id),item_id)).fetchall()
        available_rows=[]; total_available=0
        for inv_id,stack_qty in rows:
            stack_qty=max(0,int(stack_qty or 0))
            reserved_row=cursor.execute("SELECT COALESCE(SUM(quantity),0) FROM inventory_reservations WHERE inventory_id=?",(int(inv_id),)).fetchone()
            reserved=max(0,int((reserved_row[0] if reserved_row else 0) or 0))
            free=max(0,stack_qty-reserved); available_rows.append((int(inv_id),stack_qty,free)); total_available+=free
        if total_available<quantity:
            conn.rollback(); return {"success":False,"message":f"❌ Доступно для продажу лише {total_available}. Зарезервовані зілля не продаються."}
        remaining=quantity
        for inv_id,stack_qty,free in available_rows:
            take=min(remaining,free)
            if take<=0: continue
            new_qty=stack_qty-take
            if new_qty<=0: cursor.execute("DELETE FROM inventory WHERE id=? AND user_id=?",(inv_id,int(user_id)))
            else: cursor.execute("UPDATE inventory SET quantity=? WHERE id=? AND user_id=?",(new_qty,inv_id,int(user_id)))
            remaining-=take
            if remaining<=0: break
        unit=float(potion["sell_price"]); total=round(unit*quantity,2)
        changed=cursor.execute("UPDATE users SET gold=COALESCE(gold,0)+? WHERE user_id=?",(total,int(user_id))).rowcount
        if changed!=1: raise RuntimeError("Не вдалося зарахувати золото")
        normalize_potion_stacks_17_19_3_5(int(user_id), item_id, cursor)
        conn.commit(); return {"success":True,"message":f"✅ Продано {potion['name']} ×{quantity}. Отримано {total:.2f} золота.","quantity":quantity,"total":total}
    except Exception as e:
        conn.rollback(); return {"success":False,"message":f"❌ Продаж не завершено: {e}"}

