#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
city = (ROOT / "handlers/city.py").read_text(encoding="utf-8")
auction = (ROOT / "handlers/auction_house.py").read_text(encoding="utf-8")
guild = (ROOT / "handlers/guild.py").read_text(encoding="utf-8")
for source in (city, auction, guild): ast.parse(source)

for source in (city, auction, guild):
    assert source.count("ROM 17.11.2 COMPACT TEXT LOCATION DESCRIPTION") == 1

assert "def location_description_kb_17_11_2" in city
assert 'callback_data="location_desc:show"' in city
assert 'callback_data="location_desc:hide"' in city
assert "bot.edit_message_text(" in city
assert "No send_message fallback" in city
assert "def build_main_menu_text(user_id, show_location_description=False)" in city
assert "description_line" in city
assert "def register_city_handlers(bot):" in city
assert "_BASE_REGISTER_CITY_HANDLERS_17_11_2(bot)" in city

assert "_BASE_BUILD_AUCTION_HOUSE_TEXT_17_11_2" in auction
assert 'stop_marker="ℹ️ Правила:"' in auction
assert 'stop_marker="Продавці приховані."' in auction

assert "_BASE_GUILD_HALL_NO_GUILD_TEXT_17_11_2" in guild
assert '"Керування:\\n"' in guild

# Protect completed Stage 17.11.1 navigation and excluded Inventory/Potion text.
assert "def trade_district_submenu_kb_17_11_1" in city
assert 'TRADE_DISTRICT_CITY_BUTTON_17_11_1 = "⬅️ Місто"' in city
inventory = (ROOT / "handlers/inventory.py").read_text(encoding="utf-8")
assert "ROM 17.11.2 COMPACT TEXT LOCATION DESCRIPTION" not in inventory
print("[PASS] Stage 17.11.2 compact text/location-description contract")
