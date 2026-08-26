#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations
import ast
import hashlib
import sys
from pathlib import Path
R = Path(__file__).resolve().parents[1]
P = R / "handlers/guild.py"
source = P.read_text(encoding="utf-8")
tree = ast.parse(source, filename=str(P))

def defs(name):
    return [n for n in tree.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name == name]

def call_name(node):
    if isinstance(node, ast.Name): return node.id
    if isinstance(node, ast.Attribute):
        p=call_name(node.value); return f"{p}.{node.attr}" if p else node.attr
    return ""

def calls(node, suffix):
    return [n for n in ast.walk(node) if isinstance(n, ast.Call) and call_name(n.func).endswith(suffix)]

def names(node):
    targets=node.targets if isinstance(node,ast.Assign) else [node.target]
    return [t.id for t in targets if isinstance(t,ast.Name)]

assert source.count("ROM 17.21.3.2.1 KICK CONFIRMATION HANDLER HASH NEWLINE RECOVERY") == 1
members=defs("handle_guild_member_manage_message")
registers=defs("register_guild_handlers")
keyboards=defs("guild_hall_kb")
assert (len(members),len(registers),len(keyboards)) == (3,6,2)
inactive=ast.get_source_segment(source,members[0]) or ""
inactive=inactive.replace("\r\n","\n").replace("\r","\n")
assert hashlib.sha256(inactive.encode("utf-8")).hexdigest() == "796add7b4c53db6644da2137c57b318d5e9426d1091864cc38cec8f632b5103c"
bindings=[]
for n in ast.walk(tree):
    if isinstance(n,(ast.Assign,ast.AnnAssign)) and "_base_handle_guild_member_manage_message_before_progress_order_v1" in names(n):
        if isinstance(n.value,ast.Name) and n.value.id=="handle_guild_member_manage_message": bindings.append(n)
assert len(bindings)==1
active=max((n for n in members if n.end_lineno < bindings[0].lineno),key=lambda n:n.lineno)
assert active is members[1]
assert not calls(active,"kick_guild_member")
helpers=defs("guild_kick_confirmation_kb_17_21_3_2")
assert len(helpers)==1
final_register=registers[-1]
callbacks=[n for n in final_register.body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)) and n.name=="guild_kick_confirmation_callback_17_21_3_2"]
assert len(callbacks)==1
callback=callbacks[0]
assert len(calls(callback,"kick_guild_member"))==1
cb=ast.get_source_segment(source,callback) or ""
assert cb.find('action == "guild_kick_cancel"') < cb.find("kick_guild_member(user_id, target_user_id)")
kb=ast.get_source_segment(source,keyboards[-1]) or ""
assert kb.count('kb.row("🏆 Місячний рейтинг", "🏆 Рейтинг за весь час")')==2
assert 'kb.add("🏆 Місячний рейтинг")' not in kb
assert 'kb.add("🏆 Рейтинг за весь час")' not in kb
print("[PASS] Stage 17.21.3.2.1 kick confirmation handler hash/newline contract")
