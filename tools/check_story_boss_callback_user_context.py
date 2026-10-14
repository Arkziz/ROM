#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""DB-free callback-user delegation regression."""
import ast
from pathlib import Path
from types import SimpleNamespace
ROOT=Path(__file__).resolve().parents[1]
source_path=ROOT/"handlers/story_boss_invocation_wiring.py"
source=source_path.read_text(encoding="utf-8")
tree=ast.parse(source)
functions=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in {"_delegate_invoke"}]
assert len(functions)==1
namespace={"SimpleNamespace":SimpleNamespace,"_canonical_call_handler":None}
exec(compile(ast.Module(body=functions,type_ignores=[]),str(source_path),"exec"),namespace)
seen=[]
def canonical(message):seen.append(message)
namespace["_canonical_call_handler"]=lambda bot:canonical
player=SimpleNamespace(id=777)
bot_author=SimpleNamespace(id=999)
chat=SimpleNamespace(id=123)
source_message=SimpleNamespace(from_user=bot_author,chat=chat,text="card",message_id=55,date=1,content_type="text")
call=SimpleNamespace(from_user=player,message=source_message)
namespace["_delegate_invoke"](SimpleNamespace(),call)
assert len(seen)==1
adapted=seen[0]
assert adapted.from_user is player
assert adapted.from_user.id==777
assert adapted.from_user.id!=source_message.from_user.id
assert adapted.chat is chat
assert adapted.message_id==55
assert "handler(source_message)" not in source
assert "handler(player_message)" in source
print("STORY BOSS CALLBACK USER CONTEXT: PASS")
