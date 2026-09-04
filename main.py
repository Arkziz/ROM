
# ROM 17.20.1.1 CRITICAL PRODUCTION LOGGING PRINT CONTRACT RECOVERY
from systems.production_logging import configure_production_logging, get_production_logger, production_log_print as PRODUCTION_LOG_PRINT
from systems.fresh_database_bootstrap import run_fresh_database_schema_bootstrap
configure_production_logging()
PRODUCTION_LOGGER=get_production_logger('rom.main')

# ✅ TELEGRAM POLLING TIMEOUT RESILIENCE V3
import time as _rom_polling_time

try:
    import requests as _rom_polling_requests
except Exception:
    _rom_polling_requests = None

try:
    from telebot import apihelper as _rom_polling_apihelper
except Exception:
    _rom_polling_apihelper = None

if _rom_polling_apihelper is not None:
    try:
        _rom_polling_apihelper.READ_TIMEOUT = 60
        _rom_polling_apihelper.CONNECT_TIMEOUT = 15
    except Exception:
        pass


def run_bot_polling_resilient(bot):
    """
    Keeps Telegram polling alive after temporary network timeouts.
    """
    while True:
        try:
            run_bot_polling_resilient(bot)
        except Exception as error:
            error_name = type(error).__name__
            error_text = str(error)

            is_timeout = False
            is_connection = False

            if _rom_polling_requests is not None:
                try:
                    is_timeout = isinstance(error, _rom_polling_requests.exceptions.ReadTimeout)
                    is_connection = isinstance(error, _rom_polling_requests.exceptions.ConnectionError)
                except Exception:
                    pass

            if is_timeout or "Read timed out" in error_text or "ReadTimeout" in error_name:
                PRODUCTION_LOG_PRINT(PRODUCTION_LOGGER, 'warning', f"⚠️ Telegram polling read timeout, restarting polling in 5s: {error}")
                _rom_polling_time.sleep(5)
                continue

            if is_connection or "Connection" in error_name or "connection" in error_text.lower():
                PRODUCTION_LOG_PRINT(PRODUCTION_LOGGER, 'warning', f"⚠️ Telegram polling connection error, restarting polling in 10s: {error}")
                _rom_polling_time.sleep(10)
                continue

            PRODUCTION_LOG_PRINT(PRODUCTION_LOGGER, 'warning', f"⚠️ Telegram polling unexpected error, restarting polling in 10s: {error}")
            _rom_polling_time.sleep(10)

import telebot

from config import TOKEN

from db import (
    init_db,
    seed_items,
    seed_location_trash_items,
    expand_bag_slots_to_40,
    init_character_class_system,
    init_class_reset_sphere
)
from db import run_db_startup_maintenance
from db import init_rune_system

from handlers.start import register_start_handlers
from handlers.profile import register_profile_handlers
from handlers.inventory import register_inventory_handlers
from handlers.fatigue_artifact import register_fatigue_artifact_handlers
from systems.fatigue_artifact_system import init_fatigue_artifact_system
from handlers.combat import register_combat_handlers
from handlers.dev import register_dev_handlers
from handlers.map import register_map_handlers
from handlers.city import register_city_handlers
from handlers.about_game import register_about_game_handlers
from handlers.contracts import register_contract_handlers
from handlers.daily import register_daily_handlers
from handlers.refine import register_refine_handlers
from handlers.runes import register_rune_handlers, register_rune_fusion_handlers, register_simple_rune_extractor_handlers, register_rune_master_shop_handlers
from handlers.blacksmith import register_blacksmith_repair_hotfix_handlers
from handlers.guild import register_guild_handlers
from handlers.auction_house import register_auction_house_handlers
from handlers.blacksmith_repair_confirm import register_blacksmith_repair_confirmation_handlers
from handlers.crystal_shop import register_crystal_shop_handlers
from handlers.admin_crystal_credit import register_admin_crystal_credit_handlers
from handlers.player_rankings import register_player_rankings_handlers
from handlers.timed_exp_bonus import register_timed_exp_bonus_handlers
from systems.timed_exp_bonus_system import init_timed_exp_bonus_system
from handlers.name_rune import register_name_rune_handlers
from systems.name_rune_system import init_name_rune_system
from systems.crystal_shop_system import init_crystal_shop_system
from systems.crystal_bag_expansion_system import init_crystal_bag_expansion_system

from systems.notifications import start_notification_worker
from systems.telegram_rate_limit import install_global_telegram_rate_limit_guard


# ==============================
# BOT CONFIG
# ==============================

# threaded=False зменшує ризик конфліктів SQLite у handlers.
# Notification worker має окреме SQLite-підключення.
bot = telebot.TeleBot(TOKEN, threaded=False)


# ==============================
# DB INIT
# ==============================

# ROM 12.1.0 PLAYER PRESENCE AND ACTIVITY SESSIONS
from systems.player_interaction_system import init_player_interaction_foundation, install_player_presence_tracking, cleanup_player_interaction_state, init_player_trade_foundation, init_player_trade_item_policy_and_reservations, recover_active_player_trades_after_restart
init_db()

# Stage 18.1.0-a.0-b: deterministic schema owners before handlers/polling.
_fresh_schema_bootstrap_result = run_fresh_database_schema_bootstrap()
print(f"✅ FRESH DATABASE SCHEMA BOOTSTRAP: {_fresh_schema_bootstrap_result}")
PRODUCTION_LOG_PRINT(PRODUCTION_LOGGER, 'info', '✅ PLAYER INTERACTION FOUNDATION:', init_player_interaction_foundation())
# ROM 12.3.2 INTERACTION SESSION TIMEOUT AND RECOVERY
PRODUCTION_LOG_PRINT(PRODUCTION_LOGGER, 'info', '✅ PLAYER INTERACTION RECOVERY:', cleanup_player_interaction_state())
# ROM 12.4.0 PLAYER TRADE DATABASE AND HISTORY FOUNDATION
PRODUCTION_LOG_PRINT(PRODUCTION_LOGGER, 'info', '✅ PLAYER TRADE FOUNDATION:', init_player_trade_foundation())
# ROM 12.5.0 PLAYER TRADE ITEM POLICY AND RESERVATIONS
PRODUCTION_LOG_PRINT(PRODUCTION_LOGGER, 'info', '✅ PLAYER TRADE ITEM POLICY:', init_player_trade_item_policy_and_reservations())
# ROM 12.6.5: process restarts invalidate all unfinished trade UI/input state.
_PLAYER_TRADE_RESTART_RECOVERY = recover_active_player_trades_after_restart()
PRODUCTION_LOG_PRINT(PRODUCTION_LOGGER, 'info', '✅ PLAYER TRADE RESTART RECOVERY:', _PLAYER_TRADE_RESTART_RECOVERY)

# ==============================
# ✅ REFACTOR 9.0.11: RUN MIGRATIONS ON STARTUP
# ==============================
try:
    import db as _rom_db_for_migrations
    _migration_result = _rom_db_for_migrations.run_pending_migrations()
    if _migration_result.get("applied"):
        PRODUCTION_LOG_PRINT(PRODUCTION_LOGGER, 'info', f"✅ DB MIGRATIONS APPLIED: {_migration_result.get('applied')}")
except Exception as migration_error:
    PRODUCTION_LOG_PRINT(PRODUCTION_LOGGER, 'warning', f"⚠️ DB migrations skipped/error: {migration_error}")

_db_startup_maintenance_result = run_db_startup_maintenance()
if _db_startup_maintenance_result.get("success"):
    PRODUCTION_LOG_PRINT(PRODUCTION_LOGGER, 'info', f"✅ DB STARTUP MAINTENANCE: {_db_startup_maintenance_result}")

_rune_system_init_result = init_rune_system()
if _rune_system_init_result.get("success"):
    PRODUCTION_LOG_PRINT(PRODUCTION_LOGGER, 'info', f"✅ RUNE SYSTEM DATA MODEL: {_rune_system_init_result}")

seed_items()
seed_location_trash_items()
expand_bag_slots_to_40()
init_character_class_system()
init_class_reset_sphere()


# ==============================
# HANDLERS
# ==============================

init_crystal_shop_system()
init_crystal_bag_expansion_system()
init_timed_exp_bonus_system()
init_name_rune_system()
init_fatigue_artifact_system()

register_crystal_shop_handlers(bot)
register_admin_crystal_credit_handlers(bot)
register_player_rankings_handlers(bot)
register_timed_exp_bonus_handlers(bot)
register_start_handlers(bot)
register_profile_handlers(bot)
register_inventory_handlers(bot)
register_fatigue_artifact_handlers(bot)
register_combat_handlers(bot)
register_dev_handlers(bot)
register_map_handlers(bot)
register_blacksmith_repair_confirmation_handlers(bot)
register_blacksmith_repair_hotfix_handlers(bot)
register_about_game_handlers(bot)
register_city_handlers(bot)
register_guild_handlers(bot)
register_auction_house_handlers(bot)
register_contract_handlers(bot)
register_daily_handlers(bot)
register_rune_handlers(bot)
register_rune_fusion_handlers(bot)
register_simple_rune_extractor_handlers(bot)
register_rune_master_shop_handlers(bot)


register_refine_handlers(bot)
register_name_rune_handlers(bot)
# ==============================
# NOTIFICATIONS
# ==============================


# ==============================
# ROM 11.9.1 GLOBAL TELEGRAM 429 GUARD
# Installed after every handler so it remains the outermost bot API wrapper.
# Installed before the notification worker so worker sends are protected too.
# ==============================
install_global_telegram_rate_limit_guard(bot)

PRODUCTION_LOG_PRINT(PRODUCTION_LOGGER, 'info', '✅ PLAYER PRESENCE TRACKER:', install_player_presence_tracking(bot))
# ROM 12.2.0 MAP LOCATION PLAYER DISCOVERY
from handlers.player_interaction import register_player_interaction_handlers
register_player_interaction_handlers(bot)
# ROM 12.6.5: replace the stale Telegram ReplyKeyboard for every participant
# whose unfinished trade was cancelled during startup recovery.
from keyboards import main_kb as _player_trade_recovery_main_kb
for _trade_recovery_user_id in _PLAYER_TRADE_RESTART_RECOVERY.get('participant_user_ids', []):
    try:
        bot.send_message(
            int(_trade_recovery_user_id),
            "⚠️ Попередній обмін скасовано через перезапуск бота.\n\n"
            "Предмети та резервування повернено.",
            reply_markup=_player_trade_recovery_main_kb(),
        )
    except Exception as _trade_recovery_notify_error:
        PRODUCTION_LOG_PRINT(PRODUCTION_LOGGER, 'warning', f"⚠️ PLAYER TRADE RESTART NOTICE FAILED: "
            f"user={_trade_recovery_user_id}, error={_trade_recovery_notify_error}")
start_notification_worker(bot)


# ==============================
# START BOT
# ==============================

import logging

# Налаштовуємо логування
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

logger = logging.getLogger(__name__)
PRODUCTION_LOG_PRINT(PRODUCTION_LOGGER, 'info', "✅ BOT STARTED")

try:
    bot.infinity_polling()
except Exception as e:
    logger.critical(f"Помилка при запуску бота: {e}", exc_info=True)
    raise

# ✅ ROM 9.0.8d MAIN REPAIR CONFIRMATION ORDER FIX
# Repair confirmation handlers are registered before old hotfix/city handlers.
