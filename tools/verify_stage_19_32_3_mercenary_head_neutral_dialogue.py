#!/usr/bin/env python3
from pathlib import Path
import ast
ROOT=Path(__file__).resolve().parents[1]
p=ROOT/"handlers/city.py"
s=p.read_text(encoding="utf-8-sig")
ast.parse(s)
assert "def build_story_mercenary_head_neutral_text" in s
assert "Зараз окремих вказівок немає" in s
assert "⚔️ Інші справи Гільдії Найманців:" not in s
block=s[s.index("def show_story_mercenary_head"):s.index("@bot.message_handler",s.index("def show_story_mercenary_head")+1)]
assert "build_story_mercenary_head_neutral_text()" in block
assert "send_story_npc_if_present(bot, message, 'mercenary_head')" in block
print("PASS: Stage 19.32.3")
