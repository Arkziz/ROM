# -*- coding: utf-8 -*-
import ast,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
source=(ROOT/"handlers"/"event_ui.py").read_text(encoding="utf-8");tree=ast.parse(source)
assert "evt:test_event_2026:" in source
assert 'm.text==EVENTS_BUTTON' in source
assert 'm.text=="🏆 Рейтинг"' not in source
assert 'c.data or "").startswith(PREFIX)' in source
assert "⏳ Івент готується. Дати проведення буде оголошено пізніше." in source
assert "✅ Підтвердити" in source and "❌ Скасувати" in source
assert 'page=max(1,min(10' in source and 'page_size=10' not in source
assert "LEFT JOIN guild_members" in source and "LEFT JOIN guilds" in source
assert 'event_active=True' in source
city=(ROOT/"handlers"/"city.py").read_text(encoding="utf-8-sig");main=(ROOT/"main.py").read_text(encoding="utf-8-sig")
assert city.count("🎉 Івенти")==1
assert main.count("register_event_ui_handlers(bot)")==1
print("TEST_EVENT_TELEGRAM_UI_18_29_4C_OK")
