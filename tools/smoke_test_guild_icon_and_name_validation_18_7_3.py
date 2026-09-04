#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from pathlib import Path
import ast
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from systems.guild_system import (
    validate_guild_name_contract,
    validate_guild_icon_contract,
    validate_guild_tag_contract,
)

VALID_NAMES = (
    "Темний Легіон",
    "Dark Legion",
    "Вовча Зграя",
    "Руни-Магії",
    "Об'єднані Руни",
)
INVALID_NAMES = (
    "Dark Легіон",
    "Guild 2",
    "🔥 Легіон",
    "Ёлка",
    "A  B",
    "A--B",
    "-Guild",
    "Guild-",
)
VALID_ICONS = ("🏰", "🔥", "🐺", "⚔️", "🛡️", "🇺🇦", "😭")
INVALID_ICONS = ("A", "AB", "1", "!", "🔥🔥", "A🔥", "🔥A", "[🔥]")

for value in VALID_NAMES:
    assert validate_guild_name_contract(value)["success"], value
for value in INVALID_NAMES:
    assert not validate_guild_name_contract(value)["success"], value
for value in VALID_ICONS:
    assert validate_guild_icon_contract(value)["success"], value
for value in INVALID_ICONS:
    assert not validate_guild_icon_contract(value)["success"], value

assert validate_guild_icon_contract("")["icon"] == "🏰"
assert validate_guild_tag_contract("DLC")["success"]
assert not validate_guild_tag_contract("DL1")["success"]

system_source = (ROOT / "systems" / "guild_system.py").read_text(encoding="utf-8-sig")
handler_source = (ROOT / "handlers" / "guild.py").read_text(encoding="utf-8-sig")
system_tree = ast.parse(system_source)
handler_tree = ast.parse(handler_source)

assert len([n for n in system_tree.body if isinstance(n, ast.FunctionDef) and n.name == "validate_guild_name_contract"]) == 1
assert len([n for n in system_tree.body if isinstance(n, ast.FunctionDef) and n.name == "validate_guild_icon_contract"]) == 1
assert len([n for n in system_tree.body if isinstance(n, ast.FunctionDef) and n.name == "validate_guild_create_input"]) == 1
assert len([n for n in handler_tree.body if isinstance(n, ast.FunctionDef) and n.name == "validate_guild_icon_for_ui"]) == 1
assert "рівно один emoji" in handler_source
assert "цифри та emoji заборонені" in handler_source
assert "validate_guild_tag_contract" in system_source
print("PASS: name policy, one-emoji policy, uniqueness integration, tag regression and UI consolidation")
