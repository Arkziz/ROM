#!/usr/bin/env python3
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
text=(ROOT/'handlers'/'inventory.py').read_text(encoding='utf-8')
required=(
 '⚙️ Ефект:',
 '🛒 Придбання:',
 'можна придбати у Рунного Майстра за золото.',
 'можна придбати в Магазині кристалів за 20 кристалів.',
 'повертає 1 випадкову вставлену руну в інвентар;',
 'повертає всі вставлені руни в інвентар;',
)
for value in required: assert value in text,value
for stale in ('Майбутній ефект:','стане доступним у Рунного Майстра після впровадження вилучення рун.','поки не продається і не випадає звичайним гравцям.'):
 assert stale not in text,stale
assert text.count('🛒 Придбання:')==2
print('[PASS] extractor inventory descriptions use one current normalized format')
