#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations
import ast
from pathlib import Path

SOURCE = Path("handlers/guild.py").read_text(encoding="utf-8-sig")
TREE = ast.parse(SOURCE)

def owner(name):
    matches = [n for n in TREE.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name == name]
    assert len(matches) == 1, (name, len(matches))
    return matches[0]

helper = owner("guild_applicant_profile_link_kb")
show = owner("show_guild_application_detail")
assert "ast.unparse" not in SOURCE
assert "✉️ Написати через бота" not in SOURCE
assert SOURCE.count("👤 Відкрити профіль") == 1
assert SOURCE.count("tg://user?id=") == 1
show_text = ast.get_source_segment(SOURCE, show)
assert "guild_application_detail_kb()" in show_text
assert "guild_applicant_profile_link_kb(user_id, application_id)" in show_text
assert "👤 Профіль кандидата" in show_text

module = ast.Module(body=[helper], type_ignores=[])
namespace = {}
exec(compile(ast.fix_missing_locations(module), "handlers/guild.py", "exec"), namespace)
function = namespace["guild_applicant_profile_link_kb"]

class Button:
    def __init__(self, text, url=None, callback_data=None):
        self.text, self.url, self.callback_data = text, url, callback_data
class Markup:
    def __init__(self): self.keyboard = []
    def add(self, *buttons): self.keyboard.append(list(buttons))
class Types:
    InlineKeyboardMarkup = Markup
    InlineKeyboardButton = Button
namespace["types"] = Types
namespace["_app_row_get"] = lambda row, key, fallback=None: row.get(key, fallback)

state = {"app": None, "guild": None, "allowed": False}
namespace["get_guild_application_by_id"] = lambda application_id: state["app"]
namespace["get_user_guild"] = lambda user_id: state["guild"]
namespace["can_manage_guild_applications"] = lambda user_id, guild_id: state["allowed"]

assert function(10, 1) is None
state.update(app={"id": 1, "guild_id": 2, "user_id": 777, "status": "accepted"}, guild={"id": 2}, allowed=True)
assert function(10, 1) is None
state.update(app={"id": 1, "guild_id": 3, "user_id": 777, "status": "pending"}, guild={"id": 2}, allowed=True)
assert function(10, 1) is None
state.update(app={"id": 1, "guild_id": 2, "user_id": 777, "status": "pending"}, guild={"id": 2}, allowed=False)
assert function(10, 1) is None
state.update(app={"id": 1, "guild_id": 2, "user_id": 777, "status": "pending"}, guild={"id": 2}, allowed=True)
keyboard = function(10, 1)
assert keyboard is not None
button = keyboard.keyboard[0][0]
assert button.text == "👤 Відкрити профіль"
assert button.url == "tg://user?id=777"
assert button.callback_data is None
print("GUILD_APPLICANT_PROFILE_LINK_18_XX_15_OK")
