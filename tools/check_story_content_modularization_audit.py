#!/usr/bin/env python3
import ast,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent
SOURCE=ROOT/'data'/'story_quest_content.py'
tree=ast.parse(SOURCE.read_text(encoding='utf-8-sig'))
rows=[]
for node in ast.walk(tree):
 if isinstance(node,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='_DATA' for t in node.targets):
  call=node.value
  if isinstance(call,ast.Call) and len(call.args)==1 and isinstance(call.args[0],ast.Constant) and isinstance(call.args[0].value,str):rows=json.loads(call.args[0].value)
assert [r['definition']['number'] for r in rows]==list(range(1,21))
assert 21 not in [r['definition']['number'] for r in rows]
print('STORY CONTENT MODULARIZATION AUDIT: PASS')
