from pathlib import Path
from datetime import datetime
import py_compile
import sys

PATCH_NAME = "7_0_7_guild_progress_contributions"
SYSTEM_MARKER = "# ✅ GUILD PROGRESS CONTRIBUTIONS CORE V1"
DB_MARKER = "# ✅ GUILD PROGRESS CONTRIBUTIONS DB WRAPPERS V1"
HANDLER_MARKER = "# ✅ GUILD PROGRESS CONTRIBUTIONS UI V1"

SYSTEM_APPEND = r'''

# ==============================
# ✅ GUILD PROGRESS CONTRIBUTIONS CORE V1
# ==============================

# 7.0.7
# Guild EXP / Resource / внесок учасників.
# На цьому етапі додаємо:
# - рівень гільдії від загального EXP;
# - рейтинг внеску учасників;
# - helper-и для прогресу;
# - add_guild_progress() лишається центральною точкою нарахування.

GUILD_LEVEL_EXP_BASE = 1000


def get_guild_exp_required_for_level(level):
    """
    Скільки total EXP потрібно для конкретного рівня гільдії.

    Level 1: 0
    Level 2: 1000
    Level 3: 3000
    Level 4: 6000

    Формула накопичувальна: sum(base * n) для n=1..level-1.
    """

    try:
        level = int(level)
    except Exception:
        level = 1

    level = max(1, level)

    if level <= 1:
        return 0

    return int(GUILD_LEVEL_EXP_BASE * ((level - 1) * level / 2))


def calculate_guild_level_from_exp(total_exp):
    try:
        total_exp = int(total_exp or 0)
    except Exception:
        total_exp = 0

    level = 1

    while total_exp >= get_guild_exp_required_for_level(level + 1):
        level += 1

    return level


def get_guild_next_level_info(guild_id):
    guild = get_guild_by_id(guild_id)

    if not guild:
        return None

    total_exp = int(guild["total_exp"] or 0)
    level = int(guild["level"] or 1)
    calculated_level = calculate_guild_level_from_exp(total_exp)

    if calculated_level > level:
        level = calculated_level

    current_level_exp = get_guild_exp_required_for_level(level)
    next_level_exp = get_guild_exp_required_for_level(level + 1)
    progress_exp = max(0, total_exp - current_level_exp)
    needed_exp = max(1, next_level_exp - current_level_exp)
    progress_percent = min(100.0, max(0.0, progress_exp / needed_exp * 100))

    return {
        "level": level,
        "total_exp": total_exp,
        "current_level_exp": current_level_exp,
        "next_level_exp": next_level_exp,
        "progress_exp": progress_exp,
        "needed_exp": needed_exp,
        "progress_percent": progress_percent,
    }


def recalculate_guild_level(guild_id):
    guild = get_guild_by_id(guild_id)

    if not guild:
        return None

    old_level = int(guild["level"] or 1)
    total_exp = int(guild["total_exp"] or 0)
    new_level = calculate_guild_level_from_exp(total_exp)

    if new_level != old_level:
        cursor.execute(
            "UPDATE guilds SET level=?, updated_at=? WHERE id=?",
            (new_level, now_iso(), guild_id)
        )
        conn.commit()

        if new_level > old_level:
            try:
                add_guild_log(
                    guild_id=guild_id,
                    event_type="guild_level_up",
                    text=f"Гільдія піднялась до рівня {new_level}."
                )
            except Exception:
                pass

    return new_level


try:
    _base_add_guild_progress_before_contributions_v1 = add_guild_progress
except Exception:
    _base_add_guild_progress_before_contributions_v1 = None


def add_guild_progress(guild_id, exp=0, resource=0, kills=0, contracts=0, user_id=None, reason=""):
    """
    FINAL OVERRIDE:
    Додає прогрес через базову функцію 7.0.1 і після цього перераховує рівень гільдії.
    """

    if _base_add_guild_progress_before_contributions_v1 is None:
        return {
            "success": False,
            "message": "❌ Базова функція add_guild_progress недоступна."
        }

    result = _base_add_guild_progress_before_contributions_v1(
        guild_id=guild_id,
        exp=exp,
        resource=resource,
        kills=kills,
        contracts=contracts,
        user_id=user_id,
        reason=reason,
    )

    try:
        result["guild_level"] = recalculate_guild_level(guild_id)
        result["next_level_info"] = get_guild_next_level_info(guild_id)
    except Exception:
        pass

    return result


def add_user_guild_progress(user_id, exp=0, resource=0, kills=0, contracts=0, reason=""):
    """
    Додає прогрес гільдії від конкретного учасника.
    Саме цю функцію варто використовувати для майбутньої інтеграції з контрактами/елітними мобами.
    """

    member = get_user_guild_member(user_id)

    if not member:
        return {
            "success": False,
            "message": "❌ Гравець не перебуває у гільдії."
        }

    return add_guild_progress(
        guild_id=member["guild_id"],
        exp=exp,
        resource=resource,
        kills=kills,
        contracts=contracts,
        user_id=user_id,
        reason=reason,
    )


def get_guild_contribution_ranking(guild_id, scope="monthly", limit=30):
    init_guild_system()
    ensure_guild_monthly_season(guild_id)

    try:
        limit = int(limit)
    except Exception:
        limit = 30

    limit = max(1, min(100, limit))

    if scope == "total":
        cursor.execute("""
        SELECT gm.*,
               users.character_name,
               users.level
        FROM guild_members gm
        LEFT JOIN users ON users.user_id = gm.user_id
        WHERE gm.guild_id=?
        ORDER BY gm.contribution_score DESC,
                 gm.contribution_exp DESC,
                 gm.joined_at ASC
        LIMIT ?
        """, (guild_id, limit))
    else:
        cursor.execute("""
        SELECT gm.*,
               users.character_name,
               users.level
        FROM guild_members gm
        LEFT JOIN users ON users.user_id = gm.user_id
        WHERE gm.guild_id=?
        ORDER BY gm.monthly_contribution_score DESC,
                 gm.monthly_contribution_exp DESC,
                 gm.joined_at ASC
        LIMIT ?
        """, (guild_id, limit))

    return cursor.fetchall()


def cleanup_recalculate_all_guild_levels():
    init_guild_system()
    cursor.execute("SELECT id FROM guilds")
    rows = cursor.fetchall()
    updated = 0

    for row in rows:
        try:
            guild_id = row["id"]
        except Exception:
            guild_id = row[0]
        old = get_guild_by_id(guild_id)["level"]
        new = recalculate_guild_level(guild_id)
        if new != old:
            updated += 1

    return updated
'''

DB_APPEND = r'''

# ==============================
# ✅ GUILD PROGRESS CONTRIBUTIONS DB WRAPPERS V1
# ==============================

# 7.0.7 wrappers для Guild EXP / Resource / внеску учасників.


def get_guild_exp_required_for_level(level):
    from systems.guild_system import get_guild_exp_required_for_level as _get_guild_exp_required_for_level
    return _get_guild_exp_required_for_level(level)


def calculate_guild_level_from_exp(total_exp):
    from systems.guild_system import calculate_guild_level_from_exp as _calculate_guild_level_from_exp
    return _calculate_guild_level_from_exp(total_exp)


def get_guild_next_level_info(guild_id):
    from systems.guild_system import get_guild_next_level_info as _get_guild_next_level_info
    return _get_guild_next_level_info(guild_id)


def recalculate_guild_level(guild_id):
    from systems.guild_system import recalculate_guild_level as _recalculate_guild_level
    return _recalculate_guild_level(guild_id)


def add_user_guild_progress(user_id, exp=0, resource=0, kills=0, contracts=0, reason=""):
    from systems.guild_system import add_user_guild_progress as _add_user_guild_progress
    return _add_user_guild_progress(
        user_id=user_id,
        exp=exp,
        resource=resource,
        kills=kills,
        contracts=contracts,
        reason=reason,
    )


def get_guild_contribution_ranking(guild_id, scope="monthly", limit=30):
    from systems.guild_system import get_guild_contribution_ranking as _get_guild_contribution_ranking
    return _get_guild_contribution_ranking(guild_id=guild_id, scope=scope, limit=limit)


def cleanup_recalculate_all_guild_levels():
    from systems.guild_system import cleanup_recalculate_all_guild_levels as _cleanup_recalculate_all_guild_levels
    return _cleanup_recalculate_all_guild_levels()
'''

HANDLER_APPEND = r'''

# ==============================
# ✅ GUILD PROGRESS CONTRIBUTIONS UI V1
# ==============================

# 7.0.7
# UI для Guild EXP / Resource / внеску учасників.
# Також додає dev-команду для тесту прогресу:
# /guild_add_progress exp resource kills contracts

try:
    from db import (
        get_guild_next_level_info,
        add_user_guild_progress,
        get_guild_contribution_ranking,
        cleanup_recalculate_all_guild_levels,
    )
except Exception as _guild_progress_import_error:
    print(f"⚠️ Guild progress import failed: {_guild_progress_import_error}")


def _guild_progress_bar(percent, width=10):
    try:
        percent = float(percent)
    except Exception:
        percent = 0.0
    filled = int(round(width * max(0.0, min(100.0, percent)) / 100.0))
    return "█" * filled + "░" * (width - filled)


def guild_hall_kb(user_id):
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)

    if get_user_guild(user_id):
        kb.add("ℹ️ Інформація", "👥 Учасники")
        kb.add("📊 Внесок", "🏛 Прогрес гільдії")
        kb.add("📨 Заявки", "📜 Журнал")
        kb.add("🏆 Місячний рейтинг")
        kb.add("🏆 Рейтинг за весь час")
        kb.add("🔙 Місто")
    else:
        kb.add("🏗️ Створити гільдію")
        kb.add("📜 Переглянути гільдії")
        kb.add("🏆 Місячний рейтинг")
        kb.add("🏆 Рейтинг за весь час")
        kb.add("📨 Мої заявки")
        kb.add("🔙 Місто")

    return kb


def build_guild_progress_text(user_id):
    guild = get_user_guild(user_id)

    if not guild:
        return "❌ Ти не перебуваєш у гільдії."

    info = get_guild_next_level_info(guild["id"])
    guild = get_user_guild(user_id)  # refresh after possible level recalc

    if not info:
        return "❌ Не вдалося отримати прогрес гільдії."

    bar = _guild_progress_bar(info["progress_percent"])

    return (
        f"🏛 Прогрес гільдії\n\n"
        f"{get_guild_display_name(guild)}\n\n"
        f"Рівень: {guild['level']}\n"
        f"EXP до наступного рівня:\n"
        f"{bar} {info['progress_percent']:.1f}%\n"
        f"{info['progress_exp']}/{info['needed_exp']} EXP\n\n"
        f"Поточний сезон:\n"
        f"• EXP: {guild['monthly_exp']}\n"
        f"• Ресурс: {guild['monthly_resource']}\n"
        f"• Вбивства: {guild['monthly_kills']}\n"
        f"• Контракти: {guild['monthly_contracts']}\n"
        f"• Score: {guild['monthly_score']}\n\n"
        f"За весь час:\n"
        f"• EXP: {guild['total_exp']}\n"
        f"• Ресурс: {guild['total_resource']}\n"
        f"• Вбивства: {guild['total_kills']}\n"
        f"• Контракти: {guild['total_contracts']}\n"
        f"• Score: {guild['total_score']}"
    )


def build_guild_contribution_text(user_id, scope="monthly"):
    guild = get_user_guild(user_id)

    if not guild:
        return "❌ Ти не перебуваєш у гільдії."

    rows = get_guild_contribution_ranking(guild["id"], scope=scope, limit=30)

    if scope == "total":
        title = "📊 Внесок учасників за весь час"
    else:
        title = f"📊 Внесок учасників за місяць ({get_current_guild_season_key()})"

    text = f"{title}\n\n{get_guild_display_name(guild)}\n\n"

    if not rows:
        return text + "Поки немає учасників."

    for index, row in enumerate(rows, start=1):
        name = row["character_name"] or f"user_id={row['user_id']}"
        role_label = get_guild_role_label(row["role"])

        if scope == "total":
            score = row["contribution_score"] or 0
            exp = row["contribution_exp"] or 0
            resource = row["contribution_resource"] or 0
            kills = row["contribution_kills"] or 0
            contracts = row["contribution_contracts"] or 0
        else:
            score = row["monthly_contribution_score"] or 0
            exp = row["monthly_contribution_exp"] or 0
            resource = row["monthly_contribution_resource"] or 0
            kills = row["monthly_contribution_kills"] or 0
            contracts = row["monthly_contribution_contracts"] or 0

        text += (
            f"{index}. {role_label} {name}\n"
            f"   Score: {score} | EXP: {exp} | Ресурс: {resource}\n"
            f"   Вбивства: {kills} | Контракти: {contracts}\n"
        )

    return text.strip()


def guild_contribution_kb(user_id):
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("📊 Внесок за місяць")
    kb.add("📊 Внесок за весь час")
    kb.add("🔙 Зала Гільдій")
    return kb


def send_guild_contribution(bot, message, scope="monthly"):
    bot.send_message(
        message.chat.id,
        build_guild_contribution_text(message.from_user.id, scope),
        reply_markup=guild_contribution_kb(message.from_user.id)
    )


def send_guild_progress(bot, message):
    bot.send_message(
        message.chat.id,
        build_guild_progress_text(message.from_user.id),
        reply_markup=guild_hall_kb(message.from_user.id)
    )


try:
    _base_register_guild_handlers_before_progress_v1 = register_guild_handlers
except Exception:
    _base_register_guild_handlers_before_progress_v1 = None


def register_guild_handlers(bot):
    if _base_register_guild_handlers_before_progress_v1 is not None:
        _base_register_guild_handlers_before_progress_v1(bot)

    @bot.message_handler(func=lambda message: message.text == "🏛 Прогрес гільдії")
    def guild_progress_message(message):
        send_guild_progress(bot, message)

    @bot.message_handler(func=lambda message: message.text == "📊 Внесок")
    def guild_contribution_message(message):
        send_guild_contribution(bot, message, "monthly")

    @bot.message_handler(func=lambda message: message.text == "📊 Внесок за місяць")
    def guild_contribution_monthly_message(message):
        send_guild_contribution(bot, message, "monthly")

    @bot.message_handler(func=lambda message: message.text == "📊 Внесок за весь час")
    def guild_contribution_total_message(message):
        send_guild_contribution(bot, message, "total")

    @bot.message_handler(commands=["guild_add_progress", "dev_guild_progress"])
    def guild_add_progress_command(message):
        parts = (message.text or "").split()

        if len(parts) < 5:
            bot.send_message(
                message.chat.id,
                "Формат: /guild_add_progress EXP RESOURCE KILLS CONTRACTS\n"
                "Приклад: /guild_add_progress 100 5 1 0",
                reply_markup=guild_hall_kb(message.from_user.id)
            )
            return

        try:
            exp = int(parts[1])
            resource = int(parts[2])
            kills = int(parts[3])
            contracts = int(parts[4])
        except Exception:
            bot.send_message(message.chat.id, "❌ Значення мають бути цілими числами.", reply_markup=guild_hall_kb(message.from_user.id))
            return

        result = add_user_guild_progress(
            user_id=message.from_user.id,
            exp=exp,
            resource=resource,
            kills=kills,
            contracts=contracts,
            reason=f"DEV progress: +{exp} EXP, +{resource} resource, +{kills} kills, +{contracts} contracts"
        )

        bot.send_message(
            message.chat.id,
            result.get("message", "") + "\n\n" + build_guild_progress_text(message.from_user.id),
            reply_markup=guild_hall_kb(message.from_user.id)
        )
'''


def make_backup(root, target):
    backup_dir = root / "backup"
    backup_dir.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_name = str(target.relative_to(root)).replace("\\", "_").replace("/", "_")
    backup_path = backup_dir / f"{safe_name}_{PATCH_NAME}_{timestamp}.bak"
    backup_path.write_text(target.read_text(encoding="utf-8"), encoding="utf-8")
    return backup_path


def append_if_missing(root, target, marker, code):
    original = target.read_text(encoding="utf-8")
    if marker in original:
        return None, original, False
    backup = make_backup(root, target)
    target.write_text(original.rstrip() + "\n" + code + "\n", encoding="utf-8")
    return backup, original, True


def patch_system(root):
    target = root / "systems" / "guild_system.py"
    if not target.exists():
        raise SystemExit("❌ Не знайдено systems/guild_system.py")
    backup, original, changed = append_if_missing(root, target, SYSTEM_MARKER, SYSTEM_APPEND)
    return target, backup, original, changed


def patch_db(root):
    target = root / "db.py"
    if not target.exists():
        raise SystemExit("❌ Не знайдено db.py")
    backup, original, changed = append_if_missing(root, target, DB_MARKER, DB_APPEND)
    return target, backup, original, changed


def patch_handler(root):
    target = root / "handlers" / "guild.py"
    if not target.exists():
        raise SystemExit("❌ Не знайдено handlers/guild.py")
    backup, original, changed = append_if_missing(root, target, HANDLER_MARKER, HANDLER_APPEND)
    return target, backup, original, changed


def main():
    root = Path(__file__).resolve().parents[1]
    changed_files = []
    backups = []
    originals = []

    try:
        for patch_func in [patch_system, patch_db, patch_handler]:
            file_path, backup, original, changed = patch_func(root)
            if changed:
                changed_files.append(file_path)
                originals.append((file_path, original))
            if backup:
                backups.append(backup)

        unique_files = []
        for file_path in changed_files:
            if file_path not in unique_files:
                unique_files.append(file_path)

        for file_path in unique_files:
            py_compile.compile(str(file_path), doraise=True)

        sys.path.insert(0, str(root))
        from db import init_guild_system, cleanup_recalculate_all_guild_levels
        init_guild_system()
        updated_levels = cleanup_recalculate_all_guild_levels()

    except Exception as error:
        for file_path, original in originals:
            try:
                file_path.write_text(original, encoding="utf-8")
            except Exception:
                pass
        raise SystemExit(
            "❌ Помилка під час patch_7_0_7_guild_progress_contributions.\n"
            "Змінені файли відновлено, якщо це було можливо.\n\n"
            f"Помилка:\n{error}"
        )

    print("✅ Патч 7.0.7 Guild Progress/Contributions застосовано успішно.")

    if changed_files:
        print("\nЗмінені файли:")
        for file_path in sorted(set(str(p) for p in changed_files)):
            print(f"- {file_path}")

    if backups:
        print("\nBackup:")
        for backup in backups:
            print(f"- {backup}")

    print("\nЩо додано:")
    print("- Guild EXP / Resource counters уже виводяться в UI")
    print("- автоматичний перерахунок рівня гільдії від total EXP")
    print("- 🏛 Прогрес гільдії")
    print("- 📊 Внесок учасників за місяць")
    print("- 📊 Внесок учасників за весь час")
    print("- центральний helper add_user_guild_progress() для майбутньої інтеграції з контрактами/мобами")
    print("- DEV-команда для тесту: /guild_add_progress EXP RESOURCE KILLS CONTRACTS")

    try:
        print("\nРівні гільдій перераховано:")
        print(f"- changed: {updated_levels}")
    except Exception:
        pass

    print("\nПісля патча:")
    print("python -m py_compile .\\systems\\guild_system.py")
    print("python -m py_compile .\\db.py")
    print("python -m py_compile .\\handlers\\guild.py")
    print("і перезапусти бота.")


if __name__ == "__main__":
    main()
