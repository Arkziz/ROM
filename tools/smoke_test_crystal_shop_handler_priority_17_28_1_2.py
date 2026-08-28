import ast,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1];s=(R/'main.py').read_text(encoding='utf-8');ast.parse(s)
assert s.count('register_crystal_shop_handlers(bot)')==1
assert s.index('register_crystal_shop_handlers(bot)') < s.index('register_start_handlers(bot)')
assert s.index('register_crystal_shop_handlers(bot)') < s.index('register_inventory_handlers(bot)')
assert s.index('register_crystal_shop_handlers(bot)') < s.index('register_city_handlers(bot)')
assert s.index('register_crystal_shop_handlers(bot)') < s.index('register_player_interaction_handlers(bot)')
assert 'register_name_rune_handlers(bot)' in s
print('[PASS] Stage 17.28.1.2 Crystal Shop handler priority contract')
