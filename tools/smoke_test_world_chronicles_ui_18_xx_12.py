# -*- coding: utf-8 -*-
from __future__ import annotations

import ast
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from handlers.world_chronicles import build_world_chronicles_text, world_chronicles_kb

empty = {"items": [], "page": 0, "has_previous": False, "has_next": False}
empty_text = build_world_chronicles_text(empty)
assert "📜 ХРОНІКИ СВІТУ" in empty_text
assert "Важливих подій поки немає." in empty_text
empty_keyboard = world_chronicles_kb(empty)
empty_buttons = [button for row in empty_keyboard.keyboard for button in row]
assert [button.text for button in empty_buttons] == ["🔄 Оновити", "🔙 Назад"]

middle = {
    "items": [
        {
            "event_type": "player_level_up",
            "actor_name_snapshot": "Мандрівник",
            "subject_name_snapshot": None,
            "metadata_json": '{"level": 7}',
            "created_at": "2026-09-16T20:00:00+00:00",
        }
    ],
    "page": 1,
    "has_previous": True,
    "has_next": True,
}
middle_text = build_world_chronicles_text(middle)
assert "Мандрівник досяг 7 рівня." in middle_text
assert "Сторінка 2" in middle_text
middle_keyboard = world_chronicles_kb(middle)
middle_buttons = [button for row in middle_keyboard.keyboard for button in row]
assert [button.text for button in middle_buttons] == ["◀️", "▶️", "🔄 Оновити", "🔙 Назад"]
assert [button.callback_data for button in middle_buttons] == ["wc:page:0", "wc:page:2", "wc:refresh", "wc:back"]

city_source = (PROJECT_ROOT / "handlers" / "city.py").read_text(encoding="utf-8-sig")
main_source = (PROJECT_ROOT / "main.py").read_text(encoding="utf-8-sig")
ast.parse(city_source)
ast.parse(main_source)
assert city_source.count("📜 Хроніки світу") == 1
assert main_source.count("from handlers.world_chronicles import register_world_chronicle_handlers") == 1
assert main_source.count("register_world_chronicle_handlers(bot)") == 1

print("WORLD_CHRONICLES_UI_18_XX_12_OK")
