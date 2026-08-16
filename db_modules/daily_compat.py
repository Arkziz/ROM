"""Daily quest compatibility API restored from final legacy db.py definitions."""

from .connection import conn, cursor, DEFAULT_BAG_SLOTS, SLOT_ORDER

from data.balance import (
    CONTRACTS_UNLOCK_LEVEL,
    CONTRACT_MOBS_EQUIVALENT,
    CONTRACT_TARGET_KILLS,
    DAILY_CONTRACT_LIMIT,
    DAILY_QUEST_ID_KILL_MONSTERS,
    DAILY_QUEST_REWARD_ITEM_ID,
    DAILY_QUEST_REWARD_QUANTITY,
    DAILY_QUEST_TARGET_KILLS,
    ENERGY_MAX,
    ENERGY_REGEN_MINUTES,
    HP_REGEN_MINUTES,
    HP_REGEN_PERCENT,
    RARITY_REPAIR_MULTIPLIERS,
    REFINE_MATERIAL_MAX_STACK,
    REFINE_STONE_ITEM_ID,
)

def get_daily_today_str():
    from datetime import date
    return date.today().isoformat()

def init_daily_quest_system():
    """
    Щоденні завдання v1.

    Поточна версія:
    - 1 завдання на день
    - вбити 25 монстрів
    - нагорода: Мале зілля здоров’я x3
    """

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS user_daily_quests (
        user_id INTEGER PRIMARY KEY,
        quest_date TEXT,
        quest_id TEXT,
        progress INTEGER,
        target_count INTEGER,
        completed INTEGER,
        reward_claimed INTEGER
    )
    """)

    conn.commit()

def reset_daily_quest_if_needed(user_id):
    init_daily_quest_system()

    today = get_daily_today_str()

    cursor.execute("""
    SELECT quest_date
    FROM user_daily_quests
    WHERE user_id=?
    """, (user_id,))

    row = cursor.fetchone()

    if not row:
        cursor.execute("""
        INSERT INTO user_daily_quests (
            user_id,
            quest_date,
            quest_id,
            progress,
            target_count,
            completed,
            reward_claimed
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            user_id,
            today,
            DAILY_QUEST_ID_KILL_MONSTERS,
            0,
            DAILY_QUEST_TARGET_KILLS,
            0,
            0
        ))

        conn.commit()
        return

    quest_date = row[0] or ""

    if quest_date != today:
        cursor.execute("""
        UPDATE user_daily_quests
        SET
            quest_date=?,
            quest_id=?,
            progress=0,
            target_count=?,
            completed=0,
            reward_claimed=0
        WHERE user_id=?
        """, (
            today,
            DAILY_QUEST_ID_KILL_MONSTERS,
            DAILY_QUEST_TARGET_KILLS,
            user_id
        ))

        conn.commit()

def get_daily_quest_status(user_id):
    reset_daily_quest_if_needed(user_id)

    cursor.execute("""
    SELECT
        quest_date,
        quest_id,
        progress,
        target_count,
        completed,
        reward_claimed
    FROM user_daily_quests
    WHERE user_id=?
    """, (user_id,))

    row = cursor.fetchone()

    if not row:
        return {
            "exists": False,
            "message": "❌ Щоденне завдання не знайдено."
        }

    (
        quest_date,
        quest_id,
        progress,
        target_count,
        completed,
        reward_claimed
    ) = row

    return {
        "exists": True,
        "quest_date": quest_date,
        "quest_id": quest_id,
        "progress": progress or 0,
        "target_count": target_count or DAILY_QUEST_TARGET_KILLS,
        "completed": bool(completed),
        "reward_claimed": bool(reward_claimed),
        "reward_item_id": DAILY_QUEST_REWARD_ITEM_ID,
        "reward_quantity": DAILY_QUEST_REWARD_QUANTITY
    }

__all__ = ['get_daily_quest_status']
