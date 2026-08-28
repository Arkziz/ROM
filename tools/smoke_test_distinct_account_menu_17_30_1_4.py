import ast
from pathlib import Path
R=Path(__file__).resolve().parents[1];city=(R/'handlers/city.py').read_text(encoding='utf-8');shop=(R/'handlers/crystal_shop.py').read_text(encoding='utf-8')
ast.parse(city);ast.parse(shop)
assert 'def build_account_menu_text_17_30_1_4' in city
assert 'def account_menu_kb_17_30_1_4' in city
assert 'build_account_menu_text_17_30_1_4(message.from_user.id)' in city
assert 'reply_markup=account_menu_kb_17_30_1_4()' in city
assert 'return _BUILD_MAIN_MENU_TEXT_BEFORE_EXP_BONUS_STATUS_17_30_1_1' in city
assert city.count('💎 Магазин кристалів') >= 1
assert "kb.add(\"🔙 Назад\")" in city
assert 'from handlers.city import build_account_menu_text_17_30_1_4' in shop
assert "m.text==SHOP_BUTTON" in shop and "m.text==BACK" in shop
assert "m.text==MENU_BUTTON" not in shop
print('[PASS] Stage 17.30.1.4 distinct account Menu and shop submenu contracts')
