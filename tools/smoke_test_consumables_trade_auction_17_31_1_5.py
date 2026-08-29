import ast
from pathlib import Path
R=Path(__file__).resolve().parents[1]
files={p:(R/p).read_text(encoding='utf-8') for p in ('handlers/player_interaction.py','systems/player_interaction_system.py','handlers/auction_house.py','systems/auction_house_system.py')}
for s in files.values():ast.parse(s)
assert '"consumable": "🧰 Витратні предмети"' in files['handlers/player_interaction.py']
assert ':consumable:0' in files['handlers/player_interaction.py']
assert '"consumable")' in files['systems/player_interaction_system.py']
assert 'AUCTION_CATEGORY_CONSUMABLE = "consumable"' in files['systems/auction_house_system.py']
assert 'item_id", 0) or 0) == 50000' in files['systems/auction_house_system.py']
assert files['handlers/auction_house.py'].count('🧰 Витратні предмети') >= 4
print('[PASS] Stage 17.31.1.5 trade and auction consumables category contracts')
