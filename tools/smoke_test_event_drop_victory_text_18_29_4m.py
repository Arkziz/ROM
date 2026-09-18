# -*- coding: utf-8 -*-
import ast
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
source=(ROOT/"handlers"/"combat.py").read_text(encoding="utf-8")
tree=ast.parse(source)
helpers=[n for n in ast.walk(tree) if isinstance(n,ast.FunctionDef) and n.name=="_event_drop_victory_messages"]
assert len(helpers)==1
ns={}
exec(compile(ast.Module(body=helpers,type_ignores=[]),"helper","exec"),ns)
render=ns["_event_drop_victory_messages"]
assert render(None)==[]
assert render([])==[]
assert render([{"awarded":False,"payload":{"item_name":"X","quantity":1}}])==[]
assert render([{"awarded":True,"payload":{"item_name":"🧪 Експериментальний жетон","quantity":1}}])==["🧪 Експериментальний жетон ×1"]
assert render([{"awarded":True,"payload":{"item_name":"🧪 Експериментальний жетон","quantity":3}}])==["🧪 Експериментальний жетон ×3"]
assert 'event_drop_messages = _event_drop_victory_messages(' in source
assert 'reward.get("event_drop_results")' in source
assert 'if reward["loot_messages"] or event_drop_messages:' in source
assert '🎉 Івентна нагорода:' in source
section=source[source.index('event_drop_messages = _event_drop_victory_messages('):]
section=section[:section.index('if wear_result and wear_result.get("triggered"):')]
assert section.count('🎒 Лут не знайдено.')==1
assert 'if reward["loot_messages"] or event_drop_messages:' in section
assert 'for event_message in event_drop_messages:' in section
print("EVENT_DROP_VICTORY_TEXT_18_29_4M_OK")
