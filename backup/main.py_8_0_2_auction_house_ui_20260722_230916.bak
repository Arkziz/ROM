
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
                print(f"⚠️ Telegram polling read timeout, restarting polling in 5s: {error}")
                _rom_polling_time.sleep(5)
                continue

            if is_connection or "Connection" in error_name or "connection" in error_text.lower():
                print(f"⚠️ Telegram polling connection error, restarting polling in 10s: {error}")
                _rom_polling_time.sleep(10)
                continue

            print(f"⚠️ Telegram polling unexpected error, restarting polling in 10s: {error}")
            _rom_polling_time.sleep(10)

import telebot

from config import TOKEN

from db import (
    init_db,
    seed_items,
    seed_location_trash_items,
    expand_bag_slots_to_40,
    init_character_class_system,
    seed_class_reset_sphere_item
)

from handlers.start import register_start_handlers
from handlers.profile import register_profile_handlers
from handlers.inventory import register_inventory_handlers
from handlers.combat import register_combat_handlers
from handlers.dev import register_dev_handlers
from handlers.map import register_map_handlers
from handlers.city import register_city_handlers
from handlers.contracts import register_contract_handlers
from handlers.daily import register_daily_handlers
from handlers.refine import register_refine_handlers
from handlers.blacksmith_repair_hotfix import register_blacksmith_repair_hotfix_handlers
from handlers.guild import register_guild_handlers

from systems.notifications import start_notification_worker


# ==============================
# BOT CONFIG
# ==============================

# threaded=False зменшує ризик конфліктів SQLite у handlers.
# Notification worker має окреме SQLite-підключення.
bot = telebot.TeleBot(TOKEN, threaded=False)


# ==============================
# DB INIT
# ==============================

init_db()
seed_items()
seed_location_trash_items()
expand_bag_slots_to_40()
init_character_class_system()
seed_class_reset_sphere_item()


# ==============================
# HANDLERS
# ==============================

register_start_handlers(bot)
register_profile_handlers(bot)
register_inventory_handlers(bot)
register_combat_handlers(bot)
register_dev_handlers(bot)
register_map_handlers(bot)
register_blacksmith_repair_hotfix_handlers(bot)
register_city_handlers(bot)
register_guild_handlers(bot)
register_contract_handlers(bot)
register_daily_handlers(bot)


register_refine_handlers(bot)
# ==============================
# NOTIFICATIONS
# ==============================

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
print("✅ BOT STARTED")

try:
    bot.infinity_polling()
except Exception as e:
    logger.critical(f"Помилка при запуску бота: {e}", exc_info=True)
    raise