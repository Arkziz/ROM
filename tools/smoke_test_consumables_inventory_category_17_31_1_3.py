import ast
from pathlib import Path
R=Path(__file__).resolve().parents[1];s=(R/'handlers/inventory.py').read_text(encoding='utf-8');ast.parse(s)
assert 'def get_category_items(user_id, category_key):' in s
assert 'item_id == 50000 or item_type == "consumable" or category == "consumable"' in s
assert '🧰 Категорія: Витратні предмети' in s
assert '📦 У цьому стакі: ×{quantity}/10' in s
assert '✅ Корисно використати зараз: до ×{useful_now}' in s
assert 'Зайві артефакти не списуються' in s
print('[PASS] Stage 17.31.1.3 consumables filter and artifact description contracts')
