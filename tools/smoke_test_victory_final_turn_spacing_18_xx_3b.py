#!/usr/bin/env python3
from __future__ import annotations
import ast,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
import handlers.combat
source=(ROOT/'handlers/combat.py').read_text(encoding='utf-8-sig')
tree=ast.parse(source)
functions={n.name:n for n in ast.walk(tree) if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef))}
def body(name):
 n=functions[name];return '\n'.join(source.splitlines()[n.lineno-1:n.end_lineno])
victory=body('build_victory_text');defeat=body('build_lethal_combat_log')
assert victory.count('ROM Stage 18.xx.3b')==1
assert 'while "\\n\\n\\n" in text:' in victory
assert 'повалений на землю.📈 Нагорода:' in victory
assert 'повалений на землю.\\n\\n📈 Нагорода:' in victory
assert victory.count('🏆 ВИ ПЕРЕМОГЛИ!')==1
assert victory.count('💥 ФІНАЛЬНИЙ ХІД')==1
assert '💥 ОСТАННІЙ ХІД' in defeat
sample='████████░░ 84%\n\n\n\n🌱 Рунічний паросток повалений на землю.📈 Нагорода:\n✨ Досвід'
while '\n\n\n' in sample:sample=sample.replace('\n\n\n','\n\n')
sample=sample.replace('повалений на землю.📈 Нагорода:','повалений на землю.\n\n📈 Нагорода:')
assert '84%\n\n🌱 Рунічний паросток повалений на землю.\n\n📈 Нагорода:' in sample
assert '\n\n\n' not in sample
print('VICTORY_FINAL_TURN_SPACING_18_XX_3B_OK')
