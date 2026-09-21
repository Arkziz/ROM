#!/usr/bin/env python3
import ast,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
path=ROOT/'handlers'/'map.py';source=path.read_text(encoding='utf-8');tree=ast.parse(source)
def pass_only(node):
 body=[x for x in node.body if not (isinstance(x,ast.Expr) and isinstance(x.value,ast.Constant) and isinstance(x.value.value,str))]
 return len(body)==1 and isinstance(body[0],ast.Pass)
empty=[n.name for n in ast.walk(tree) if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)) and n.decorator_list and pass_only(n)]
assert not empty,empty
assert '🗺️ Мапа світу' in source
assert 'Доступні напрямки:' in source
import handlers.map
print('[PASS] Stage 18.31.2 empty handler removed and canonical map renderer remains')
