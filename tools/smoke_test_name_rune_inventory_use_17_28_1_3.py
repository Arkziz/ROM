import ast,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1]
inv=(R/'handlers/inventory.py').read_text(encoding='utf-8');nrh=(R/'handlers/name_rune.py').read_text(encoding='utf-8');nrs=(R/'systems/name_rune_system.py').read_text(encoding='utf-8')
for s in (inv,nrh,nrs):ast.parse(s)
assert '✍️ Використати Руну імені' in inv
assert '📦 Категорія: Матеріали' in inv
assert 'name_rune_use:' in inv and 'name_rune_use:' in nrh
assert "'✍️ Руна імені'" in nrs
assert 'inventory_id' in nrh and 'Це меню вже неактивне.' in nrh
print('[PASS] Stage 17.28.1.3 inventory action and localization contract')
