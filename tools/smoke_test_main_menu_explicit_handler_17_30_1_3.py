import ast
from pathlib import Path
R = Path(__file__).resolve().parents[1]
city = (R / "handlers/city.py").read_text(encoding="utf-8")
shop = (R / "handlers/crystal_shop.py").read_text(encoding="utf-8")
ast.parse(city)
ast.parse(shop)
assert city.count('== "📋 Меню"') == 1
assert "open_main_menu_17_30_1_3" in city
assert "build_main_menu_text(message.from_user.id)" in city
assert "reply_markup=main_kb()" in city
assert "💎 Premium: активний" in city
assert "m.text==MENU_BUTTON" not in shop
assert "m.text==SHOP_BUTTON" in shop
assert "m.text==BACK" in shop
print("[PASS] Stage 17.30.1.3 explicit Main Menu handler contract")
