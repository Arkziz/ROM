#!/usr/bin/env python3
import ast,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1]
main=(R/'main.py').read_text(encoding='utf-8');mp=(R/'handlers'/'map.py').read_text(encoding='utf-8')
t=ast.parse(main)
def name(n):
 if not isinstance(n,ast.Expr) or not isinstance(n.value,ast.Call):return None
 f=n.value.func;return f.id if isinstance(f,ast.Name) else None
def reg(n):
 k=name(n);return bool(k and k.startswith('register_') and k.endswith('_handlers') and n.value.args and isinstance(n.value.args[0],ast.Name) and n.value.args[0].id=='bot')
order=[name(n) for n in t.body if reg(n)]
assert order and order[0]=='register_map_handlers' and order.count('register_map_handlers')==1,order
mt=ast.parse(mp)
registrar=[n for n in ast.walk(mt) if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)) and n.name=='register_map_handlers']
assert len(registrar)==1,len(registrar)
registrar_source=ast.get_source_segment(mp,registrar[0]) or ''
assert 'render_map_message' in registrar_source
assert 'message_handler' in registrar_source
assert 'build_map_inline_kb' in mp
assert '🗺️ Мапу відкрито.' not in mp
print('[PASS] canonical Map dispatch order and renderer owner')
