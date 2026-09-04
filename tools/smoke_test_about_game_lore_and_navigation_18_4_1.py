#!/usr/bin/env python3
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from data.about_game import ABOUT_GAME_INTRO,ABOUT_GAME_SECTION_ORDER,ABOUT_GAME_SECTIONS,build_about_game_section_text
from handlers.about_game import _about_menu_kb,_section_kb
assert len(ABOUT_GAME_SECTION_ORDER)==9 and tuple(ABOUT_GAME_SECTIONS)==ABOUT_GAME_SECTION_ORDER
all_text=ABOUT_GAME_INTRO+"\n"+"\n".join(build_about_game_section_text(k) for k in ABOUT_GAME_SECTION_ORDER)
assert "Прогрес зберігається між перезапусками гри." not in all_text
for key in ABOUT_GAME_SECTION_ORDER:
 text=build_about_game_section_text(key);assert 0<len(text)<=4096;assert len(f"about:section:{key}".encode())<=64
menu=str(_about_menu_kb().to_dict());assert menu.count("about:section:")==9 and "about:close" in menu
for key in ABOUT_GAME_SECTION_ORDER:
 payload=str(_section_kb(key).to_dict());assert "about:menu" in payload and "about:close" in payload
city=(ROOT/"handlers/city.py").read_text(encoding="utf-8-sig");main=(ROOT/"main.py").read_text(encoding="utf-8-sig")
assert city.count("📖 Про гру")==1;assert main.count("from handlers.about_game import register_about_game_handlers")==1;assert main.count("register_about_game_handlers(bot)")==1
print("PASS: nine sections, Telegram limits, navigation and registration")
