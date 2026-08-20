#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
source = (ROOT / "handlers/city.py").read_text(encoding="utf-8")
tree = ast.parse(source)

assert source.count("ROM 17.11.2.1 CITY CRAFT TAVERN TEXT CLEANUP") == 1
assert "def build_city_text(user_id):" in source
assert "Перед тобою центральна площа табору мандрівників" in source
assert "дороги торговців, ремісників і шукачів пригод" in source
assert "поповнити припаси та дізнатися" in source
assert "def build_craft_district_text(user_id):" in source
assert 'marker = "\\n\\nДоступні місця:\\n"' in source
assert "def build_tavern_text():" in source
assert 'marker = "\\n\\nℹ️ Пізніше тут можна буде додати:\\n"' in source

# Inspect the last active definitions, which override the earlier legacy builders.
active = {}
for node in tree.body:
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
        active[node.name] = ast.get_source_segment(source, node) or ""
for name in ("build_city_text", "build_craft_district_text", "build_tavern_text"):
    assert name in active, name

city = active["build_city_text"]
assert "Куди підеш?" not in city
assert "Торговий ряд — купівля та продаж" not in city
assert "Ремісничий квартал — коваль і алхімік" not in city

craft = active["build_craft_district_text"]
assert "Доступні місця" in craft  # removal marker, not output content
assert "_BASE_BUILD_CRAFT_DISTRICT_TEXT_17_11_2_1" in craft

tavern = active["build_tavern_text"]
assert "Пізніше тут можна буде додати" in tavern  # removal marker, not output content
assert "_BASE_BUILD_TAVERN_TEXT_17_11_2_1" in tavern

# Protect completed Stage 17.11 navigation and description toggle.
assert "def trade_district_submenu_kb_17_11_1" in source
assert "def build_base_equipment_return_view_17_11_1_1" in source
assert "def location_description_kb_17_11_2" in source
assert 'callback_data="location_desc:show"' in source
assert 'callback_data="location_desc:hide"' in source
print("[PASS] Stage 17.11.2.1 City/Craft/Tavern text cleanup contract")
