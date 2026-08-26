#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import ast
from pathlib import Path
R = Path(__file__).resolve().parents[1]
GUILD = R / "handlers/guild.py"
DB_INIT = R / "db_modules/__init__.py"
WRAPPERS = R / "db_modules/systems_wrappers.py"
source = GUILD.read_text(encoding="utf-8")
tree = ast.parse(source, filename=str(GUILD))
imports = [n for n in tree.body if isinstance(n, ast.ImportFrom) and n.module == "db"]
assert sum(1 for n in imports for a in n.names if a.name == "get_character_name_by_user_id" and a.asname is None) == 1
assert source.count("ROM 17.21.3.2.3.4 KICK CONFIRMATION DB NEUTRAL SMOKE RECOVERY") == 1
members = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "handle_guild_member_manage_message"]
assert len(members) == 3
assert any(isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == "get_character_name_by_user_id" for n in ast.walk(members[1]))
assert not any(isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == "kick_guild_member" for n in ast.walk(members[1]))
wrapper_source = WRAPPERS.read_text(encoding="utf-8")
wrapper_tree = ast.parse(wrapper_source, filename=str(WRAPPERS))
assert len([n for n in wrapper_tree.body if isinstance(n, ast.FunctionDef) and n.name == "get_character_name_by_user_id"]) == 1
init_source = DB_INIT.read_text(encoding="utf-8")
init_tree = ast.parse(init_source, filename=str(DB_INIT))
exports=[]
for n in ast.walk(init_tree):
    if isinstance(n,(ast.List,ast.Tuple,ast.Set)):
        exports.extend(e.value for e in n.elts if isinstance(e,ast.Constant) and isinstance(e.value,str))
assert "get_character_name_by_user_id" in exports
print("[PASS] Stage 17.21.3.2.3.4 character-name import and DB-neutral smoke contract")
