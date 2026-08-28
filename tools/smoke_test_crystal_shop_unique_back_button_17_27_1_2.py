import ast,re,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1]
p=R/'handlers/crystal_shop.py';s=p.read_text(encoding='utf-8');ast.parse(s)
assert "BACK='🔙 Закрити магазин'" in s
assert "BACK='🔙 Назад'" not in s
assert 'k.add(BACK)' in s
assert 'm.text==BACK' in s
assert '_close_shop_session(bot,message.from_user.id)' in s
assert '_active_shop_callback' in s
assert 'Це меню покупки вже неактивне.' in s
print('[PASS] Stage 17.27.1.2 unique Crystal Shop back button contract')
