#!/usr/bin/env python3
import ast
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
source=(ROOT/'handlers'/'city.py').read_text(encoding='utf-8');tree=ast.parse(source)
helpers=[n for n in tree.body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)) and n.name=='_format_registration_date_kyiv_18_31_4a']
assert len(helpers)==1,len(helpers)
ns={}
exec(compile(ast.Module(body=[helpers[0]],type_ignores=[]),'<helper>','exec'),ns)
f=ns['_format_registration_date_kyiv_18_31_4a']
assert f('2026-09-21T23:05:00+00:00')=='22.09.2026 02:05 за Києвом'
assert f('21.09.2026 23:05 UTC')=='22.09.2026 02:05 за Києвом'
assert f('2026-01-15T12:00:00+00:00')=='15.01.2026 14:00 за Києвом'
assert f('')=='не зафіксована'
assert f('broken')=='не зафіксована'
joined=[]
for n in ast.walk(tree):
 if isinstance(n,ast.JoinedStr):joined.append(ast.get_source_segment(source,n) or '')
registration_joined=[x for x in joined if 'Дата реєстрації:' in x]
assert len(registration_joined)==2,registration_joined
assert all('_format_registration_date_kyiv_18_31_4a' in x for x in registration_joined),registration_joined
requirements=(ROOT/'requirements.txt').read_text(encoding='utf-8').lower()
assert 'tzdata' in requirements
print('[PASS] registration date renders Europe/Kyiv with DST, rollover and fallback')
