from pathlib import Path
from datetime import datetime
import py_compile
import sys

PATCH_NAME = "7_0_10_guild_cleanup_diagnostics"
SYSTEM_MARKER = "# ✅ GUILD DIAGNOSTICS CORE V1"
DB_MARKER = "# ✅ GUILD DIAGNOSTICS DB WRAPPERS V1"
HANDLER_MARKER = "# ✅ GUILD CLEANUP DIAGNOSTICS UI V1"

SYSTEM_APPEND = r'''

# ==============================
# ✅ GUILD DIAGNOSTICS CORE V1
# ==============================

# 7.0.10
# Stabilization / cleanup / diagnostics helpers.


def get_guild_pending_applications_count(guild_id):
    init_guild_system()
    cursor.execute(
        "SELECT COUNT(*) AS cnt FROM guild_applications WHERE guild_id=? AND status=?",
        (guild_id, GUILD_APPLICATION_PENDING)
    )
    row = cursor.fetchone()
    try:
        return int(row["cnt"] or 0)
    except Exception:
        return int(row[0] or 0) if row else 0


def get_user_pending_applications_count(user_id):
    init_guild_system()
    cursor.execute(
        "SELECT COUNT(*) AS cnt FROM guild_applications WHERE user_id=? AND status=?",
        (user_id, GUILD_APPLICATION_PENDING)
    )
    row = cursor.fetchone()
    try:
        return int(row["cnt"] or 0)
    except Exception:
        return int(row[0] or 0) if row else 0


def get_guild_diagnostics(user_id):
    """
    Technical diagnostics for /guild_debug.
    Safe read-only helper.
    """

    init_guild_system()

    diagnostics = {
        "user_id": user_id,
        "season_key": get_current_guild_season_key(),
        "has_guild": False,
        "guild": None,
        "member": None,
        "member_count": 0,
        "pending_applications": 0,
        "user_pending_applications": 0,
        "officer_count": 0,
        "next_level_info": None,
    }

    try:
        member = get_user_guild_member(user_id)
        diagnostics["member"] = member
        diagnostics["user_pending_applications"] = get_user_pending_applications_count(user_id)

        if not member:
            return diagnostics

        guild = get_guild_by_id(member["guild_id"])
        diagnostics["guild"] = guild
        diagnostics["has_guild"] = bool(guild)

        if guild:
            ensure_guild_monthly_season(guild["id"])
            diagnostics["member_count"] = get_guild_member_count(guild["id"])
            diagnostics["pending_applications"] = get_guild_pending_applications_count(guild["id"])

            try:
                diagnostics["officer_count"] = get_guild_officer_count(guild["id"])
            except Exception:
                diagnostics["officer_count"] = 0

            try:
                diagnostics["next_level_info"] = get_guild_next_level_info(guild["id"])
            except Exception:
                diagnostics["next_level_info"] = None

    except Exception as error:
        diagnostics["error"] = str(error)

    return diagnostics


def run_guild_sanity_cleanup():
    """
    Conservative cleanup used by /guild_fix_states and startup-compatible calls:
    - stale pending applications for players already in guilds;
    - guild levels recalculation;
    - duplicate icon/index checks if available.
    """

    result = {
        "stale_applications": None,
        "levels_recalculated": None,
        "icons_checked": False,
        "ok": True,
        "errors": [],
    }

    try:
        try:
            result["stale_applications"] = cleanup_stale_guild_applications()
        except Exception as error:
            result["errors"].append(f"cleanup_stale_guild_applications: {error}")

        try:
            result["levels_recalculated"] = cleanup_recalculate_all_guild_levels()
        except Exception as error:
            result["errors"].append(f"cleanup_recalculate_all_guild_levels: {error}")

        try:
            ensure_unique_guild_icon_index()
            result["icons_checked"] = True
        except Exception as error:
            result["errors"].append(f"ensure_unique_guild_icon_index: {error}")

    except Exception as error:
        result["ok"] = False
        result["errors"].append(str(error))

    if result["errors"]:
        result["ok"] = False

    return result
'''

DB_APPEND = r'''

# ==============================
# ✅ GUILD DIAGNOSTICS DB WRAPPERS V1
# ==============================

# 7.0.10 wrappers для diagnostics / cleanup.


def get_guild_pending_applications_count(guild_id):
    from systems.guild_system import get_guild_pending_applications_count as _get_guild_pending_applications_count
    return _get_guild_pending_applications_count(guild_id)


def get_user_pending_applications_count(user_id):
    from systems.guild_system import get_user_pending_applications_count as _get_user_pending_applications_count
    return _get_user_pending_applications_count(user_id)


def get_guild_diagnostics(user_id):
    from systems.guild_system import get_guild_diagnostics as _get_guild_diagnostics
    return _get_guild_diagnostics(user_id)


def run_guild_sanity_cleanup():
    from systems.guild_system import run_guild_sanity_cleanup as _run_guild_sanity_cleanup
    return _run_guild_sanity_cleanup()
'''

HANDLER_APPEND = r'''

# ==============================
# ✅ GUILD CLEANUP DIAGNOSTICS UI V1
# ==============================

# 7.0.10
# Stabilization / cleanup / diagnostics:
# - one central state reset;
# - global pass-through for common buttons;
# - /guild_debug;
# - /guild_fix_states.

try:
    from db import get_guild_diagnostics, run_guild_sanity_cleanup
except Exception as _guild_diag_import_error:
    print(f"⚠️ Guild diagnostics import failed: {_guild_diag_import_error}")


def reset_all_guild_ui_states(user_id):
    """
    Central state cleanup for all guild menus.
    Safe to call even if a state does not exist in this build.
    """

    for reset_func_name in [
        "reset_guild_create_state",
        "reset_guild_browse_state",
        "reset_guild_application_review_state",
        "reset_guild_member_manage_state",
        "reset_guild_logs_state",
    ]:
        try:
            globals()[reset_func_name](user_id)
        except Exception:
            pass


def get_active_guild_ui_states(user_id):
    active = []

    state_checks = [
        ("create", "get_guild_create_state"),
        ("browse", "get_guild_browse_state"),
        ("applications", "get_guild_application_review_state"),
        ("members", "get_guild_member_manage_state"),
        ("logs", "get_guild_logs_state"),
    ]

    for label, getter_name in state_checks:
        try:
            getter = globals().get(getter_name)
            if getter and getter(user_id) is not None:
                active.append(label)
        except Exception:
            pass

    return active


def format_guild_debug_text(user_id):
    try:
        diagnostics = get_guild_diagnostics(user_id)
    except Exception as error:
        return f"🧪 Guild Debug\n\n❌ Не вдалося отримати diagnostics: {error}"

    active_states = get_active_guild_ui_states(user_id)
    guild = diagnostics.get("guild")
    member = diagnostics.get("member")
    next_level = diagnostics.get("next_level_info") or {}

    text = "🧪 Guild Debug\n\n"
    text += f"User ID: {diagnostics.get('user_id')}\n"
    text += f"Season: {diagnostics.get('season_key')}\n"
    text += f"Active UI states: {', '.join(active_states) if active_states else 'none'}\n"
    text += f"User pending applications: {diagnostics.get('user_pending_applications', 0)}\n\n"

    if not guild or not member:
        text += "Guild: none\n"
        return text.strip()

    text += f"Guild ID: {guild['id']}\n"
    text += f"Guild: {get_guild_display_name(guild)}\n"
    text += f"Role: {get_guild_role_label(member['role'])}\n"
    text += f"Members: {diagnostics.get('member_count', 0)}/{guild['member_limit']}\n"
    text += f"Officers: {diagnostics.get('officer_count', 0)}\n"
    text += f"Pending applications: {diagnostics.get('pending_applications', 0)}\n\n"

    text += f"Level: {guild['level']}\n"
    if next_level:
        text += f"Level progress: {next_level.get('progress_exp', 0)}/{next_level.get('needed_exp', 0)} EXP ({next_level.get('progress_percent', 0):.1f}%)\n"

    text += "\nMonthly:\n"
    text += f"EXP: {guild['monthly_exp']} | Resource: {guild['monthly_resource']} | Kills: {guild['monthly_kills']} | Contracts: {guild['monthly_contracts']}\n"
    text += f"Score: {guild['monthly_score']}\n"

    text += "\nTotal:\n"
    text += f"EXP: {guild['total_exp']} | Resource: {guild['total_resource']} | Kills: {guild['total_kills']} | Contracts: {guild['total_contracts']}\n"
    text += f"Score: {guild['total_score']}"

    if diagnostics.get("error"):
        text += f"\n\nError: {diagnostics.get('error')}"

    return text.strip()


def format_guild_cleanup_result_text(result):
    text = "🧹 Guild Cleanup\n\n"
    text += f"Status: {'✅ OK' if result.get('ok') else '⚠️ issues'}\n"

    stale = result.get("stale_applications")
    if isinstance(stale, dict):
        text += f"Stale pending fixed: {stale.get('fixed_same_guild', 0)}\n"
        text += f"Other pending cancelled: {stale.get('cancelled_other_guild', 0)}\n"
    else:
        text += "Stale applications: n/a\n"

    text += f"Levels recalculated: {result.get('levels_recalculated')}\n"
    text += f"Icons checked: {result.get('icons_checked')}\n"

    errors = result.get("errors") or []
    if errors:
        text += "\nErrors:\n"
        for error in errors:
            text += f"- {error}\n"

    return text.strip()


def _guild_global_navigation_passthrough_v2(bot, message):
    """
    Final global pass-through for common buttons that should work even if a guild state is active.
    """

    user_id = message.from_user.id
    text = (message.text or "").strip()

    if text in ["🏰 Зала Гільдій", "🔙 Зала Гільдій"]:
        reset_all_guild_ui_states(user_id)
        open_guild_hall(bot, message.chat.id, user_id)
        return True

    if text in ["🏙️ Місто", "🔙 Місто"]:
        reset_all_guild_ui_states(user_id)
        try:
            send_city(bot, message)
        except Exception:
            try:
                from handlers.city import build_city_text
                from keyboards import city_kb
                bot.send_message(message.chat.id, build_city_text(user_id), reply_markup=city_kb())
            except Exception as error:
                bot.send_message(message.chat.id, f"❌ Не вдалося повернутися в місто: {error}", reply_markup=guild_hall_kb(user_id))
        return True

    if text == "🏛 Прогрес гільдії":
        reset_all_guild_ui_states(user_id)
        send_guild_progress(bot, message)
        return True

    if text in ["📊 Внесок", "📊 Внесок за місяць"]:
        reset_all_guild_ui_states(user_id)
        send_guild_contribution(bot, message, "monthly")
        return True

    if text == "📊 Внесок за весь час":
        reset_all_guild_ui_states(user_id)
        send_guild_contribution(bot, message, "total")
        return True

    if text == "👥 Учасники":
        reset_all_guild_ui_states(user_id)
        show_guild_members_manage(bot, message)
        return True

    if text == "📨 Заявки":
        reset_all_guild_ui_states(user_id)
        show_guild_applications(bot, message)
        return True

    if text == "📜 Журнал":
        reset_all_guild_ui_states(user_id)
        show_guild_logs(bot, message, 0)
        return True

    if text == "📜 Переглянути гільдії":
        reset_all_guild_ui_states(user_id)
        show_guild_list(bot, message, 0)
        return True

    return False


# Chain into the existing 7.0.7a global handler if present.
try:
    _base_guild_progress_handle_global_buttons_before_cleanup_v1 = _guild_progress_handle_global_guild_buttons_v1
except Exception:
    _base_guild_progress_handle_global_buttons_before_cleanup_v1 = None


def _guild_progress_handle_global_guild_buttons_v1(bot, message):
    if _guild_global_navigation_passthrough_v2(bot, message):
        return True

    if _base_guild_progress_handle_global_buttons_before_cleanup_v1 is not None:
        return _base_guild_progress_handle_global_buttons_before_cleanup_v1(bot, message)

    return False


try:
    _base_register_guild_handlers_before_cleanup_diag_v1 = register_guild_handlers
except Exception:
    _base_register_guild_handlers_before_cleanup_diag_v1 = None


def register_guild_handlers(bot):
    if _base_register_guild_handlers_before_cleanup_diag_v1 is not None:
        _base_register_guild_handlers_before_cleanup_diag_v1(bot)

    @bot.message_handler(commands=["guild_debug"])
    def guild_debug_command(message):
        bot.send_message(
            message.chat.id,
            format_guild_debug_text(message.from_user.id),
            reply_markup=guild_hall_kb(message.from_user.id)
        )

    @bot.message_handler(commands=["guild_fix_states", "guild_cleanup"])
    def guild_fix_states_command(message):
        reset_all_guild_ui_states(message.from_user.id)
        try:
            result = run_guild_sanity_cleanup()
        except Exception as error:
            result = {"ok": False, "errors": [str(error)]}

        bot.send_message(
            message.chat.id,
            format_guild_cleanup_result_text(result),
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
        from db import init_guild_system, run_guild_sanity_cleanup
        init_guild_system()
        cleanup_result = run_guild_sanity_cleanup()

    except Exception as error:
        for file_path, original in originals:
            try:
                file_path.write_text(original, encoding="utf-8")
            except Exception:
                pass
        raise SystemExit(
            "❌ Помилка під час patch_7_0_10_guild_cleanup_diagnostics.\n"
            "Змінені файли відновлено, якщо це було можливо.\n\n"
            f"Помилка:\n{error}"
        )

    print("✅ Патч 7.0.10 Guild cleanup/diagnostics застосовано успішно.")

    if changed_files:
        print("\nЗмінені файли:")
        for file_path in sorted(set(str(p) for p in changed_files)):
            print(f"- {file_path}")

    if backups:
        print("\nBackup:")
        for backup in backups:
            print(f"- {backup}")

    print("\nЩо додано:")
    print("- центральний reset_all_guild_ui_states()")
    print("- глобальний pass-through для основних кнопок Зали Гільдій")
    print("- /guild_debug")
    print("- /guild_fix_states або /guild_cleanup")
    print("- conservative sanity cleanup pending-заявок, рівнів і унікальних іконок")

    try:
        print("\nInitial cleanup result:")
        stale = cleanup_result.get("stale_applications") if isinstance(cleanup_result, dict) else None
        if isinstance(stale, dict):
            print(f"- stale fixed: {stale.get('fixed_same_guild', 0)}")
            print(f"- other pending cancelled: {stale.get('cancelled_other_guild', 0)}")
        print(f"- levels recalculated: {cleanup_result.get('levels_recalculated')}")
        print(f"- icons checked: {cleanup_result.get('icons_checked')}")
    except Exception:
        pass

    print("\nПісля патча:")
    print("python -m py_compile .\\systems\\guild_system.py")
    print("python -m py_compile .\\db.py")
    print("python -m py_compile .\\handlers\\guild.py")
    print("і перезапусти бота.")


if __name__ == "__main__":
    main()
