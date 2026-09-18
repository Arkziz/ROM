# -*- coding: utf-8 -*-
import ast
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
source=(ROOT/"handlers"/"combat.py").read_text(encoding="utf-8")
tree=ast.parse(source)
node=[n for n in ast.walk(tree) if isinstance(n,ast.FunctionDef) and n.name=="_event_drop_victory_messages"]
assert len(node)==1
ns={}
exec(compile(ast.Module(body=node,type_ignores=[]),"helper","exec"),ns)
render=ns["_event_drop_victory_messages"]
success={"payload":{"item_id":4000,"quantity":1},"result":{"success":True,"name":"🧪 Експериментальний жетон","added":1,"lost":0}}
failed={"payload":{"item_id":4000,"quantity":1},"result":{"success":False,"name":"🧪 Експериментальний жетон","added":0,"lost":1}}
assert render((success,))==["🧪 Експериментальний жетон ×1"]
assert render((failed,))==[]
helper=ast.get_source_segment(source,node[0]) or ""
for token in ('entry.get("result")','award_result.get("success")','award_result.get("added"','award_result.get("name")'):
    assert token in helper, token
assert "add_item(" not in helper
assert 'reward.get("event_drop_results")' in source
assert '🎉 Івентна нагорода:' in source
print("EVENT_DROP_RESULT_CONTRACT_18_29_4N_OK")
