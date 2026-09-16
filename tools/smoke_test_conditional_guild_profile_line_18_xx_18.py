#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations
import ast
from pathlib import Path

TARGET = Path("db_modules/systems_wrappers.py")
source = TARGET.read_text(encoding="utf-8-sig")
tree = ast.parse(source)
owners = [
    node for node in tree.body
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    and node.name == "get_user_guild_profile_line"
]
assert len(owners) == 1, len(owners)
helper = owners[0]
returns = [node for node in ast.walk(helper) if isinstance(node, ast.Return)]
constant_returns = [
    node.value.value for node in returns
    if isinstance(node.value, ast.Constant) and isinstance(node.value.value, str)
]
assert constant_returns.count("") == 1, constant_returns
assert "🏰 Гільдія: Без гільдії\n" not in constant_returns
joined = "\n".join(
    node.value for node in ast.walk(helper)
    if isinstance(node, ast.Constant) and isinstance(node.value, str)
)
assert "🏰 Гільдія:" in joined
assert "Без гільдії" not in joined
assert "icon" in {node.id for node in ast.walk(helper) if isinstance(node, ast.Name)}
assert "tag" in {node.id for node in ast.walk(helper) if isinstance(node, ast.Name)}

# Execute only the isolated helper AST with a controlled fake guild system.
module = ast.Module(body=[helper], type_ignores=[])
compiled = compile(ast.fix_missing_locations(module), str(TARGET), "exec")
namespace = {}
exec(compiled, namespace)
function = namespace["get_user_guild_profile_line"]

class FakeGuildSystem:
    def __init__(self, guild):
        self.guild = guild
    def get_user_guild(self, user_id):
        return self.guild

namespace["_guild_system"] = lambda: FakeGuildSystem(None)
assert function(1001) == ""

namespace["_guild_system"] = lambda: FakeGuildSystem({"icon": "🐉", "tag": "TAG"})
assert function(1002) == "🏰 Гільдія: 🐉 [TAG]\n"

namespace["_guild_system"] = lambda: FakeGuildSystem({"icon": "", "tag": ""})
assert function(1003) == "🏰 Гільдія: 🏰 [???]\n"

print("CONDITIONAL_GUILD_PROFILE_LINE_18_XX_18_OK")
