import telebot

from config import TOKEN
from db import init_db, seed_items

from handlers.start import register_start_handlers
from handlers.profile import register_profile_handlers
from handlers.inventory import register_inventory_handlers
from handlers.combat import register_combat_handlers
from handlers.dev import register_dev_handlers
from handlers.map import register_map_handlers
from handlers.city import register_city_handlers


bot = telebot.TeleBot(TOKEN)

init_db()
seed_items()

register_start_handlers(bot)
register_profile_handlers(bot)
register_inventory_handlers(bot)
register_combat_handlers(bot)
register_dev_handlers(bot)
register_map_handlers(bot)
register_city_handlers(bot)

print("✅ BOT STARTED")
bot.infinity_polling()