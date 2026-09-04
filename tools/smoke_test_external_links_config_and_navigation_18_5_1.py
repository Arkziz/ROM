#!/usr/bin/env python3
from pathlib import Path
import os
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from config import _validated_external_https_url
from handlers.external_links import _external_links_kb, _external_links_text

assert _validated_external_https_url("", {"t.me"}) is None
assert _validated_external_https_url("http://t.me/example", {"t.me"}) is None
assert _validated_external_https_url("https://evil.example/x", {"t.me"}) is None
assert _validated_external_https_url("https://user:pass@t.me/x", {"t.me"}) is None
assert _validated_external_https_url("https://t.me/x#fragment", {"t.me"}) is None
assert _validated_external_https_url("https://t.me/example", {"t.me"}) == "https://t.me/example"
assert _validated_external_https_url("https://send.monobank.ua/jar/example", {"send.monobank.ua"})

empty = str(_external_links_kb({"game_chat": None, "news_channel": None, "support": None}).to_dict())
assert "Чат гри" not in empty and "Канал новин" not in empty and "Підтримати проєкт" not in empty
assert "links:close" in empty
assert "ще не налаштовані" in _external_links_text(False)

support = str(_external_links_kb({
    "game_chat": None,
    "news_channel": None,
    "support": "https://send.monobank.ua/jar/example",
}).to_dict())
assert "Підтримати проєкт" in support
assert "Чат гри" not in support and "Канал новин" not in support

all_links = str(_external_links_kb({
    "game_chat": "https://t.me/game_chat",
    "news_channel": "https://t.me/news_channel",
    "support": "https://send.monobank.ua/jar/example",
}).to_dict())
assert "Чат гри" in all_links and "Канал новин" in all_links and "Підтримати проєкт" in all_links

city = (ROOT / "handlers" / "city.py").read_text(encoding="utf-8-sig")
main = (ROOT / "main.py").read_text(encoding="utf-8-sig")
assert city.count("🔗 Корисні посилання") == 1
assert 'kb.row("📖 Про гру", "🔗 Корисні посилання")' in city
assert main.count("from handlers.external_links import register_external_links_handlers") == 1
assert main.count("register_external_links_handlers(bot)") == 1
print("PASS: URL validation, fail-closed buttons, account row and registration")
