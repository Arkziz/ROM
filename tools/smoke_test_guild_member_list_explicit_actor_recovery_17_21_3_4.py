#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import ast
from pathlib import Path
R = Path(__file__).resolve().parents[1]
P = R / "handlers/guild.py"
source = P.read_text(encoding="utf-8")
tree = ast.parse(source, filename=str(P))

def defs(name):
    return [n for n in tree.body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)) and n.name==name]

def call_name(node):
    if isinstance(node,ast.Name): return node.id
    if isinstance(node,ast.Attribute):
        owner=call_name(node.value)
        return f"{owner}.{node.attr}" if owner else node.attr
    return ""

def calls(node,suffix):
    return [n for n in ast.walk(node) if isinstance(n,ast.Call) and call_name(n.func).endswith(suffix)]

assert source.count("ROM 17.21.3.4 GUILD MEMBER LIST EXPLICIT ACTOR RECOVERY")==1
assert len(defs("show_guild_members_manage"))==2
assert len(defs("send_guild_members_manage_for_actor_17_21_3_4"))==1
assert len(defs("register_guild_handlers"))==6
helper=defs("send_guild_members_manage_for_actor_17_21_3_4")[0]
assert [a.arg for a in helper.args.args]==["bot","chat_id","user_id"]
assert len(calls(helper,"build_guild_member_manage_text"))==1
assert len(calls(helper,"guild_members_manage_kb"))==1
active=defs("show_guild_members_manage")[-1]
assert len(calls(active,"send_guild_members_manage_for_actor_17_21_3_4"))==1
callbacks=[]
for register in defs("register_guild_handlers"):
    callbacks += [n for n in register.body if isinstance(n,ast.FunctionDef) and n.name=="guild_kick_confirmation_callback_17_21_3_2"]
assert len(callbacks)==1
cb=callbacks[0]
assert len(calls(cb,"kick_guild_member"))==1
cb_text=ast.get_source_segment(source,cb) or ""
assert "show_guild_members_manage(bot, call.message)" not in cb_text
assert "send_guild_members_manage_for_actor_17_21_3_4(bot, call.message.chat.id, user_id)" in cb_text
print("[PASS] Stage 17.21.3.4 explicit actor rendering contract")
