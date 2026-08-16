"""
Database migrations and startup maintenance module.
"""

from .connection import conn, cursor, DEFAULT_BAG_SLOTS


def expand_bag_slots_to_40():
    """
    Робить базовий розмір сумки 40 слотів.
    Для існуючих персонажів, у кого менше 40, піднімає до 40.
    """

    try:
        cursor.execute("""
        UPDATE users
        SET bag_slots=?
        WHERE bag_slots IS NULL OR bag_slots < ?
        """, (DEFAULT_BAG_SLOTS, DEFAULT_BAG_SLOTS))

        conn.commit()
    except Exception:
        pass


def seed_location_trash_items():
    """
    Сірий лут для нової структури мобів 1–10.
    """

    trash_items = [
        # 1–5: Початок Шляху
        (107, "🐗 Ікло дикого кабана", "trash", "grey", "trash", None, 1, 20, 0.12, 0, 0, 0, 0, 0, 0, 0),
        (108, "🌱 Рунічний пагін", "trash", "grey", "trash", None, 1, 20, 0.14, 0, 0, 0, 0, 0, 0, 0),
        (109, "🦡 Борсучий кіготь", "trash", "grey", "trash", None, 1, 20, 0.18, 0, 0, 0, 0, 0, 0, 0),
        (110, "💎 Слиз рунічного слимака", "trash", "grey", "trash", None, 1, 20, 0.20, 0, 0, 0, 0, 0, 0, 0),
        (111, "🦇 Крило лісового кажана", "trash", "grey", "trash", None, 1, 20, 0.24, 0, 0, 0, 0, 0, 0, 0),
        (112, "🩸 Крапля темної крові", "trash", "grey", "trash", None, 1, 20, 0.28, 0, 0, 0, 0, 0, 0, 0),
        (113, "🕷️ Павуча лапка", "trash", "grey", "trash", None, 1, 20, 0.32, 0, 0, 0, 0, 0, 0, 0),
        (114, "🧪 Кислотна залоза", "trash", "grey", "trash", None, 1, 20, 0.36, 0, 0, 0, 0, 0, 0, 0),
        (115, "🐺 Вовче ікло", "trash", "grey", "trash", None, 1, 20, 0.42, 0, 0, 0, 0, 0, 0, 0),
        (116, "👻 Примарна шерсть", "trash", "grey", "trash", None, 1, 20, 0.48, 0, 0, 0, 0, 0, 0, 0),

        # 6–10: Темний Бір
        (117, "👺 Гоблінський зуб", "trash", "grey", "trash", None, 1, 20, 0.55, 0, 0, 0, 0, 0, 0, 0),
        (118, "🧪 Знахарський амулет", "trash", "grey", "trash", None, 1, 20, 0.62, 0, 0, 0, 0, 0, 0, 0),
        (119, "🗡️ Тупий гоблінський кинджал", "trash", "grey", "trash", None, 1, 20, 0.70, 0, 0, 0, 0, 0, 0, 0),
        (120, "🧙 Шаманська намистина", "trash", "grey", "trash", None, 1, 20, 0.78, 0, 0, 0, 0, 0, 0, 0),
        (121, "🪓 Уламок сокири берсерка", "trash", "grey", "trash", None, 1, 20, 0.88, 0, 0, 0, 0, 0, 0, 0),
        (122, "🔥 Обвуглений рунічний попіл", "trash", "grey", "trash", None, 1, 20, 0.95, 0, 0, 0, 0, 0, 0, 0),
        (123, "🛡️ Іржава пластина щита", "trash", "grey", "trash", None, 1, 20, 1.05, 0, 0, 0, 0, 0, 0, 0),
        (124, "🔮 Рунічний уламок культиста", "trash", "grey", "trash", None, 1, 20, 1.15, 0, 0, 0, 0, 0, 0, 0),
        (125, "🧟 Осквернений уламок обладунку", "trash", "grey", "trash", None, 1, 20, 1.30, 0, 0, 0, 0, 0, 0, 0),
        (126, "🕯️ Чорна свічка віщуна", "trash", "grey", "trash", None, 1, 20, 1.45, 0, 0, 0, 0, 0, 0, 0),
    ]

    for item in trash_items:
        cursor.execute("""
        INSERT INTO items (
            id, name, type, rarity, category,
            slot_key, weapon_hands,
            max_stack, sell_price,
            bonus_str, bonus_dex, bonus_int, bonus_wis, bonus_sta,
            pdef, mdef
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(id) DO UPDATE SET
            name=excluded.name,
            type=excluded.type,
            rarity=excluded.rarity,
            category=excluded.category,
            slot_key=excluded.slot_key,
            weapon_hands=excluded.weapon_hands,
            max_stack=excluded.max_stack,
            sell_price=excluded.sell_price,
            bonus_str=excluded.bonus_str,
            bonus_dex=excluded.bonus_dex,
            bonus_int=excluded.bonus_int,
            bonus_wis=excluded.bonus_wis,
            bonus_sta=excluded.bonus_sta,
            pdef=excluded.pdef,
            mdef=excluded.mdef
        """, item)

    conn.commit()


def init_migration_system():
    from migrations.runner import ensure_migrations_table
    ensure_migrations_table(conn)
    return True


def run_pending_migrations():
    from migrations.runner import run_pending_migrations as _run
    return _run(conn)


def get_migration_status():
    from migrations.runner import get_migration_status as _status
    return _status(conn)


def run_db_startup_maintenance():
    """
    Run idempotent database maintenance explicitly during application startup.
    """
    from data.balance import REFINE_MATERIAL_MAX_STACK
    
    result = {
        "success": False,
        "refine_material_stack_sizes": None,
        "contract_target_kills": None,
    }

    # Refine material stack sizes fix
    try:
        cursor.execute("""
        UPDATE items
        SET max_stack=?
        WHERE id IN (401, 402)
        """, (REFINE_MATERIAL_MAX_STACK,))
        conn.commit()
        result["refine_material_stack_sizes"] = True
    except Exception:
        result["refine_material_stack_sizes"] = False

    # Contract target kills migration
    try:
        cursor.execute("""
        UPDATE user_active_contracts
        SET target_kills=5
        WHERE target_kills > 5
        """)

        cursor.execute("""
        UPDATE user_active_contracts
        SET completed=1,
            current_kills=5
        WHERE target_kills=5
          AND current_kills >= 5
          AND reward_claimed=0
        """)

        conn.commit()
        result["contract_target_kills"] = True
    except Exception:
        result["contract_target_kills"] = False

    result["success"] = True
    return result
