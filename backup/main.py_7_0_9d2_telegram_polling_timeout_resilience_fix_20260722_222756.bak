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